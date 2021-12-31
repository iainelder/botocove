from concurrent import futures
import sys
from itertools import filterfalse, tee
from typing import Callable, Tuple

from botocove.cove_runner import CoveRunner, tqdm
from botocove.cove_types import CoveResults, CoveSessionInformation


class MultiThreadedListCoveRunner(CoveRunner):
    pass


class MultiThreadedGenCoveRunner(CoveRunner):
    def _async_boto3_call(
        self,
    ) -> Tuple[CoveResults, CoveResults]:
        with futures.ThreadPoolExecutor(max_workers=20) as executor:
            completed: CoveResults = tqdm(
                executor.map(self.cove_exception_wrapper_func, self.sessions),
                total=len(self.sessions),
                desc="Executing function",
                colour="#ff69b4",  # hotpink
            )

        successful_results, exceptions = partition(
            lambda r: bool(r.ExceptionDetails), completed
        )

        return successful_results, exceptions


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


class MonoThreadedGenCoveRunner(CoveRunner):
    def _async_boto3_call(
        self,
    ) -> Tuple[CoveResults, CoveResults]:
        completed: CoveResults = tqdm(
            map(self.cove_exception_wrapper_func, self.sessions),
            total=len(self.sessions),
            desc="Executing function",
            colour="#ff69b4",  # hotpink
        )

        successful_results, exceptions = partition(
            lambda r: bool(r.ExceptionDetails), completed
        )

        return successful_results, exceptions


def partition(
    pred: Callable[[CoveSessionInformation], bool], iterable: CoveResults
) -> Tuple[CoveResults, CoveResults]:
    "Use a predicate to partition entries into false entries and true entries."
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)


ALL_RUNNERS = {
    MultiThreadedListCoveRunner,
    MultiThreadedGenCoveRunner,
    MonoThreadedListCoveRunner,
    MonoThreadedGenCoveRunner,
}


def main() -> None:
    option = sys.argv[1]
    {"--list-runners": list_runners}[option]()


def list_runners() -> None:
    for runner_name in (runner.__name__ for runner in ALL_RUNNERS):
        print(runner_name)


if __name__ == "__main__":
    main()
