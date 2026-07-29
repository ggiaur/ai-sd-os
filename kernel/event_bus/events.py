import time
import uuid
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class EventType(str, Enum):
    SYSTEM_INITIALIZED = "system.initialized"
    DISCOVERY_COMPLETED = "discovery.completed"
    CODEBASE_SURVEYED = "codebase.surveyed"
    SPEC_CREATED = "spec.created"
    WORKPACKAGE_CREATED = "workpackage.created"
    SPRINT_PLANNING_PROPOSED = "sprint.planning.proposed"
    SPRINT_PLANNING_APPROVED = "sprint.planning.approved"
    DEVELOPMENT_COMPLETED = "development.completed"
    TESTS_PASSED = "tests.passed"
    TESTS_FAILED = "tests.failed"
    SPRINT_REVIEW_REQUESTED = "sprint.review.requested"
    SPRINT_REVIEW_APPROVED = "sprint.review.approved"
    PIPELINE_BLOCKED = "pipeline.blocked"
    ACTION_DESTRUCTIVE_REQUESTED = "action.destructive.requested"
    RETROSPECTIVE_RECORDED = "retrospective.recorded"
    LESSONS_LEARNED_UPDATED = "lessons.learned.updated"
    SYSTEM_ERROR = "system.error"

class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    sender: str = "system"
