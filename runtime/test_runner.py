from pathlib import Path
from typing import Dict, Any, List
from sdk.base_agent import BaseAgentSDK
from kernel.event_bus.events import Event, EventType
from contracts.work_package import WorkPackage
from runtime.sandbox import SubprocessSandbox

class TestRunnerAgent(BaseAgentSDK):
    def register_subscriptions(self) -> None:
        self.bus.subscribe(EventType.DEVELOPMENT_COMPLETED, self.process_event)

    async def process_event(self, event: Event) -> None:
        payload = event.payload
        wp_dict = payload.get("work_package", {})
        project_root = Path(payload.get("project_root", "."))
        retry_count = payload.get("retry_count", 0)
        wp = WorkPackage.model_validate(wp_dict)

        self.logger.info(f"Running tests for WorkPackage {wp.id} (retry={retry_count})")

        sandbox = SubprocessSandbox()
        # Run pytest inside project_root with PYTHONPATH=.
        cmd = "PYTHONPATH=. python3 -m pytest tests/ -v"
        res = sandbox.run_command(cmd, cwd=project_root)

        pytest_passed = (res.exit_code == 0)

        # Coverage mapping verification
        coverage_passed, coverage_errors = self._verify_coverage_mapping(project_root, wp, res.stdout)

        all_passed = pytest_passed and coverage_passed

        if all_passed:
            self.logger.info(f"All tests & coverage mapping PASSED for {wp.id}")
            await self.emit_event(
                event_type=EventType.TESTS_PASSED,
                payload={
                    "work_package": wp.model_dump(),
                    "project_root": str(project_root),
                    "auto_dod_passed": 2,
                    "auto_dod_total": 2,
                    "manual_dods": ["DOD-003 (README / API docs update)"],
                    "pytest_output": res.stdout,
                    "retry_count": retry_count
                },
                correlation_id=event.correlation_id
            )
        else:
            error_msg = res.stderr or res.stdout or "\n".join(coverage_errors)
            self.logger.warning(f"Tests or coverage mapping FAILED for {wp.id}: {error_msg}")
            await self.emit_event(
                event_type=EventType.TESTS_FAILED,
                payload={
                    "work_package": wp.model_dump(),
                    "project_root": str(project_root),
                    "error": error_msg,
                    "retry_count": retry_count,
                    "max_retries": 3
                },
                correlation_id=event.correlation_id
            )

    def _verify_coverage_mapping(self, project_root: Path, wp: WorkPackage, pytest_output: str) -> (bool, List[str]):
        errors = []
        tests_dir = project_root / "tests"

        if not tests_dir.exists():
            return False, ["tests/ directory does not exist"]

        for req_id, test_names in wp.coverage_mapping.items():
            for tname in test_names:
                # Check if test function exists in any file under tests/
                found = False
                for tfile in tests_dir.glob("test_*.py"):
                    content = tfile.read_text(encoding="utf-8", errors="ignore")
                    if f"def {tname}" in content:
                        found = True
                        break
                if not found:
                    errors.append(f"Coverage mapping requirement {req_id} test '{tname}' missing in tests/ directory.")

        return len(errors) == 0, errors
