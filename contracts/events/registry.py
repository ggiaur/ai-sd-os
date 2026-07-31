from typing import Dict, Optional, Type

from pydantic import BaseModel, ValidationError

from kernel.contracts.validator import ContractValidationError
from kernel.event_bus.events import Event, EventType

from contracts.events.gate_events import (
    ActionDestructiveRequestedPayload,
    LessonsLearnedUpdatedPayload,
    PipelineBlockedPayload,
    RetrospectiveRecordedPayload,
    SprintPlanningApprovedPayload,
    SprintPlanningProposedPayload,
    SprintReviewApprovedPayload,
    SprintReviewRequestedPayload,
)
from contracts.events.spec_events import CodebaseSurveyedPayload, SpecCreatedPayload
from contracts.events.sprint_events import (
    DevelopmentCompletedPayload,
    TestsFailedPayload,
    TestsPassedPayload,
    WorkPackageCreatedPayload,
)

EVENT_PAYLOAD_SCHEMAS: Dict[EventType, Type[BaseModel]] = {
    EventType.SPEC_CREATED: SpecCreatedPayload,
    EventType.CODEBASE_SURVEYED: CodebaseSurveyedPayload,
    EventType.WORKPACKAGE_CREATED: WorkPackageCreatedPayload,
    EventType.SPRINT_PLANNING_PROPOSED: SprintPlanningProposedPayload,
    EventType.SPRINT_PLANNING_APPROVED: SprintPlanningApprovedPayload,
    EventType.DEVELOPMENT_COMPLETED: DevelopmentCompletedPayload,
    EventType.TESTS_PASSED: TestsPassedPayload,
    EventType.TESTS_FAILED: TestsFailedPayload,
    EventType.SPRINT_REVIEW_REQUESTED: SprintReviewRequestedPayload,
    EventType.SPRINT_REVIEW_APPROVED: SprintReviewApprovedPayload,
    EventType.PIPELINE_BLOCKED: PipelineBlockedPayload,
    EventType.RETROSPECTIVE_RECORDED: RetrospectiveRecordedPayload,
    EventType.LESSONS_LEARNED_UPDATED: LessonsLearnedUpdatedPayload,
    EventType.ACTION_DESTRUCTIVE_REQUESTED: ActionDestructiveRequestedPayload,
}


def validate_event_payload(event: Event) -> Optional[BaseModel]:
    """Ellenőrzi az esemény payload-ját a hozzá tartozó séma alapján, ha van ilyen.

    Ismeretlen event_type-ra (nincs regisztrált séma) None-t ad vissza —
    a validáció csak a regisztrált, kritikus eseménytípusokra kötelező.
    """
    schema_cls = EVENT_PAYLOAD_SCHEMAS.get(event.event_type)
    if schema_cls is None:
        return None
    try:
        return schema_cls.model_validate(event.payload)
    except ValidationError as err:
        raise ContractValidationError(event.event_type.value, err) from err
