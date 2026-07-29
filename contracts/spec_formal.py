from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import re

class PriorityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RequirementStatus(str, Enum):
    PENDING = "PENDING"
    SATISFIED = "SATISFIED"
    IN_PROGRESS = "IN_PROGRESS"

class RequirementItem(BaseModel):
    id: str = Field(..., description="Requirement ID (e.g. FR-001)")
    title: str
    description: str
    priority: PriorityEnum = PriorityEnum.MEDIUM
    status: RequirementStatus = RequirementStatus.PENDING

    @field_validator("id")

    def validate_fr_id(cls, v: str) -> str:
        if not re.match(r"^FR-\d+$", v):
            raise ValueError(f"Requirement ID must match pattern FR-XXX, got: {v}")
        return v

class SpecFormal(BaseModel):
    project_name: str
    version: str = "1.0.0"
    goal: str
    tech_stack: List[str] = Field(default_factory=list)
    requirements: List[RequirementItem] = Field(default_factory=list)

    @field_validator("tech_stack")

    def validate_tech_stack(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("tech_stack must contain at least 1 technology item")
        return v

    @field_validator("requirements")

    def validate_requirements(cls, v: List[RequirementItem]) -> List[RequirementItem]:
        if not v:
            raise ValueError("requirements must contain at least 1 requirement item")
        return v
