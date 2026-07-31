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

    DEFAULT_GITIGNORE = (
        "__pycache__/\n"
        "*.pyc\n"
        ".pytest_cache/\n"
        ".venv/\n"
        ".env\n"
    )

    def ensure_repo(self, project_root: Path) -> Repo:
        try:
            return Repo(project_root)
        except Exception:
            repo = Repo.init(project_root)
            self._ensure_gitignore(project_root)
            return repo

    def _ensure_gitignore(self, project_root: Path) -> None:
        gitignore_path = project_root / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text(self.DEFAULT_GITIGNORE, encoding="utf-8")

    def commit_sprint_increment(self, project_root: Path, sprint_id: str, wp_id: str, goal: str) -> None:
        repo = self.ensure_repo(project_root)

        # Update CHANGELOG.md BEFORE staging, so a real commit captures both
        # the code and its changelog entry together. Writing the changelog
        # only after committing left it as an untracked leftover that only
        # got swept into the *next* run's commit — producing a misleading
        # "always one commit behind" duplicate pattern (caught by
        # tests/test_sandbox_and_git_driver.py). update_changelog() is itself
        # idempotent (skips if the exact entry is already present), so
        # calling it unconditionally here is safe even when nothing else changed.
        self.update_changelog(project_root, sprint_id, goal)

        repo.git.add(A=True)

        if not self._has_staged_changes(repo):
            self.logger.info(
                f"No changes to commit for {sprint_id} ({wp_id}) — skipping commit. "
                f"(Previously this ran unconditionally on every pipeline execution, which "
                f"is what produced the duplicate-commit spam seen in the engine's own history.)"
            )
            return

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
            return

        self.push_to_remote(repo)

    def push_to_remote(self, repo: Repo) -> bool:
        """Push the current branch to 'origin', if one is configured.

        Deliberately never blocks the pipeline: a missing remote, missing
        credentials, or a network hiccup must not turn an otherwise-successful
        sprint into a failure. Up-to-date version control on the remote is the
        goal, not a hard requirement for a project to be considered DONE.
        """
        try:
            remote_names = [r.name for r in repo.remotes]
            if "origin" not in remote_names:
                self.logger.info("No 'origin' remote configured — skipping push.")
                return False

            branch = repo.active_branch.name
            repo.remotes.origin.push(branch)
            self.logger.info(f"Pushed '{branch}' to origin.")
            return True
        except Exception as e:
            self.logger.warning(f"Push to origin failed (commit stays local, pipeline continues): {e}")
            return False

    @staticmethod
    def _has_staged_changes(repo: Repo) -> bool:
        if not repo.head.is_valid():
            # No commits yet: anything staged at all counts as a real change.
            return len(repo.index.entries) > 0
        return len(repo.index.diff("HEAD")) > 0

    def update_changelog(self, project_root: Path, sprint_id: str, goal: str) -> None:
        changelog_path = project_root / "CHANGELOG.md"
        entry_body = f"## [{sprint_id}] - {time.strftime('%Y-%m-%d')}\n- {goal}\n"

        if changelog_path.exists():
            content = changelog_path.read_text(encoding="utf-8")
            if entry_body.strip() in content:
                # Same sprint/goal entry already recorded — don't duplicate it.
                self.logger.info(f"CHANGELOG.md already has an entry for {sprint_id}/{goal!r} — skipping.")
                return
            changelog_path.write_text(content + "\n" + entry_body, encoding="utf-8")
        else:
            changelog_path.write_text(f"# Changelog\n\n{entry_body}", encoding="utf-8")
