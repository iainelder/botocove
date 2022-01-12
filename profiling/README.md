# Profiling Botocove

## Usage

Set management account profile and region.
```
export AWS_PROFILE=sandbox-mgmt
export AWS_DEFAULT_REGION=eu-west-1

Run demo.py to generate a plot of memory use by various runner implementations.

The first argument is an AWS account to connect to. It must be a member of the management account. The second argument is the size of the organization to simulate. It will connect to the member account this many times.

```
poetry run python demo.py 897617218731 50
```

## Changes to the library

Botocove is more testable with the following changes.

1. Parameterize CoveRunner implementation
2. Type CoveOutput values as iterables
3. Set CoveOutput values as generators
4. Allow duplicate target account IDs (list not set)

Change 3 is incompatible with clients that rely on the CoveOutput values being lists. 

The test code assumes only that an iterable is returned.

It could be made backwards compatible by parameterizing the CoveOutput type (CoveListOutput, CoveIterOutput).

Change 4 is incompatible with clients that rely on CoveSessions deduping the account IDs.

The test code depends on duplicate account IDs to simplify the test infrastructure.

It could be made backwards compatible by parameterizing the CoveSessions type (CoveSessionSet, CoveSessionList, CoveOrgSessions).

## Test Harness

The test harness consists of:

1. A set of experimental runners
2. A python program that executes these runners on a simulated organization of a given size and plots the memory use of each one.

Logging the memory of a running process is surprisingly complicated.

Some options I considered for the task:

* https://github.com/benfred/py-spy
* https://github.com/sysstat/sysstat/blob/master/pidstat.c
* https://github.com/ColinIanKing/smemstat
* https://heptapod.host/saajns/procpath
* https://docs.python.org/3/library/tracemalloc.html

In the end, as the least bad option, I used a bash script to run top in a loop.

What about good old ps? The OG!

More options:

* https://pypi.org/project/psutil/
* https://pypi.org/project/memory-profiler/

## Plotting

A demo of how to use GnuPlot.

* https://www.thanassis.space/gnuplotStreaming.html

https://realpython.com/pandas-plot-python/

https://stackoverflow.com/questions/13872533/plot-different-dataframes-in-the-same-figure

## Results

mem_50.png

mem_300.png
