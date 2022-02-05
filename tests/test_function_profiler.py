import inspect

import pytest

from profiling.memory_profiler import (
    Profilable,
    Profile,
    Profiler,
    profile,
    profile_suite,
)


@pytest.fixture()
def mock_profiler(mock_profile_1: Profile, mock_profile_2: Profile) -> Profiler:
    """
    This profiler when called alternates between two mock profiles.
    """

    def p(_: Profilable) -> Profile:
        nonlocal mock_profile_1, mock_profile_2
        mock_profile_1, mock_profile_2 = mock_profile_2, mock_profile_1
        return mock_profile_2

    return p


def test_profile_suite_no_args() -> None:
    with pytest.raises(ValueError, match="needs at least one function"):
        profile_suite()


def test_profile_suite_uses_run_process_by_default() -> None:
    default = inspect.signature(profile_suite).parameters["profiler"].default
    assert default == profile


def test_profile_suite_one_fn(mock_profile_1: Profile, mock_profiler: Profiler) -> None:
    def fn() -> None:
        pass

    suite = profile_suite(fn, profiler=mock_profiler)
    assert suite == {"fn": mock_profile_1}


def test_profile_suite_many_fns(
    mock_profile_1: Profile, mock_profile_2: Profile, mock_profiler: Profiler
) -> None:
    def fn1() -> None:
        pass

    def fn2() -> None:
        pass

    suite = profile_suite(fn1, fn2, profiler=mock_profiler)

    assert suite == {
        "fn1": mock_profile_1,
        "fn2": mock_profile_2,
    }
