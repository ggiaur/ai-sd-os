import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
MOTOR_DIR = Path(__file__).parent.resolve()
if str(MOTOR_DIR) not in sys.path:
    sys.path.insert(0, str(MOTOR_DIR))

from kernel.system.config import KernelConfig
from kernel.event_bus.bus import EventBus
from kernel.event_bus.events import Event, EventType
from kernel.state.states import ProjectState
from kernel.state.validators import validate_transition
from kernel.hitl.gate_manager import HITLGateManager
from kernel.ledger.ledger_chain import LedgerChain
from kernel.policy.policy_compiler import PolicyCompiler
from workspace.project_detector import detect_project, list_projects, save_project_state
from planning.cli_planner import CLIPlanner
from agents.discovery_agent import DiscoveryAgent
from agents.architect_agent import ArchitectAgent
from agents.developer_agent import DeveloperAgent
from runtime.test_runner import TestRunnerAgent
from runtime.git_driver import GitDriver
from agents.retrospective_collector import RetrospectiveCollector
from sdk.provider_adapter import MockProviderAdapter, AnthropicAdapter, ClaudeCodeCLIAdapter
from kernel.system.answer_log import write_answer
from kernel.system.version import __version__

class EngineRunner:
    def __init__(self, cwd: Path, config: KernelConfig):
        self.cwd = cwd
        self.config = config
        self.policy = PolicyCompiler(policy_dir=MOTOR_DIR / "kernel" / "policy").compile()
        self.ledger = LedgerChain(cwd / ".ai-sd-os" / "ledger" / "chain.json")
        self.bus = EventBus(ledger=self.ledger)

        # Provider setup: which AIProvider backs generate()/review()/analyze()
        # for every agent below. mock_mode always wins (deterministic, no API
        # key needed) — otherwise config.provider picks between a one-shot API
        # call (anthropic) and a file-aware, iterative CLI session (claude_code_cli).
        if config.mock_mode:
            self.provider = MockProviderAdapter()
        elif config.provider == "claude_code_cli":
            self.provider = ClaudeCodeCLIAdapter(model=config.ai_model, cwd=cwd)
        elif config.api_key:
            self.provider = AnthropicAdapter(api_key=config.api_key, model=config.ai_model)
        else:
            self.provider = MockProviderAdapter()

        # Initialize HITL Gate Manager & Agents
        self.gate_manager = HITLGateManager(self.bus, auto_approve=config.mock_mode)
        self.discovery_agent = DiscoveryAgent(
            "DiscoveryAgent", self.bus, self.provider,
            secret_scan_patterns=self.policy.security.secret_scan.patterns or None,
        )
        self.architect_agent = ArchitectAgent("ArchitectAgent", self.bus, self.provider)
        # Complexity-based model choice (sdk/model_selector.py): simple
        # WorkPackages/reviews use config.light_model (e.g. Haiku), everything
        # else uses config.ai_model (e.g. Sonnet). Applies to both codegen and
        # independent review — one shared heuristic, not two separate ones.
        self.developer_agent = DeveloperAgent(
            "DeveloperAgent", self.bus, self.provider,
            light_model=config.light_model, strong_model=config.ai_model,
        )
        self.test_runner = TestRunnerAgent(
            "TestRunnerAgent", self.bus, self.provider,
            max_retries=self.policy.execution.max_retries, review_model=config.light_model,
        )
        self.git_driver = GitDriver("GitDriver", self.bus, self.provider)
        self.retro_collector = RetrospectiveCollector("RetrospectiveCollector", self.bus, self.provider)

    async def run(self) -> None:
        handle = detect_project(self.cwd)

        if handle:
            print(f"╔══════════════════════════════════════════════════╗")
            print(f"║  AI-SD-OS V{__version__} — Meglévő projekt: {self.cwd.name:<16} ║")
            print(f"╚══════════════════════════════════════════════════╝\n")
            print(f"Állapot: {handle.state.value}\n")
            print("[1] Új sprint indítása (új követelmények hozzáadása)")
            print("[2] Kódbázis felmérése és specifikáció frissítése (Discovery)")
            print("[3] Detektált projektek listázása")
            print("[4] Projekt állapotának törlése (Reset)")

            if self.config.mock_mode:
                choice = "1"
            else:
                try:
                    choice = input("> ").strip()
                except EOFError:
                    choice = "1"

            if choice == "4":
                import shutil
                ai_sd_dir = self.cwd / ".ai-sd-os"
                if ai_sd_dir.exists():
                    shutil.rmtree(ai_sd_dir)
                print("✓ Projekt állapota törölve (.ai-sd-os/ eltávolítva).")
                return
            elif choice == "3":
                workspace_root = self.cwd.parent if self.cwd.parent.exists() else self.cwd
                projects = list_projects(workspace_root, MOTOR_DIR)
                print(f"\n📋 Detektált AI-SD-OS projektek ({len(projects)}):\n")
                if not projects:
                    print("  (Nincs még aktív projekt a szülőkönyvtárban)")
                for p in projects:
                    print(f"  • {p.name:<25} [{p.state}] -> {p.path}")
                print()
                return
            elif choice == "2":
                print(f"\n[DISCOVERY] Kódbázis felmérése elindítva...")
                save_project_state(self.cwd, ProjectState.DISCOVERY)
                snapshot = await self.discovery_agent.survey_codebase(self.cwd)
                planner = CLIPlanner()
                spec = planner.create_spec_interactive(self.cwd, snapshot=snapshot, auto_approve=self.config.mock_mode)
                save_project_state(self.cwd, ProjectState.SPEC)
                await self.start_sprint_pipeline(spec)
                return
            else:
                await self.execute_from_state(handle.state)
                return
        else:
            print(f"╔══════════════════════════════════════════════════╗")
            print(f"║  AI-SD-OS V{__version__} — Mi a helyzet?                     ║")
            print(f"╚══════════════════════════════════════════════════╝\n")
            print(f"Ebben a könyvtárban ({self.cwd.resolve()})")
            print(f"még nincs AI-SD-OS projekt.\n")
            print("[1] Új projektet indítok (üres lapról, tervezési kérdések)")
            print("[2] Felmérem a meglévő kódot, és onnan folytatom")
            print("[3] Detektált projektek listázása")

            if self.config.mock_mode:
                choice = "1"
            else:
                try:
                    choice = input("> ").strip()
                except EOFError:
                    choice = "1"

            if choice == "3":
                workspace_root = self.cwd.parent if self.cwd.parent.exists() else self.cwd
                projects = list_projects(workspace_root, MOTOR_DIR)
                print(f"\n📋 Detektált AI-SD-OS projektek ({len(projects)}):\n")
                if not projects:
                    print("  (Nincs még aktív projekt a szülőkönyvtárban)")
                for p in projects:
                    print(f"  • {p.name:<25} [{p.state}] -> {p.path}")
                print()
                return
            elif choice == "2":
                print(f"\n[DISCOVERY] Kódbázis felmérése elindítva...")
                save_project_state(self.cwd, ProjectState.DISCOVERY)
                snapshot = await self.discovery_agent.survey_codebase(self.cwd)
                planner = CLIPlanner()
                spec = planner.create_spec_interactive(self.cwd, snapshot=snapshot, auto_approve=self.config.mock_mode)
                save_project_state(self.cwd, ProjectState.SPEC)
                await self.start_sprint_pipeline(spec)
            else:
                save_project_state(self.cwd, ProjectState.DISCOVERY)
                planner = CLIPlanner()
                spec = planner.create_spec_interactive(self.cwd, snapshot=None, auto_approve=self.config.mock_mode)
                save_project_state(self.cwd, ProjectState.SPEC)
                await self.start_sprint_pipeline(spec)

    async def execute_from_state(self, current_state: ProjectState) -> None:
        from kernel.contracts.serializer import load_yaml_contract
        from contracts.spec_formal import SpecFormal

        spec_file = self.cwd / ".ai-sd-os" / "SPEC_FORMAL.yaml"
        if spec_file.exists():
            spec = load_yaml_contract(spec_file, SpecFormal)
            await self.start_sprint_pipeline(spec)
        else:
            save_project_state(self.cwd, ProjectState.INIT)
            await self.run()

    async def start_sprint_pipeline(self, spec) -> None:
        save_project_state(self.cwd, ProjectState.WORK_PACKAGE)

        # One unique correlation id per pipeline run, so we can inspect exactly
        # which events this run produced afterwards (bus.history is shared
        # across the whole process, not scoped to a single publish() call).
        correlation_id = f"pipeline-{spec.project_name}-{int(time.time()*1000)}"

        # Trigger Spec Created Event -> Architect Agent -> WorkPackage -> HITL -> Developer -> Test -> Review -> Retro
        await self.bus.publish(Event(
            event_type=EventType.SPEC_CREATED,
            payload={"spec": spec.model_dump(), "project_root": str(self.cwd.resolve())},
            correlation_id=correlation_id
        ))

        chain_events = [e for e in self.bus.history if e.correlation_id == correlation_id]
        blocked_events = [e for e in chain_events if e.event_type == EventType.PIPELINE_BLOCKED]

        if blocked_events:
            reason = blocked_events[-1].payload.get("reason", "Unknown reason")
            save_project_state(self.cwd, ProjectState.BLOCKED)
            summary = (
                f"# Sprint Pipeline — BLOCKED\n\n"
                f"- Spec: {spec.project_name}\n"
                f"- Ok: {reason}\n\n"
                f"A pipeline NEM ért véget sikeresen — emberi beavatkozás szükséges.\n"
                f"A `.ai-sd-os/state.json` most `BLOCKED` állapotban van.\n"
            )
            write_answer(self.cwd, summary)
            print(f"\n⛔ Sprint pipeline BLOCKED: {reason}")
            print(f"Projekt állapota: BLOCKED — emberi beavatkozás szükséges.\n")
            return

        was_planned = any(e.event_type == EventType.WORKPACKAGE_CREATED for e in chain_events)
        if not was_planned:
            # ArchitectAgent found nothing PENDING to build — nothing actually
            # happened this run. That is not the same thing as "DONE".
            save_project_state(self.cwd, ProjectState.SPEC)
            print(f"\nℹ️  Nincs elvégezhető (PENDING) követelmény a specifikációban. Nincs mit sprintelni.\n")
            return

        save_project_state(self.cwd, ProjectState.DONE)
        summary = (
            f"# Sprint Pipeline — DONE\n\n"
            f"- Spec: {spec.project_name}\n"
            f"- A sprint sikeresen lefutott, a tesztek és a HITL kapuk jóváhagyással zárultak.\n"
        )
        write_answer(self.cwd, summary)
        print(f"\n🎉 Sprint lefutott és elküldve! Projekt állapota: DONE\n")

def main():
    parser = argparse.ArgumentParser(description=f"AI-SD-OS V{__version__} Engine")
    parser.add_argument("command", nargs="?", default=None, help="Command (list, status)")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without requiring API keys")

    args = parser.parse_args()
    cwd = Path.cwd()

    if args.command == "list":
        workspace_root = cwd.parent if cwd.parent.exists() else cwd
        projects = list_projects(workspace_root, MOTOR_DIR)
        print(f"\n📋 Detektált AI-SD-OS projektek ({len(projects)}):\n")
        if not projects:
            print("  (Nincs még aktív projekt a szülőkönyvtárban)")
        for p in projects:
            print(f"  • {p.name:<25} [{p.state}] -> {p.path}")
        print()
        return

    if args.command == "status":
        handle = detect_project(cwd)
        if handle:
            print(f"\n📍 Projekt: {cwd.name}")
            print(f"   Állapot: {handle.state.value}")
            print(f"   Fájl:    {handle.state_file}\n")
        else:
            print(f"\n❌ Nincs AI-SD-OS projekt ebben a könyvtárban ({cwd.resolve()})\n")
        return

    if _is_motor_directory(cwd):
        print(
            "\n❌ A motor (ai-sd-os/) és a generált projektek soha nem élhetnek ugyanabban a "
            "könyvtárban / Git repóban (lásd README, 'Kritikus Tervezési Alapelvek').\n"
            f"   Jelenlegi könyvtár: {cwd.resolve()}\n"
            f"   Ez a motor saját könyvtára: {MOTOR_DIR}\n\n"
            "   Menj a célprojekted saját (testvér-)könyvtárába, és onnan indítsd:\n"
            f"   cd /path/to/your-project && python3 {MOTOR_DIR / 'main.py'}\n"
        )
        sys.exit(1)

    config = KernelConfig.from_env(cwd=cwd, mock=args.mock)
    runner = EngineRunner(cwd=cwd, config=config)
    asyncio.run(runner.run())


def _is_motor_directory(cwd: Path) -> bool:
    """True if cwd is the motor's own directory (or inside it).

    Running the project pipeline here is exactly what produced the historical
    duplicate-commit / duplicate-CHANGELOG spam in this repository's own git
    history: the motor wrote generated-project artifacts into itself.
    """
    cwd_resolved = cwd.resolve()
    return cwd_resolved == MOTOR_DIR or MOTOR_DIR in cwd_resolved.parents


if __name__ == "__main__":
    main()
