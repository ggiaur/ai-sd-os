from pathlib import Path

from git import Repo

from runtime.sandbox import SubprocessSandbox
from runtime.git_driver import GitDriver
from kernel.event_bus.bus import EventBus
from sdk.provider_adapter import MockProviderAdapter


# --- SubprocessSandbox --------------------------------------------------

def test_subprocess_sandbox_reports_success_exit_code(tmp_path):
    res = SubprocessSandbox().run_command("exit 0", cwd=tmp_path)
    assert res.exit_code == 0


def test_subprocess_sandbox_reports_failure_exit_code(tmp_path):
    res = SubprocessSandbox().run_command("exit 7", cwd=tmp_path)
    assert res.exit_code == 7


def test_subprocess_sandbox_captures_stdout(tmp_path):
    res = SubprocessSandbox().run_command("echo hello-sandbox", cwd=tmp_path)
    assert "hello-sandbox" in res.stdout


def test_subprocess_sandbox_never_raises_on_bad_command(tmp_path):
    res = SubprocessSandbox().run_command("this-binary-does-not-exist-xyz", cwd=tmp_path)
    assert res.exit_code != 0


# --- GitDriver idempotency (unit-level, not just the e2e proof) --------

def _make_driver():
    return GitDriver("GitDriver", EventBus(), MockProviderAdapter())


def test_git_driver_first_commit_creates_changelog(tmp_path):
    driver = _make_driver()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def f():\n    return 1\n", encoding="utf-8")

    driver.commit_sprint_increment(tmp_path, "SPRINT-001", "WP-001", "Implement features: FR-001")

    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.count("SPRINT-001") == 1
    assert len(list(driver.ensure_repo(tmp_path).iter_commits())) == 1


def test_git_driver_rerun_without_changes_does_not_duplicate(tmp_path):
    driver = _make_driver()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def f():\n    return 1\n", encoding="utf-8")

    driver.commit_sprint_increment(tmp_path, "SPRINT-001", "WP-001", "Implement features: FR-001")
    # Same content, same goal, no real change — must be a no-op.
    driver.commit_sprint_increment(tmp_path, "SPRINT-001", "WP-001", "Implement features: FR-001")

    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.count("## [SPRINT-001]") == 1
    assert len(list(driver.ensure_repo(tmp_path).iter_commits())) == 1


def test_git_driver_creates_gitignore_for_new_project_repo(tmp_path):
    driver = _make_driver()
    driver.ensure_repo(tmp_path)

    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "__pycache__/" in gitignore
    assert ".pytest_cache/" in gitignore


def test_git_driver_does_not_overwrite_existing_gitignore(tmp_path):
    driver = _make_driver()
    (tmp_path / ".gitignore").write_text("custom-ignore-rule/\n", encoding="utf-8")

    driver.ensure_repo(tmp_path)

    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == "custom-ignore-rule/\n"


def test_git_driver_pushes_to_configured_origin_remote(tmp_path):
    """Real push, no network needed — the 'remote' is a local bare repo."""
    remote_path = tmp_path / "remote.git"
    Repo.init(remote_path, bare=True)

    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "src").mkdir()
    (project_root / "src" / "app.py").write_text("def f():\n    return 1\n", encoding="utf-8")

    driver = _make_driver()
    repo = driver.ensure_repo(project_root)
    repo.create_remote("origin", str(remote_path))

    driver.commit_sprint_increment(project_root, "SPRINT-001", "WP-001", "Implement features: FR-001")

    remote_repo = Repo(remote_path)
    assert len(list(remote_repo.iter_commits())) == 1


def test_git_driver_skips_push_gracefully_without_a_remote(tmp_path):
    """No 'origin' configured must never crash the pipeline."""
    driver = _make_driver()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def f():\n    return 1\n", encoding="utf-8")

    driver.commit_sprint_increment(tmp_path, "SPRINT-001", "WP-001", "Implement features: FR-001")

    assert len(list(driver.ensure_repo(tmp_path).iter_commits())) == 1


def test_git_driver_real_change_produces_a_second_commit(tmp_path):
    driver = _make_driver()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    driver.commit_sprint_increment(tmp_path, "SPRINT-001", "WP-001", "Implement features: FR-001")

    (tmp_path / "src" / "app.py").write_text("def f():\n    return 2\n", encoding="utf-8")
    driver.commit_sprint_increment(tmp_path, "SPRINT-002", "WP-002", "Implement features: FR-002")

    assert len(list(driver.ensure_repo(tmp_path).iter_commits())) == 2
