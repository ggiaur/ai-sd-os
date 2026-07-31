from typing import Any, Dict
from pydantic import BaseModel, ConfigDict


class WorkPackageCreatedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    work_package: Dict[str, Any]


class DevelopmentCompletedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    work_package: Dict[str, Any]
    written_files: Dict[str, Any]
    project_root: str


class TestsPassedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    work_package: Dict[str, Any]
    project_root: str
    auto_dod_passed: int
    auto_dod_total: int


class TestsFailedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    work_package: Dict[str, Any]
    project_root: str
    error: str
    retry_count: int
    max_retries: int
