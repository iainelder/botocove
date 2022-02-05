import argparse
from typing import Any, Callable, Iterable

from boto3 import Session
from mypy_boto3_ec2 import EC2Client
from mypy_boto3_ec2.type_defs import DescribeAvailabilityZonesResultTypeDef

from botocove import cove
from profiling import allow_duplicate_target_ids, plot, profile


def get_availability_zones(session: Session) -> DescribeAvailabilityZonesResultTypeDef:
    ec2: EC2Client = session.client("ec2", region_name="eu-west-1")
    return ec2.describe_availability_zones()


DEFAULT_POOL_SIZES: Iterable[int] = [4, 8, 16, 32]

DEFAULT_ORG_SIZE: int = 100

DEFAULT_TEST_FUNCTION: Callable[..., Any] = get_availability_zones


def main() -> None:

    args = parse_args()

    with allow_duplicate_target_ids():
        compare_performance(
            member_account_id=args.member_account_id,
            org_size=args.org_size,
            test_function=DEFAULT_TEST_FUNCTION,
            pool_sizes=args.pool_sizes,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile botocove")
    parser.add_argument(
        "--member-account-id", type=str, help="Real member account to back the fake org"
    )
    parser.add_argument(
        "--org-size",
        type=int,
        default=DEFAULT_ORG_SIZE,
        help="Number of member accounts in fake org",
    )
    parser.add_argument(
        "--pool-sizes",
        type=int,
        nargs="*",
        default=DEFAULT_POOL_SIZES,
        help="Thread pool sizes to test",
    )
    return parser.parse_args()


def compare_performance(
    *,
    member_account_id: str,
    org_size: int = DEFAULT_ORG_SIZE,
    test_function: Callable[..., Any] = DEFAULT_TEST_FUNCTION,
    pool_sizes: Iterable[int] = DEFAULT_POOL_SIZES,
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
