import sys
from typing import Any

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
        compare(member_account_id=member_account_id, org_size=int(org_size))


def compare(member_account_id: str, org_size: int) -> None:
    fake_org = [member_account_id] * org_size

    def cove_2() -> Any:
        nonlocal fake_org
        return cove(get_availability_zones, target_ids=fake_org, thread_workers=2)()

    def cove_20() -> Any:
        nonlocal fake_org
        return cove(get_availability_zones, target_ids=fake_org, thread_workers=20)()

    suite = profile(cove_2, cove_20)
    figure = plot(suite)
    figure.savefig("plot.png")


if __name__ == "__main__":
    main()
