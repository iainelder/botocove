import matplotlib.pyplot as plt
from matplotlib.figure import Figure  # type: ignore[import]

from profiling.profiler import Profile


def plot(suite: Profile) -> Figure:  # type: ignore[no-any-unimported]

    if not suite:
        raise ValueError("needs at least one profile")

    figure = plt.figure()

    for profile_name, profile in suite.items():
        plt.plot(*zip(*profile), label=profile_name)  # type: ignore[arg-type]

    figure.axes[0].legend()  # type: ignore[attr-defined]
    figure.axes[0].set_xlabel("Wall clock time (s)")  # type: ignore[attr-defined]
    figure.axes[0].set_ylabel("Memory (B)")  # type: ignore[attr-defined]
    figure.suptitle("Botocove profiling")  # type: ignore[attr-defined]

    return figure
