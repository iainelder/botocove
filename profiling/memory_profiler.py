from multiprocessing import Process
from time import perf_counter, sleep
from typing import Any, Callable, Dict, Generator, List, NamedTuple, Union

import matplotlib.pyplot as plt  # type:ignore
import psutil
from matplotlib.figure import Figure  # type:ignore


class MemoryLog(NamedTuple):
    timestamp: float
    rss: int


Profile = List[MemoryLog]

ProfileSuite = Dict[str, Profile]

SimpleFunction = Callable[[], Any]

Profilable = Union[Process, SimpleFunction]

Profiler = Callable[[Profilable], Profile]


def profile(profilable: Profilable) -> Profile:

    proc: Process = _proc(profilable)

    # A simplification of watsonic's precise timer.
    # https://stackoverflow.com/a/28034554/111424
    def ticker() -> Generator[float, None, None]:
        t = perf_counter()
        while True:
            t += 0.25
            yield t - perf_counter()

    logs = []
    t0 = perf_counter()
    proc.start()
    tick = ticker()

    while proc.is_alive():
        ts = perf_counter() - t0
        rss = psutil.Process(proc.pid).memory_info().rss
        logs.append(MemoryLog(timestamp=ts, rss=rss))
        sleep(next(tick))

    return logs


def _proc(proc_or_callable: Profilable) -> Process:
    if callable(proc_or_callable):
        return Process(target=proc_or_callable)
    return proc_or_callable


def profile_suite(*suite: SimpleFunction, profiler: Profiler = profile) -> ProfileSuite:
    if len(suite) == 0:
        raise ValueError("needs at least one function")
    return {fn.__name__: profiler(fn) for fn in suite}


def plot(suite: ProfileSuite) -> Figure:  # type:ignore

    if not suite:
        raise ValueError("needs at least one profile")

    figure = plt.figure()

    for profile_name, profile in suite.items():
        plt.plot(*zip(*profile), label=profile_name)  # type:ignore

    figure.axes[0].legend()  # type:ignore

    return figure
