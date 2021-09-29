from typing import Any, Dict

from boto3.session import Session

from botocove.cove_types import AccountDetails


class CoveSession(Session):
    """Enriches a boto3 Session with account data from Master account if run from
    an organization master.
    Provides internal helper functions for managing concurrent boto3 calls
    """

    assume_role_success: bool = False
    session_information: AccountDetails
    stored_exception: Exception

    def __init__(self, account_details: AccountDetails) -> None:
        self.session_information = account_details

    def __repr__(self) -> str:
        # Overwrite boto3's repr to avoid AttributeErrors
        return f"{self.__class__.__name__}(account_id={self.session_information['Id']})"

    def initialize_boto_session(self, *args: Any, **kwargs: Any) -> None:
        # Inherit from and initialize standard boto3 Session object
        super().__init__(*args, **kwargs)
        self.assume_role_success = True
        self.session_information["AssumeRoleSuccess"] = self.assume_role_success

    def store_exception(self, err: Exception) -> None:
        self.stored_exception = err

    def format_cove_result(self, result: Any) -> Dict[str, Any]:
        self.session_information["Result"] = result
        return self.session_information

    def format_cove_error(self) -> Dict[str, Any]:
        self.session_information["ExceptionDetails"] = self.stored_exception
        self.session_information["AssumeRoleSuccess"] = self.assume_role_success
        return self.session_information
