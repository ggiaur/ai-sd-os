from typing import Dict, Any, List

class CLIPrompter:
    def prompt_sprint_planning(self, wp_id: str, sprint_id: str, goal: str, reqs: List[Dict[str, Any]], est_minutes: int, dod_list: List[str], paths: List[str], auto_approve: bool = False) -> str:
        if auto_approve:
            return "j"
        print("\n" + "═" * 54)
        print(f"  SPRINT PLANNING — {wp_id} ({sprint_id})")
        print("═" * 54)
        print(f"\nCél: {goal}\n")
        print("Ebbe a sprintbe bekerülő követelmények:")
        for r in reqs:
            print(f"  {r.get('id', '')} [{r.get('priority', 'MEDIUM')}]   {r.get('description', '')}")
        print(f"\nBecsült idő: ~{est_minutes} perc autonóm munka")
        print(f"Definition of Done: {', '.join(dod_list)}")
        print(f"Érintett elérési utak: {', '.join(paths)}\n")
        print("[j] Jóváhagyom, indulhat        [m] Módosítom a scope-ot")
        print("[n] Elutasítom, vissza a backlogba")

        try:
            choice = input("> ").strip().lower()
        except EOFError:
            choice = "j"
        return choice if choice in ["j", "m", "n"] else "j"

    def prompt_sprint_review(self, wp_id: str, sprint_id: str, auto_dod_passed: int, auto_dod_total: int, manual_dods: List[str], auto_approve: bool = False) -> str:
        if auto_approve:
            return "j"
        print("\n" + "═" * 54)
        print(f"  SPRINT REVIEW — {wp_id} ({sprint_id})")
        print("═" * 54)
        print(f"\n✓ Automatikus DoD kritériumok: {auto_dod_passed}/{auto_dod_total} teljesítve")
        if manual_dods:
            print(f"⚠ Manuális DoD kritériumok ellenőrzése: {', '.join(manual_dods)}")
        print("\n[j] Elfogadom, commit-olhat        [d] Diff megtekintése")
        print("[n] Elutasítom, vissza fejlesztésre")

        try:
            choice = input("> ").strip().lower()
        except EOFError:
            choice = "j"
        return choice if choice in ["j", "d", "n"] else "j"

    def prompt_blocked(self, wp_id: str, sprint_id: str, last_error: str, auto_approve: bool = False) -> str:
        if auto_approve:
            return "r"
        print("\n" + "═" * 54)
        print(f"  ⚠ BLOCKED — {wp_id} ({sprint_id})")
        print("═" * 54)
        print(f"\nMax retries elfogyott. Utolsó hiba:\n  {last_error}\n")
        print("[r] Újrapróbálom módosított instrukcióval")
        print("[e] Szerkesztem a WorkPackage-et / követelményt")
        print("[s] Sprint felfüggesztése, később folytatom")

        try:
            choice = input("> ").strip().lower()
        except EOFError:
            choice = "r"
        return choice if choice in ["r", "e", "s"] else "r"

    def prompt_destructive(self, action_name: str, target: str, auto_approve: bool = False) -> bool:
        if auto_approve:
            return True
        print("\n" + "═" * 54)
        print("  🔒 DESTRUCTIVE ACTION GATE")
        print("═" * 54)
        print(f"\nMűvelet: {action_name}")
        print(f"Célpont: {target}\n")
        print("Engedélyezed a műveletet? [y/N]")

        try:
            choice = input("> ").strip().lower()
        except EOFError:
            choice = "y"
        return choice == "y"
