import logging
from concurrent import futures
from typing import Any, Dict, List, Optional, Set, Tuple, Literal, Union
from botocove.cove_types import IncompleteDescribeAccount, DescrbeAccountResponse

import boto3
from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import ClientError
from mypy_boto3_organizations.type_defs import AccountTypeDef
from tqdm import tqdm
from mypy_boto3_sts.client import STSClient
from mypy_boto3_organizations.client import OrganizationsClient

from botocove.cove_session import CoveSession

logger = logging.getLogger(__name__)


DEFAULT_ROLENAME = "OrganizationAccountAccessRole"


class CoveSessions(object):
    def __init__(
        self,
        target_ids: Optional[List[str]],
        ignore_ids: Optional[List[str]],
        rolename: Optional[str],
        role_session_name: Optional[str],
        assuming_session: Optional[Session],
        org_master: bool,
    ) -> None:

        self.sts_client: STSClient = self._get_boto3_client("sts", assuming_session)
        self.org_client: OrganizationsClient = self._get_boto3_client("organizations", assuming_session)

        self.provided_ignore_ids = ignore_ids
        self.target_accounts = self._resolve_target_accounts(target_ids)
        if not self.target_accounts:
            raise ValueError(
                "There are no eligible account ids to run decorated func against"
            )

        self.role_to_assume = rolename or DEFAULT_ROLENAME
        self.role_session_name = role_session_name or self.role_to_assume

        self.org_master = org_master

    def get_cove_sessions(self) -> Tuple[List[CoveSession], List[Dict[str, Any]]]:
        logger.info(
            f"Getting sessions in accounts: {self.role_to_assume=} "
            f"{self.role_session_name=} {self.target_accounts=} "
            f"{self.provided_ignore_ids=}"
        )

        sessions = []
        with futures.ThreadPoolExecutor() as executor:
            for result in tqdm(
                executor.map(self._cove_session_factory, self.target_accounts)
            ):
                sessions.append(result)

        self.valid_sessions = [
            session for session in sessions if session.assume_role_success is True
        ]
        if not self.valid_sessions:
            raise ValueError("No accounts are accessible: check logs for detail")

        self.invalid_sessions = self._get_invalid_cove_sessions(sessions)
        return self.valid_sessions, self.invalid_sessions

    def _cove_session_factory(self, account_id: str) -> CoveSession:
        role_arn = f"arn:aws:iam::{account_id}:role/{self.role_to_assume}"
        account_details: Union[AccountTypeDef, IncompleteDescribeAccount]
        if self.org_master:
            try:
                 DescrbeAccountResponse(dict(self.org_client.describe_account(
                    AccountId=account_id
                )["Account"]))
            except ClientError:
                logger.exception(f"Failed to call describe_account for {account_id}")
                account_details = IncompleteDescribeAccount(Id=account_id, RoleSessionName=self.role_session_name)

        else:
            account_details = IncompleteDescribeAccount(Id=account_id, RoleSessionName=self.role_session_name)

        cove_session = CoveSession(account_details)
        try:
            logger.debug(f"Attempting to assume {role_arn}")
            creds = self.sts_client.assume_role(
                RoleArn=role_arn, RoleSessionName=self.role_session_name
            )["Credentials"]
            cove_session.initialize_boto_session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds["SessionToken"],
            )
        except ClientError as e:
            cove_session.store_exception(e)

        return cove_session

    def _get_invalid_cove_sessions(
        self, sessions: List[CoveSession]
    ) -> List[Dict[str, Any]]:
        invalid_sessions = [
            session.format_cove_error()
            for session in sessions
            if session.assume_role_success is False
        ]

        if invalid_sessions:
            logger.warning("Could not assume role into these accounts:")
            for invalid_session in invalid_sessions:
                logger.warning(invalid_session)
            invalid_ids = [failure["Id"] for failure in invalid_sessions]
            logger.warning(f"\n\nInvalid session Account IDs as list: {invalid_ids}")

        return invalid_sessions

    def _get_boto3_client(
        self, clientname: Union[Literal["organizations"], Literal["sts"]], assuming_session: Optional[Session]
    ) -> Any:
        if assuming_session:
            logger.info(f"Using provided Boto3 session {assuming_session}")
            return assuming_session.client(service_name=clientname, config=Config(max_pool_connections=20))
        logger.info("No Boto3 session argument: using credential chain")
        return boto3.client(clientname, config=Config(max_pool_connections=20))

    def _resolve_target_accounts(self, target_ids: Optional[List[str]]) -> Set[str]:
        if self.provided_ignore_ids:
            validated_ignore_ids = self.format_ignore_ids()
        else:
            validated_ignore_ids = set()

        if target_ids is None:
            # No target_ids passed
            target_accounts = self._gather_org_assume_targets()
        else:
            # Specific list of IDs passed
            target_accounts = set(target_ids)

        return target_accounts - validated_ignore_ids

    def format_ignore_ids(self) -> Set[str]:
        if not isinstance(self.provided_ignore_ids, list):
            raise TypeError("ignore_ids must be a list of account IDs")
        for account_id in self.provided_ignore_ids:
            if len(account_id) != 12:
                raise TypeError("All ignore_id in list must be 12 character strings")
            if not isinstance(account_id, str):
                raise TypeError("All ignore_id list entries must be strings")
        return set(self.provided_ignore_ids)

    def _get_active_org_accounts(self) -> Set[str]:
        all_org_accounts = (
            self.org_client.get_paginator("list_accounts")
            .paginate()
            .build_full_result()["Accounts"]
        )
        return {acc["Id"] for acc in all_org_accounts if acc["Status"] == "ACTIVE"}

    def _build_account_ignore_list(self) -> Set[str]:
        calling_account: Set[str] = {
            self.sts_client.get_caller_identity()["Account"]
        }  # TODO we can do this smarter surely
        if self.provided_ignore_ids:
            accounts_to_ignore = set(self.provided_ignore_ids) | calling_account
        else:
            accounts_to_ignore = calling_account
        logger.info(f"{accounts_to_ignore=}")
        return accounts_to_ignore

    def _gather_org_assume_targets(self) -> Set[str]:
        accounts_to_ignore = self._build_account_ignore_list()
        active_accounts = self._get_active_org_accounts()
        target_accounts = active_accounts - accounts_to_ignore
        return target_accounts
