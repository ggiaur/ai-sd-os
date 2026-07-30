import logging
from typing import Optional
from kernel.event_bus.bus import EventBus
from kernel.event_bus.events import Event, EventType
from kernel.hitl.cli_prompts import CLIPrompter

logger = logging.getLogger("HITLGateManager")

class HITLGateManager:
    def __init__(self, bus: EventBus, prompter: Optional[CLIPrompter] = None, auto_approve: bool = False):
        self.bus = bus
        self.prompter = prompter or CLIPrompter()
        self.auto_approve = auto_approve
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.bus.subscribe(EventType.WORKPACKAGE_CREATED, self.handle_workpackage_created)
        self.bus.subscribe(EventType.TESTS_PASSED, self.handle_tests_passed)
        self.bus.subscribe(EventType.PIPELINE_BLOCKED, self.handle_pipeline_blocked)
        self.bus.subscribe(EventType.ACTION_DESTRUCTIVE_REQUESTED, self.handle_destructive_requested)

    async def handle_workpackage_created(self, event: Event) -> None:
        payload = event.payload
        wp = payload.get("work_package", {})
        wp_id = wp.get("id", "WP-UNKNOWN")
        sprint_id = wp.get("sprint_id", "SPRINT-UNKNOWN")
        goal = wp.get("goal", "N/A")
        reqs = payload.get("selected_requirements", [])
        est_minutes = wp.get("max_execution_time_minutes", 30)
        dod_list = payload.get("dod_list", ["DOD-001 (Automated tests pass)"])
        paths = wp.get("allowed_paths", ["src/", "tests/"])

        logger.info(f"Triggering Sprint Planning gate for {wp_id}")
        await self.bus.publish(Event(
            event_type=EventType.SPRINT_PLANNING_PROPOSED,
            payload={"work_package": wp, "sprint_id": sprint_id},
            correlation_id=event.correlation_id
        ))

        choice = self.prompter.prompt_sprint_planning(
            wp_id, sprint_id, goal, reqs, est_minutes, dod_list, paths, auto_approve=self.auto_approve
        )

        if choice == "j":
            logger.info(f"Sprint Planning APPROVED for {sprint_id}")
            await self.bus.publish(Event(
                event_type=EventType.SPRINT_PLANNING_APPROVED,
                payload={"work_package": wp, "sprint_id": sprint_id, "project_root": payload.get("project_root", ".")},
                correlation_id=event.correlation_id
            ))
        else:
            logger.warning(f"Sprint Planning REJECTED for {sprint_id} (choice={choice})")
            await self.bus.publish(Event(
                event_type=EventType.PIPELINE_BLOCKED,
                payload={"reason": f"Sprint planning rejected by human with choice: {choice}", "sprint_id": sprint_id},
                correlation_id=event.correlation_id
            ))

    async def handle_tests_passed(self, event: Event) -> None:
        payload = event.payload
        wp = payload.get("work_package", {})
        wp_id = wp.get("id", "WP-UNKNOWN")
        sprint_id = wp.get("sprint_id", "SPRINT-UNKNOWN")
        auto_dod_passed = payload.get("auto_dod_passed", 2)
        auto_dod_total = payload.get("auto_dod_total", 2)
        manual_dods = payload.get("manual_dods", [])

        logger.info(f"Triggering Sprint Review gate for {sprint_id}")
        await self.bus.publish(Event(
            event_type=EventType.SPRINT_REVIEW_REQUESTED,
            payload={"work_package": wp, "sprint_id": sprint_id},
            correlation_id=event.correlation_id
        ))

        choice = self.prompter.prompt_sprint_review(
            wp_id, sprint_id, auto_dod_passed, auto_dod_total, manual_dods, auto_approve=self.auto_approve
        )

        if choice in ["j", "d"]:
            logger.info(f"Sprint Review APPROVED for {sprint_id}")
            await self.bus.publish(Event(
                event_type=EventType.SPRINT_REVIEW_APPROVED,
                payload=payload,
                correlation_id=event.correlation_id
            ))
        else:
            logger.warning(f"Sprint Review REJECTED for {sprint_id}")
            await self.bus.publish(Event(
                event_type=EventType.PIPELINE_BLOCKED,
                payload={"reason": "Sprint review rejected by human", "sprint_id": sprint_id},
                correlation_id=event.correlation_id
            ))

    async def handle_pipeline_blocked(self, event: Event) -> None:
        payload = event.payload
        sprint_id = payload.get("sprint_id", "SPRINT-UNKNOWN")
        last_error = payload.get("reason", "Unknown error")
        wp_id = payload.get("work_package_id", "WP-UNKNOWN")

        choice = self.prompter.prompt_blocked(wp_id, sprint_id, last_error, auto_approve=self.auto_approve)
        logger.info(f"Pipeline Blocked resolution chosen: {choice}")

    async def handle_destructive_requested(self, event: Event) -> None:
        payload = event.payload
        action_name = payload.get("action", "DESTRUCTIVE_ACTION")
        target = payload.get("target", "Unknown")

        approved = self.prompter.prompt_destructive(action_name, target, auto_approve=self.auto_approve)
        if not approved:
            raise PermissionError(f"Destructive action '{action_name}' on '{target}' rejected by user.")
