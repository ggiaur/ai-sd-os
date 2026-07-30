from pathlib import Path

from kernel.policy.policy_compiler import PolicyCompiler, CompiledPolicy


def test_policy_compiler_loads_real_yaml_files():
    policy_dir = Path(__file__).parent.parent / "kernel" / "policy"
    compiled = PolicyCompiler(policy_dir=policy_dir).compile()

    assert isinstance(compiled, CompiledPolicy)
    assert "SPRINT_PLANNING" in compiled.rules.require_human_gates
    assert compiled.requires_human_gate("SPRINT_PLANNING") is True
    assert compiled.requires_human_gate("NON_EXISTENT_GATE") is False

    assert compiled.security.secret_scan.enabled is True
    assert any("sk-ant" in p for p in compiled.security.secret_scan.patterns)

    assert compiled.execution.max_retries == 3
    assert compiled.execution.timeout_seconds == 1800


def test_policy_compiler_defaults_when_dir_missing(tmp_path):
    compiled = PolicyCompiler(policy_dir=tmp_path / "does_not_exist").compile()
    assert compiled.execution.max_retries == 3
    assert compiled.rules.require_human_gates == []
