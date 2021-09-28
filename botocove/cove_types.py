from typing import Any, Dict, List, Optional, TypedDict
from mypy_boto3_organizations.type_defs import AccountTypeDef

class CoveFunctionOutput(TypedDict):
    Results: List[Dict[str, Any]]
    Exceptions: List[Dict[str, Any]]


class CoveOutput(CoveFunctionOutput):
    FailedAssumeRole: List[Dict[str, Any]]

class BaseDescribeAccount(TypedDict):
    AssumeRoleSuccess: Optional[bool]
    Result: Optional[Any]
    ExceptionDetails: Optional[List[Exception]]

class IncompleteDescribeAccount(BaseDescribeAccount):
    Id: str
    RoleSessionName: str

class DescrbeAccountResponse(BaseDescribeAccount, AccountTypeDef):
    pass