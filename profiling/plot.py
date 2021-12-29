import re
import sys
from datetime import datetime, timedelta
from glob import iglob
from itertools import islice
from pathlib import Path
from typing import no_type_check, Iterable

# There are no type hints or stubs for these modules.
import matplotlib.pyplot as plt  # type: ignore
import pandas as pd  # type: ignore
from humanfriendly import parse_size

@no_type_check
def main() -> None:
    output_dir = sys.argv[1]

    profiles = glob_in_dir(dir=output_dir, expr="*CoveRunner.csv")

    ax = None
    for p in profiles:
        df = pd.read_csv(p)
        df["CPU_Time"] = df["CPU_Time"].apply(convert_top_cpu_time_to_seconds)
        df["Resident_Memory_Size"] = df["Resident_Memory_Size"].apply(convert_top_mem_to_bytes)
        ax = df.plot(ax=ax, x="CPU_Time", y="Resident_Memory_Size", label=p)

    plt.show()


# TODO: unit tests: mock dir structure? pytest temporary directories?
def glob_in_dir(*, dir: str, expr: str) -> Iterable[str]:
    return iglob(str(Path(dir, expr)))


def convert_top_cpu_time_to_seconds(cpu_time: str) -> float:
    """Converts top's CPU_Time value to a float number of seconds."""
    stamp = datetime.strptime(cpu_time, "%M:%S.%f")
    delta = timedelta(minutes=stamp.minute, seconds=stamp.second, microseconds=stamp.microsecond)
    return delta.total_seconds()


# TODO: units tests for the k part
# FIXME: type isn't always str
# FIXME: find a more pythonic way to collect this data!
def convert_top_mem_to_bytes(resident_memory_size: str) -> int:
    if type(resident_memory_size) == int:
        return resident_memory_size
    if re.match(r"\d+", resident_memory_size):
        resident_memory_size = f"{resident_memory_size}k"
    return parse_size(resident_memory_size)


if __name__ == "__main__":
    main()
