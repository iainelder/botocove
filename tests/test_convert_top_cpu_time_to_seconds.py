from datetime import timedelta

import pytest

from plot import convert_top_cpu_time_to_seconds


def test_empty() -> None:
    instr = ""
    with pytest.raises(ValueError, match=f"time data '{instr}' does not match format '%M:%S\.%f'"):
        convert_top_cpu_time_to_seconds(instr)


def test_junk() -> None:
    instr = "notatime"
    with pytest.raises(ValueError, match=f"time data '{instr}' does not match format '%M:%S\.%f'"):
        convert_top_cpu_time_to_seconds(instr)


def test_zero() -> None:
    assert convert_top_cpu_time_to_seconds("0:00.00") == 0.0


def test_millis() -> None:
    assert convert_top_cpu_time_to_seconds("0:00.35") == 0.35


def test_seconds() -> None:
    assert convert_top_cpu_time_to_seconds("0:07.42") == 7.42


def test_minutes() -> None:
    assert convert_top_cpu_time_to_seconds("1:23.45") == 83.45
