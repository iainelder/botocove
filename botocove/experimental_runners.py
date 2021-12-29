from typing import Tuple

from botocove.cove_runner import CoveRunner, tqdm
from botocove.cove_types import CoveResults


class MultiThreadedListCoveRunner(CoveRunner):
    pass


class MonoThreadedListCoveRunner(CoveRunner):
    def _async_boto3_call(
        self,
    ) -> Tuple[CoveResults, CoveResults]:
        completed: CoveResults = list(
            tqdm(
                map(self.cove_exception_wrapper_func, self.sessions),
                total=len(self.sessions),
                desc="Executing function",
                colour="#ff69b4",  # hotpink
            )
        )

        successful_results = [
            result for result in completed if not result.ExceptionDetails
        ]
        exceptions = [result for result in completed if result.ExceptionDetails]
        return successful_results, exceptions


ALL_RUNNERS = [
    MultiThreadedListCoveRunner,
    MonoThreadedListCoveRunner,
]
