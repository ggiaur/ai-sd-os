"""Tests for ClaudeCodeCLIAdapter — never invoke the real `claude` binary here.

Spawning a real nested Claude Code session from inside the test suite would be
slow, costly, and could recurse in ways nothing here is designed to handle.
subprocess.run is patched in every test that would otherwise shell out.
"""

import subprocess
import pytest

from sdk.provider_adapter import ClaudeCodeCLIAdapter, ReviewResult


class _FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_generate_invokes_cli_with_model_and_permission_mode(tmp_path, monkeypatch):
    captured = {}

    def fake_run(cmd, cwd, capture_output, text, timeout):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return _FakeCompletedProcess(returncode=0, stdout="```python\ndef f():\n    return 1\n```")

    monkeypatch.setattr(subprocess, "run", fake_run)

    adapter = ClaudeCodeCLIAdapter(model="claude-sonnet-4-6", cwd=tmp_path)
    import asyncio
    result = asyncio.run(adapter.generate("implement f()"))

    assert "def f()" in result
    assert captured["cwd"] == tmp_path
    assert "--model" in captured["cmd"]
    assert "claude-sonnet-4-6" in captured["cmd"]
    assert "--permission-mode" in captured["cmd"]
    assert "-p" in captured["cmd"]


def test_generate_raises_on_nonzero_exit(tmp_path, monkeypatch):
    def fake_run(cmd, cwd, capture_output, text, timeout):
        return _FakeCompletedProcess(returncode=1, stdout="", stderr="something broke")

    monkeypatch.setattr(subprocess, "run", fake_run)

    adapter = ClaudeCodeCLIAdapter(model="claude-sonnet-4-6", cwd=tmp_path)
    import asyncio
    with pytest.raises(RuntimeError, match="something broke"):
        asyncio.run(adapter.generate("implement f()"))


def test_generate_raises_clear_error_when_cli_not_installed(tmp_path, monkeypatch):
    def fake_run(cmd, cwd, capture_output, text, timeout):
        raise FileNotFoundError("no such file: claude")

    monkeypatch.setattr(subprocess, "run", fake_run)

    adapter = ClaudeCodeCLIAdapter(model="claude-sonnet-4-6", cwd=tmp_path)
    import asyncio
    with pytest.raises(RuntimeError, match="not found on PATH"):
        asyncio.run(adapter.generate("implement f()"))


def test_generate_raises_on_timeout(tmp_path, monkeypatch):
    def fake_run(cmd, cwd, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr(subprocess, "run", fake_run)

    adapter = ClaudeCodeCLIAdapter(model="claude-sonnet-4-6", cwd=tmp_path, timeout_seconds=5)
    import asyncio
    with pytest.raises(RuntimeError, match="timed out"):
        asyncio.run(adapter.generate("implement f()"))


def test_review_never_calls_cli_when_deterministic_check_already_fails(tmp_path, monkeypatch):
    """A hardcoded secret must be rejected WITHOUT paying for a CLI session."""
    def fake_run(cmd, cwd, capture_output, text, timeout):
        raise AssertionError("CLI should not have been invoked — deterministic check should short-circuit")

    monkeypatch.setattr(subprocess, "run", fake_run)

    adapter = ClaudeCodeCLIAdapter(model="claude-sonnet-4-6", cwd=tmp_path)
    import asyncio
    result = asyncio.run(adapter.review('api_key = "sk-ant-abcdefghijklmnopqrstuvwx"', criteria=["no secrets"]))

    assert isinstance(result, ReviewResult)
    assert result.passed is False


def test_embed_is_explicitly_unsupported(tmp_path):
    adapter = ClaudeCodeCLIAdapter(model="claude-sonnet-4-6", cwd=tmp_path)
    import asyncio
    with pytest.raises(NotImplementedError):
        asyncio.run(adapter.embed("some text"))
