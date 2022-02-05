import sys
from typing import Any, Callable, Iterable

from boto3 import Session
from mypy_boto3_ec2 import EC2Client
from mypy_boto3_ec2.type_defs import DescribeAvailabilityZonesResultTypeDef

from botocove import cove
from profiling import allow_duplicate_target_ids, plot, profile


def get_availability_zones(session: Session) -> DescribeAvailabilityZonesResultTypeDef:
    ec2: EC2Client = session.client("ec2", region_name="eu-west-1")
    return ec2.describe_availability_zones()


def main() -> None:

    member_account_id, org_size = sys.argv[1:3]

    with allow_duplicate_target_ids():
        compare_performance(
            member_account_id=member_account_id,
            org_size=int(org_size),
            test_function=get_availability_zones,
            pool_sizes=[4, 8, 16, 32],
        )


def compare_performance(
    member_account_id: str,
    org_size: int,
    test_function: Callable[..., Any],
    pool_sizes: Iterable[int],
) -> None:
    fake_org = [member_account_id] * org_size

    def set_workers(workers: int) -> Callable[..., Any]:
        nonlocal fake_org, test_function

        def fn() -> Any:
            return cove(
                test_function,
                target_ids=fake_org,
                thread_workers=workers,
            )()

        fn.__name__ = f"cove_with_{workers}_threads"
        return fn

    suite = profile(*[set_workers(w) for w in pool_sizes])
    figure = plot(suite)
    figure.savefig("plot.png")


if __name__ == "__main__":
    main()
