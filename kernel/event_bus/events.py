from enum import Enum

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

from contracts.events.base_event import BaseEvent as Event
