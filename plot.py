import sys
from datetime import datetime, timedelta
from glob import iglob
from itertools import islice
from pathlib import Path
from typing import no_type_check, Iterable

# There are no type hints or stubs for these modules.
import matplotlib.pyplot as plt  # type: ignore
import pandas as pd  # type: ignore


@no_type_check
def main() -> None:
    output_dir = sys.argv[1]

    profiles = glob_in_dir(dir=output_dir, expr="*CoveRunner.csv")

    ax = None
    for p in profiles:
        df = pd.read_csv(p)
        df["CPU_Time"] = df["CPU_Time"].apply(cpu_timedelta)
        ax = df.plot(ax=ax, x="CPU_Time", y="Resident_Memory_Size", label=p)

    plt.show()


# TODO: unit tests: mock dir structure? pytest temporary directories?
def glob_in_dir(*, dir: str, expr: str) -> Iterable[str]:
    return iglob(str(Path(dir, expr)))


def cpu_timedelta(cpu_time: str) -> timedelta:
    dt = datetime.strptime(cpu_time, "%M:%S.%f")
    return timedelta(minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)


if __name__ == "__main__":
    main()
