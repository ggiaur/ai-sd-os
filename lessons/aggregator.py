from pathlib import Path
from typing import Dict, Any, List
import yaml

class LessonsAggregator:
    def __init__(self, motor_dir: Path):
        self.motor_dir = motor_dir
        self.lessons_file = motor_dir / "lessons" / "lessons_learned.yaml"
        self.lessons_file.parent.mkdir(parents=True, exist_ok=True)

    def load_lessons(self) -> Dict[str, Any]:
        if not self.lessons_file.exists():
            return {"entries": []}
        with open(self.lessons_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"entries": []}

    def save_lessons(self, data: Dict[str, Any]) -> None:
        with open(self.lessons_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    def add_lesson(self, pattern: str, project_sprint: str, suggested_action: str) -> None:
        data = self.load_lessons()
        entries: List[Dict[str, Any]] = data.get("entries", [])

        # Check if pattern exists
        existing = None
        for e in entries:
            if e.get("pattern") == pattern:
                existing = e
                break

        if existing:
            existing["occurrences"] = existing.get("occurrences", 1) + 1
            if project_sprint not in existing.get("projects", []):
                existing.setdefault("projects", []).append(project_sprint)
        else:
            entries.append({
                "pattern": pattern,
                "occurrences": 1,
                "projects": [project_sprint],
                "suggested_action": suggested_action,
                "status": "PENDING_HUMAN_REVIEW"
            })

        data["entries"] = entries
        self.save_lessons(data)
