import pytest
from pathlib import Path
from main import EngineRunner
from kernel.system.config import KernelConfig
from workspace.project_detector import detect_project

@pytest.mark.asyncio
async def test_full_golden_path(tmp_path):
    project_dir = tmp_path / "sample_app"
    project_dir.mkdir()

    config = KernelConfig(mock_mode=True)
    runner = EngineRunner(cwd=project_dir, config=config)

    await runner.run()

    # Verify directory native state and generated files
    state_handle = detect_project(project_dir)
    assert state_handle is not None
    assert (project_dir / ".ai-sd-os" / "SPEC_FORMAL.yaml").exists()
    assert (project_dir / ".ai-sd-os" / "WORK_PACKAGE.yaml").exists()

    # Generated files are namespaced by WorkPackage id (WP-001 -> ...) rather
    # than a fixed "app.py" — this is what keeps the engine from ever
    # overwriting a human's pre-existing files when adopting a real project.
    generated_modules = list((project_dir / "src").glob("ai_sd_os_generated_*.py"))
    generated_tests = list((project_dir / "tests").glob("test_ai_sd_os_generated_*.py"))
    assert len(generated_modules) == 1
    assert len(generated_tests) == 1
    assert (project_dir / "CHANGELOG.md").exists()
