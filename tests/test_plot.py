from datetime import timedelta

import pytest

from plot import cpu_timedelta


def test_empty() -> None:
    with pytest.raises(ValueError, match="%H:%S.%f"):
        cpu_timedelta("")


def test_junk() -> None:
    with pytest.raises(ValueError, match="%H:%S.%f"):
        cpu_timedelta("notatime")


def test_zero() -> None:
    assert cpu_timedelta("0:00.00") == timedelta(0)


def test_millis() -> None:
    assert cpu_timedelta("0:00.35") == timedelta(milliseconds=350)


def test_seconds() -> None:
    assert cpu_timedelta("0:07.42") == timedelta(seconds=7, milliseconds=420)


def test_minutes() -> None:
    assert cpu_timedelta("1:23.45") == timedelta(
        minutes=1, seconds=23, milliseconds=450
    )
