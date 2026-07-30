from typing import List, Dict
from pydantic import BaseModel, Field, field_validator
import re

class TaskItem(BaseModel):
    task_id: str = Field(..., description="Task ID (e.g. TASK-001)")
    description: str
    requirement_ref: str = Field(..., description="Requirement ID reference (e.g. FR-001)")

    @field_validator("task_id")

    def validate_task_id(cls, v: str) -> str:
        if not re.match(r"^TASK-\d+$", v):
            raise ValueError(f"Task ID must match pattern TASK-XXX, got: {v}")
        return v

    @field_validator("requirement_ref")

    def validate_req_ref(cls, v: str) -> str:
        if not re.match(r"^FR-\d+$", v):
            raise ValueError(f"requirement_ref must match pattern FR-XXX, got: {v}")
        return v

class WorkPackage(BaseModel):
    id: str = Field(..., description="WorkPackage ID (e.g. WP-001)")
    sprint_id: str = Field(..., description="Sprint ID (e.g. SPRINT-001)")
    goal: str
    allowed_paths: List[str] = Field(default_factory=lambda: ["src/", "tests/"])
    tasks: List[TaskItem] = Field(default_factory=list)
    max_execution_time_minutes: int = 30
    tests_required: bool = True
    coverage_mapping: Dict[str, List[str]] = Field(default_factory=dict)

    @field_validator("id")

    def validate_wp_id(cls, v: str) -> str:
        if not re.match(r"^WP-\d+$", v):
            raise ValueError(f"WorkPackage ID must match pattern WP-XXX, got: {v}")
        return v

    @field_validator("sprint_id")

    def validate_sprint_id(cls, v: str) -> str:
        if not re.match(r"^SPRINT-\d+$", v):
            raise ValueError(f"sprint_id must match pattern SPRINT-XXX, got: {v}")
        return v
