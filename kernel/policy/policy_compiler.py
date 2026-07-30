import yaml
from pathlib import Path

class PolicyCompiler:
    """
    Corporate & Compliance szabályfordító.
    Olvassa és validálja a policy YAML fájlokat a kernel/policy mappából.
    """
    def __init__(self, policy_dir: Path):
        self.policy_dir = policy_dir
        self.rules = self._load_yaml("rules.yaml")
        self.security = self._load_yaml("security.yaml")
        self.execution = self._load_yaml("execution.yaml")

    def _load_yaml(self, filename: str) -> dict:
        filepath = self.policy_dir / filename
        if not filepath.exists():
            return {}
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_max_retries(self) -> int:
        return self.execution.get("max_retries", 3)

    def is_human_required(self, action: str) -> bool:
        require_human = self.rules.get("require_human", [])
        return action in require_human

    def check_sandbox_policy(self) -> dict:
        return self.security.get("sandbox", {})
