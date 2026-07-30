import pytest
from kernel.event_bus.bus import EventBus
from kernel.event_bus.events import Event, EventType
from kernel.state.states import ProjectState
from kernel.state.validators import validate_transition, InvalidStateTransitionError

@pytest.mark.asyncio
async def test_event_bus_publishing():
    bus = EventBus()
    received = []

    async def handler(evt: Event):
        received.append(evt)

    bus.subscribe(EventType.SPEC_CREATED, handler)
    evt = Event(event_type=EventType.SPEC_CREATED, payload={"test": 123})
    await bus.publish(evt)

    assert len(received) == 1
    assert received[0].payload["test"] == 123
    assert len(bus.history) == 1

def test_state_transitions():
    validate_transition(ProjectState.INIT, ProjectState.SPEC)
    validate_transition(ProjectState.SPEC, ProjectState.WORK_PACKAGE)

    with pytest.raises(InvalidStateTransitionError):
        validate_transition(ProjectState.INIT, ProjectState.DONE)
