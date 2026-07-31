from pathlib import Path

from security.secret_scanner import SecretScanner
from security.permission_manager import PermissionManager
from security.sandbox_policy import SandboxPolicy


# --- SecretScanner -----------------------------------------------------

def test_secret_scanner_detects_known_pattern(tmp_path):
    f = tmp_path / "config.py"
    f.write_text('ANTHROPIC_KEY = "sk-ant-abcdefghijklmnopqrstuvwx"\n', encoding="utf-8")

    findings = SecretScanner().scan_file(f)

    assert len(findings) == 1
    assert findings[0]["line"] == 1


def test_secret_scanner_does_not_flag_clean_file(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

    findings = SecretScanner().scan_file(f)

    assert findings == []


def test_secret_scanner_truncates_the_match_in_findings(tmp_path):
    f = tmp_path / "config.py"
    secret = "sk-ant-abcdefghijklmnopqrstuvwx"
    f.write_text(f'KEY = "{secret}"\n', encoding="utf-8")

    findings = SecretScanner().scan_file(f)

    # The full secret must never end up verbatim in a findings report.
    assert secret not in findings[0]["match"]
    assert findings[0]["match"].endswith("...")


def test_secret_scanner_ignores_vendored_and_state_directories(tmp_path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text(
        'KEY = "sk-ant-abcdefghijklmnopqrstuvwx"\n', encoding="utf-8"
    )
    (tmp_path / ".ai-sd-os").mkdir()
    (tmp_path / ".ai-sd-os" / "state.json").write_text(
        '{"key": "sk-ant-abcdefghijklmnopqrstuvwx"}\n', encoding="utf-8"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        'KEY = "sk-ant-abcdefghijklmnopqrstuvwx"\n', encoding="utf-8"
    )

    findings = SecretScanner().scan_directory(tmp_path)

    assert len(findings) == 1
    assert findings[0]["file"].endswith("src/app.py") or findings[0]["file"].endswith("src\\app.py")


# --- PermissionManager --------------------------------------------------

def test_permission_manager_allows_paths_inside_allowed_prefix(tmp_path):
    mgr = PermissionManager(allowed_paths=["src/"])
    target = tmp_path / "src" / "app.py"

    assert mgr.is_path_allowed(target, tmp_path) is True


def test_permission_manager_rejects_paths_outside_allowed_prefix(tmp_path):
    mgr = PermissionManager(allowed_paths=["src/"])
    target = tmp_path / "secrets" / "keys.env"

    assert mgr.is_path_allowed(target, tmp_path) is False


def test_permission_manager_rejects_similarly_named_sibling_directory(tmp_path):
    """Regression: 'src-evil/' must NOT be treated as inside 'src/'.

    The previous implementation used str.startswith on the raw path string,
    so "src-evil/x.py".startswith("src") was True — a real allowed_paths
    bypass for what is meant to be a security boundary.
    """
    mgr = PermissionManager(allowed_paths=["src/"])
    target = tmp_path / "src-evil" / "x.py"

    assert mgr.is_path_allowed(target, tmp_path) is False


def test_permission_manager_rejects_path_outside_project_root(tmp_path):
    mgr = PermissionManager(allowed_paths=["src/"])
    outside = tmp_path.parent / "somewhere-else" / "file.py"

    assert mgr.is_path_allowed(outside, tmp_path) is False


# --- SandboxPolicy --------------------------------------------------------

def test_sandbox_policy_allows_ordinary_command(tmp_path):
    policy = SandboxPolicy()
    assert policy.validate_command_execution("python3 -m pytest tests/ -v", tmp_path) is True


def test_sandbox_policy_blocks_known_destructive_patterns(tmp_path):
    policy = SandboxPolicy()
    import pytest

    with pytest.raises(PermissionError):
        policy.validate_command_execution("rm -rf /", tmp_path)
