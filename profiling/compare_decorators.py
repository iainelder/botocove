import sys
import time
from typing import Any, Callable, List
import multiprocessing as mp

import boto3
from mypy_boto3_iam import IAMClient
from mypy_boto3_iam.type_defs import ListUsersResponseTypeDef

from profiling.experimental_decorators import one_phase_cove, two_phase_cove

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

    for decorator_impl in [one_phase_cove, two_phase_cove]:

        run_process_and_log_memory(
            mp.Process(
                target=print_cove_results,
                name=decorator_impl.__name__,
                args=(get_iam_users, target_ids, decorator_impl)
            ),
            memory_log
        )

    for runner_name, profile in memory_log.items():
        plt.plot(profile, label=runner_name)
    
    plt.legend()
    plt.savefig("botocove_decorator_memory.png")


def run_process_and_log_memory(process: mp.Process, memory_log):
    process.start()
    memory_log[process.name] = []
    while process.is_alive():
        time.sleep(0.25)
        rss = psutil.Process(process.pid).memory_info().rss
        memory_log[process.name].append(rss)


def print_cove_results(func: Callable[[boto3.Session], Any], target_ids: List[str], decorator_impl: Callable):

    all_results = decorator_impl(func, target_ids=target_ids)()

    for r in all_results["Results"]:
        print(r)

    for e in all_results["Exceptions"]:
        print(e)

    for f in all_results["FailedAssumeRole"]:
        print(f)


if __name__ == "__main__":
    main()
