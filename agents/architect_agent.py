from pathlib import Path
from typing import List, Dict, Any
from sdk.base_agent import BaseAgentSDK
from kernel.event_bus.events import Event, EventType
from contracts.spec_formal import SpecFormal, RequirementItem, PriorityEnum
from contracts.work_package import WorkPackage, TaskItem
from contracts.definition_of_done import DefinitionOfDone, DoDCriterion
from kernel.contracts.serializer import save_yaml_contract

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
            tasks.append(TaskItem(
                task_id=task_id,
                description=f"Implement {req.title}: {req.description}",
                requirement_ref=req.id
            ))
            fn_name = req.title.lower().replace(" ", "_").replace("-", "_")
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

        req_dicts = [r.model_dump() for r in selected_reqs]
        dod_str_list = [f"{c.id}: {c.description}" for c in dod.criteria]

        await self.emit_event(
            event_type=EventType.WORKPACKAGE_CREATED,
            payload={
                "work_package": wp.model_dump(),
                "definition_of_done": dod.model_dump(),
                "selected_requirements": req_dicts,
                "dod_list": dod_str_list,
                "project_root": str(project_root)
            },
            correlation_id=event.correlation_id
        )

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
