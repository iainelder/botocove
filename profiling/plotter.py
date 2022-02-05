import matplotlib.pyplot as plt  # type:ignore
from matplotlib.figure import Figure  # type:ignore

from profiling.profiler import Profile


def plot(suite: Profile) -> Figure:  # type:ignore

    if not suite:
        raise ValueError("needs at least one profile")

    figure = plt.figure()

    for profile_name, profile in suite.items():
        plt.plot(*zip(*profile), label=profile_name)  # type:ignore

    figure.axes[0].legend()  # type:ignore

    return figure
