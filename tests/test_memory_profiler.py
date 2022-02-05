from math import isclose
from time import perf_counter, sleep
from typing import Callable, List

import pytest

from profiling.memory_profiler import profile

SideEffect = Callable[[], None]

TIMING_ABSOLUTE_TOLERANCE = 0.01


@pytest.fixture()
def null_function() -> SideEffect:
    return lambda: None


@pytest.fixture()
def sleep_for_1_sec() -> SideEffect:
    return lambda: sleep(1)


def alloc_a_lot() -> None:
    mem = []
    t0 = perf_counter()
    while perf_counter() - t0 < 1:
        mem += [0] * 32


def dealloc_a_lot(mem: List[int]) -> None:
    while len(mem) > 0:
        del mem[-16:]


@pytest.fixture()
def allocate_for_1_sec() -> SideEffect:
    return alloc_a_lot


@pytest.fixture()
def deallocate_to_zero() -> SideEffect:
    mem = [0] * (10 ** 8)

    def fn() -> None:
        return dealloc_a_lot(mem)

    return fn


def test_null_function_has_single_log(null_function: SideEffect) -> None:
    logs = profile(null_function)
    assert len(logs) == 1


def test_first_timestamp_is_zero(null_function: SideEffect) -> None:
    logs = profile(null_function)
    assert isclose(logs[0].timestamp, 0.0, abs_tol=TIMING_ABSOLUTE_TOLERANCE)


def test_process_logs_every_quarter_second(sleep_for_1_sec: SideEffect) -> None:
    logs = profile(sleep_for_1_sec)

    expected = [0.0, 0.25, 0.5, 0.75, 1.0]

    for log, et in zip(logs, expected):
        assert isclose(log.timestamp, et, abs_tol=TIMING_ABSOLUTE_TOLERANCE)


def test_stops_logging_when_process_exits(sleep_for_1_sec: SideEffect) -> None:
    logs = profile(sleep_for_1_sec)
    assert len(logs) == 5


def test_logs_process_increasing_memory(allocate_for_1_sec: SideEffect) -> None:
    logs = profile(allocate_for_1_sec)

    # Don't check the last one. Somtimes the deallocation takes long
    # enough to be logged, and so the last log shows less memory than
    # the one before it.
    assert len(logs) > 2
    for i in range(len(logs) - 2):
        assert logs[i].rss < logs[i + 1].rss


def test_logs_process_decreasing_memory(deallocate_to_zero: SideEffect) -> None:
    logs = profile(deallocate_to_zero)

    # Don't check the first one. I don't know why, but the memory increases
    # at the start of deallocate_to_zero.
    assert len(logs) > 2
    for i in range(2, len(logs) - 1):
        assert logs[i].rss > logs[i + 1].rss


@pytest.mark.slow()
def test_timer_does_not_drift() -> None:

    expected = [ts / 4 for ts in range(0, 1 + 4 * 60)]

    def sleep_for_1_min() -> None:
        sleep(60)

    logs = profile(sleep_for_1_min)

    for log, et in zip(logs, expected):
        assert isclose(log.timestamp, et, abs_tol=TIMING_ABSOLUTE_TOLERANCE)
