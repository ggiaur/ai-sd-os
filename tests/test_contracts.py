import pytest
from pydantic import ValidationError
from contracts.spec_formal import SpecFormal, RequirementItem, PriorityEnum, RequirementStatus
from contracts.work_package import WorkPackage, TaskItem
from contracts.definition_of_done import DefinitionOfDone, DoDCriterion

def test_spec_formal_validation():
    req = RequirementItem(
        id="FR-001",
        title="Test req",
        description="Test desc",
        priority=PriorityEnum.HIGH,
        status=RequirementStatus.PENDING
    )
    spec = SpecFormal(
        project_name="TestApp",
        version="1.0.0",
        goal="Build test app",
        tech_stack=["python"],
        requirements=[req]
    )
    assert spec.project_name == "TestApp"

    with pytest.raises(ValidationError):
        RequirementItem(id="INVALID-ID", title="T", description="D")

def test_work_package_validation():
    task = TaskItem(task_id="TASK-001", description="Do task", requirement_ref="FR-001", expected_output="FR-001-DONE")
    wp = WorkPackage(
        id="WP-001",
        sprint_id="SPRINT-001",
        goal="Sprint goal",
        tasks=[task],
        coverage_mapping={"FR-001": ["test_do_task"]}
    )
    assert wp.id == "WP-001"
    assert wp.coverage_mapping["FR-001"] == ["test_do_task"]
