import os
import sys
import time
from typing import Any, Callable, List, Type
from threading import Thread
import multiprocessing as mp

import boto3
from mypy_boto3_iam import IAMClient
from mypy_boto3_iam.type_defs import ListUsersResponseTypeDef

from botocove import cove
from botocove.cove_runner import CoveRunner
from profiling.experimental_runners import ALL_RUNNERS

import psutil

import matplotlib.pyplot as plt


def get_iam_users(session: boto3.Session) -> ListUsersResponseTypeDef:
    iam: IAMClient = session.client("iam", region_name="eu-west-1")
    all_users: ListUsersResponseTypeDef = (
        iam.get_paginator("list_users").paginate().build_full_result()
    )
    return all_users


def main() -> None:

    mp.set_start_method("spawn")

    member_account_id, repetitions = sys.argv[1:3]

    target_ids = [member_account_id] * int(repetitions)

    memory_log = {}

    for runner_impl in ALL_RUNNERS:

        run_process_and_log_memory(
            mp.Process(target=print_cove_results, name=runner_impl.__name__, args=(get_iam_users, target_ids, runner_impl)),
            memory_log
        )

    for runner_name, profile in memory_log.items():
        plt.plot(profile, label=runner_name)
    
    plt.legend()
    plt.show()

def run_process_and_log_memory(process: mp.Process, memory_log):
    process.start()
    memory_log[process.name] = []
    while process.is_alive():
        time.sleep(0.25)
        rss = psutil.Process(process.pid).memory_info().rss
        memory_log[process.name].append(rss)


def print_cove_results(func: Callable[[boto3.Session], Any], target_ids: List[str], runner_impl: CoveRunner):

    all_results = cove(get_iam_users, target_ids=target_ids, runner_impl=runner_impl)()

    for r in all_results["Results"]:
        print(r)

    for e in all_results["Exceptions"]:
        print(e)

    for f in all_results["FailedAssumeRole"]:
        print(f)


def resolve_runner(runner_name: str) -> Type[CoveRunner]:
    try:
        return next(runner for runner in ALL_RUNNERS if runner_name == runner.__name__)
    except StopIteration:
        class_list = ", ".join(runner.__name__ for runner in ALL_RUNNERS)
        raise ValueError(
            f"{runner_name} is not a runner class. Runner classes are {class_list}."
        )


if __name__ == "__main__":
    main()
