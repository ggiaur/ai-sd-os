from contracts.events.base_event import BaseEvent

class WorkPackageCreatedEvent(BaseEvent):
    event_type: str = "workpackage.created"

class DevelopmentCompletedEvent(BaseEvent):
    event_type: str = "development.completed"

class TestsPassedEvent(BaseEvent):
    event_type: str = "tests.passed"

class TestsFailedEvent(BaseEvent):
    event_type: str = "tests.failed"
