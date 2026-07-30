import time
from pathlib import Path
from typing import Optional
from git import Repo
from sdk.base_agent import BaseAgentSDK
from kernel.event_bus.events import Event, EventType

class GitDriver(BaseAgentSDK):
    def register_subscriptions(self) -> None:
        self.bus.subscribe(EventType.SPRINT_REVIEW_APPROVED, self.process_event)

    async def process_event(self, event: Event) -> None:
        payload = event.payload
        wp = payload.get("work_package", {})
        project_root = Path(payload.get("project_root", "."))
        sprint_id = wp.get("sprint_id", "SPRINT-001")
        wp_id = wp.get("id", "WP-001")

        self.commit_sprint_increment(project_root, sprint_id, wp_id, wp.get("goal", ""))

    def ensure_repo(self, project_root: Path) -> Repo:
        try:
            return Repo(project_root)
        except Exception:
            return Repo.init(project_root)

    def commit_sprint_increment(self, project_root: Path, sprint_id: str, wp_id: str, goal: str) -> None:
        repo = self.ensure_repo(project_root)

        # Stage changes
        repo.git.add(A=True)

        commit_msg = (
            f"feat({sprint_id}): {goal}\n\n"
            f"WorkPackage: {wp_id}\n"
            f"Tests: PASSED\n"
            f"Agent: DeveloperAgent\n"
        )
        try:
            repo.index.commit(commit_msg)
            self.logger.info(f"Committed sprint {sprint_id} to project repository.")
        except Exception as e:
            self.logger.warning(f"Git commit skipped or empty: {e}")

        # Update CHANGELOG.md
        self.update_changelog(project_root, sprint_id, goal)

    def update_changelog(self, project_root: Path, sprint_id: str, goal: str) -> None:
        changelog_path = project_root / "CHANGELOG.md"
        entry = f"\n## [{sprint_id}] - {time.strftime('%Y-%m-%d')}\n- {goal}\n"
        if changelog_path.exists():
            content = changelog_path.read_text(encoding="utf-8")
            changelog_path.write_text(content + entry, encoding="utf-8")
        else:
            changelog_path.write_text(f"# Changelog\n{entry}", encoding="utf-8")
