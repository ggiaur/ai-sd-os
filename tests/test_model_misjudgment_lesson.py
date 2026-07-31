"""Proves a wrong 'this looks simple' model choice leaves a reviewable trail.

Constitution rule: kernel behavior (here, the model_selector heuristic) is
never auto-tuned — a human decides whether/how to adjust it. This only checks
that the EVIDENCE for that decision actually gets recorded when the light
model demonstrably fails on a WorkPackage the heuristic called "simple".
"""

import pytest
from pathlib import Path

from agents.developer_agent import DeveloperAgent, MOTOR_DIR
from kernel.event_bus.bus import EventBus
from kernel.event_bus.events import Event, EventType
from sdk.provider_adapter import MockProviderAdapter
from lessons.aggregator import LessonsAggregator


@pytest.mark.asyncio
async def test_retry_after_simple_wp_first_failure_logs_a_lesson(tmp_path, monkeypatch):
    lessons_file = tmp_path / "lessons_learned.yaml"
    monkeypatch.setattr(
        "agents.developer_agent.MOTOR_DIR", tmp_path
    )

    bus = EventBus()
    agent = DeveloperAgent(
        "DeveloperAgent", bus, MockProviderAdapter(),
        light_model="haiku", default_model="sonnet-4-6", escalation_model="sonnet-5",
    )

    wp = {
        "id": "WP-001", "sprint_id": "SPRINT-001", "goal": "g",
        "tasks": [{"task_id": "TASK-001", "description": "short",
                   "requirement_ref": "FR-001", "expected_output": "X"}],
        "coverage_mapping": {"FR-001": ["test_fr_001_feature"]},
    }

    await agent.handle_retry(Event(
        event_type=EventType.TESTS_FAILED,
        payload={
            "work_package": wp, "project_root": str(tmp_path / "project"),
            "error": "assertion failed", "retry_count": 0, "max_retries": 3,
        },
        correlation_id="corr-1",
    ))

    aggregator = LessonsAggregator(motor_dir=tmp_path)
    data = aggregator.load_lessons()
    patterns = [e["pattern"] for e in data["entries"]]
    assert "light_model misjudged a WorkPackage as simple" in patterns


@pytest.mark.asyncio
async def test_no_lesson_logged_when_wp_was_never_judged_simple(tmp_path, monkeypatch):
    monkeypatch.setattr("agents.developer_agent.MOTOR_DIR", tmp_path)

    bus = EventBus()
    agent = DeveloperAgent(
        "DeveloperAgent", bus, MockProviderAdapter(),
        light_model="haiku", default_model="sonnet-4-6", escalation_model="sonnet-5",
    )

    wp = {
        "id": "WP-001", "sprint_id": "SPRINT-001", "goal": "g",
        "tasks": [{"task_id": "TASK-001", "description": "x" * 300,
                   "requirement_ref": "FR-001", "expected_output": "X"}],
        "coverage_mapping": {"FR-001": ["test_fr_001_feature"]},
    }

    await agent.handle_retry(Event(
        event_type=EventType.TESTS_FAILED,
        payload={
            "work_package": wp, "project_root": str(tmp_path / "project"),
            "error": "assertion failed", "retry_count": 0, "max_retries": 3,
        },
        correlation_id="corr-1",
    ))

    aggregator = LessonsAggregator(motor_dir=tmp_path)
    data = aggregator.load_lessons()
    assert data["entries"] == []
