"""A completed requirement must not stay PENDING forever.

Without this, re-running the engine on an already-done project re-selects and
re-"implements" the same requirement on every run, producing misleading
repeat commits for work that was already finished.
"""

from pathlib import Path

from agents.retrospective_collector import RetrospectiveCollector
from contracts.spec_formal import SpecFormal, RequirementItem, PriorityEnum, RequirementStatus
from kernel.contracts.serializer import save_yaml_contract, load_yaml_contract


def test_mark_requirements_satisfied_updates_spec_file(tmp_path):
    spec = SpecFormal(
        project_name="demo",
        goal="demo goal",
        tech_stack=["python"],
        requirements=[
            RequirementItem(id="FR-001", title="T1", description="D1",
                             priority=PriorityEnum.HIGH, status=RequirementStatus.PENDING),
            RequirementItem(id="FR-002", title="T2", description="D2",
                             priority=PriorityEnum.HIGH, status=RequirementStatus.PENDING),
        ],
    )
    spec_file = tmp_path / ".ai-sd-os" / "SPEC_FORMAL.yaml"
    save_yaml_contract(spec, spec_file)

    wp = {"tasks": [{"requirement_ref": "FR-001"}]}
    RetrospectiveCollector._mark_requirements_satisfied(tmp_path, wp)

    reloaded = load_yaml_contract(spec_file, SpecFormal)
    statuses = {r.id: r.status for r in reloaded.requirements}
    assert statuses["FR-001"] == RequirementStatus.SATISFIED
    assert statuses["FR-002"] == RequirementStatus.PENDING
