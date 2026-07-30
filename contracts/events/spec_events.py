from contracts.events.base_event import BaseEvent

class SpecCreatedEvent(BaseEvent):
    event_type: str = "spec.created"

class DiscoveryCompletedEvent(BaseEvent):
    event_type: str = "discovery.completed"
