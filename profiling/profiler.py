from multiprocessing import Process
from time import perf_counter, sleep
from typing import Any, Callable, Dict, Generator, List, NamedTuple

import psutil


class MemoryLog(NamedTuple):
    timestamp: float
    rss: int


SimpleFunction = Callable[[], Any]

Profile = Dict[str, List[MemoryLog]]

Profiler = Callable[[SimpleFunction], Profile]


def profile(*profilable: SimpleFunction) -> Profile:

    if len(profilable) == 0:
        raise ValueError("needs at least one function")

    return {fn.__name__: _profile_process(Process(target=fn)) for fn in profilable}


def _profile_process(proc: Process) -> List[MemoryLog]:

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
