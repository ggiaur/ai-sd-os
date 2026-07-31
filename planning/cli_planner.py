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
            if snapshot.security.risk_flags:
                print(f"  ⚠ Biztonsági kockázatok: {len(snapshot.security.risk_flags)} gyanús elem")

            if auto_approve:
                q1_ans = "Kész, alapfunkciók rendben"
                q2_ans = "Autentikáció és biztonsági javítások"
                q3_ans = "Régi nem használt modulok kivezetése"
                q4_ans = "Igen, a secreteket környezeti változókba helyezzük"
                q5_ans = "Auth működik, secretek env-be, tesztek lefutnak"
            else:
                print("\nKérlek, válaszolj az alábbi felmérési kérdésekre:\n")
                try:
                    q1_ans = input("[1/5] Jól látom a felmért alapfunkciókat? (Igen / Megjegyzés)\n> ").strip()
                    q2_ans = input("[2/5] Mi a következő fő fejlesztési cél/funkció?\n> ").strip()
                    q3_ans = input("[3/5] Mi a technikai adóssága a programnak, és mi az a modul amit ki kell vezetni?\n> ").strip()
                    q4_ans = input(f"[4/5] A detektált biztonsági jelzéseket ({snapshot.security.secret_scan_status}) kezeljük most? [Y/n]\n> ").strip()
                    q5_ans = input("[5/5] Mi a Definition of Done (DoD) elvárásod?\n> ").strip()
                except EOFError:
                    q1_ans = "Rendben"
                    q2_ans = "Következő funkciók megvalósítása"
                    q3_ans = "Nincs"
                    q4_ans = "Y"
                    q5_ans = "Tesztek zöldek"

            reqs = [
                RequirementItem(
                    id="FR-001",
                    title="Meglévő alapfunkciók",
                    description=q1_ans or "Kódbázis alapfunkciók igazolva",
                    priority=PriorityEnum.HIGH,
                    status=RequirementStatus.SATISFIED
                ),
                RequirementItem(
                    id="FR-002",
                    title=q2_ans or "Következő fő fejlesztési modul",
                    description=f"Cél: {q2_ans}. DoD elvárás: {q5_ans}",
                    priority=PriorityEnum.HIGH,
                    status=RequirementStatus.PENDING
                )
            ]
            if q3_ans and q3_ans.lower() != "nincs":
                reqs.append(RequirementItem(
                    id="FR-003",
                    title="Technikai adósság és kivezetés",
                    description=q3_ans,
                    priority=PriorityEnum.MEDIUM,
                    status=RequirementStatus.PENDING
                ))
            if q4_ans.lower() in ["y", "igen", ""]:
                reqs.append(RequirementItem(
                    id="FR-004",
                    title="Biztonsági secretek környezeti változókba rendezése",
                    description="Secret scanner által jelzett hardcode-olt elemek env-be szervezése",
                    priority=PriorityEnum.HIGH,
                    status=RequirementStatus.PENDING
                ))

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

        print(f"\n✓ .ai-sd-os/ SPEC_FORMAL.yaml frissítve az alábbi követelményekkel:")
        for r in spec.requirements:
            print(f"  • {r.id} [{r.status.value}] {r.title}")
        print()
        return spec
