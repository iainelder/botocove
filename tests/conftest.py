import logging

import pytest
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from profiling.memory_profiler import MemoryLog, Profile


@pytest.fixture(autouse=True)
def _set_log_level(caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: MonkeyPatch) -> None:
    env_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    # Setting bad credentials invalidates file-based credentials too
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials
    for env_var in env_vars:
        monkeypatch.setenv(env_var, "broken_not_real_profile")


# TODO Find somewhere better to put these.
@pytest.fixture()
def mock_profile_1() -> Profile:
    return [
        MemoryLog(timestamp=0, rss=0),
        MemoryLog(timestamp=0.25, rss=500),
        MemoryLog(timestamp=0.5, rss=1000),
    ]


@pytest.fixture()
def mock_profile_2() -> Profile:
    return [
        MemoryLog(timestamp=0, rss=0),
        MemoryLog(timestamp=0.33, rss=125),
        MemoryLog(timestamp=0.67, rss=250),
    ]
