from pathlib import Path
from typing import List

class PermissionManager:
    def __init__(self, allowed_paths: List[str] = None):
        self.allowed_paths = allowed_paths or ["src/", "tests/", "docs/", ".ai-sd-os/"]

    def is_path_allowed(self, target_path: Path, project_root: Path) -> bool:
        try:
            rel_path = target_path.resolve().relative_to(project_root.resolve())
        except ValueError:
            return False

        rel_parts = rel_path.parts
        for allowed in self.allowed_paths:
            # Compare by path SEGMENTS, not raw string prefix: a naive
            # str.startswith("src") would incorrectly let "src-evil/x.py"
            # through as if it were inside "src/" — a real allowed_paths
            # bypass for a security boundary.
            allowed_parts = Path(allowed.rstrip("/")).parts
            if rel_parts[: len(allowed_parts)] == allowed_parts:
                return True
        return False
