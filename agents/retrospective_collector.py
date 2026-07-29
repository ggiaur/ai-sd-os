from pathlib import Path
from sdk.base_agent import BaseAgentSDK
from kernel.event_bus.events import Event, EventType
from contracts.retrospective import Retrospective
from kernel.contracts.serializer import save_yaml_contract
from lessons.aggregator import LessonsAggregator

class RetrospectiveCollector(BaseAgentSDK):
    def register_subscriptions(self) -> None:
        self.bus.subscribe(EventType.SPRINT_REVIEW_APPROVED, self.process_event)

    async def process_event(self, event: Event) -> None:
        payload = event.payload
        wp = payload.get("work_package", {})
        sprint_id = wp.get("sprint_id", "SPRINT-001")
        project_root = Path(payload.get("project_root", "."))
        retry_count = payload.get("retry_count", 0)

        retro = Retrospective(
            sprint_id=sprint_id,
            what_worked=f"WorkPackage {wp.get('id', '')} features implemented successfully.",
            what_failed="Single retry needed if assertions failed on first run." if retry_count > 0 else "None",
            carry_forward_note="Ensure exact type checking and unit test isolation for new requirements.",
            retry_count=retry_count,
            duration_minutes=10
        )

        retro_dir = project_root / ".ai-sd-os" / "retrospectives"
        retro_dir.mkdir(parents=True, exist_ok=True)
        save_yaml_contract(retro, retro_dir / f"{sprint_id}.yaml")

        # Update motor-level Lessons Learned
        aggregator = LessonsAggregator(motor_dir=Path(__file__).parent.parent)
        aggregator.add_lesson(
            pattern=f"Sprint {sprint_id} execution pattern",
            project_sprint=f"{project_root.name} / {sprint_id}",
            suggested_action="Maintain automated unit test checks and coverage mapping verification."
        )

        await self.emit_event(
            event_type=EventType.RETROSPECTIVE_RECORDED,
            payload={
                "retrospective": retro.model_dump(),
                "project_root": str(project_root)
            },
            correlation_id=event.correlation_id
        )

        await self.emit_event(
            event_type=EventType.LESSONS_LEARNED_UPDATED,
            payload={"sprint_id": sprint_id},
            correlation_id=event.correlation_id
        )
