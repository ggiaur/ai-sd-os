from typing import Any, Dict
from pydantic import BaseModel, ConfigDict


class SpecCreatedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    spec: Dict[str, Any]
    project_root: str


class CodebaseSurveyedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    snapshot: Dict[str, Any]
    project_root: str


class DiscoveryCompletedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    discovery_summary: str
