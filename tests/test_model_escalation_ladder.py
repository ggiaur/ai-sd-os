from contracts.work_package import WorkPackage, TaskItem
from sdk.model_selector import select_model_for_attempt

LIGHT, DEFAULT, ESCALATION = "haiku", "sonnet-4-6", "sonnet-5"


def _simple_wp():
    return WorkPackage(
        id="WP-001", sprint_id="SPRINT-001", goal="g",
        tasks=[TaskItem(task_id="TASK-001", description="short", requirement_ref="FR-001",
                        expected_output="X")],
    )


def _complex_wp():
    return WorkPackage(
        id="WP-002", sprint_id="SPRINT-001", goal="g",
        tasks=[TaskItem(task_id="TASK-001", description="x" * 300, requirement_ref="FR-001",
                        expected_output="X")],
    )


def test_first_attempt_simple_uses_light():
    assert select_model_for_attempt(_simple_wp(), 0, 3, LIGHT, DEFAULT, ESCALATION) == LIGHT


def test_first_attempt_complex_uses_default():
    assert select_model_for_attempt(_complex_wp(), 0, 3, LIGHT, DEFAULT, ESCALATION) == DEFAULT


def test_mid_retry_uses_default_even_for_simple_wp():
    # Already failed once on light — don't just retry the same cheap model.
    assert select_model_for_attempt(_simple_wp(), 1, 3, LIGHT, DEFAULT, ESCALATION) == DEFAULT


def test_last_retry_escalates_regardless_of_simplicity():
    assert select_model_for_attempt(_simple_wp(), 2, 3, LIGHT, DEFAULT, ESCALATION) == ESCALATION
    assert select_model_for_attempt(_complex_wp(), 2, 3, LIGHT, DEFAULT, ESCALATION) == ESCALATION


def test_first_attempt_never_escalates_even_with_max_retries_one():
    # retry_count=0 must never escalate, regardless of how small max_retries is.
    assert select_model_for_attempt(_complex_wp(), 0, 1, LIGHT, DEFAULT, ESCALATION) == DEFAULT


def test_zero_max_retries_never_escalates():
    assert select_model_for_attempt(_complex_wp(), 0, 0, LIGHT, DEFAULT, ESCALATION) == DEFAULT
