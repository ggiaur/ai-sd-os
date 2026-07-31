from pathlib import Path
from typing import Dict, Any, List
from sdk.base_agent import BaseAgentSDK
from kernel.event_bus.events import Event, EventType
from contracts.work_package import WorkPackage
from runtime.sandbox import SubprocessSandbox

class TestRunnerAgent(BaseAgentSDK):
    def __init__(self, name: str, bus, provider, max_retries: int = 3):
        self.max_retries = max_retries
        super().__init__(name, bus, provider)

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

        # Independent QA review: a SEPARATE check from "did the acceptance
        # test pass", using provider.review() with its own criteria (secrets,
        # dangerous execution patterns, goal alignment). Two people/teams
        # verifying the same work by different methods catches things a
        # single pass/fail signal cannot — e.g. code that returns the right
        # value but does it via eval() or leaks a hardcoded key.
        review_passed, review_feedback = await self._independent_review(
            wp, payload.get("written_files", {})
        )

        all_passed = pytest_passed and coverage_passed and review_passed

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
            error_parts = []
            if not pytest_passed:
                error_parts.append(res.stderr or res.stdout)
            if not coverage_passed:
                error_parts.append("\n".join(coverage_errors))
            if not review_passed:
                error_parts.append(f"Independent QA review REJECTED the implementation: {review_feedback}")
            error_msg = "\n".join(p for p in error_parts if p) or "Verification failed for an unknown reason."
            self.logger.warning(f"Tests or coverage mapping FAILED for {wp.id}: {error_msg}")
            await self.emit_event(
                event_type=EventType.TESTS_FAILED,
                payload={
                    "work_package": wp.model_dump(),
                    "project_root": str(project_root),
                    "error": error_msg,
                    "retry_count": retry_count,
                    "max_retries": self.max_retries
                },
                correlation_id=event.correlation_id
            )

    async def _independent_review(self, wp: WorkPackage, written_files: Dict[str, str]) -> (bool, str):
        combined_code = "\n\n".join(written_files.values())
        if not combined_code.strip():
            # Nothing was written at all — the pytest/coverage gate above
            # already fails this case with a clearer message; don't pile on.
            return True, ""

        result = await self.provider.review(
            combined_code,
            criteria=[
                "The code does not contain hardcoded secrets or API keys",
                "The code does not use eval(), exec(), os.system(), or shell=True subprocess calls",
                f"The code plausibly implements the WorkPackage goal: {wp.goal}",
            ],
        )
        return result.passed, result.feedback

    def _verify_coverage_mapping(self, project_root: Path, wp: WorkPackage, pytest_output: str) -> (bool, List[str]):
        errors = []
        tests_dir = project_root / "tests"

        if not tests_dir.exists():
            return False, ["tests/ directory does not exist"]

        # A WorkPackage with no requirement-to-test links has no verifiable
        # acceptance criteria — that must never be treated as "done".
        if not wp.coverage_mapping:
            return False, ["coverage_mapping is empty — no requirement is linked to a test, nothing was verified"]

        passed_node_ids = self._parse_passed_test_nodes(pytest_output)

        for req_id, test_names in wp.coverage_mapping.items():
            if not test_names:
                errors.append(f"Coverage mapping requirement {req_id} lists no tests.")
                continue
            for tname in test_names:
                # Require the test to have actually PASSED in this pytest run —
                # not merely to exist as text somewhere under tests/. A test that
                # was never collected, was skipped, or failed must not count.
                if not any(node.endswith(f"::{tname}") for node in passed_node_ids):
                    errors.append(
                        f"Coverage mapping requirement {req_id} test '{tname}' did not PASS "
                        f"(not found among passed pytest node ids)."
                    )

        return len(errors) == 0, errors

    @staticmethod
    def _parse_passed_test_nodes(pytest_output: str) -> set:
        """Extract test node ids reported as PASSED from `pytest -v` output.

        This is what makes coverage-mapping verification honest: a test string
        merely existing in a source file proves nothing; only pytest actually
        collecting and passing it does.
        """
        passed = set()
        for line in pytest_output.splitlines():
            line = line.strip()
            if not line or " PASSED" not in line:
                continue
            node_id = line.split(" ", 1)[0]
            if "::" in node_id:
                passed.add(node_id)
        return passed
