from pathlib import Path
from security.permission_manager import PermissionManager

class SandboxPolicy:
    def __init__(self, permission_manager: PermissionManager = None):
        self.perm_mgr = permission_manager or PermissionManager()

    def validate_command_execution(self, cmd: str, cwd: Path) -> bool:
        forbidden = ["rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:"]
        for f in forbidden:
            if f in cmd:
                raise PermissionError(f"Forbidden command pattern detected: '{f}'")
        return True
