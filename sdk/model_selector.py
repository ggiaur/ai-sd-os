"""Shared complexity heuristic for picking a model.

Used identically for BOTH code generation (DeveloperAgent) and independent
review (TestRunner) — one decision, applied uniformly, not two separately
tuned heuristics that could quietly drift apart.

Deliberately simple: a WorkPackage with a single short, well-specified task
is cheap to get right and doesn't need a stronger (slower, costlier) model.
Anything bigger — multiple tasks, or a task with a substantial description —
gets the stronger model. This is a starting heuristic, not a claim of being
optimal; it exists so the choice is explicit and testable instead of a single
hardcoded model everywhere.
"""

from contracts.work_package import WorkPackage

SIMPLE_TASK_COUNT_THRESHOLD = 1
SIMPLE_DESCRIPTION_LENGTH_THRESHOLD = 200


def is_simple_work_package(wp: WorkPackage) -> bool:
    total_description_length = sum(len(t.description) for t in wp.tasks)
    return (
        len(wp.tasks) <= SIMPLE_TASK_COUNT_THRESHOLD
        and total_description_length < SIMPLE_DESCRIPTION_LENGTH_THRESHOLD
    )


def select_model(wp: WorkPackage, light_model: str, strong_model: str) -> str:
    return light_model if is_simple_work_package(wp) else strong_model
