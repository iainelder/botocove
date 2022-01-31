from contextlib import contextmanager
from multiprocessing import Process
from time import perf_counter, sleep
from typing import Generator, List, NamedTuple

# FIXME: "module is installed, but missing library stubs or py.typed marker  [import]""
import psutil  # type:ignore

from botocove.cove_host_account import CoveHostAccount


@contextmanager
def allow_duplicate_target_ids() -> Generator[None, None, None]:
    def allow_duplicates_and_dont_ignore(
        self: CoveHostAccount, target_ids: List[str]
    ) -> List[str]:
        return target_ids

    original_impl = CoveHostAccount._resolve_target_accounts

    # Ignore incompatible callable return types: `Set[str]` and `List[str]`.
    # In practice they are compatible as sized iterables.
    # Ignore assigning a callable.
    CoveHostAccount._resolve_target_accounts = (  # type:ignore
        allow_duplicates_and_dont_ignore  # type:ignore
    )

    yield

    # Ignore assigning a callable.
    CoveHostAccount._resolve_target_accounts = original_impl  # type:ignore


class MemoryLog(NamedTuple):
    timestamp: float
    rss: int


def run_process_and_log_memory(pr: Process) -> List[MemoryLog]:

    logs = []
    t0 = perf_counter()
    pr.start()

    while pr.is_alive():
        ts = perf_counter() - t0
        rss = psutil.Process(pr.pid).memory_info().rss
        logs.append(MemoryLog(timestamp=ts, rss=rss))
        sleep(0.25)

    return logs
