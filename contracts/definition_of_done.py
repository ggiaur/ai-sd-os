from typing import List
from pydantic import BaseModel, Field, field_validator
import re

class DoDCriterion(BaseModel):
    id: str = Field(..., description="DoD ID (e.g. DOD-001)")
    description: str
    automated_check: bool = True

    @field_validator("id")

    def validate_dod_id(cls, v: str) -> str:
        if not re.match(r"^DOD-\d+$", v):
            raise ValueError(f"DoD ID must match pattern DOD-XXX, got: {v}")
        return v

class DefinitionOfDone(BaseModel):
    work_package_ref: str
    criteria: List[DoDCriterion] = Field(default_factory=list)
