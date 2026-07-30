from runtime.test_runner import TestRunnerAgent
from contracts.work_package import WorkPackage, TaskItem
from sdk.provider_adapter import MockProviderAdapter
from kernel.event_bus.bus import EventBus

def test_coverage_mapping_validation(tmp_path):
    bus = EventBus()
    agent = TestRunnerAgent("TestRunner", bus, MockProviderAdapter())

    wp = WorkPackage(
        id="WP-001",
        sprint_id="SPRINT-001",
        goal="Test goal",
        tasks=[TaskItem(task_id="TASK-001", description="desc", requirement_ref="FR-001")],
        coverage_mapping={"FR-001": ["test_feature_x"]}
    )

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text("def test_feature_x(): pass\n", encoding="utf-8")

    passed, errors = agent._verify_coverage_mapping(tmp_path, wp, "test_feature_x PASSED")
    assert passed is True
    assert len(errors) == 0

    # Missing test verification
    wp_missing = WorkPackage(
        id="WP-002",
        sprint_id="SPRINT-001",
        goal="Test goal",
        tasks=[TaskItem(task_id="TASK-001", description="desc", requirement_ref="FR-002")],
        coverage_mapping={"FR-002": ["test_missing_feature"]}
    )
    passed_missing, errors_missing = agent._verify_coverage_mapping(tmp_path, wp_missing, "")
    assert passed_missing is False
    assert len(errors_missing) > 0
