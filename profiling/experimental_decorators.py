from concurrent import futures
from util import partition
import functools
from typing import Any, Callable, List, Optional, Type

from boto3 import Session
from tqdm import tqdm

from botocove.cove_runner import CoveRunner
from botocove.cove_sessions import CoveSessions
from botocove.cove_types import CoveOutput, R
from botocove.cove_decorator import cove, dataclass_converter

def two_phase_cove(*args, **kwargs):
    return cove(*args, **kwargs)


def one_phase_cove(
    _func: Optional[Callable[..., R]] = None,
    *,
    target_ids: Optional[List[str]] = None,
    ignore_ids: Optional[List[str]] = None,
    rolename: Optional[str] = None,
    role_session_name: Optional[str] = None,
    assuming_session: Optional[Session] = None,
    raise_exception: bool = False,
    org_master: bool = True,
    runner_impl: Type[CoveRunner] = CoveRunner,
    sessions_impl: Type[CoveSessions] = CoveSessions,
) -> Callable:
    def decorator(func: Callable[..., R]) -> Callable[..., CoveOutput]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> CoveOutput:

            targets = CoveSessions(
                target_ids=target_ids,
                ignore_ids=ignore_ids,
                rolename=rolename,
                role_session_name=role_session_name,
                assuming_session=assuming_session,
                org_master=org_master,
            )._resolve_target_accounts(target_ids)

            query_with_func = functools.partial(query, func)
            
            with futures.ThreadPoolExecutor(max_workers=20) as executor:
                results = list(
                    tqdm(
                        executor.map(query_with_func, targets),
                        total=len(targets),
                        desc="Querying organization",
                        colour="#39ff14",  # neon green
                    )
                )
            
            return format_output(results)

        return wrapper

    # Handle both bare decorator and with argument
    if _func is None:
        return decorator
    else:
        return decorator(_func)


def query(func, target):
    
    session_factory = CoveSessions(
        target_ids=None,
        ignore_ids=None,
        rolename=None,
        role_session_name=None,
        assuming_session=None,
        org_master=False
    )._cove_session_factory

    session = session_factory(target)

    if not session.assume_role_success:
        return session.format_cove_error()
    
    runner = CoveRunner(
        valid_sessions=[session],
        func=func,
        raise_exception=False,
        func_args=(),
        func_kwargs={}
    )
    
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

    return CoveOutput(
        FailedAssumeRole=[dataclass_converter(f) for f in invalid_sessions],
        Results=[dataclass_converter(r) for r in successful_results],
        Exceptions=[dataclass_converter(e) for e in exceptions],
    )
