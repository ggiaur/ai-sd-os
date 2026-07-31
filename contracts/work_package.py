from typing import List, Dict
from pydantic import BaseModel, Field, field_validator
import re

class TaskItem(BaseModel):
    task_id: str = Field(..., description="Task ID (e.g. TASK-001)")
    description: str
    requirement_ref: str = Field(..., description="Requirement ID reference (e.g. FR-001)")
    expected_output: str = Field(
        ..., description="Concrete, spec-derived acceptance value the implementation must produce. "
                          "Defined independently of the implementation so acceptance tests can verify "
                          "real behavior instead of being derived from whatever code gets written."
    )

    @field_validator("expected_output")
    def validate_expected_output(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("expected_output must not be empty — acceptance criteria are mandatory (spec-first)")
        return v

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

def _wp_module_name(wp_id: str) -> str:
    """Deterministic, collision-safe module name for generated code.

    Using a fixed name like `app.py` for every WorkPackage meant DeveloperAgent
    silently overwrote whatever a human already had at that path — catastrophic
    when adopting an existing project. Namespacing generated files by
    WorkPackage id keeps every sprint additive: nothing the engine writes ever
    replaces pre-existing project files, and earlier sprints' generated code
    keeps working (and keeps being tested) after later sprints run.
    """
    return "ai_sd_os_generated_" + wp_id.lower().replace("-", "_")


class WorkPackage(BaseModel):
    id: str = Field(..., description="WorkPackage ID (e.g. WP-001)")
    sprint_id: str = Field(..., description="Sprint ID (e.g. SPRINT-001)")
    goal: str
    allowed_paths: List[str] = Field(default_factory=lambda: ["src/", "tests/"])
    tasks: List[TaskItem] = Field(default_factory=list)
    max_execution_time_minutes: int = 30
    tests_required: bool = True
    coverage_mapping: Dict[str, List[str]] = Field(default_factory=dict)

    def module_name(self) -> str:
        return _wp_module_name(self.id)

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
