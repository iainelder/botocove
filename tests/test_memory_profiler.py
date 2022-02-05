from math import isclose
from multiprocessing import Process
from time import perf_counter, sleep
from typing import List

import pytest

from profiling.memory_profiler import profile

TIMING_ABSOLUTE_TOLERANCE = 0.01


@pytest.fixture()
def null_process() -> Process:
    return Process()


@pytest.fixture()
def sleep_for_1_sec() -> Process:
    return Process(target=lambda: sleep(1))


def alloc_a_lot() -> List[int]:
    mem = []
    t0 = perf_counter()
    while perf_counter() - t0 < 1:
        mem += [0] * 32

    return mem


def dealloc_a_lot(mem: List[int]) -> None:
    while len(mem) > 0:
        del mem[-16:]


@pytest.fixture()
def allocate_for_1_sec() -> Process:
    return Process(target=alloc_a_lot)


@pytest.fixture()
def deallocate_to_zero() -> Process:
    return Process(target=dealloc_a_lot, args=([0] * (10 ** 8),))


def test_process_is_executed(null_process: Process) -> None:
    profile(null_process)
    assert null_process.exitcode is not None


def test_null_process_has_single_log(null_process: Process) -> None:
    logs = profile(null_process)
    assert len(logs) == 1


def test_first_process_timestamp_is_zero(null_process: Process) -> None:
    logs = profile(null_process)
    assert isclose(logs[0].timestamp, 0.0, abs_tol=TIMING_ABSOLUTE_TOLERANCE)


def test_raises_error_for_started_process(null_process: Process) -> None:
    null_process.start()
    with pytest.raises(AssertionError, match="cannot start a process twice"):
        profile(null_process)


def test_process_logs_every_quarter_second(sleep_for_1_sec: Process) -> None:
    logs = profile(sleep_for_1_sec)

    expected = [0.0, 0.25, 0.5, 0.75, 1.0]

    for log, et in zip(logs, expected):
        assert isclose(log.timestamp, et, abs_tol=TIMING_ABSOLUTE_TOLERANCE)


def test_stops_logging_when_process_exits(sleep_for_1_sec: Process) -> None:
    logs = profile(sleep_for_1_sec)
    assert len(logs) == 5


def test_logs_process_increasing_memory(allocate_for_1_sec: Process) -> None:
    logs = profile(allocate_for_1_sec)

    # Don't check the last one. Somtimes the deallocation takes long
    # enough to be logged, and so the last log shows less memory than
    # the one before it.
    assert len(logs) > 2
    for i in range(len(logs) - 2):
        assert logs[i].rss < logs[i + 1].rss


def test_logs_process_decreasing_memory(deallocate_to_zero: Process) -> None:
    logs = profile(deallocate_to_zero)

    assert len(logs) > 1
    for i in range(len(logs) - 1):
        assert logs[i].rss > logs[i + 1].rss


def test_logs_a_function() -> None:
    def fn() -> None:
        return None

    logs = profile(fn)

    assert len(logs) > 0


@pytest.mark.slow()
def test_timer_does_not_drift() -> None:

    expected = [ts / 4 for ts in range(0, 1 + 4 * 60)]
    sleep_for_1_min = Process(target=lambda: sleep(60))
    logs = profile(sleep_for_1_min)

    for log, et in zip(logs, expected):
        assert isclose(log.timestamp, et, abs_tol=TIMING_ABSOLUTE_TOLERANCE)
