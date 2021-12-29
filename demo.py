import sys
from typing import Type

import boto3
from mypy_boto3_iam import IAMClient
from mypy_boto3_iam.type_defs import ListUsersResponseTypeDef

from botocove import cove
from botocove.cove_runner import CoveRunner
from botocove.experimental_runners import ALL_RUNNERS


def get_iam_users(session: boto3.Session) -> ListUsersResponseTypeDef:
    iam: IAMClient = session.client("iam", region_name="eu-west-1")
    all_users: ListUsersResponseTypeDef = (
        iam.get_paginator("list_users").paginate().build_full_result()
    )
    return all_users


def main() -> None:

    runner_name, member_account_id, repetitions = sys.argv[1:4]

    target_ids = [member_account_id] * int(repetitions)

    runner_impl = resolve_runner(runner_name)

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
        class_list = ', '.join(runner.__name__ for runner in ALL_RUNNERS)
        raise ValueError(
            f"{runner_name} is not a runner class. Runner classes are {class_list}."
        )


if __name__ == "__main__":
    main()
