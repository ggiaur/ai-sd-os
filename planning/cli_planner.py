from pathlib import Path
from typing import Optional, List
from contracts.spec_formal import SpecFormal, RequirementItem, PriorityEnum, RequirementStatus
from contracts.codebase_snapshot import CodebaseSnapshot
from kernel.contracts.serializer import save_yaml_contract

class CLIPlanner:
    def create_spec_interactive(self, project_root: Path, snapshot: Optional[CodebaseSnapshot] = None, auto_approve: bool = False) -> SpecFormal:
        project_name = project_root.name

        if snapshot:
            print(f"\n╔══════════════════════════════════════════════════════╗")
            print(f"║  AI-SD-OS — Meglévő projekt: {project_name:<24} ║")
            print(f"╚══════════════════════════════════════════════════════╝\n")
            print("A felmérés alapján ezt találtam:")
            for inf in snapshot.inferred_requirements:
                print(f"  ✓ {inf.title} ({inf.description})")

            reqs = [
                RequirementItem(
                    id="FR-001",
                    title="Alapfunkciók stabilizálása",
                    description="Meglévő kód felmérése és alaptesztek biztosítása",
                    priority=PriorityEnum.HIGH,
                    status=RequirementStatus.SATISFIED
                ),
                RequirementItem(
                    id="FR-002",
                    title="Autentikáció és biztonsági javítások",
                    description="Kódbázis biztonsági kockázatok és secret leakek kezeése",
                    priority=PriorityEnum.HIGH,
                    status=RequirementStatus.PENDING
                )
            ]
            tech_stack = snapshot.stack.languages + snapshot.stack.frameworks
        else:
            if auto_approve:
                goal = f"Build awesome application for {project_name}"
                req_title = "Fő funkciók implementálása"
                req_desc = "Alapvető CRUD és üzleti logika megvalósítása"
                stack_choice = "python, fastapi"
            else:
                print(f"\n╔══════════════════════════════════════════════════════╗")
                print(f"║  AI-SD-OS — Új projekt: {project_name:<28} ║")
                print(f"╚══════════════════════════════════════════════════════╝\n")
                try:
                    goal = input("Mi a projekt fő célja?\n> ").strip() or "General Software Application"
                    req_title = input("Első fő funkció megnevezése:\n> ").strip() or "Core API module"
                    req_desc = input("Részletes leírás:\n> ").strip() or "Implement core API functionality"
                    stack_choice = input("Technológiai stack (pl. python, fastapi, sqlite):\n> ").strip() or "python"
                except EOFError:
                    goal = "General Application"
                    req_title = "Core module"
                    req_desc = "Core functionality"
                    stack_choice = "python"

            reqs = [
                RequirementItem(
                    id="FR-001",
                    title=req_title,
                    description=req_desc,
                    priority=PriorityEnum.HIGH,
                    status=RequirementStatus.PENDING
                )
            ]
            tech_stack = [s.strip() for s in stack_choice.split(",") if s.strip()] or ["python"]

        spec = SpecFormal(
            project_name=project_name,
            version="1.0.0",
            goal=snapshot.architecture if snapshot else goal,
            tech_stack=tech_stack,
            requirements=reqs
        )

        ai_sd_dir = project_root / ".ai-sd-os"
        ai_sd_dir.mkdir(parents=True, exist_ok=True)
        save_yaml_contract(spec, ai_sd_dir / "SPEC_FORMAL.yaml")

        print(f"\n✓ .ai-sd-os/ SPEC_FORMAL.yaml sikeresen létrehozva!\n")
        return spec
