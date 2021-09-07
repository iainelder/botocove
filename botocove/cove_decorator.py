import asyncio
import functools
import logging
from concurrent import futures
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypedDict

import boto3
from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import ClientError

from botocove.cove_session import CoveSession

logger = logging.getLogger(__name__)

DEFAULT_ROLENAME = "OrganizationAccountAccessRole"


class CoveOutput(TypedDict):
    Results: List[Dict[str, Any]]
    Exceptions: List[Dict[str, Any]]
    FailedAssumeRole: List[Dict[str, Any]]


class CoveRunner(object):

    # """
    # docs
    # """

    def __init__(
        self,
        func: Optional[Callable],
        target_ids: Optional[List[str]],
        ignore_ids: Optional[List[str]],
        rolename: Optional[str],
        role_session_name: Optional[str],
        assuming_session: Optional[Session],
        raise_exception: bool,
        org_master: bool,
        func_args: Any,
        func_kwargs: Any,
    ) -> None:
        self.sts_client = self._get_boto3_client("sts", assuming_session)
        self.org_client = self._get_boto3_client("organizations", assuming_session)

        self.provided_ignore_ids = ignore_ids
        self.target_accounts = self._resolve_target_accounts(target_ids)
        if not self.target_accounts:
            raise ValueError(
                "There are no eligible account ids to run decorated func "
                f"{func.__name__} against"
            )

        self.role_to_assume = rolename or DEFAULT_ROLENAME
        self.role_session_name = role_session_name or self.role_to_assume

        self.raise_exception = raise_exception
        self.org_master = org_master

        self.cove_wrapped_func = func
        self.func_args = func_args
        self.func_kwargs = func_kwargs

    def get_cove_sessions(self):
        logger.info(
            f"Running func {self.cove_wrapped_func.__name__} against accounts passing arguments: "
            f"{self.role_to_assume=} {self.role_session_name=} {self.target_accounts=} {self.provided_ignore_ids=} "
        )
        logger.debug(f"accounts targeted are {self.target_accounts}")

        # Get sessions in all targeted accounts
        self.sessions = asyncio.run(
            _get_account_sessions(
                self.org_client,
                self.sts_client,
                self.role_to_assume,
                self.role_session_name,
                self.target_accounts,
                self.org_master,
            )
        )

        self.valid_sessions = [
            session for session in self.sessions if session.assume_role_success is True
        ]
        if not self.valid_sessions:
            raise ValueError("No accounts are accessible: check logs for detail")

        self.invalid_sessions = self._get_invalid_cove_sessions()

    def run_cove(self) -> CoveOutput:
        self.get_cove_sessions()
        # Run decorated func with all valid sessions
        results, exceptions = asyncio.run(
            _async_boto3_call(
                self.valid_sessions,
                self.raise_exception,
                self.cove_wrapped_func,
                *self.func_args,
                **self.func_kwargs,
            )
        )
        return CoveOutput(
            Results=results,
            Exceptions=exceptions,
            FailedAssumeRole=self.invalid_sessions,
        )

    def _get_invalid_cove_sessions(self) -> List[Dict[str, Any]]:
        invalid_sessions = [
            session.format_cove_error()
            for session in self.sessions
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
        self, clientname: str, assuming_session: Optional[Session]
    ) -> Any:
        if assuming_session:
            logger.info(f"Using provided Boto3 session {assuming_session}")
            return assuming_session.client(clientname)
        logger.info("No Boto3 session argument: using credential chain")
        return boto3.client(clientname, config=Config(max_pool_connections=20))

    def _resolve_target_accounts(self, target_ids: Optional[List[str]]) -> Set[str]:
        if self.provided_ignore_ids:
            validated_ignore_ids = self.format_ignore_ids()
        else:
            validated_ignore_ids: Set[str] = set()

        if target_ids is None:
            # No target_ids passed
            target_accounts = self._gather_org_assume_targets()
        else:
            # Specific list of IDs passed
            target_accounts: Set[str] = set(target_ids)

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

    def _build_account_ignore_list(self):
        calling_account: Set = {
            self.sts_client.get_caller_identity()["Account"]
        }  # TODO we can do this smarter surely
        if self.provided_ignore_ids:
            accounts_to_ignore = set(self.provided_ignore_ids) | calling_account
        else:
            accounts_to_ignore = calling_account
        logger.info(f"{accounts_to_ignore=}")
        return accounts_to_ignore

    def _gather_org_assume_targets(self):
        accounts_to_ignore = self._build_account_ignore_list()
        active_accounts = self._get_active_org_accounts()
        target_accounts = active_accounts - accounts_to_ignore
        return target_accounts


# TODO boto3 types - s/Any/mypy_boto3 types


def _get_cove_session(
    org_client: Any,
    sts_client: Any,
    account_id: str,
    rolename: str,
    role_session_name: str,
    org_master: bool,
) -> CoveSession:
    role_arn = f"arn:aws:iam::{account_id}:role/{rolename}"
    if org_master:
        try:
            account_details = org_client.describe_account(AccountId=account_id)[
                "Account"
            ]
        except ClientError:
            logger.exception(f"Failed to call describe_account for {account_id}")
            account_details = {
                "Id": account_id,
                "RoleSessionName": role_session_name,
            }

    else:
        account_details = {"Id": account_id, "RoleSessionName": role_session_name}
    cove_session = CoveSession(account_details)
    try:
        logger.debug(f"Attempting to assume {role_arn}")
        creds = sts_client.assume_role(
            RoleArn=role_arn, RoleSessionName=role_session_name
        )["Credentials"]
        cove_session.initialize_boto_session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
        )
    except Exception as e:
        cove_session.store_exception(e)

    return cove_session


async def _get_account_sessions(
    org_client: Any,
    sts_client: Any,
    rolename: str,
    role_session_name: str,
    accounts: Set[str],
    org_master: bool,
) -> List[CoveSession]:
    with futures.ThreadPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(
                executor,
                _get_cove_session,
                org_client,
                sts_client,
                account_id,
                rolename,
                role_session_name,
                org_master,
            )
            for account_id in accounts
        ]
    sessions = await asyncio.gather(*tasks)
    return sessions


def wrap_func(
    func: Callable,
    raise_exception: bool,
    account_session: CoveSession,
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    # Wrapper capturing exceptions and formatting results
    try:
        result = func(account_session, *args, **kwargs)
        return account_session.format_cove_result(result)
    except Exception as e:
        if raise_exception is True:
            account_session.store_exception(e)
            logger.exception(account_session.format_cove_error())
            raise
        else:
            account_session.store_exception(e)
            return account_session.format_cove_error()


async def _async_boto3_call(
    valid_sessions: List[CoveSession],
    raise_exception: bool,
    func: Callable,
    *args: Any,
    **kwargs: Any,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    with futures.ThreadPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(
                executor,
                partial(
                    wrap_func, func, raise_exception, account_session, *args, **kwargs
                ),
            )
            for account_session in valid_sessions
        ]

    completed = await asyncio.gather(*tasks)
    successful_results = [
        result for result in completed if not result.get("ExceptionDetails")
    ]
    exceptions = [result for result in completed if result.get("ExceptionDetails")]
    return successful_results, exceptions


def cove(
    _func: Optional[Callable] = None,
    *,
    target_ids: Optional[List[str]] = None,
    ignore_ids: Optional[List[str]] = None,
    rolename: Optional[str] = None,
    role_session_name: Optional[str] = None,
    assuming_session: Optional[Session] = None,
    raise_exception: bool = False,
    org_master: bool = True,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> CoveOutput:
            runner = CoveRunner(
                func=func,
                target_ids=target_ids,
                ignore_ids=ignore_ids,
                rolename=rolename,
                role_session_name=role_session_name,
                assuming_session=assuming_session,
                raise_exception=raise_exception,
                org_master=org_master,
                func_args=args,
                func_kwargs=kwargs,
            )
            return runner.run_cove()

        return wrapper

    # Handle both bare decorator and with argument
    if _func is None:
        return decorator
    else:
        return decorator(_func)
