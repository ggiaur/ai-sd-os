"""Proves DeveloperAgent and TestRunnerAgent actually apply model selection —
not just that the heuristic function works in isolation.
"""

import pytest
from pathlib import Path
from typing import List, Optional

from sdk.provider_adapter import AIProvider, ReviewResult, AnalysisResult
from agents.developer_agent import DeveloperAgent
from runtime.test_runner import TestRunnerAgent
from kernel.event_bus.bus import EventBus
from kernel.event_bus.events import Event, EventType
from contracts.work_package import WorkPackage, TaskItem


class _CapturingProvider(AIProvider):
    """Records what model each call was asked to use; returns canned, valid output."""

    def __init__(self):
        self.generate_calls = []
        self.review_calls = []

    async def generate(self, prompt: str, context: Optional[dict] = None) -> str:
        self.generate_calls.append((context or {}).get("model"))
        return "```python\ndef fr_001_feature():\n    return 'FR-001-DONE'\n```"

    async def review(self, code: str, criteria: List[str], context: Optional[dict] = None) -> ReviewResult:
        self.review_calls.append((context or {}).get("model"))
        return ReviewResult(passed=True, feedback="ok")

    async def embed(self, text: str) -> List[float]:
        return [0.0]

    async def analyze(self, artifact: str) -> AnalysisResult:
        return AnalysisResult(summary="", key_findings=[])


def _simple_wp():
    return WorkPackage(
        id="WP-001", sprint_id="SPRINT-001", goal="g",
        tasks=[TaskItem(task_id="TASK-001", description="short", requirement_ref="FR-001",
                        expected_output="FR-001-DONE")],
        coverage_mapping={"FR-001": ["test_fr_001_feature"]},
    )


def _complex_wp():
    return WorkPackage(
        id="WP-002", sprint_id="SPRINT-001", goal="g",
        tasks=[
            TaskItem(task_id="TASK-001", description="a" * 300, requirement_ref="FR-001",
                     expected_output="FR-001-DONE"),
        ],
        coverage_mapping={"FR-001": ["test_fr_001_feature"]},
    )


@pytest.mark.asyncio
async def test_developer_agent_uses_light_model_for_simple_workpackage(tmp_path):
    provider = _CapturingProvider()
    agent = DeveloperAgent("DeveloperAgent", EventBus(), provider, light_model="haiku", strong_model="sonnet")

    await agent._generate_implementation(tmp_path, _simple_wp())

    assert provider.generate_calls == ["haiku"]


@pytest.mark.asyncio
async def test_developer_agent_uses_strong_model_for_complex_workpackage(tmp_path):
    provider = _CapturingProvider()
    agent = DeveloperAgent("DeveloperAgent", EventBus(), provider, light_model="haiku", strong_model="sonnet")

    await agent._generate_implementation(tmp_path, _complex_wp())

    assert provider.generate_calls == ["sonnet"]


@pytest.mark.asyncio
async def test_developer_agent_omits_model_override_when_not_configured(tmp_path):
    provider = _CapturingProvider()
    agent = DeveloperAgent("DeveloperAgent", EventBus(), provider)  # no light/strong model set

    await agent._generate_implementation(tmp_path, _simple_wp())

    assert provider.generate_calls == [None]


@pytest.mark.asyncio
async def test_test_runner_passes_review_model_to_independent_review(tmp_path):
    provider = _CapturingProvider()
    runner = TestRunnerAgent("TestRunnerAgent", EventBus(), provider, review_model="haiku")

    await runner._independent_review(_simple_wp(), {"src/app.py": "def f():\n    return 1\n"})

    assert provider.review_calls == ["haiku"]
