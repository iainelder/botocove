import sys
import boto3
from botocove import cove
from typing import cast, no_type_check, Type
from botocove.cove_runner import CoveRunner
from botocove.experimental_runners import ALL_RUNNERS

# No type check because the correct type requires importing more from mypy boto3
@no_type_check
def get_iam_users(session):
    iam = session.client("iam", region_name="eu-west-1")
    all_users = iam.get_paginator("list_users").paginate().build_full_result()
    return all_users

def main() -> None:

    runner_name, member_account_id, repetitions = sys.argv[1:4]

    target_ids = [member_account_id] * int(repetitions)

    runner_impl = load_runner(runner_name)

    all_results = cove(get_iam_users, target_ids=target_ids, runner_impl=runner_impl)()

    for r in all_results["Results"]:
        print(r)

    for e in all_results["Exceptions"]:
        print(e)
        
    for f in all_results["FailedAssumeRole"]:
        print(f)


def load_runner(class_name: str) -> Type[CoveRunner]:
    for c in ALL_RUNNERS:
        if class_name == c.__name__:
            return c
    raise ValueError(f"{class_name} is not a runner class")


if __name__ == "__main__":
    main()
