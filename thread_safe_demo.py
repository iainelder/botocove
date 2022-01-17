from concurrent import futures
from functools import partial
import botocove
from tqdm import tqdm
from botocove.cove_decorator import dataclass_converter
from profiling.util import partition
from pprint import pprint


def whoami(session):
    result = session.client("sts").get_caller_identity()
    del result["ResponseMetadata"]
    return result


def query(session_factory, target):
    
    session = session_factory(target)

    if not session.assume_role_success:
        return session.format_cove_error()
    
    runner = botocove.cove_runner.CoveRunner(valid_sessions=[session], func=whoami, raise_exception=False, func_args=(), func_kwargs={})
    
    return runner.cove_exception_wrapper_func(session)


def partition_result_streams(results):
    
    successful_results, exceptions = partition(
        lambda r: bool(r.ExceptionDetails), results
    )

    invalid_sessions, exceptions = partition(
        lambda r: r.AssumeRoleSuccess, exceptions
    )

    return successful_results, exceptions, invalid_sessions


def format_output(results):

    successful_results, exceptions, invalid_sessions = partition_result_streams(results)

    return botocove.cove_types.CoveOutput(
        FailedAssumeRole=[dataclass_converter(f) for f in invalid_sessions],
        Results=[dataclass_converter(r) for r in successful_results],
        Exceptions=[dataclass_converter(e) for e in exceptions],
    )


def main():

  session_factory = botocove.cove_sessions.CoveSessions(target_ids=None, ignore_ids=None, rolename=None, role_session_name=None, assuming_session=None, org_master=False)
  
  targets = session_factory._gather_org_assume_targets()
  
  targets |= set(["111111111111"])

  query_with_session_factory = partial(query, session_factory._cove_session_factory)
  
  with futures.ThreadPoolExecutor(max_workers=20) as executor:
      results = list(
          tqdm(
              executor.map(query_with_session_factory, targets),
              total=len(targets),
              desc="Querying organization",
              colour="#39ff14",  # neon green
          )
      )
  
  pprint(format_output(results))


if __name__ == "__main__":
    main()
