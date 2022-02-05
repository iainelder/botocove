# type: ignore

import pytest
from matplotlib.lines import Line2D

from profiling import plot
from profiling.profiler import MemoryLog, Profile

# How can I write unit tests against code that uses matplotlib?
# Explains the use of get_xydata.
# https://stackoverflow.com/questions/27948126/how-can-i-write-unit-tests-against-code-that-uses-matplotlib

# Unit Testing Python data visualizations
# TODO Use plt.gcf().number to check whether plot was really called.
# https://towardsdatascience.com/unit-testing-python-data-visualizations-18e0250430


@pytest.fixture()
def mock_profile_1() -> Profile:
    return {
        "fn1": [
            MemoryLog(timestamp=0, rss=0),
            MemoryLog(timestamp=0.25, rss=500),
            MemoryLog(timestamp=0.5, rss=1000),
        ]
    }


@pytest.fixture()
def mock_profile_2() -> Profile:
    return {
        "fn1": [
            MemoryLog(timestamp=0, rss=0),
            MemoryLog(timestamp=0.25, rss=500),
            MemoryLog(timestamp=0.5, rss=1000),
        ],
        "fn2": [
            MemoryLog(timestamp=0, rss=0),
            MemoryLog(timestamp=0.33, rss=125),
            MemoryLog(timestamp=0.67, rss=250),
        ],
    }


def assert_line_plots_profile(line: Line2D, profile: Profile) -> None:
    points = line.get_xydata()
    assert len(points) == len(profile)
    for point, log in zip(points, profile):
        x, y = point
        assert log.timestamp == x
        assert log.rss == y


def test_plotter_plots_all_logs(mock_profile_1: Profile) -> None:
    figure = plot(mock_profile_1)
    lines = figure.axes[0].get_lines()
    assert_line_plots_profile(lines[0], mock_profile_1["fn1"])


def test_plotter_plots_multiple_profiles(mock_profile_2: Profile) -> None:
    figure = plot(mock_profile_2)
    lines = figure.axes[0].get_lines()
    assert_line_plots_profile(lines[0], mock_profile_2["fn1"])
    assert_line_plots_profile(lines[1], mock_profile_2["fn2"])


def test_plotter_labels_profile(mock_profile_1: Profile) -> None:
    figure = plot({"fn1": mock_profile_1})
    lines = figure.axes[0].get_lines()
    assert lines[0].get_label() == "fn1"


def test_figure_has_legend(mock_profile_1: Profile) -> None:
    figure = plot({"fn1": mock_profile_1})
    legend = figure.axes[0].get_legend()
    assert legend is not None


def test_legend_text_is_suite_key(mock_profile_1: Profile) -> None:
    figure = plot(mock_profile_1)
    legend = figure.axes[0].get_legend()
    texts = legend.get_texts()
    assert len(texts) == 1
    assert texts[0].get_text() == "fn1"


def test_plotter_fails_for_empty_suite() -> None:
    with pytest.raises(ValueError, match="needs at least one profile"):
        plot({})
