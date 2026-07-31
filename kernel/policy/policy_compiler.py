from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field


class ConstitutionalRule(BaseModel):
    id: str
    name: str
    enforce: bool = True


class RulesPolicy(BaseModel):
    require_human_gates: List[str] = Field(default_factory=list)
    constitutional_rules: List[ConstitutionalRule] = Field(default_factory=list)


class SecretScanPolicy(BaseModel):
    enabled: bool = True
    patterns: List[str] = Field(default_factory=list)


class SandboxPolicy(BaseModel):
    enforce_docker: bool = False
    fallback_subprocess: bool = True
    allowed_directories: List[str] = Field(default_factory=lambda: ["src/", "tests/"])


class SecurityPolicy(BaseModel):
    secret_scan: SecretScanPolicy = Field(default_factory=SecretScanPolicy)
    sandbox: SandboxPolicy = Field(default_factory=SandboxPolicy)


class ExecutionPolicy(BaseModel):
    max_retries: int = 3
    timeout_seconds: int = 1800
    token_budget_per_sprint: int = 500000
    auto_checkpoint: bool = True


class CompiledPolicy(BaseModel):
    rules: RulesPolicy = Field(default_factory=RulesPolicy)
    security: SecurityPolicy = Field(default_factory=SecurityPolicy)
    execution: ExecutionPolicy = Field(default_factory=ExecutionPolicy)

    def requires_human_gate(self, gate_name: str) -> bool:
        return gate_name in self.rules.require_human_gates


class PolicyCompiler:
    """Beolvassa és egyetlen érvényesített CompiledPolicy objektummá fordítja
    a kernel/policy/ alatt lévő rules.yaml, security.yaml és execution.yaml
    fájlokat, amelyeket eddig semmilyen komponens nem használt fel."""

    def __init__(self, policy_dir: Path = Path("./kernel/policy")):
        self.policy_dir = Path(policy_dir)

    def _load_yaml(self, filename: str) -> dict:
        file_path = self.policy_dir / filename
        if not file_path.exists():
            return {}
        return yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}

    def compile(self) -> CompiledPolicy:
        rules_data = self._load_yaml("rules.yaml")
        security_data = self._load_yaml("security.yaml")
        execution_data = self._load_yaml("execution.yaml")

        return CompiledPolicy(
            rules=RulesPolicy(**rules_data),
            security=SecurityPolicy(**security_data),
            execution=ExecutionPolicy(**execution_data.get("execution", {})),
        )
