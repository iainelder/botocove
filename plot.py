# type: ignore

from glob import glob

import matplotlib.pyplot as plt
import pandas as pd

profiles = glob("*CoveRunner.csv")

ax = None
for p in profiles:
    df = pd.read_csv(p)
    ax = df.plot(ax=ax, x="CPU_Time", y="Resident_Memory_size")

plt.show()
