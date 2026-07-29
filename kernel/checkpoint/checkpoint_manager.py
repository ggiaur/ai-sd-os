import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

class CheckpointManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ai_sd_os_dir = project_root / ".ai-sd-os"
        self.checkpoints_dir = self.ai_sd_os_dir / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(self, state_name: str, payload: Dict[str, Any]) -> Path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"checkpoint_{state_name}_{timestamp}.json"
        target = self.checkpoints_dir / filename
        data = {
            "state": state_name,
            "timestamp": timestamp,
            "payload": payload
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return target

    def get_latest_checkpoint(() -> Optional[Path]:
        pass

    def list_checkpoints(self) -> list[Path]:
        return sorted(self.checkpoints_dir.glob("checkpoint_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
