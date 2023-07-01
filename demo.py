import inspect
import os
import sys
from argparse import ArgumentParser
from boto3.session import Session
from botocove import cove
from pprint import pprint


def use_standard_boto3_credential_chain():
    """
    The wrapper uses the default session, which gets its profile and region from
    the AWS_PROFILE and AWS_DEFAULT_REGION environment variables.
    
    The session passed to the wrapped function has the same region.
    """

    @cove(target_ids=[os.environ["COVE_TARGET_ACCOUNT"]])
    def _use_standard_boto3_credential_chain(session: Session) -> str:
        return call_regional_api(session)

    return _use_standard_boto3_credential_chain()


def use_assuming_session():
    """
    The wrapper uses the assuming session, which gets its profile and region
    from the non-standard COVE_ASSUMING_PROFILE and COVE_ASSUMING_REGION
    environment variables.

    The session passed to the wrapped function has no region set.
    """
    @cove(
        target_ids=[os.environ["COVE_TARGET_ACCOUNT"]],
        assuming_session=Session(
            profile_name=os.environ.get("COVE_ASSUMING_PROFILE"),
            region_name=os.environ.get("COVE_ASSUMING_REGION"),
        )
    )
    def _use_assuming_session(session: Session) -> str:
        return call_regional_api(session)
    
    return _use_assuming_session()


def call_regional_api(session: Session) -> str:
    error = None
    try:
        session.client("ec2").describe_availability_zones()
    except Exception as ex:
        error = ex
    return {
        "Caller": inspect.stack()[1].function,
        "Region": session.region_name,
        "Error": error
    }


parser = ArgumentParser()
parser.add_argument("mode", choices=["use_standard_boto3_credential_chain", "use_assuming_session"])
args = parser.parse_args()

if args.mode == "use_standard_boto3_credential_chain":
    output = use_standard_boto3_credential_chain()
elif args.mode == "use_assuming_session":
    output = use_assuming_session()

# Strip everything from the output except the result of function passed to cove.
for group in output.values():
    for result in group:
        for k in list(result.keys()):
            if k not in ["Result", "ExceptionDetails"]:
                del result[k]

pprint(output)
