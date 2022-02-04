from contextlib import contextmanager
from typing import Generator, List

from botocove.cove_host_account import CoveHostAccount


@contextmanager
def allow_duplicate_target_ids() -> Generator[None, None, None]:
    def allow_duplicates_and_dont_ignore(
        self: CoveHostAccount, target_ids: List[str]
    ) -> List[str]:
        return target_ids

    original_impl = CoveHostAccount._resolve_target_accounts

    # Ignore incompatible callable return types: `Set[str]` and `List[str]`.
    # In practice they are compatible as sized iterables.
    # Ignore assigning a callable.
    CoveHostAccount._resolve_target_accounts = (  # type:ignore
        allow_duplicates_and_dont_ignore  # type:ignore
    )

    yield

    # Ignore assigning a callable.
    CoveHostAccount._resolve_target_accounts = original_impl  # type:ignore
