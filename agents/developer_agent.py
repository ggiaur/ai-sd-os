import re
from pathlib import Path
from typing import Dict, Any, Optional
from sdk.base_agent import BaseAgentSDK
from kernel.event_bus.events import Event, EventType
from contracts.work_package import WorkPackage
from sdk.model_selector import select_model

CODE_FENCE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)

class DeveloperAgent(BaseAgentSDK):
    """Implements src/ against acceptance tests that ArchitectAgent already wrote.

    Deliberately does NOT write to tests/ — the tests were authored independently
    from the spec before this agent ran (see ArchitectAgent._write_acceptance_tests),
    so this agent has no way to make a test match a wrong implementation.
    """

    def __init__(
        self, name: str, bus, provider,
        light_model: Optional[str] = None, strong_model: Optional[str] = None,
    ):
        # Complexity-based model choice (sdk/model_selector.py): a simple,
        # single-task WorkPackage uses light_model (e.g. Haiku); anything
        # bigger uses strong_model (e.g. Sonnet). Both optional — if either
        # is unset, the provider's own default model is used for everything.
        self.light_model = light_model
        self.strong_model = strong_model
        super().__init__(name, bus, provider)

    def register_subscriptions(self) -> None:
        self.bus.subscribe(EventType.SPRINT_PLANNING_APPROVED, self.process_event)
        self.bus.subscribe(EventType.TESTS_FAILED, self.handle_retry)

    async def process_event(self, event: Event) -> None:
        payload = event.payload
        wp_dict = payload.get("work_package", {})
        project_root = Path(payload.get("project_root", "."))
        wp = WorkPackage.model_validate(wp_dict)

        self.logger.info(f"DeveloperAgent starting development for {wp.id}")
        written_files = await self._generate_implementation(project_root, wp)

        await self.emit_event(
            event_type=EventType.DEVELOPMENT_COMPLETED,
            payload={
                "work_package": wp.model_dump(),
                "written_files": written_files,
                "project_root": str(project_root)
            },
            correlation_id=event.correlation_id
        )

    async def handle_retry(self, event: Event) -> None:
        payload = event.payload
        retry_count = payload.get("retry_count", 0)
        max_retries = payload.get("max_retries", 3)
        if retry_count >= max_retries:
            self.logger.warning(f"Max retries ({max_retries}) reached. Escalating to PIPELINE_BLOCKED.")
            await self.emit_event(
                event_type=EventType.PIPELINE_BLOCKED,
                payload={
                    "reason": f"Max retries ({max_retries}) reached without passing tests. Last error: {payload.get('error', '')}",
                    "sprint_id": payload.get("work_package", {}).get("sprint_id", "UNKNOWN"),
                    "work_package_id": payload.get("work_package", {}).get("id", "UNKNOWN")
                },
                correlation_id=event.correlation_id
            )
            return

        self.logger.info(f"DeveloperAgent retrying development (retry {retry_count + 1}/{max_retries})")
        wp_dict = payload.get("work_package", {})
        project_root = Path(payload.get("project_root", "."))
        wp = WorkPackage.model_validate(wp_dict)

        written_files = await self._generate_implementation(
            project_root, wp, previous_error=payload.get("error", "")
        )

        await self.emit_event(
            event_type=EventType.DEVELOPMENT_COMPLETED,
            payload={
                "work_package": wp.model_dump(),
                "written_files": written_files,
                "project_root": str(project_root),
                "retry_count": retry_count + 1
            },
            correlation_id=event.correlation_id
        )

    async def _generate_implementation(
        self, project_root: Path, wp: WorkPackage, previous_error: str = ""
    ) -> Dict[str, str]:
        src_dir = project_root / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "__init__.py").touch(exist_ok=True)

        prompt = self._build_prompt(wp, previous_error)
        context = {"work_package_id": wp.id}
        if self.light_model and self.strong_model:
            context["model"] = select_model(wp, self.light_model, self.strong_model)
        response = await self.provider.generate(prompt, context=context)
        module_code = self._extract_code(response)

        # Namespaced by WorkPackage id — never a fixed "app.py". A fixed path
        # meant every sprint silently overwrote whatever was already there,
        # which is catastrophic when adopting an existing project with real
        # pre-existing code (verified live: it deleted a human's function).
        module_file = src_dir / f"{wp.module_name()}.py"
        module_file.write_text(module_code, encoding="utf-8")

        return {str(module_file): module_code}

    def _build_prompt(self, wp: WorkPackage, previous_error: str = "") -> str:
        module_name = wp.module_name()
        lines = [
            f"You are implementing the Python module `src/{module_name}.py` for WorkPackage {wp.id} ({wp.goal}).",
            "Implement each of the following functions EXACTLY as specified below. Each function takes",
            "no arguments and must return precisely the given value (as a Python string literal).",
            "Return ONLY a single ```python code block containing the full module. No explanation.",
            "",
        ]
        for task in wp.tasks:
            fn_name = task.requirement_ref.lower().replace("-", "_") + "_feature"
            lines.append(
                f"- fn_name: {fn_name} | requirement: {task.requirement_ref} | "
                f"task: {task.description} | must return exactly: {task.expected_output!r}"
            )
        if previous_error:
            lines.append("")
            lines.append("The previous attempt FAILED verification with this error — fix it:")
            lines.append(previous_error[:2000])
        return "\n".join(lines)

    @staticmethod
    def _extract_code(response: str) -> str:
        match = CODE_FENCE_RE.search(response)
        code = match.group(1) if match else response
        code = code.strip()
        if not code:
            code = "# DeveloperAgent produced no usable code for this WorkPackage.\n"
        return code + "\n"
