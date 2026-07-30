import pytest
from pydantic import ValidationError

from contracts.events.registry import EVENT_PAYLOAD_SCHEMAS, validate_event_payload
from contracts.events.sprint_events import TestsFailedPayload
from kernel.contracts.validator import ContractValidationError
from kernel.event_bus.events import Event, EventType


def test_registry_has_a_schema_for_every_pipeline_critical_event():
    for expected in [
        EventType.SPEC_CREATED,
        EventType.WORKPACKAGE_CREATED,
        EventType.SPRINT_PLANNING_APPROVED,
        EventType.DEVELOPMENT_COMPLETED,
        EventType.TESTS_PASSED,
        EventType.TESTS_FAILED,
        EventType.PIPELINE_BLOCKED,
    ]:
        assert expected in EVENT_PAYLOAD_SCHEMAS


def test_validate_event_payload_accepts_well_formed_payload():
    event = Event(
        event_type=EventType.TESTS_FAILED,
        payload={
            "work_package": {"id": "WP-001"},
            "project_root": ".",
            "error": "AssertionError",
            "retry_count": 1,
            "max_retries": 3,
        },
    )
    result = validate_event_payload(event)
    assert isinstance(result, TestsFailedPayload)
    assert result.retry_count == 1


def test_validate_event_payload_rejects_missing_required_fields():
    event = Event(
        event_type=EventType.TESTS_FAILED,
        payload={"work_package": {"id": "WP-001"}},
    )
    with pytest.raises(ContractValidationError):
        validate_event_payload(event)


def test_validate_event_payload_returns_none_for_unregistered_event_type():
    event = Event(event_type=EventType.SYSTEM_ERROR, payload={"anything": True})
    assert validate_event_payload(event) is None
