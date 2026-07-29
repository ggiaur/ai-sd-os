from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class AgentStatusCode(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRY_REQUIRED = "RETRY_REQUIRED"
    BLOCKED = "BLOCKED"

class AgentContext(BaseModel):
    project_root: Path
    sprint_id: Optional[str] = None
    carry_forward_note: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

class ExecutionResult(BaseModel):
    status: AgentStatusCode
    output_files: Dict[str, str] = Field(default_factory=dict) # path -> content
    logs: str = ""
    error_message: Optional[str] = None
    retry_count: int = 0
