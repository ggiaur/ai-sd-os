from typing import Any, Dict
from pydantic import BaseModel, ConfigDict


class SprintPlanningProposedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    work_package: Dict[str, Any]
    sprint_id: str


class SprintPlanningApprovedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    work_package: Dict[str, Any]
    sprint_id: str
    project_root: str


class SprintReviewRequestedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    work_package: Dict[str, Any]
    sprint_id: str


class SprintReviewApprovedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    work_package: Dict[str, Any]
    project_root: str


class PipelineBlockedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    reason: str


class RetrospectiveRecordedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    retrospective: Dict[str, Any]
    project_root: str


class LessonsLearnedUpdatedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    sprint_id: str


class ActionDestructiveRequestedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: str
    target: str
