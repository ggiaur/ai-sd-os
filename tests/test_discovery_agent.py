"""Proves the codebase survey reflects the real project, not fabricated constants.

The previous implementation reported dependencies.count=10, outdated=1, and
technical_debt.missing_tests=["src/admin.py"] unconditionally, regardless of
what the surveyed project actually contained — a snapshot that lies is worse
than no snapshot, especially since this is the path used to adopt an existing
(real) project.
"""

import pytest
from pathlib import Path

from kernel.event_bus.bus import EventBus
from agents.discovery_agent import DiscoveryAgent
from sdk.provider_adapter import MockProviderAdapter


def _make_agent():
    return DiscoveryAgent("DiscoveryAgent", EventBus(), MockProviderAdapter())


@pytest.mark.asyncio
async def test_dependency_count_reflects_real_requirements_txt(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "pydantic>=2.0\n# a comment\n\nfastapi\nuvicorn\n", encoding="utf-8"
    )

    snapshot = await _make_agent().survey_codebase(tmp_path)

    assert snapshot.dependencies.count == 3  # pydantic, fastapi, uvicorn — comment/blank ignored
    assert snapshot.dependencies.outdated == 0  # never fabricated — no network access


@pytest.mark.asyncio
async def test_dependency_count_is_zero_for_empty_project(tmp_path):
    snapshot = await _make_agent().survey_codebase(tmp_path)
    assert snapshot.dependencies.count == 0


@pytest.mark.asyncio
async def test_test_count_matches_actual_test_functions(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text(
        "def test_one():\n    pass\n\n"
        "def test_two():\n    pass\n\n"
        "async def test_three():\n    pass\n",
        encoding="utf-8",
    )

    snapshot = await _make_agent().survey_codebase(tmp_path)

    assert snapshot.test_quality.existing_tests_count == 3


@pytest.mark.asyncio
async def test_missing_tests_is_not_a_fabricated_filename(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def f():\n    return 1\n", encoding="utf-8")

    snapshot = await _make_agent().survey_codebase(tmp_path)

    assert "src/admin.py" not in snapshot.technical_debt.missing_tests
    assert snapshot.technical_debt.missing_tests != []  # honestly flags "no tests found"


@pytest.mark.asyncio
async def test_missing_tests_is_empty_when_tests_exist(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text("def test_x():\n    pass\n", encoding="utf-8")

    snapshot = await _make_agent().survey_codebase(tmp_path)

    assert snapshot.technical_debt.missing_tests == []
