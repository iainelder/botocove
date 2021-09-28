import functools
import logging
from typing import Any, Callable, List, Optional

from boto3.session import Session

from botocove.cove_runner import CoveRunner
from botocove.cove_sessions import CoveSessions
from botocove.cove_types import CoveOutput

logger = logging.getLogger(__name__)


def cove(
    _func: Optional[Callable] = None,
    *,
    target_ids: Optional[List[str]] = None,
    ignore_ids: Optional[List[str]] = None,
    rolename: Optional[str] = None,
    role_session_name: Optional[str] = None,
    assuming_session: Optional[Session] = None,
    raise_exception: bool = False,
    org_master: bool = True,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> CoveOutput:
            valid_sessions, invalid_sessions = CoveSessions(
                target_ids=target_ids,
                ignore_ids=ignore_ids,
                rolename=rolename,
                role_session_name=role_session_name,
                org_master=org_master,
                assuming_session=assuming_session,
            ).get_cove_sessions()

            runner = CoveRunner(
                valid_sessions=valid_sessions,
                func=func,
                raise_exception=raise_exception,
                func_args=args,
                func_kwargs=kwargs,
            )

            output = runner.run_cove_function()
            return CoveOutput(
                FailedAssumeRole=invalid_sessions,
                Results=output["Results"],
                Exceptions=output["Exceptions"],
            )

        return wrapper

    # Handle both bare decorator and with argument
    if _func is None:
        return decorator
    else:
        return decorator(_func)
