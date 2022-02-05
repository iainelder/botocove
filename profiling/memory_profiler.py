from multiprocessing import Process
from time import perf_counter, sleep
from typing import Any, Callable, Dict, Generator, List, NamedTuple

import matplotlib.pyplot as plt  # type:ignore
import psutil
from matplotlib.figure import Figure  # type:ignore


class MemoryLog(NamedTuple):
    timestamp: float
    rss: int


SimpleFunction = Callable[[], Any]

Profile = Dict[str, List[MemoryLog]]

Profiler = Callable[[SimpleFunction], Profile]


def profile(*profilable: SimpleFunction) -> Profile:

    if len(profilable) == 0:
        raise ValueError("needs at least one function")

    proc: Process = Process(target=profilable[0])

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

    return {profilable[0].__name__: logs}


def plot(suite: Profile) -> Figure:  # type:ignore

    if not suite:
        raise ValueError("needs at least one profile")

    figure = plt.figure()

    for profile_name, profile in suite.items():
        plt.plot(*zip(*profile), label=profile_name)  # type:ignore

    figure.axes[0].legend()  # type:ignore

    return figure
