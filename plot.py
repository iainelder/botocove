import os
import sys
from datetime import datetime, timedelta
from glob import glob
from typing import no_type_check

# There are no type hints or stubs for these modules.
import matplotlib.pyplot as plt  # type: ignore
import pandas as pd  # type: ignore


@no_type_check
def main() -> None:
    output_dir = sys.argv[1]

    os.chdir(output_dir)

    profiles = glob("*CoveRunner.csv")

    ax = None
    for p in profiles:
        df = pd.read_csv(p)
        ax = df.plot(ax=ax, x="CPU_Time", y="Resident_Memory_Size", label=p)

    plt.show()


def cpu_timedelta(cpu_time: str) -> timedelta:
    dt = datetime.strptime(cpu_time, "%M:%S.%f")
    return timedelta(minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)


if __name__ == "__main__":
    main()
