"""Regression test for a real, live-verified bug: DeveloperAgent used to
write to a fixed `src/app.py` / `tests/test_app.py`, silently deleting
whatever a human already had there. This is exactly what happens when
adopting an existing project — the single most important scenario for this
engine to get right, since a code generator that destroys the code you asked
it to adopt is worse than useless.
"""

import pytest
from pathlib import Path

from kernel.event_bus.bus import EventBus
from agents.architect_agent import ArchitectAgent
from agents.developer_agent import DeveloperAgent
from sdk.provider_adapter import MockProviderAdapter
from contracts.spec_formal import SpecFormal, RequirementItem, PriorityEnum, RequirementStatus
from kernel.event_bus.events import Event, EventType


@pytest.mark.asyncio
async def test_pipeline_never_touches_preexisting_src_and_test_files(tmp_path):
    # A human's real, pre-existing project content.
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text(
        "def test_hello():\n    assert True\n", encoding="utf-8"
    )

    bus = EventBus()
    provider = MockProviderAdapter()
    architect = ArchitectAgent("ArchitectAgent", bus, provider)
    developer = DeveloperAgent("DeveloperAgent", bus, provider)

    spec = SpecFormal(
        project_name="existing-demo",
        goal="demo",
        tech_stack=["python"],
        requirements=[
            RequirementItem(id="FR-001", title="New feature", description="desc",
                             priority=PriorityEnum.HIGH, status=RequirementStatus.PENDING)
        ],
    )

    await bus.publish(Event(
        event_type=EventType.SPEC_CREATED,
        payload={"spec": spec.model_dump(), "project_root": str(tmp_path)},
        correlation_id="corr-1",
    ))
    await bus.publish(Event(
        event_type=EventType.SPRINT_PLANNING_APPROVED,
        payload={
            "work_package": _last_workpackage(bus),
            "project_root": str(tmp_path),
        },
        correlation_id="corr-1",
    ))

    # The human's original files must be byte-for-byte untouched.
    assert (tmp_path / "src" / "app.py").read_text(encoding="utf-8") == "def hello():\n    return 'hi'\n"
    assert (tmp_path / "tests" / "test_app.py").read_text(encoding="utf-8") == (
        "def test_hello():\n    assert True\n"
    )

    # The engine's own generated files must exist ALONGSIDE, not instead of, them.
    generated_modules = list((tmp_path / "src").glob("ai_sd_os_generated_*.py"))
    assert len(generated_modules) == 1


def _last_workpackage(bus: EventBus) -> dict:
    for evt in reversed(bus.history):
        if evt.event_type == EventType.WORKPACKAGE_CREATED:
            return evt.payload["work_package"]
    raise AssertionError("ArchitectAgent did not emit WORKPACKAGE_CREATED")
