import logging
from concurrent import futures
from typing import Any, Callable, Dict, List, Tuple

from botocove.cove_session import CoveSession
from botocove.cove_types import CoveFunctionOutput

logger = logging.getLogger(__name__)


class CoveRunner(object):

    # """
    # docs
    # """

    def __init__(
        self,
        valid_sessions: List[CoveSession],
        func: Callable,
        raise_exception: bool,
        func_args: Any,
        func_kwargs: Any,
    ) -> None:
        self.sessions = valid_sessions
        self.raise_exception = raise_exception
        self.cove_wrapped_func = func
        self.func_args = func_args
        self.func_kwargs = func_kwargs

    def run_cove_function(self) -> CoveFunctionOutput:
        # Run decorated func with all valid sessions
        results, exceptions = self._async_boto3_call()
        return CoveFunctionOutput(
            Results=results,
            Exceptions=exceptions,
        )

    def wrap_func(
        self,
        account_session: CoveSession,
    ) -> Dict[str, Any]:
        # Wrapper capturing exceptions and formatting results
        try:
            result = self.cove_wrapped_func(
                account_session, *self.func_args, **self.func_kwargs
            )
            return account_session.format_cove_result(result)
        except Exception as e:
            if self.raise_exception is True:
                account_session.store_exception(e)
                logger.exception(account_session.format_cove_error())
                raise
            else:
                account_session.store_exception(e)
                return account_session.format_cove_error()

    def _async_boto3_call(
        self,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        completed = []
        with futures.ThreadPoolExecutor() as executor:
            for result in executor.map(self.wrap_func, self.sessions):
                completed.append(result)

        successful_results = [
            result for result in completed if not result.get("ExceptionDetails")
        ]
        exceptions = [result for result in completed if result.get("ExceptionDetails")]
        return successful_results, exceptions
