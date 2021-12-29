# type: ignore

from glob import glob
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd

output_dir = sys.argv[1]

os.chdir(output_dir)

profiles = glob("*CoveRunner.csv")

ax = None
for p in profiles:
    df = pd.read_csv(p)
    ax = df.plot(ax=ax, x="CPU_Time", y="Resident_Memory_size", label=p)

plt.show()
