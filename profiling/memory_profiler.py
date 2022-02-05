from multiprocessing import Process
from time import perf_counter, sleep
from typing import Any, Callable, Dict, Generator, List, NamedTuple

import matplotlib.pyplot as plt  # type:ignore
import psutil
from matplotlib.figure import Figure  # type:ignore


class MemoryLog(NamedTuple):
    timestamp: float
    rss: int


Profile = List[MemoryLog]

ProfileSuite = Dict[str, Profile]

Profilable = Callable[[], Any]

ProcessProfiler = Callable[[Process], Profile]


def run_process_and_log_memory(pr: Process) -> Profile:

    # A simplification of watsonic's precise timer.
    # https://stackoverflow.com/a/28034554/111424
    def ticker() -> Generator[float, None, None]:
        t = perf_counter()
        while True:
            t += 0.25
            yield t - perf_counter()

    logs = []
    t0 = perf_counter()
    pr.start()
    tick = ticker()

    while pr.is_alive():
        ts = perf_counter() - t0
        rss = psutil.Process(pr.pid).memory_info().rss
        logs.append(MemoryLog(timestamp=ts, rss=rss))
        sleep(next(tick))

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
