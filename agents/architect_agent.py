from pathlib import Path
from typing import List, Dict, Any
from sdk.base_agent import BaseAgentSDK
from kernel.event_bus.events import Event, EventType
from contracts.spec_formal import SpecFormal, RequirementItem, PriorityEnum
from contracts.work_package import WorkPackage, TaskItem
from contracts.definition_of_done import DefinitionOfDone, DoDCriterion
from kernel.contracts.serializer import save_yaml_contract
from kernel.swarm.orchestrator import SwarmOrchestrator

PRIORITY_WEIGHT = {
    PriorityEnum.HIGH: 3,
    PriorityEnum.MEDIUM: 2,
    PriorityEnum.LOW: 1
}

def estimate_effort_minutes(req: RequirementItem) -> int:
    return 15 if req.priority == PriorityEnum.HIGH else 10

class ArchitectAgent(BaseAgentSDK):
    def register_subscriptions(self) -> None:
        self.bus.subscribe(EventType.SPEC_CREATED, self.process_event)

    async def process_event(self, event: Event) -> None:
        payload = event.payload
        spec_data = payload.get("spec")
        project_root = Path(payload.get("project_root", "."))
        sprint_number = payload.get("sprint_number", 1)

        if isinstance(spec_data, dict):
            spec = SpecFormal.model_validate(spec_data)
        else:
            spec = spec_data

        selected_reqs = self.select_sprint_backlog(spec, capacity_minutes=45)
        if not selected_reqs:
            self.logger.info("No PENDING requirements left to process in SpecFormal.")
            return

        sprint_id = f"SPRINT-{sprint_number:03d}"
        wp_id = f"WP-{sprint_number:03d}"

        tasks = []
        coverage_mapping: Dict[str, List[str]] = {}

        for idx, req in enumerate(selected_reqs, 1):
            task_id = f"TASK-{idx:03d}"
            fn_name = self._function_name_for(req.id)
            # Acceptance value derived purely from the requirement — NOT from any
            # implementation. This is what makes the later test meaningful: the
            # DeveloperAgent never sees this until it independently tries to satisfy it.
            expected_output = f"{req.id}-DONE"
            tasks.append(TaskItem(
                task_id=task_id,
                description=f"Implement {req.title}: {req.description}",
                requirement_ref=req.id,
                expected_output=expected_output
            ))
            coverage_mapping[req.id] = [f"test_{fn_name}"]

        wp = WorkPackage(
            id=wp_id,
            sprint_id=sprint_id,
            goal=f"Implement features: {', '.join([r.id for r in selected_reqs])}",
            allowed_paths=["src/", "tests/"],
            tasks=tasks,
            max_execution_time_minutes=30,
            tests_required=True,
            coverage_mapping=coverage_mapping
        )

        dod = DefinitionOfDone(
            work_package_ref=wp_id,
            criteria=[
                DoDCriterion(id="DOD-001", description="Minden coverage_mapping teszt lefut és zöld", automated_check=True),
                DoDCriterion(id="DOD-002", description="Nincs lint hiba és a kódszerkezet tiszta", automated_check=True),
                DoDCriterion(id="DOD-003", description="README vagy kód dokumentáció frissítve ha szükséges", automated_check=False)
            ]
        )

        ai_sd_dir = project_root / ".ai-sd-os"
        save_yaml_contract(wp, ai_sd_dir / "WORK_PACKAGE.yaml")
        save_yaml_contract(dod, ai_sd_dir / "DEFINITION_OF_DONE.yaml")

        # Spec-first / TDD: the acceptance tests are written here, from the
        # requirements, BEFORE the DeveloperAgent writes a single line of
        # implementation. This is what makes TESTS_PASSED a real signal instead
        # of a rubber stamp — the developer cannot shape the test to match
        # whatever it happens to implement.
        self._write_acceptance_tests(project_root, wp)

        req_dicts = [r.model_dump() for r in selected_reqs]
        dod_str_list = [f"{c.id}: {c.description}" for c in dod.criteria]

        # Swarm partícionálás: melyik taskok futtathatók biztonságosan párhuzamosan
        orchestrator = SwarmOrchestrator()
        task_groups = orchestrator.partition_tasks(wp.tasks)

        await self.emit_event(
            event_type=EventType.WORKPACKAGE_CREATED,
            payload={
                "work_package": wp.model_dump(),
                "definition_of_done": dod.model_dump(),
                "selected_requirements": req_dicts,
                "dod_list": dod_str_list,
                "project_root": str(project_root),
                "task_groups": [[t.task_id for t in group] for group in task_groups],
            },
            correlation_id=event.correlation_id
        )

    @staticmethod
    def _function_name_for(requirement_ref: str) -> str:
        return requirement_ref.lower().replace("-", "_") + "_feature"

    def _write_acceptance_tests(self, project_root: Path, wp: WorkPackage) -> None:
        tests_dir = project_root / "tests"
        src_dir = project_root / "src"
        tests_dir.mkdir(parents=True, exist_ok=True)
        src_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "__init__.py").touch(exist_ok=True)
        (src_dir / "__init__.py").touch(exist_ok=True)

        fn_names = [self._function_name_for(t.requirement_ref) for t in wp.tasks]
        module_name = wp.module_name()

        header = (
            '"""Acceptance tests generated by ArchitectAgent from SPEC_FORMAL / WORK_PACKAGE.\n\n'
            "These are written BEFORE the implementation exists (spec-first) and encode the\n"
            "expected_output of each task exactly as required by the specification. DeveloperAgent\n"
            "must make these pass without being able to redefine them — this is what turns\n"
            "TESTS_PASSED into a real verification signal instead of a rubber stamp.\n\n"
            f"Generated file for {wp.id} — do not hand-edit, regenerated on every ArchitectAgent\n"
            "run for this WorkPackage. Namespaced by WorkPackage id so it never collides with, or\n"
            "overwrites, pre-existing project files or earlier sprints' generated modules.\n"
            '"""\n'
            "import sys, os\n"
            "sys.path.insert(0, os.path.abspath('.'))\n"
            f"from src.{module_name} import {', '.join(fn_names)}\n\n"
        )

        body_parts = []
        for task in wp.tasks:
            fn_name = self._function_name_for(task.requirement_ref)
            test_name = f"test_{fn_name}"
            body_parts.append(
                f"def {test_name}():\n"
                f"    # Acceptance criterion for {task.requirement_ref}: {task.description}\n"
                f"    assert {fn_name}() == {task.expected_output!r}\n"
            )

        test_file = tests_dir / f"test_{module_name}.py"
        test_file.write_text(header + "\n\n".join(body_parts) + "\n", encoding="utf-8")

    def select_sprint_backlog(self, spec: SpecFormal, capacity_minutes: int) -> List[RequirementItem]:
        pending = [r for r in spec.requirements if r.status == "PENDING"]
        pending.sort(key=lambda r: PRIORITY_WEIGHT.get(r.priority, 1), reverse=True)

        selected, used_capacity = [], 0
        for req in pending:
            estimate = estimate_effort_minutes(req)
            if used_capacity + estimate > capacity_minutes:
                continue
            selected.append(req)
            used_capacity += estimate
        return selected
