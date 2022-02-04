from contextlib import contextmanager
from multiprocessing import Process
from time import perf_counter, sleep
from typing import Any, Callable, Dict, Generator, List, NamedTuple

import matplotlib.pyplot as plt  # type:ignore
import psutil
from matplotlib.figure import Figure  # type:ignore

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


Profile = List[MemoryLog]

ProfileSuite = Dict[str, Profile]

Profilable = Callable[[], Any]

ProcessProfiler = Callable[[Process], Profile]


def run_process_and_log_memory(pr: Process) -> Profile:

    logs = []
    memory_info = psutil.Process(pr.pid).memory_info

    t0 = perf_counter()
    pr.start()

    while pr.is_alive():
        ts = perf_counter() - t0
        rss = memory_info().rss
        logs.append(MemoryLog(timestamp=ts, rss=rss))
        sleep(0.25)

    return logs


def profile_function(
    fn: Profilable, profiler: ProcessProfiler = run_process_and_log_memory
) -> Profile:
    return profiler(Process(target=fn))


def profile_suite(
    *suite: Profilable, profiler: ProcessProfiler = run_process_and_log_memory
) -> ProfileSuite:
    if len(suite) == 0:
        raise ValueError("needs at least one function")
    return {fn.__name__: profile_function(fn, profiler=profiler) for fn in suite}


def plot(suite: ProfileSuite) -> Figure:  # type:ignore

    if not suite:
        raise ValueError("needs at least one profile")

    figure = plt.figure()

    for profile_name, profile in suite.items():
        plt.plot(*zip(*profile), label=profile_name)  # type:ignore

    figure.axes[0].legend()  # type:ignore

    return figure
