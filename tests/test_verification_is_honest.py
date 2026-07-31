"""Proves the verification pipeline actually discriminates correct vs. broken code.

This exists because the DeveloperAgent used to write both the implementation
and a test that trivially matched it — meaning TESTS_PASSED was guaranteed by
construction, not by anything being verified. These tests simulate the fixed
architecture: an acceptance test is written independently from the spec (as
ArchitectAgent now does), and only THEN is an implementation checked against
it. A real verification system must fail the red case and pass the green one.
"""

import pytest
from pathlib import Path

from kernel.event_bus.bus import EventBus
from kernel.event_bus.events import Event, EventType
from runtime.test_runner import TestRunnerAgent
from sdk.provider_adapter import MockProviderAdapter
from contracts.work_package import WorkPackage, TaskItem


def _make_wp() -> WorkPackage:
    return WorkPackage(
        id="WP-999",
        sprint_id="SPRINT-999",
        goal="Honest verification check",
        tasks=[
            TaskItem(
                task_id="TASK-001",
                description="Return the sentinel value for FR-001",
                requirement_ref="FR-001",
                expected_output="FR-001-DONE",
            )
        ],
        coverage_mapping={"FR-001": ["test_fr_001_feature"]},
    )


def _write_spec_first_acceptance_test(project_root: Path) -> None:
    """What ArchitectAgent writes BEFORE any implementation exists."""
    tests_dir = project_root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "__init__.py").touch()
    (tests_dir / "test_app.py").write_text(
        "import sys, os\n"
        "sys.path.insert(0, os.path.abspath('.'))\n"
        "from src.app import fr_001_feature\n\n"
        "def test_fr_001_feature():\n"
        "    assert fr_001_feature() == 'FR-001-DONE'\n",
        encoding="utf-8",
    )


def _write_implementation(project_root: Path, return_value: str) -> None:
    src_dir = project_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").touch()
    (src_dir / "app.py").write_text(
        f"def fr_001_feature():\n    return {return_value!r}\n",
        encoding="utf-8",
    )


async def _run_test_runner(project_root: Path):
    bus = EventBus()
    passed_events, failed_events = [], []

    async def on_passed(evt: Event):
        passed_events.append(evt)

    async def on_failed(evt: Event):
        failed_events.append(evt)

    bus.subscribe(EventType.TESTS_PASSED, on_passed)
    bus.subscribe(EventType.TESTS_FAILED, on_failed)

    runner = TestRunnerAgent("TestRunnerAgent", bus, MockProviderAdapter())
    wp = _make_wp()

    await runner.process_event(Event(
        event_type=EventType.DEVELOPMENT_COMPLETED,
        payload={
            "work_package": wp.model_dump(),
            "project_root": str(project_root),
            "retry_count": 0,
        },
        correlation_id="corr-verification-honesty",
    ))

    return passed_events, failed_events


@pytest.mark.asyncio
async def test_verification_fails_a_genuinely_wrong_implementation(tmp_path):
    """RED: an implementation that violates the spec's acceptance test must be rejected."""
    _write_spec_first_acceptance_test(tmp_path)
    _write_implementation(tmp_path, "SOMETHING-ELSE-ENTIRELY")

    passed_events, failed_events = await _run_test_runner(tmp_path)

    assert len(failed_events) == 1, "a broken implementation must produce TESTS_FAILED"
    assert len(passed_events) == 0, "a broken implementation must never produce TESTS_PASSED"
    assert "FR-001" in failed_events[0].payload["error"]


@pytest.mark.asyncio
async def test_verification_passes_a_genuinely_correct_implementation(tmp_path):
    """GREEN: an implementation that satisfies the spec's acceptance test must be accepted."""
    _write_spec_first_acceptance_test(tmp_path)
    _write_implementation(tmp_path, "FR-001-DONE")

    passed_events, failed_events = await _run_test_runner(tmp_path)

    assert len(passed_events) == 1, "a correct implementation must produce TESTS_PASSED"
    assert len(failed_events) == 0, "a correct implementation must never produce TESTS_FAILED"


@pytest.mark.asyncio
async def test_verification_rejects_missing_implementation(tmp_path):
    """RED: no src/app.py at all (e.g. codegen produced nothing usable) must fail loudly, not pass by accident."""
    _write_spec_first_acceptance_test(tmp_path)
    # Deliberately do not create src/app.py at all.
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "__init__.py").touch()

    passed_events, failed_events = await _run_test_runner(tmp_path)

    assert len(failed_events) == 1
    assert len(passed_events) == 0
