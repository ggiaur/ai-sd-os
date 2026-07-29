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
    assert (project_dir / "src" / "app.py").exists()
    assert (project_dir / "tests" / "test_app.py").exists()
    assert (project_dir / "CHANGELOG.md").exists()
