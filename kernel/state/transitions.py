from typing import Dict, Set
from kernel.state.states import ProjectState

ALLOWED_TRANSITIONS: Dict[ProjectState, Set[ProjectState]] = {
    ProjectState.INIT: {ProjectState.DISCOVERY, ProjectState.SPEC},
    ProjectState.DISCOVERY: {ProjectState.SPEC},
    ProjectState.SPEC: {ProjectState.WORK_PACKAGE},
    ProjectState.WORK_PACKAGE: {ProjectState.SPRINT_PLANNING, ProjectState.DONE},
    ProjectState.SPRINT_PLANNING: {ProjectState.DEVELOPMENT, ProjectState.WORK_PACKAGE},
    ProjectState.DEVELOPMENT: {ProjectState.TEST, ProjectState.BLOCKED},
    ProjectState.TEST: {ProjectState.DEVELOPMENT, ProjectState.SPRINT_REVIEW, ProjectState.BLOCKED},
    ProjectState.BLOCKED: {ProjectState.DEVELOPMENT, ProjectState.WORK_PACKAGE, ProjectState.SPEC},
    ProjectState.SPRINT_REVIEW: {ProjectState.PR_CREATED, ProjectState.DEVELOPMENT},
    ProjectState.PR_CREATED: {ProjectState.RETROSPECTIVE},
    ProjectState.RETROSPECTIVE: {ProjectState.WORK_PACKAGE, ProjectState.DONE},
    ProjectState.DONE: set()
}
