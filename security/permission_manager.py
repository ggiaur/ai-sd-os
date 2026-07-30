from pathlib import Path
from typing import List

class PermissionManager:
    def __init__(self, allowed_paths: List[str] = None):
        self.allowed_paths = allowed_paths or ["src/", "tests/", "docs/", ".ai-sd-os/"]

    def is_path_allowed(self, target_path: Path, project_root: Path) -> bool:
        try:
            rel_path = target_path.resolve().relative_to(project_root.resolve())
            path_str = str(rel_path)
            for allowed in self.allowed_paths:
                if path_str.startswith(allowed.rstrip("/")):
                    return True
            return False
        except ValueError:
            return False
