from kernel.state.states import ProjectState
from kernel.state.transitions import ALLOWED_TRANSITIONS

class InvalidStateTransitionError(Exception):
    def __init__(self, current_state: ProjectState, target_state: ProjectState, reason: str = ""):
        message = f"Illegal transition from {current_state.value} to {target_state.value}."
        if reason:
            message += f" Reason: {reason}"
        super().__init__(message)
        self.current_state = current_state
        self.target_state = target_state

def validate_transition(current: ProjectState, target: ProjectState) -> None:
    if current == target:
        return
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(current, target, f"Target '{target.value}' is not in allowed next states: {[s.value for s in allowed]}")
