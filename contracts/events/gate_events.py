from contracts.events.base_event import BaseEvent

class SprintPlanningProposedEvent(BaseEvent):
    event_type: str = "sprint.planning.proposed"

class SprintPlanningApprovedEvent(BaseEvent):
    event_type: str = "sprint.planning.approved"

class SprintReviewRequestedEvent(BaseEvent):
    event_type: str = "sprint.review.requested"

class SprintReviewApprovedEvent(BaseEvent):
    event_type: str = "sprint.review.approved"

class PipelineBlockedEvent(BaseEvent):
    event_type: str = "pipeline.blocked"
