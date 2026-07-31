from contracts.work_package import WorkPackage, TaskItem
from sdk.model_selector import select_model, is_simple_work_package


def _wp(tasks):
    return WorkPackage(id="WP-001", sprint_id="SPRINT-001", goal="g", tasks=tasks)


def test_single_short_task_is_simple():
    wp = _wp([TaskItem(task_id="TASK-001", description="short", requirement_ref="FR-001",
                        expected_output="X")])
    assert is_simple_work_package(wp) is True
    assert select_model(wp, "light", "strong") == "light"


def test_multiple_tasks_is_not_simple():
    wp = _wp([
        TaskItem(task_id="TASK-001", description="short", requirement_ref="FR-001", expected_output="X"),
        TaskItem(task_id="TASK-002", description="short", requirement_ref="FR-002", expected_output="Y"),
    ])
    assert is_simple_work_package(wp) is False
    assert select_model(wp, "light", "strong") == "strong"


def test_single_but_long_task_is_not_simple():
    wp = _wp([TaskItem(task_id="TASK-001", description="x" * 500, requirement_ref="FR-001",
                        expected_output="X")])
    assert is_simple_work_package(wp) is False
    assert select_model(wp, "light", "strong") == "strong"
