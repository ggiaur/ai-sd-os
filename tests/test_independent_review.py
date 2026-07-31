"""Proves the independent QA review catches what the acceptance test cannot.

This is the direct answer to "the tests are too easy to pass": before this,
verification was a SINGLE signal — did pytest return the exact expected
string. Code that returns the right value while doing something else bad
(leaking a secret, calling eval()) sailed through. Now there are two
INDEPENDENT checks that must both pass, using different methods, and this
file proves the second one actually rejects things the first one would miss.
"""

import pytest
from pathlib import Path

from kernel.event_bus.bus import EventBus
from kernel.event_bus.events import Event, EventType
from runtime.test_runner import TestRunnerAgent
from sdk.provider_adapter import MockProviderAdapter, ReviewResult
from contracts.work_package import WorkPackage, TaskItem


def _make_wp() -> WorkPackage:
    return WorkPackage(
        id="WP-777",
        sprint_id="SPRINT-777",
        goal="Independent review check",
        tasks=[
            TaskItem(task_id="TASK-001", description="d", requirement_ref="FR-001",
                      expected_output="FR-001-DONE")
        ],
        coverage_mapping={"FR-001": ["test_fr_001_feature"]},
    )


def _write_acceptance_test(project_root: Path) -> None:
    tests_dir = project_root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "__init__.py").touch()
    (tests_dir / "test_app.py").write_text(
        "import sys, os\nsys.path.insert(0, os.path.abspath('.'))\n"
        "from src.app import fr_001_feature\n\n"
        "def test_fr_001_feature():\n"
        "    assert fr_001_feature() == 'FR-001-DONE'\n",
        encoding="utf-8",
    )


def _write_implementation(project_root: Path, body: str) -> str:
    src_dir = project_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").touch()
    code = f"def fr_001_feature():\n{body}\n    return 'FR-001-DONE'\n"
    (src_dir / "app.py").write_text(code, encoding="utf-8")
    return code


async def _run(project_root: Path, written_files: dict):
    bus = EventBus()
    passed_events, failed_events = [], []

    async def on_passed(evt):
        passed_events.append(evt)

    async def on_failed(evt):
        failed_events.append(evt)

    bus.subscribe(EventType.TESTS_PASSED, on_passed)
    bus.subscribe(EventType.TESTS_FAILED, on_failed)

    runner = TestRunnerAgent("TestRunnerAgent", bus, MockProviderAdapter())
    await runner.process_event(Event(
        event_type=EventType.DEVELOPMENT_COMPLETED,
        payload={
            "work_package": _make_wp().model_dump(),
            "project_root": str(project_root),
            "retry_count": 0,
            "written_files": written_files,
        },
        correlation_id="corr-review",
    ))
    return passed_events, failed_events


@pytest.mark.asyncio
async def test_pytest_alone_would_pass_but_independent_review_rejects_leaked_secret(tmp_path):
    """The acceptance test only checks the return value — it has no idea a
    hardcoded API key sits right next to it. The independent reviewer does.
    """
    _write_acceptance_test(tmp_path)
    code = _write_implementation(
        tmp_path, '    api_key = "sk-ant-abcdefghijklmnopqrstuvwx"  # leaked secret\n'
    )

    passed_events, failed_events = await _run(tmp_path, {"src/app.py": code})

    assert len(failed_events) == 1, "a leaked secret must fail verification even if pytest passes"
    assert len(passed_events) == 0
    assert "secret" in failed_events[0].payload["error"].lower()


@pytest.mark.asyncio
async def test_pytest_alone_would_pass_but_independent_review_rejects_eval(tmp_path):
    _write_acceptance_test(tmp_path)
    code = _write_implementation(tmp_path, '    eval("1+1")  # dangerous\n')

    passed_events, failed_events = await _run(tmp_path, {"src/app.py": code})

    assert len(failed_events) == 1
    assert len(passed_events) == 0
    assert "eval" in failed_events[0].payload["error"].lower()


@pytest.mark.asyncio
async def test_clean_implementation_passes_both_checks(tmp_path):
    _write_acceptance_test(tmp_path)
    code = _write_implementation(tmp_path, "")

    passed_events, failed_events = await _run(tmp_path, {"src/app.py": code})

    assert len(passed_events) == 1, "clean code must still pass — the reviewer isn't a rubber stamp either way"
    assert len(failed_events) == 0


@pytest.mark.asyncio
async def test_review_result_feedback_is_not_generic_boilerplate():
    """A reviewer whose feedback text never changes regardless of input is
    itself a rubber stamp. Confirm the mock reviewer's feedback differs
    between a rejection and an approval.
    """
    provider = MockProviderAdapter()
    bad = await provider.review('api_key = "sk-ant-abcdefghijklmnopqrstuvwx"', criteria=["no secrets"])
    good = await provider.review("def f():\n    return 1\n", criteria=["no secrets"])

    assert isinstance(bad, ReviewResult) and isinstance(good, ReviewResult)
    assert bad.passed is False
    assert good.passed is True
    assert bad.feedback != good.feedback
