from typing import List

import pytest

from botocove.cove_host_account import CoveHostAccount
from profiling.host_patcher import allow_duplicate_target_ids


@pytest.fixture()
def duplicate_target_ids() -> List[str]:
    return ["111111111111"] * 2


def test_unpatched_host_account_deduplicates_target_ids(
    duplicate_target_ids: List[str],
) -> None:
    host = CoveHostAccount(
        target_ids=duplicate_target_ids,
        ignore_ids=None,
        rolename=None,
        role_session_name=None,
        policy=None,
        policy_arns=None,
        assuming_session=None,
        org_master=False,
    )
    assert len(host.target_accounts) == 1


def test_patched_host_account_allows_duplicate_account_ids(
    duplicate_target_ids: List[str],
) -> None:
    with allow_duplicate_target_ids():
        host = CoveHostAccount(
            target_ids=duplicate_target_ids,
            ignore_ids=None,
            rolename=None,
            role_session_name=None,
            policy=None,
            policy_arns=None,
            assuming_session=None,
            org_master=False,
        )

        # Ignore a non-overlapping equality check between `Set[str]` and `List[str]`.
        # Mypy doesn't see that the context manager changes the type of
        # target_accounts to `List[str]`.
        assert host.target_accounts == duplicate_target_ids  # type:ignore
