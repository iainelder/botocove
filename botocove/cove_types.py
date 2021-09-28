from typing import Any, Dict, List, TypedDict


class CoveFunctionOutput(TypedDict):
    Results: List[Dict[str, Any]]
    Exceptions: List[Dict[str, Any]]


class CoveOutput(CoveFunctionOutput):
    FailedAssumeRole: List[Dict[str, Any]]
