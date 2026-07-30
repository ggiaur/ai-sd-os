import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from kernel.state.states import ProjectState

class ProjectHandle(BaseModel):
    project_root: Path
    state: ProjectState
    state_file: Path

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_state(cls, state_file: Path) -> "ProjectHandle":
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        state_str = data.get("state", "INIT")
        return cls(
            project_root=state_file.parent.parent,
            state=ProjectState(state_str),
            state_file=state_file
        )

class ProjectSummary(BaseModel):
    name: str
    path: str
    state: str

    @classmethod
    def from_state(cls, state_file: Path) -> "ProjectSummary":
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        project_root = state_file.parent.parent
        return cls(
            name=project_root.name,
            path=str(project_root.resolve()),
            state=data.get("state", "UNKNOWN")
        )

def detect_project(cwd: Path) -> Optional[ProjectHandle]:
    state_file = cwd / ".ai-sd-os" / "state.json"
    if state_file.exists():
        return ProjectHandle.from_state(state_file)
    return None

def save_project_state(cwd: Path, state: ProjectState, extra: Optional[dict] = None) -> None:
    ai_sd_dir = cwd / ".ai-sd-os"
    ai_sd_dir.mkdir(parents=True, exist_ok=True)
    state_file = ai_sd_dir / "state.json"
    payload = {"state": state.value}
    if extra:
        payload.update(extra)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

def list_projects(workspace_root: Path, motor_dir: Path) -> List[ProjectSummary]:
    motor_dir_resolved = motor_dir.resolve()
    summaries = []
    if not workspace_root.exists():
        return summaries
    for d in workspace_root.iterdir():
        if d.is_dir() and d.resolve() != motor_dir_resolved:
            state_file = d / ".ai-sd-os" / "state.json"
            if state_file.exists():
                try:
                    summaries.append(ProjectSummary.from_state(state_file))
                except Exception:
                    pass
    return summaries
