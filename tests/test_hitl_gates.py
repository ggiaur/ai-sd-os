import pytest
from kernel.event_bus.bus import EventBus
from kernel.event_bus.events import Event, EventType
from kernel.hitl.gate_manager import HITLGateManager

@pytest.mark.asyncio
async def test_hitl_gate_auto_approve():
    bus = EventBus()
    gate_mgr = HITLGateManager(bus, auto_approve=True)

    approved_events = []
    async def handler(evt: Event):
        approved_events.append(evt)

    bus.subscribe(EventType.SPRINT_PLANNING_APPROVED, handler)

    wp = {"id": "WP-001", "sprint_id": "SPRINT-001", "goal": "Auto approve test"}
    await bus.publish(Event(
        event_type=EventType.WORKPACKAGE_CREATED,
        payload={"work_package": wp, "selected_requirements": []}
    ))

    assert len(approved_events) == 1
    assert approved_events[0].payload["sprint_id"] == "SPRINT-001"
