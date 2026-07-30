import argparse
import asyncio
import os
import sys
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
from workspace.project_detector import detect_project, list_projects, save_project_state
from planning.cli_planner import CLIPlanner
from agents.discovery_agent import DiscoveryAgent
from agents.architect_agent import ArchitectAgent
from agents.developer_agent import DeveloperAgent
from runtime.test_runner import TestRunnerAgent
from runtime.git_driver import GitDriver
from agents.retrospective_collector import RetrospectiveCollector
from sdk.provider_adapter import MockProviderAdapter, AnthropicAdapter

class EngineRunner:
    def __init__(self, cwd: Path, config: KernelConfig):
        self.cwd = cwd
        self.config = config
        self.bus = EventBus()
        from kernel.ledger.ledger_chain import LedgerChain
        self.ledger = LedgerChain(cwd / ".ai-sd-os" / "ledger")
        self.bus.set_ledger(self.ledger)

        # Provider setup
        if config.mock_mode or not config.api_key:
            self.provider = MockProviderAdapter()
        else:
            self.provider = AnthropicAdapter(api_key=config.api_key, model=config.ai_model)

        # Initialize HITL Gate Manager & Agents
        self.gate_manager = HITLGateManager(self.bus, auto_approve=config.mock_mode)
        self.discovery_agent = DiscoveryAgent("DiscoveryAgent", self.bus, self.provider)
        self.architect_agent = ArchitectAgent("ArchitectAgent", self.bus, self.provider)
        self.developer_agent = DeveloperAgent("DeveloperAgent", self.bus, self.provider)
        self.test_runner = TestRunnerAgent("TestRunnerAgent", self.bus, self.provider)
        self.git_driver = GitDriver("GitDriver", self.bus, self.provider)
        self.retro_collector = RetrospectiveCollector("RetrospectiveCollector", self.bus, self.provider)

    async def run(self) -> None:
        handle = detect_project(self.cwd)

        if handle:
            print(f"📌 Folytatás meglévő AI-SD-OS projektből ({self.cwd.name}). Állapot: {handle.state.value}")
            await self.execute_from_state(handle.state)
        else:
            print(f"╔══════════════════════════════════════════════════╗")
            print(f"║  AI-SD-OS V5 — Mi a helyzet?                     ║")
            print(f"╚══════════════════════════════════════════════════╝\n")
            print(f"Ebben a könyvtárban ({self.cwd.resolve()})")
            print(f"még nincs AI-SD-OS projekt.\n")
            print("[1] Új projektet indítok (üres lapról, tervezési kérdések)")
            print("[2] Felmérem a meglévő kódot, és onnan folytatom")

            if self.config.mock_mode:
                choice = "1"
            else:
                try:
                    choice = input("> ").strip()
                except EOFError:
                    choice = "1"

            if choice == "2":
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

        # Trigger Spec Created Event -> Architect Agent -> WorkPackage -> HITL -> Developer -> Test -> Review -> Retro
        await self.bus.publish(Event(
            event_type=EventType.SPEC_CREATED,
            payload={"spec": spec.model_dump(), "project_root": str(self.cwd.resolve())},
            correlation_id="pipeline-main"
        ))

        save_project_state(self.cwd, ProjectState.DONE)
        print(f"\n🎉 Sprint lefutott és elküldve! Projekt állapota: DONE\n")

def main():
    parser = argparse.ArgumentParser(description="AI-SD-OS V5 Engine")
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

    config = KernelConfig.from_env(cwd=cwd, mock=args.mock)
    runner = EngineRunner(cwd=cwd, config=config)
    asyncio.run(runner.run())

if __name__ == "__main__":
    main()
