# AI-SD-OS V5 — AI Software Development Operating System

> **"Clone it. Answer the questions. Ship the project."**

---

## Mi ez?

Az **AI-SD-OS** (AI Software Development Operating System) egy letölthető, önálló fejlesztési keretrendszer, amely bármilyen szoftverprojektet képes végigvezetni az ötlettől a kész, tesztelt kódbázisig — minimális emberi beavatkozással.

Nem egy konkrét projekt. Nem egy sablon. Hanem egy **projekt-generátor motor**: egy fix, stabil kernel, amely körül az agentek, promptok, szerződések és sprintek automatikusan hajtják a fejlesztési folyamatot.

A rendszer stack-agnosztikus: Python, TypeScript, vagy bármilyen más technológia feletti projektekhez egyaránt használható.

**Kritikus tervezési elv:** a motor (ez a repó) és a vele generált projektek **soha nem élnek ugyanabban a git repóban**. A motort egyszer klónozod. Utána tetszőleges számú, egymástól teljesen független, párhuzamos projektet generálhatsz vele — mindegyiknek saját könyvtára, saját git története, saját állapota van. Lásd: [Motor vs Projekt](#motor-vs-projekt--a-workspace-architektúra).

**Fejlesztési környezet:** a rendszer az **Antigravity CLI** (`agy`) alatt fut, Linux rendszeren. Az `agy` **nem azonos a bash terminállal** — külön IDE-felület, amelyen belül a `python main.py` parancsok az aktuális munkakönyvtár kontextusában értendők. A kódpéldákban szereplő shell szintaxis Linux-kompatibilis, de a tényleges futtatás az `agy` munkaterületéről történik.

---

## Hogyan működik? (30 másodperc)

```bash
# 1. A motort egyszer klónozod — ez a "gyár", nem a "termék"
git clone https://github.com/yourorg/ai-sd-os.git /srv/projekts/ai-sd-os
pip install -r /srv/projekts/ai-sd-os/requirements.txt

# 2. Minden projektmunkát a PROJEKT könyvtárából indítasz
cd /srv/projekts/webarchivum
python /srv/projekts/ai-sd-os/main.py
```

A `main.py` megvizsgálja a munkakönyvtárat:

- **Van `.ai-sd-os/` mappa?** → Folytatja onnan, ahol tartott.
- **Nincs `.ai-sd-os/` mappa?** → Megkérdezi: új projekt, vagy meglévő kódbázis felmérése?

```
╔══════════════════════════════════════════════════╗
║  AI-SD-OS V4 — Mi a helyzet?                     ║
╚══════════════════════════════════════════════════╝

Ebben a könyvtárban (/srv/projekts/webarchivum)
még nincs AI-SD-OS projekt.

[1] Új projektet indítok (üres lapról, tervezési kérdések)
[2] Felmér em a meglévő kódot, és onnan folytatom
> _
```

Nincs `new` / `adopt` alparancs — a motor a **cwd-ből** ért mindent, pont ahogy a `git`, a `terraform`, vagy az `npm` is teszi.

---

## A rendszer felépítése

```
ai-sd-os/                               ← a motor (egyszer klónozod, soha nem módosítod futás közben)
├── kernel/
│   ├── system/
│   │   ├── config.py                   # KernelConfig: retries, checkpoint, storage
│   │   └── SYSTEM_CONSTITUTION.md      # A rendszer törvényei
│   ├── event_bus/
│   │   ├── events.py                   # Összes eseménytípus definíciója
│   │   └── bus.py                      # Aszinkron EventBus implementáció
│   ├── state/
│   │   ├── states.py                   # Állapot definíciók (INIT, DISCOVERY, SPEC...)
│   │   ├── transitions.py              # Engedélyezett átmenetek táblája
│   │   └── validators.py               # Átmenet-validátorok (illegális lépés → kivétel)
│   ├── hitl/
│   │   ├── gate_manager.py             # HITLGateManager: jóváhagyási pontok
│   │   └── cli_prompts.py              # Sprint Planning / Review / Blocked / Destructive CLI
│   ├── contracts/
│   │   ├── validator.py                # Pydantic-alapú contract validáció
│   │   └── serializer.py               # YAML szerializáció/deszérializáció
│   ├── policy/
│   │   ├── rules.yaml                  # Végrehajtási szabályok (require_human, etc.)
│   │   ├── security.yaml               # Biztonsági policy (secret scan, sandbox)
│   │   └── execution.yaml              # Budget, retry, timeout szabályok
│   └── checkpoint/
│       └── checkpoint_manager.py       # Állapot mentés és visszaállítás
│
├── contracts/
│   ├── spec_formal.py                  # SpecFormal: projekt célok, követelmények (FR-XXX)
│   ├── work_package.py                 # WorkPackage: sprint feladatok, coverage_mapping
│   ├── definition_of_done.py           # DefinitionOfDone: validált DoD kritériumok
│   ├── codebase_snapshot.py            # CodebaseSnapshot: meglévő projekt felmérés
│   └── retrospective.py               # Retrospective: sprint tanulságok
│
├── sdk/
│   ├── models.py                       # AgentContext, ExecutionResult, AgentStatusCode
│   ├── provider_adapter.py             # AI provider interfész + Mock implementáció
│   └── base_agent.py                   # BaseAgentSDK — minden agent ebből örököl
│
├── agents/
│   ├── prompts.py                      # Összes system prompt egy helyen
│   ├── architect_agent.py              # SPEC → WORK_PACKAGE (Sprint Backlog kiválasztás)
│   ├── developer_agent.py              # WORK_PACKAGE → forráskód generálás
│   ├── discovery_agent.py              # Meglévő projekt felmérése (0. lépés)
│   └── retrospective_collector.py      # Sprint tanulságok + Lessons Learned aggregáció
│
├── runtime/
│   ├── artifacts.py                    # ArtifactRegistry: minden kimenet nyilvántartva
│   ├── sandbox.py                      # DockerSandbox (fallback: subprocess)
│   ├── test_runner.py                  # Pytest + coverage mapping + DoD validáció
│   └── git_driver.py                   # Git init/adopt, commit, branch kezelés
│
├── planning/
│   └── cli_planner.py                  # CLI kérdések → SpecFormal (survey-aware)
│
├── workspace/
│   └── project_detector.py             # cwd alapú projekt detektálás (.ai-sd-os/ keresés)
│
├── lessons/
│   └── aggregator.py                   # Motor-szintű Lessons Learned aggregátor
│
├── security/
│   ├── secret_scanner.py               # Hardcode-olt secret detektálás (discovery + sprint)
│   ├── permission_manager.py           # Agent jogosultságok — soha nem korlátlan
│   └── sandbox_policy.py               # Futtatási sandbox szabályok
│
├── tests/
│   ├── test_kernel.py
│   ├── test_contracts.py
│   ├── test_coverage_mapping.py
│   ├── test_hitl_gates.py
│   └── test_golden_path.py
│
├── main.py                             # Belépési pont — cwd-tudatos, nincs kötelező alparancs
├── requirements.txt
└── README.md
```

A motor repóban **nincs** `projects/` mappa. Az egyes projektek állapota a **projekt saját könyvtárában**, egy `.ai-sd-os/` rejtett mappában él — pontosan úgy, ahogy a `.git/` sem a git binárisan, hanem a munkakönyvtárban tárolódik.

---

## Motor vs Projekt — a workspace architektúra

Ez a legfontosabb strukturális szabály, és a rendszer minden más része ennek van alárendelve.

### A két, egymástól élesen elválasztott entitás

| | **A motor (ez a repó)** | **A projekt** |
|---|---|---|
| Mi ez? | Kernel, agentek, contract-ok, promptok | Egy konkrét szoftvertermék |
| Hol él? | `/srv/projekts/ai-sd-os/` — egyszer klónozva | `/srv/projekts/<projekt-neve>/` — a saját helyén |
| Git története | A motor saját fejlesztésének history-ja | A generált/fejlesztett kód saját, tiszta commit-je |
| Verziózás | Motor release-ek (v4.0, v4.1...) | Sprint tagek (SPRINT-001, SPRINT-002...) |
| Állapot tárolás | Nincs — a motor állapotmentes | `.ai-sd-os/` mappa a projekt könyvtárában |
| Hány létezhet? | Egy (amit használsz) | Tetszőlegesen sok, párhuzamosan |

### Egyetlen workspace gyökér — testvérkönyvtárak

A motor és a projektek **kényelmesen élhetnek ugyanabban a szülőkönyvtárban** — ez nem sérti az elvet, mert az elv lényege nem a fizikai távolság, hanem a **git izoláció**:

```
/srv/projekts/
├── ai-sd-os/              ← a motor saját git repója (egyszer klónozod)
├── webarchivum/            ← projekt, saját git repó, saját .ai-sd-os/
├── todo-app-a1b2c3/        ← projekt, saját git repó, saját .ai-sd-os/
└── crm-backend-d4e5f6/     ← projekt, saját git repó, saját .ai-sd-os/
```

Ha a `list` parancsot futtatod, a motor végigpásztázza a szülőkönyvtár alkönyvtárait, és összeszedi, melyikben van `.ai-sd-os/` — de **saját magát** (`ai-sd-os/`) kihagyja a listából.

### A directory-native állapot (.ai-sd-os/)

Nincs central `registry.json`. Az állapot ott él, ahol a projekt:

```
/srv/projekts/webarchivum/
└── .ai-sd-os/
    ├── state.json              ← projekt állapotgép (INIT → DONE)
    ├── SPEC_FORMAL.yaml        ← formális specifikáció
    ├── CODEBASE_SNAPSHOT.yaml  ← (meglévő projektnél: felmérés eredménye)
    ├── checkpoints/
    │   ├── checkpoint_SPEC_20240115_143025.json
    │   └── checkpoint_DEVELOPMENT_20240115_143041.json
    ├── retrospectives/
    │   ├── SPRINT-001.yaml
    │   └── SPRINT-002.yaml
    └── memory/                 ← projekt strukturált memóriája (Phase 1.5)
        ├── decisions.yaml      ← architekturális döntések + indoklás
        ├── architecture.yaml   ← detektált / tervezett architektúra
        └── known_issues.yaml   ← ismert problémák, technical debt
```

**Miért ez a jobb modell?**

| Kérdés | Central registry.json | Directory-native (.ai-sd-os/) |
|---|---|---|
| Mi történik, ha kézzel törölsz egy projektmappát? | Árva bejegyzés marad a registry-ben | Semmi — a mappa törlésével minden eltűnik |
| Hogyan viszed át egy projektet másik gépre? | Szinkronizálni kell a registry-t is | `cp -r webarchivum/ ...` — minden benne van |
| Tud-e két AI-SD-OS példány egyszerre dolgozni? | Versenyhelyzet a registry-n | Mindenki a saját könyvtárában dolgozik |
| Mi az egyetlen igazságforrás? | Két hely (registry + mappa) | Egy hely (a mappa maga) |

Ez a git, a terraform és az npm mintáját követi: **bemész a könyvtárba, a tool ott, helyben detektálja az állapotot.**

### A Project Detector

A `workspace/project_detector.py` felelős a felismerésért:

```python
def detect_project(cwd: Path) -> ProjectHandle | None:
    """
    Megvizsgálja a cwd-t. Ha van .ai-sd-os/state.json,
    visszaad egy ProjectHandle-t a mentett állapottal.
    Ha nincs, None-t ad vissza (→ interaktív wizard indul).
    """
    state_file = cwd / ".ai-sd-os" / "state.json"
    if state_file.exists():
        return ProjectHandle.from_state(state_file)
    return None
```

A `list` parancs kényelmi funkció — végigiterál a szülőkönyvtáron, és összeszedi a detektált projekteket, de **nem ez az egyetlen igazságforrás**:

```python
def list_projects(workspace_root: Path, motor_dir: Path) -> list[ProjectSummary]:
    """
    Végigpásztázza a workspace_root alkönyvtárait.
    Kihagyja a motor saját könyvtárát (motor_dir).
    Csak azokat listázza, amelyekben van .ai-sd-os/state.json.
    """
    return [
        ProjectSummary.from_state(d / ".ai-sd-os" / "state.json")
        for d in workspace_root.iterdir()
        if d.is_dir()
        and d != motor_dir
        and (d / ".ai-sd-os" / "state.json").exists()
    ]
```

---

## Az állapotgép (State Machine)

A rendszer minden projekthez egy szigorú, validált állapotgépen halad végig. Illegális átmenetek kivételt dobnak — nincs „átugrás".

A legfontosabb tervezési elv: **az autonóm munka és az emberi jóváhagyás élesen el van választva**. Az AI hosszú ideig, önállóan dolgozik két gate között — de a gate-eken nem lép át emberi megerősítés nélkül.

```
INIT
  │
  ▼
DISCOVERY            ← CLI kérdések (+ meglévő projektnél: kódbázis felmérés)
  │
  ▼
SPEC                 ← SPEC_FORMAL.yaml generálva és validálva
  │
  ▼
WORK_PACKAGE         ← Sprint Backlog kiválasztva (prioritás + kapacitás alapján)
  │
  ▼
┌─────────────────────────────────────────┐
│ 🔒 SPRINT_PLANNING  — HUMAN GATE         │  ← „Ezt a scope-ot, ennyi taszkkal,
│    (jóváhagyás szükséges)                │     ezzel a Definition of Done-nal
└─────────────────────────────────────────┘     elindítsam?" — igen/nem/módosít
  │
  ▼
┌─────────────────────────────────────────┐
│  AUTONÓM VÉGREHAJTÁSI ABLAK              │  ← ember NEM avatkozik bele,
│  DEVELOPMENT ⇄ TEST (retry loop)         │     amíg a sprint fut
│  max_retries-ig önállóan fut             │
└─────────────────────────────────────────┘
  │                              │
  │ retry kimerült                │ tesztek + coverage mapping zöld
  ▼                              ▼
┌─────────────────┐    ┌─────────────────────────────────────────┐
│ 🔒 BLOCKED        │    │ 🔒 SPRINT_REVIEW  — HUMAN GATE            │
│  (escalation,     │    │    (jóváhagyás szükséges)                 │
│   human dönt)     │    │    „Ez az increment elfogadható?"         │
└─────────────────┘    └─────────────────────────────────────────┘
  │                              │
  │ human döntés után             │ elfogadva
  ▼                              ▼
DEVELOPMENT / WORK_PACKAGE   PR_CREATED   ← Git commit + branch
  (újratervezés)                │
                                 ▼
                          RETROSPECTIVE   ← sprint tanulságok (.ai-sd-os/retrospectives/)
                                 │
                                 ▼
                    ┌──── van még Sprint Backlog elem? ────┐
                    │ igen                         nem     │
                    ▼                                       ▼
              WORK_PACKAGE (köv. sprint)                  DONE ✓
```

**Bárhonnan, bármikor** elsülhet egy ötödik gate is:

```
┌─────────────────────────────────────────┐
│ 🔒 DESTRUCTIVE_ACTION  — HUMAN GATE       │  ← fájltörlés az allowed_paths-on
│    (jóváhagyás szükséges)                 │     kívül, séma migráció, force push,
└─────────────────────────────────────────┘     külső integráció, stb.
```

### Miért pont ezek a gate-ek?

| Gate | Mikor kell ember | Miért NEM kell ember |
|---|---|---|
| **Sprint Planning** | A scope és a Definition of Done rögzítése előtt | A tesztek megírásához, a kód szerkezetéhez |
| **Sprint Review** | Az increment elfogadása előtt | Az egyes retry ciklusokhoz |
| **Blocked/Escalation** | Ha `max_retries` után sem zöld | Egyetlen sikertelen teszt önmagában |
| **Destructive Action** | Visszafordíthatatlan műveletek | Új fájl az `allowed_paths`-on belül |

---

## A Kernel alkotmánya

A `kernel/system/SYSTEM_CONSTITUTION.md` a rendszer változtathatatlan törvényei:

1. **Kód nem születhet formális spec és work package nélkül.**
2. **Minden változás visszavezethető egy követelmény ID-ra (FR-XXX).**
3. **Az emberi override (L0) mindig elsőbbséget élvez.**
4. **Minden végrehajtás szigorúan event-driven az EventBus-on keresztül.**
5. **Budget vagy hibaszám limit azonnali rendszerleállást és checkpointot vált ki.**
6. **Sprint Planning és Sprint Review emberi jóváhagyást igényel — ezek nem bypass-olhatók.**
7. **Destruktív műveletek mindig explicit, egyedi jóváhagyást igényelnek — sprint-szintű jóváhagyás nem terjed ki rájuk automatikusan.**
8. **A motor kernel-szintű változtatása (prompt, agent, schema) soha nem automatikus — mindig emberi döntés, review és verzióemelés szükséges hozzá.**

---

## Az EventBus és az eseményfolyam

A rendszer komponensei **nem hívják egymást közvetlenül**. Minden kommunikáció az EventBus-on keresztül zajlik.

```
main.py
  │
  └─► SPEC_CREATED event
          │
          ▼
      ArchitectAgent
          │
          └─► WORKPACKAGE_CREATED event
                  │
                  ▼
              SPRINT_PLANNING_PROPOSED event
                  │
                  ▼
          🔒 [ember jóváhagy] ──► SPRINT_PLANNING_APPROVED event
                  │
                  ▼
              DeveloperAgent
                  │
                  └─► DEVELOPMENT_COMPLETED event
                          │
                          ▼
                      TestRunnerAgent
                          │
                          ├─► TESTS_PASSED + coverage OK ──► SPRINT_REVIEW_REQUESTED
                          │                                       │
                          │                                       ▼
                          │                            🔒 [ember jóváhagy] ──► SPRINT_REVIEW_APPROVED
                          │                                       │
                          │                                       ▼
                          │                                 Git commit → RETROSPECTIVE_RECORDED
                          │                                       │
                          │                                       ▼
                          │                              LESSONS_LEARNED_UPDATED ← aggregátor
                          │
                          ├─► TESTS_FAILED (retry < max) ──► retry loop (DeveloperAgent)
                          │
                          └─► TESTS_FAILED (retry == max) ──► PIPELINE_BLOCKED event
                                                                    │
                                                                    ▼
                                                        🔒 [ember dönt] ──► folytatás vagy újratervezés
```

**Eseménytípusok:**

| Esemény | Kiváltó | Fogadó |
|---|---|---|
| `system.initialized` | main.py | — |
| `discovery.completed` | CLI Planner | ArchitectAgent |
| `codebase.surveyed` | DiscoveryAgent | CLI Planner |
| `spec.created` | main.py | ArchitectAgent |
| `workpackage.created` | ArchitectAgent | HITL Gate Manager |
| `sprint.planning.proposed` | HITL Gate Manager | **Ember** |
| `sprint.planning.approved` | Ember | DeveloperAgent |
| `development.completed` | DeveloperAgent | TestRunnerAgent |
| `tests.passed` | TestRunnerAgent | HITL Gate Manager |
| `tests.failed` | TestRunnerAgent | DeveloperAgent (retry) *vagy* Gate Manager |
| `sprint.review.requested` | HITL Gate Manager | **Ember** |
| `sprint.review.approved` | Ember | Git Driver |
| `pipeline.blocked` | HITL Gate Manager | **Ember** (escalation) |
| `action.destructive.requested` | Bármely agent | **Ember** |
| `retrospective.recorded` | Retrospective Collector | ArchitectAgent (köv. sprint) |
| `lessons.learned.updated` | Lessons Aggregator | (log, emberi áttekintésre) |
| `system.error` | Bármely agent | Checkpoint Manager |

---

## A Contract rendszer

### SpecFormal (SPEC_FORMAL.yaml)

A projekt formális leírása. Minden mező validált.

**Szabályok:**
- `id` kötelezően `FR-XXX` formátum
- `priority` csak `HIGH | MEDIUM | LOW`
- `status` alapértelmezetten `PENDING`; meglévő projekt bevonásakor a DiscoveryAgent `SATISFIED`-del is létrehozhat elemeket
- minimum 1 követelmény, minimum 1 tech stack elem

Ez a `requirements` lista a **Product Backlog**. Minden sprint ebből választ ki egy alhalmazt — ez a **Sprint Backlog**.

### DefinitionOfDone (formális contract, nem csak CLI szöveg)

```yaml
work_package_ref: "WP-001"
criteria:
  - id: "DOD-001"
    description: "Minden coverage_mapping teszt lefut és zöld"
    automated_check: true
  - id: "DOD-002"
    description: "Nincs lint hiba (ruff / eslint, stack szerint)"
    automated_check: true
  - id: "DOD-003"
    description: "README vagy API dokumentáció frissítve, ha új endpoint készült"
    automated_check: false     # ember ellenőrzi a Sprint Review-nál
```

Az `automated_check: false` elemek automatikusan a **Sprint Review gate** részévé válnak.

### WorkPackage (WORK_PACKAGE.yaml)

```yaml
id: "WP-001"
sprint_id: "SPRINT-001"
goal: "FastAPI CRUD endpoint-ok implementálása"
allowed_paths:
  - "src/"
  - "tests/"
tasks:
  - task_id: "TASK-001"
    description: "Todo modell és adatbázis séma"
    requirement_ref: "FR-001"
max_execution_time_minutes: 30
tests_required: true
coverage_mapping:
  "FR-001": ["test_create_todo", "test_read_todo"]
```

**Szabályok:**
- `id` kötelezően `WP-XXX` formátum
- `task_id` kötelezően `TASK-XXX` formátum
- `requirement_ref` kötelezően létező `FR-XXX` ID-ra mutat
- `tests_required: true` — tesztek nélkül nincs commit
- `coverage_mapping` — minden `requirements`-ben szereplő FR-XXX-hez legalább egy konkrét, megnevezett teszt kötelező

---

## Az Agent SDK

Minden agent a `BaseAgentSDK`-ból örököl. Új agent hozzáadása:

```python
class MyCustomAgent(BaseAgentSDK):
    def register_subscriptions(self) -> None:
        self.bus.subscribe(EventType.SPEC_CREATED, self.handle_event)

    async def process_event(self, event: Event) -> None:
        await self.emit_event(
            event_type=EventType.WORKPACKAGE_CREATED,
            payload={"result": "..."},
            correlation_id=event.correlation_id
        )
```

**Beépített agentek:**

| Agent | Figyel | Kibocsát | Feladata |
|---|---|---|---|
| `ArchitectAgent` | `SPEC_CREATED` | `WORKPACKAGE_CREATED` | Spec → Work Package |
| `HITLGateManager` | `WORKPACKAGE_CREATED`, `TESTS_PASSED`, `PIPELINE_BLOCKED` | `SPRINT_*_APPROVED` | Emberi jóváhagyási pontok |
| `DeveloperAgent` | `SPRINT_PLANNING_APPROVED`, `TESTS_FAILED` | `DEVELOPMENT_COMPLETED` | Work Package → Kód |
| `TestRunnerAgent` | `DEVELOPMENT_COMPLETED` | `TESTS_PASSED / TESTS_FAILED` | Pytest + coverage mapping + DoD |
| `RetrospectiveCollector` | `SPRINT_REVIEW_APPROVED` | `RETROSPECTIVE_RECORDED`, `LESSONS_LEARNED_UPDATED` | Sprint tanulságok + Lessons Learned |
| `DiscoveryAgent` | *(CLI trigger)* | `CODEBASE_SURVEYED` | Meglévő projekt felmérése |

---

## Sprint Engine — professzionális fejlesztési ciklus

### Sprint Backlog kiválasztás

Az `ArchitectAgent` a `SpecFormal.requirements` listából automatikusan választ ki egy alhalmazt egy adott sprintre:

```python
def select_sprint_backlog(spec: SpecFormal, capacity_minutes: int) -> list[RequirementItem]:
    pending = [r for r in spec.requirements if r.status == "PENDING"]
    pending.sort(key=lambda r: PRIORITY_WEIGHT[r.priority], reverse=True)

    selected, used_capacity = [], 0
    for req in pending:
        estimate = estimate_effort_minutes(req)
        if used_capacity + estimate > capacity_minutes:
            continue
        selected.append(req)
        used_capacity += estimate
    return selected
```

### Sprint Planning gate — az első szükséges emberi döntés

```
╔══════════════════════════════════════════════════════╗
║  SPRINT PLANNING — WP-002 (SPRINT-002)                ║
╚══════════════════════════════════════════════════════╝

Cél: JWT alapú autentikáció implementálása

Ebbe a sprintbe bekerülő követelmények:
  FR-002 [HIGH]   JWT alapú autentikáció
  FR-004 [MEDIUM] Jelszó reset endpoint

Becsült idő: ~45 perc autonóm munka
Definition of Done: DOD-001, DOD-002, DOD-003
Érintett elérési utak: src/auth/, tests/auth/

[j] Jóváhagyom, indulhat        [m] Módosítom a scope-ot
[n] Elutasítom, vissza a backlogba
> _
```

### Az autonóm végrehajtási ablak

```
[SPRINT-002] Fejlesztés indul...
[SPRINT-002] Kód generálva (src/auth/jwt_handler.py, src/auth/routes.py)
[SPRINT-002] Tesztek futnak... 3/5 PASSED, 2 FAILED
[SPRINT-002] Retry 1/3 — hibajavítás a test_expired_token alapján...
[SPRINT-002] Tesztek futnak... 5/5 PASSED
[SPRINT-002] Coverage mapping ellenőrzés... FR-002 ✓  FR-004 ✓
[SPRINT-002] Definition of Done automatikus elemei... DOD-001 ✓  DOD-002 ✓
[SPRINT-002] DOD-003 manuális ellenőrzést igényel → Sprint Review-ra vár
```

### Blocked / Escalation

```
╔══════════════════════════════════════════════════════╗
║  ⚠ BLOCKED — WP-002 (SPRINT-002)                      ║
╚══════════════════════════════════════════════════════╝

3/3 retry elfogyott. Utolsó hiba:
  test_expired_token: AssertionError

[r] Újrapróbálom módosított instrukcióval
[e] Szerkesztem a WorkPackage-et / követelményt
[s] Sprint felfüggesztése, később folytatom
> _
```

### Sprint Review gate

```
╔══════════════════════════════════════════════════════╗
║  SPRINT REVIEW — WP-002 (SPRINT-002)                  ║
╚══════════════════════════════════════════════════════╝

✓ Automatikus DoD kritériumok: 2/2 teljesítve
⚠ Manuális DoD kritérium: DOD-003 (README frissítve?)
   → src/auth/README.md diff megtekintése: [d]

[j] Elfogadom, commit-olhat        [d] Diff megtekintése
[n] Elutasítom, vissza fejlesztésre
> _
```

### Retrospective — projekt-szintű tanulás

Minden `SPRINT_REVIEW_APPROVED` után a `RetrospectiveCollector` rögzít egy strukturált tanulságot a **projekt saját `.ai-sd-os/retrospectives/`** könyvtárába:

```yaml
sprint_id: "SPRINT-002"
what_worked: "JWT implementáció első nekifutásra jó struktúrát kapott"
what_failed: "Token lejárati idő tesztje 1 retry-t igényelt — a spec nem volt elég explicit az időzónáról"
carry_forward_note: "Jövőbeli időalapú követelményeknél kérj explicit időzóna specifikációt"
retry_count: 1
duration_minutes: 12
```

A `carry_forward_note` bekerül a **következő sprint** promptjának kontextusába.

---

## A kétszintű tanulási modell

Ez az egyik legfontosabb tervezési döntés. A két szintet soha nem szabad összekeverni.

### A) Projekt-szintű tanulás — automatikus, biztonságos

A Retrospective mechanizmus pontosan ezt csinálja: egyetlen projekten belül, sprintről sprintre okosabb lesz a kontextus. A `carry_forward_note` bekerül a következő sprint `ArchitectAgent` és `DeveloperAgent` promptjának kontextusába. Automatikus és kockázatmentes — a hatóköre egyetlen projektre korlátozódik.

### B) Motor-szintű Lessons Learned — aggregált, emberi döntéssel

Ezt az **Alkotmány 8. törvénye** szabályozza: a kernel-szintű változtatás soha nem automatikus.

A `RetrospectiveCollector` minden sprintzáráskor frissít egy **motor-szintű aggregált naplót** is:

```
lessons/
└── lessons_learned.yaml      ← motor oldali, git-ben verziókezelt
```

```yaml
# lessons/lessons_learned.yaml
entries:
  - pattern: "Időzóna-kezelésű követelmények"
    occurrences: 3
    projects:
      - "webarchivum / SPRINT-003"
    suggested_action: "Frissíteni a discovery fázis CLI kérdéseit"
    status: "PENDING_HUMAN_REVIEW"
```

A folyamat:

```
Projekt retrospective-ok (sok projektből)
        │
        ▼
Aggregált lessons_learned.yaml  ← automatikusan gyűlik, NEM módosítja a kernelt
        │
        ▼
    Ember átnézi (pl. havonta)
        │
        ▼
    Ember dönt: érdemes-e ez alapján módosítani egy promptot,
    egy contract sémát, vagy magát a kernelt?
        │
        ▼
    Normál szoftverfejlesztési ciklus a motoron:
    commit → verzióemelés → changelog
```

**A `suggested_action` mező csak javasol — soha nem hajt végre semmit.**

---

## Discovery Mode — meglévő projekt bevonása

A motor a cwd-t vizsgálja. Ha egy könyvtárban nincs `.ai-sd-os/`, de van kód, a wizard felajánlja a felmérést:

```
[2] Felmér em a meglévő kódot, és onnan folytatom
> 2

[DISCOVERY] /srv/projekts/webarchivum felmérése...
[DISCOVERY] Git történet: 214 commit, utolsó: 2024-11-03
[DISCOVERY] Detektált stack: Python 3.11, Flask, SQLite
[DISCOVERY] Meglévő tesztek: tests/ alatt 12 fájl, 41 teszt függvény
[DISCOVERY] README.md található
[DISCOVERY] ⚠ Nincs .env.example, de van hardcode-olt kulcsnak tűnő string 2 helyen
[DISCOVERY] ⚠ Nincs CI konfiguráció, nincs Dockerfile

→ .ai-sd-os/ létrehozva
→ CODEBASE_SNAPSHOT.yaml generálva
```

A `CODEBASE_SNAPSHOT.yaml` bővített mezői:

```yaml
# .ai-sd-os/CODEBASE_SNAPSHOT.yaml
project_path: "/srv/projekts/webarchivum"
stack:
  languages: ["python"]
  frameworks: ["flask"]
  databases: ["sqlite"]
architecture: "monolith"           # monolith | microservices | serverless
dependencies:
  count: 18
  outdated: 3
  has_lockfile: true
security:
  risk_flags:
    - "Possible hardcoded secret in config.py:14"
  secret_scan_status: "FLAGGED"
technical_debt:
  missing_tests: ["src/admin.py"]
  no_type_hints: true
test_quality:
  existing_tests_count: 41
  structural_only: false
deployment:
  has_dockerfile: false
  has_ci_config: false
```

**Fontos, amit a felmérés nem tesz meg:** nem generál automatikusan `SATISFIED` státuszú FR-eket — csak javaslatot (`inferred_requirements`), amit a következő lépésben az ember hagy jóvá.

### A felmérésre épülő planning kérdések

```
╔══════════════════════════════════════════════════════╗
║  AI-SD-OS — Meglévő projekt: webarchivum              ║
╚══════════════════════════════════════════════════════╝

A felmérés alapján ezt találtam:
  ✓ Weblap archiválás URL alapján (magas megbízhatóság)
  ? Felhasználói autentikáció (alacsony megbízhatóság)

[1/5] Jól látom a „weblap archiválás" funkciót?
      > Kész, de lassú nagy oldalaknál — nem prioritás most

[2/5] Az „autentikáció" — tényleg hiányzik?
      > Igen, ez lenne a következő cél

[3/5] Van más, amit tudnom kell?
      > Igen, van egy régi admin felület, amit ki kell vezetni

[4/5] A 2 gyanús hardcode-olt secret — kezeljük most?
      > Igen, ez blocker

[5/5] Definition of Done?
      > Auth működik, secretek env-be, admin felület törölve

══════════════════════════════════════════════════════
✓ .ai-sd-os/ konfigurálva
✓ SPEC_FORMAL.yaml frissítve (FR-001 SATISFIED, FR-002-004 PENDING)
```

---

## Teszt-integritás — strukturális vs. szemantikus validáció

**Ez a rendszer egyik legkritikusabb pontja.**

### 1. Strukturális teszt (gyenge, önmagában nem elég)

Csak azt bizonyítja, hogy egy fájl létezik. Üres vagy hibás `app.py` is átmenne ezen.

### 2. Szemantikus teszt (kötelező, a valódi mérce)

Ez ténylegesen a `FR-001` viselkedését ellenőrzi — nem a fájl létét, hanem a funkció működését.

### A validációs lánc, ami ezt kikényszeríti

```
1. Pytest futtatás           → exit_code == 0 ?
2. Coverage mapping ellenőrzés → minden FR-XXX-hez van-e legalább
                                   egy, a coverage_mapping-ben
                                   megnevezett teszt, AMI TÉNYLEG
                                   LÉTEZIK ÉS LEFUTOTT?
```

Ha a `coverage_mapping` hiányos, vagy a benne megnevezett tesztek nem futottak le — a sprint **`TESTS_FAILED`**-del zár, **függetlenül attól, hogy a pytest exit code 0 volt**.

---

## AI Provider konfiguráció

A `BaseProviderAdapter` **képesség-alapú interfészt** definiál — nem modell neve az alapja, hanem mit tud csinálni:

```python
class AIProvider(ABC):
    async def generate(self, prompt: str, context: dict) -> str: ...
    async def review(self, code: str, criteria: list) -> ReviewResult: ...
    async def embed(self, text: str) -> list[float]: ...
    async def analyze(self, artifact: str) -> AnalysisResult: ...
```

Az agentek mindig `AIProvider`-t kapnak — nem `ClaudeAdapter`-t, nem `OpenAIAdapter`-t. Modellcsere egyetlen helyen történik, az összes agent érintetlen marad.

```python
# Anthropic Claude (ajánlott)
from sdk.provider_adapter import AnthropicAdapter
provider = AnthropicAdapter(api_key="sk-ant-...")

# OpenAI-kompatibilis
from sdk.provider_adapter import OpenAIAdapter
provider = OpenAIAdapter(api_key="sk-...", model="gpt-4o")

# Mock (teszteléshez, API kulcs nélkül)
from sdk.provider_adapter import MockProviderAdapter
provider = MockProviderAdapter()
```

`.env` fájlban:
```
ANTHROPIC_API_KEY=sk-ant-...
AI_MODEL=claude-sonnet-4-6
MAX_RETRIES=3
```

---

## CLI parancsok

> **Fontos:** a parancsokat az **`agy` termináljából** futtatod, Linux rendszeren. A motor a **cwd-ből** detektálja a projektet.

```bash
# Projekt könyvtárába lépés, majd motor indítása
cd /srv/projekts/webarchivum
python /srv/projekts/ai-sd-os/main.py

# Az összes detektált projekt listázása
python /srv/projekts/ai-sd-os/main.py list

# Egy projekt állapotának lekérdezése (cwd-ből)
python /srv/projekts/ai-sd-os/main.py status

# Mock módban (teszteléshez)
python /srv/projekts/ai-sd-os/main.py --mock
```

**Nincs `resume <project-id>` parancs** — mivel az állapot a projekt könyvtárában van, elég `cd` a projektbe és `python main.py`.

---

## Git integráció

Minden projekt **saját, önálló git repóval** rendelkezik. Meglévő projektnél a motor munka branch-et hoz létre (`ai-sd-os/sprint-NNN`). Minden sikeres sprint automatikusan commit-ol a projekt saját repójában:

```
feat(SPRINT-001): FastAPI CRUD endpoint-ok implementálása

Requirements: FR-001, FR-002
WorkPackage: WP-001
Tests: PASSED (12/12)
Agent: developer-01
```

A motor emellett automatikusan frissíti a projekt két dokumentumát is:

- **`CHANGELOG.md`** — minden sprint után a változások és a lefedett FR-ek rögzítése
- **`ARCHITECTURE_DECISIONS.md`** — ha az `ArchitectAgent` döntést rögzít a `.ai-sd-os/memory/decisions.yaml`-ban, az ADR formátumban átkerül ide is

---

## Telepítés

### Előfeltételek
- Linux rendszer
- **Antigravity CLI (`agy`)**
- Python 3.12+, Docker, Git

### Telepítés

```bash
git clone https://github.com/yourorg/ai-sd-os.git /srv/projekts/ai-sd-os
cd /srv/projekts/ai-sd-os
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# → .env szerkesztése: ANTHROPIC_API_KEY beállítása
```

### Futtatás (cwd-alapú)

```bash
# Minden munkát a PROJEKT könyvtárából indítasz:
cd /srv/projekts/webarchivum
python /srv/projekts/ai-sd-os/main.py
# → Ha van .ai-sd-os/: folytatja
# → Ha nincs: wizard indul (új projekt vagy felmérés)

# Projektek listázása (szülőkönyvtár alapján)
python /srv/projekts/ai-sd-os/main.py list

# Állapot lekérdezése (cwd-ből)
python /srv/projekts/ai-sd-os/main.py status

# Mock módban (teszteléshez, API kulcs nélkül)
python /srv/projekts/ai-sd-os/main.py --mock
```

Nincs `resume <project-id>` parancs — mivel az állapot a projekt könyvtárában van, elég `cd` a projektbe és `python main.py`.

### Tesztek futtatása

```bash
# Összes teszt
pytest tests/

# Csak unit tesztek
pytest tests/test_kernel.py tests/test_contracts.py

# Teljes E2E golden path
pytest tests/test_golden_path.py -v
```

---

## Függőségek (requirements.txt)

```
pydantic>=2.0
pyyaml>=6.0
anthropic>=0.25.0
docker>=7.0.0
gitpython>=3.1.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
python-dotenv>=1.0.0
asyncio>=3.4.3
```

---

## Terjesztési útvonal (Roadmap)

### Phase 1 — Kernel MVP ✅ (jelen verzió)
- Event-driven kernel (asyncio, typed event model, correlation_id, event history)
- Contract validáció (SpecFormal + WorkPackage + DefinitionOfDone + CodebaseSnapshot)
- Architect + Developer + TestRunner + HITLGateManager + RetrospectiveCollector + DiscoveryAgent
- CLI planning fázis (üres lapról **és** meglévő kódbázisra építve)
- Docker sandbox
- **Directory-native állapot** — `.ai-sd-os/` a projekt könyvtárában, nincs central registry
- **cwd-alapú projekt detektálás** — `cd <projekt>`, `python main.py`, semmi más
- **Coverage mapping validáció** — minden FR-XXX-hez kötelező, ténylegesen lefutott teszt
- **Sprint Engine** — Sprint Backlog kiválasztás, Sprint Planning / Review gate-ek, retry loop, Blocked/Escalation, Destructive Action gate, Retrospective
- **Discovery Mode** — meglévő projekt felmérése, bővített CODEBASE_SNAPSHOT (stack, architecture, security, technical_debt, test_quality, deployment)
- **Kétszintű tanulás** — projekt Retrospective + motor Lessons Learned (emberi döntéssel)
- Checkpoint rendszer (`.ai-sd-os/` alatt)
- State Machine strukturált bontás (`states.py`, `transitions.py`, `validators.py`)
- `security/` modul alapjai (secret_scanner, permission_manager, sandbox_policy)

### Phase 1.5 — Stabilizálás

> Akkor kezdődik, amikor az MVP-t már valós projekten futtattuk. Nem új funkció — a meglévő rendszer belső minőségének emelése.

- **Policy Engine** (`kernel/policy/`) — a `SYSTEM_CONSTITUTION.md` szabályai gépileg kikényszeríthető YAML formátumba kerülnek (`rules.yaml`, `security.yaml`, `execution.yaml`). A Constitution marad az egyetlen igazságforrás, a YAML a kódba kompilált érvényesítés.
- **Project Memory** (`.ai-sd-os/memory/`) — `decisions.yaml`, `architecture.yaml`, `known_issues.yaml`; a projekt strukturált „agya"
- **AIProvider képesség-alapú interfész** véglegesítése — `.generate()`, `.review()`, `.embed()`, `.analyze()`; modellcsere egyetlen helyen
- **Artifact Registry bővítés** — forrás, teszt, dokumentáció, döntés mind artifact; `id`, `type`, `version`, `requirement_ref`, `checksum` mezőkkel
- **CHANGELOG.md + ARCHITECTURE_DECISIONS.md** automatikus frissítése sprintenként

### Phase 2 — Minőségi mélység
- **ReviewerAgent** — nem azt nézi, *van-e* teszt egy FR-hez, hanem hogy a teszt *ténylegesen bizonyítja-e* a követelményt (pl. jelszóváltásnál: régi jelszóval nem lehet belépni; nem elég a 200 OK)
- **SecurityAgent** — secret leak, CVE ellenőrzés, jogosultság-audit, OWASP problémák
- **MCP Tool Layer** (`tools/mcp/`) — szabványos eszközkapcsolat: filesystem, git, GitHub, browser, postgres, Docker; az agentek nem ismerik az eszközök részleteit, csak a Tool interfészt hívják
- Effort-becslés finomítása korábbi sprintek tényadatai alapján
- Budget controller (token használat limitálása projektenként és globálisan)
- **Lessons Learned dashboard** — aggregált minták vizualizálása emberi áttekintéshez

> **Megjegyzés az OrchestratorAgent ötletről:** több forrás javasolta egy explicit OrchestratorAgent bevezetését. Phase 1-2-ben ez redundáns — az EventBus + HITLGateManager már ellátja az orchestrációt. Ha a rendszer valódi multi-agent párhuzamosságot igényel (több DeveloperAgent egyszerre, különböző sprint-eken), Phase 3-ban érdemes elővenni.

### Phase 3 — Platform
- Semantic replay (sikeres minták újrafelhasználása)
- Project DNA (projekt „génkészlet" mentése és betöltése)
- Multi-projekt portfolio dashboard (cost, velocity, state, errors egyszerre)
- **DevOpsAgent** — Docker, CI/CD, cloud deployment konfiguráció
- Observability dashboard (token cost, sprint velocity, retry count, agent teljesítmény)

---

## A rendszer törvényei (röviden)

```
1. Kód csak validált spec után születhet.
2. Minden sor visszavezethető egy FR-XXX ID-ra.
3. Az ember mindig felülírhat mindent (L0 override).
4. Minden kommunikáció EventBus-on keresztül zajlik.
5. Hiba esetén: checkpoint → leáll → vár.
6. A kernel megváltoztatása soha nem automatikus — mindig emberi döntés.
7. Az agent soha nem kap korlátlan jogosultságot.
```

---

## Közreműködés

Ez a rendszer maga is AI-SD-OS-sel fejleszthető (self-hosting). Ha új agentet, promptot vagy adaptert szeretnél hozzáadni:

1. Hozz létre egy üres könyvtárat a fejlesztéshez, lépj bele, indítsd a motort
2. A wizard végigvezet: spec → sprint → kód
3. A generált bővítményt átnézés és tesztelés után te olvasztod be a motorba

A kernel megváltoztatása — még ha AI-SD-OS segítségével is történik — mindig emberi jóváhagyással, review-val és changelog bejegyzéssel jár.

---

## Licenc

MIT License — szabad felhasználás, módosítás, terjesztés.

---

*AI-SD-OS V5 — Directory-Native. Human-in-the-Loop. Policy-Driven. Build Phase Active.*
