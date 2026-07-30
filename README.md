# AI-SD-OS V6.1.0 — Enterprise Software Factory Operating System

**Master Architecture Specification & Reference Documentation**

> "Clone it. Answer the questions. Ship the enterprise project."

## Tartalomjegyzék

1. [Rendszer Áttekintés és Alapelvek](#1-rendszer-áttekintés-és-alapelvek)
2. [Hogyan Működik? (Quick Start)](#2-hogyan-működik-quick-start)
3. [Motor vs. Projekt Architektúra](#3-motor-vs-projekt-architektúra)
4. [Teljes Könyvtárszerkezet (ai-sd-os/)](#4-teljes-könyvtárszerkezet-ai-sd-os)
5. [A Rendszer Alkotmánya](#5-a-rendszer-alkotmánya-kernelsystemsystem_constitutionmd)
6. [Formális Matematikai és Garanciális Modell](#6-formális-matematikai-és-garanciális-modell)
7. [Az Állapotgép (State Machine) és a HITL Kapuk](#7-az-állapotgép-state-machine-és-a-hitl-kapuk)
8. [Formális Szoftverszerződések és Sémák](#8-formális-szoftverszerződések-és-sémák)
9. [Discovery Mode — a "README-First" Megközelítés](#9-discovery-mode--a-readme-first-megközelítés)
10. [Kétszintű Tanulási Modell](#10-kétszintű-tanulási-modell)
11. [Telepítés és Használat](#11-telepítés-és-használat)
12. [Függőségek (requirements.txt)](#12-függőségek-requirementstxt)
13. [Licenc](#13-licenc)

> **Architektúra blueprint külön fájlban:** a V6.1.0 tervezéskori referencia-forráskódja (a `contracts/`, `kernel/`, `sdk/`, `agents/`, `runtime/` modulok teljes kódmelléklete) már nem ennek a README-nek a része — az egy külön tervezési dokumentum, nem felhasználói leírás. Lásd: [`docs/ARCHITECTURE_BLUEPRINT_V6.1.0.md`](docs/ARCHITECTURE_BLUEPRINT_V6.1.0.md). Az a fájl a repóban ténylegesen megvalósított kódtól több ponton eltér (más osztálynevek, más állapotkezelés) — ezt a blueprint dokumentum végén egy auditálási megjegyzés tisztázza.

---

## 1. Rendszer Áttekintés és Alapelvek

Az AI-SD-OS (AI Software Development Operating System) egy letölthető, eseményvezérelt, formálisan verifikálható fejlesztési keretrendszer és szoftvergyár. Bármilyen szoftverprojektet képes végigvezetni a nyers üzleti ötlettől a kész, tesztelt és auditálható kódbázisig — szigorúan szabályozott emberi jóváhagyási pontok (Human-in-the-Loop Gates) mellett.

Nem egy konkrét projekt, és nem egy statikus sablon. Hanem egy projekt-generátor motor: egy fix, stabil kernel, amely körül az ágensek, promptok, szoftverszerződések és sprintek automatikusan hajtják a fejlesztési folyamatot.

A rendszer stack-agnosztikus: Python, TypeScript, Go, Rust, Java, C#, PHP vagy bármilyen más technológia feletti projektekhez egyaránt használható.

### Kritikus Tervezési Alapelvek

- **Motor vs. Projekt Elválasztás (Git Izoláció):** A motor (`ai-sd-os/`) és a generált projektek soha nem élnek ugyanabban a Git repóban. A motort egyszer klónozod, a projekteket független testvérkönyvtárakként kezeled.
- **Directory-Native Állapot (`.ai-sd-os/`):** Nincs központi adatbázis vagy `registry.json`. A projekt teljes állapota, memóriája és audit-naplója a projekt saját könyvtárában, a `.ai-sd-os/` mappában él.
- **Contract-First & Event-Driven Architecture:** A komponensek nem hívják egymást közvetlenül. Minden kommunikáció a szigorúan típusos EventBus-on és Pydantic sémákon keresztül zajlik.
- **Formális Garanciák:** Kriptográfiai eseménynapló (Ledger), kétirányú nyomonkövethetőség (Traceability), AST-szintű párhuzamos ágens-zárolás (Swarm Protocol) és automatikus architektúra-eltérés érzékelés (Drift Detection).
- **Fejlesztési Környezet:** A rendszer az Antigravity CLI (`agy`) alatt fut, Linux környezetben. A motor a munkakönyvtárból (cwd) automatikusan detektálja az állapotot.

## 2. Hogyan Működik? (Quick Start)

```bash
# 1. A motort egyszer klónozod egy központi helyre — ez a "gyár", nem a "termék"
git clone https://github.com/yourorg/ai-sd-os.git /srv/projekts/ai-sd-os
cd /srv/projekts/ai-sd-os
pip install -r requirements.txt

# 2. Minden projektmunkát a PROJEKT saját könyvtárából indítasz
cd /srv/projekts/webarchivum
python /srv/projekts/ai-sd-os/main.py
```

A `main.py` megvizsgálja az aktuális munkakönyvtárat (cwd):

- Van `.ai-sd-os/` mappa? → Folytatja a fejlesztést a mentett állapotgép státusztól.
- Nincs `.ai-sd-os/` mappa? → Elindítja az interaktív varázslót (Új projekt tervezése vagy meglévő kód felmérése).

```text
╔══════════════════════════════════════════════════╗
║  AI-SD-OS V6.1.0 — Mi a helyzet?                 ║
╚══════════════════════════════════════════════════╝

Ebben a könyvtárban (/srv/projekts/webarchivum)
még nincs AI-SD-OS projekt.

[1] Új projektet indítok (üres lapról, tervezési kérdések)
[2] Felmérem a meglévő kódot, és onnan folytatom
> _
```

Nincs `new` / `adopt` alparancs — a motor a cwd-ből ért mindent, pont ahogy a git, a terraform, vagy az npm is teszi.

## 3. Motor vs. Projekt Architektúra

| Tulajdonság  | A Motor (`ai-sd-os/`)                  | A Projekt (`<projekt-neve>/`)             |
|--------------|-----------------------------------------|--------------------------------------------|
| Szerep       | Kernel, ágensek, sémák, promptok        | Konkrét szoftvertermék és forráskód         |
| Útvonal      | `/srv/projekts/ai-sd-os/`               | `/srv/projekts/webarchivum/`                |
| Git Repó     | A motor saját fejlesztési története     | A termék saját, tiszta commit története     |
| Verziózás    | Motor kiadások (v6.0.0, v6.1.0)         | Sprint tagek (SPRINT-001, SPRINT-002)       |
| Állapot      | Állapotmentes (Stateless)                | `.ai-sd-os/` mappa a munkakönyvtárban       |
| Példányszám  | Egyetlen központi klón                   | Tetszőleges számú párhuzamos projekt        |

### Workspace Gyökér és Testvérkönyvtárak

```text
/srv/projekts/
├── ai-sd-os/              ← A motor saját Git repója (egyszer klónozod)
├── webarchivum/           ← Projekt A (saját Git repó, saját .ai-sd-os/)
├── todo-app-a1b2c3/       ← Projekt B (saját Git repó, saját .ai-sd-os/)
└── crm-backend-d4e5f6/    ← Projekt C (saját Git repó, saját .ai-sd-os/)
```

### A Directory-Native Állapot (`.ai-sd-os/`)

```text
/srv/projekts/webarchivum/
├── README.md                   # Elsődleges információforrás
└── .ai-sd-os/
    ├── state.json              # Állapotgép státusza és engine metaadatok
    ├── SPEC_FORMAL.yaml         # Formális specifikáció (Product Backlog)
    ├── CODEBASE_SNAPSHOT.yaml   # Meglévő kódbázis felmérésének eredménye
    ├── ledger/                  # Kriptográfiai esemény-blokklánc
    │   └── chain.json
    ├── checkpoints/             # Mentési pontok (state snapshots)
    │   ├── checkpoint_SPEC_20260730_143025.json
    │   └── checkpoint_DEVELOPMENT_20260730_143041.json
    ├── retrospectives/          # Sprint tanulságok
    │   ├── SPRINT-001.yaml
    │   └── SPRINT-002.yaml
    └── memory/                  # Projekt strukturált memóriája
        ├── decisions.yaml       # ADR-ek (Decision Freeze engedélyezve)
        ├── architecture.yaml    # Detektált és tervezett struktúra
        └── known_issues.yaml    # Technikai adósságok és ismert hibák
```

## 4. Teljes Könyvtárszerkezet (`ai-sd-os/`)

```text
ai-sd-os/                               ← A motor könyvtára
├── kernel/
│   ├── system/
│   │   ├── config.py                   # KernelConfig: budget, retries, checkpoint
│   │   └── SYSTEM_CONSTITUTION.md      # A rendszer 8 megszeghetetlen törvénye
│   ├── event_bus/
│   │   ├── events.py                   # Typed Events (EventType enum, Event envelope)
│   │   └── bus.py                      # Aszinkron EventBus hibaizolációval és drainnel
│   ├── state/
│   │   ├── states.py                   # StateEnum (INIT -> DISCOVERY -> SPEC -> ...)
│   │   ├── transitions.py              # ALLOWED_TRANSITIONS mátrix
│   │   └── validators.py               # Állapotváltás-validátorok
│   ├── ledger/                         # Kriptográfiai Audit Réteg
│   │   ├── ledger_chain.py             # Kriptográfiai SHA-256 Hash Chain
│   │   └── replay_engine.py            # Szemantikai Replay Engine (AST/Teszt ekvivalencia)
│   ├── policy/
│   │   ├── policy_compiler.py          # Corporate & Compliance szabályfordító
│   │   ├── rules.yaml                  # Végrehajtási szabályok
│   │   ├── security.yaml               # Secret scan & sandbox szabályok
│   │   └── execution.yaml              # Budget, timeout és retry szabályok
│   ├── hitl/
│   │   ├── gate_manager.py             # SPRINT_PLANNING, REVIEW, BLOCKED kapuk
│   │   └── cli_prompts.py              # Interaktív CLI felületek
│   ├── swarm/                          # Párhuzamos Végrehajtási Modul
│   │   ├── orchestrator.py             # Swarm Orchestration Engine
│   │   ├── ast_locker.py               # AST Namespace Locking Engine
│   │   └── merge_agent.py              # 3-Lépcsős Konfliktus-feloldó (Lexikális/AST/LLM)
│   ├── contracts/
│   │   ├── validator.py                # Pydantic validáció
│   │   └── serializer.py               # YAML be- és kimenet kezelés
│   ├── economics/                      # Erőforrás & Értékkezelő Modul
│   │   ├── budget_controller.py        # Token/USD figyelés és Dynamic Economy Mode
│   │   └── value_evaluator.py          # Strategic Evaluation Engine (ROI Index)
│   └── checkpoint/
│       └── checkpoint_manager.py       # Állapot mentés és visszaállítás
│
├── contracts/                          # Formális Szoftverszerződések
│   ├── events/                         # Event Schema Registry
│   │   ├── base_event.py
│   │   ├── spec_events.py
│   │   ├── sprint_events.py
│   │   └── gate_events.py
│   ├── spec_formal.py                  # SPEC_FORMAL: FR-XXX követelmények
│   ├── work_package.py                 # WORK_PACKAGE: taskok, coverage_mapping
│   ├── definition_of_done.py           # DOD kritériumok (Automated & Manual)
│   ├── codebase_snapshot.py            # Meglévő projektek felmérése
│   └── traceability_matrix.py          # Kód-to-Business nyomonkövetési mátrix
│
├── versions/                           # Séma-verziók visszamenőleges kompatibilitáshoz
│   ├── v5_schemas/
│   └── v6_schemas/
│
├── sdk/
│   ├── models.py                       # AgentContext, ExecutionResult, AgentStatusCode
│   ├── provider_adapter.py             # Provider-független interfész (Claude, OpenAI, Ollama)
│   └── base_agent.py                   # BaseAgentSDK — minden ágens ősosztálya
│
├── capabilities/                       # Képesség-absztrakciós Réteg
│   └── CAPABILITY_REGISTRY.yaml        # Provider-független képességek regisztere
│
├── agents/
│   ├── core/                           # Beépített törzságensek
│   │   ├── architect_agent.py          # SPEC -> WORK_PACKAGE
│   │   ├── developer_agent.py          # WORK_PACKAGE -> Forráskód
│   │   ├── discovery_agent.py          # README-First & Codebase Survey
│   │   ├── drift_detector_agent.py     # Static AST vs Architecture Drift Detector
│   │   └── retrospective_collector.py  # Sprint tanulságok gyűjtője
│   └── plugins/                        # Technológia-specifikus ágensek (FastAPI, React)
│       ├── fastapi_agent.py
│       └── wordpress_agent.py
│
├── runtime/
│   ├── artifacts.py                    # ArtifactRegistry (checksum, req_ref)
│   ├── sandbox.py                      # DockerSandbox (subprocess fallback-el)
│   ├── test_runner.py                  # Pytest + coverage mapping ellenőrzés
│   └── git_driver.py                   # Git init, feature branch, commit, PR
│
├── planning/
│   └── cli_planner.py                  # CLI kérdések -> SpecFormal
│
├── compliance/                         # Vállalati Megfelelőségi Profilok
│   └── profiles/                       # GDPR.yaml, ISO27001.yaml, NIS2.yaml
│
├── genome/                             # Szervezeti Szintű Tudástár
│   └── ORGANIZATION_GENOME.yaml        # Bevált minták és tiltott anti-patternök
│
├── workspace/
│   └── project_detector.py             # Cwd-alapú projekt felismerő
│
├── lessons/
│   └── aggregator.py                   # Motor-szintű Lessons Learned aggregátor
│
├── security/
│   ├── secret_scanner.py               # Hardcode-olt secret detektálás
│   ├── permission_manager.py           # Ágens jogosultságkezelő
│   └── sandbox_policy.py               # Futtatási sandbox szabályok
│
├── tests/                              # Motor saját tesztkészlete
│   ├── test_kernel.py
│   ├── test_contracts.py
│   ├── test_coverage_mapping.py
│   ├── test_hitl_gates.py
│   └── test_golden_path.py
│
├── CHANGELOG.md                        # A motor saját kiadásainak naplója
├── CONTRIBUTING.md                     # Szabályok a motor módosításához
├── MIGRATION.md                        # Útmutató sémafrissítésekhez
├── main.py                             # Belépési pont
├── requirements.txt
└── README.md
```

## 5. A Rendszer Alkotmánya (`kernel/system/SYSTEM_CONSTITUTION.md`)

```markdown
# AI-SD-OS SYSTEM CONSTITUTION

1. INVARIANT_SPEC_FIRST: Kód nem születhet formális specifikáció (SPEC_FORMAL.yaml) és munkacsomag (WORK_PACKAGE.yaml) nélkül.
2. INVARIANT_TRACEABILITY: Minden forráskód-módosításnak (Commit) és tesztnek közvetlenül visszavezethetőnek kell lennie legalább egy követelmény azonosítóra (FR-XXX).
3. INVARIANT_HUMAN_OVERRIDE: Az emberi override (L0) mindig, minden körülmények között elsőbbséget élvez.
4. INVARIANT_EVENT_DRIVEN: Minden végrehajtás szigorúan aszinkron eseményvezérelt az EventBus-on keresztül.
5. INVARIANT_BUDGET_SAFETY: Budget- vagy hibaszám-limit túllépése esetén a rendszer azonnal leáll és checkpointot hoz létre.
6. INVARIANT_HITL_GATES: A Sprint Planning és Sprint Review kapuk emberi jóváhagyása nem bypass-olható.
7. INVARIANT_DESTRUCTIVE_SAFETY: Destruktív műveletek (fájltörlés az allowed_paths-on kívül, adatbázis-droppolás, force push) mindig explicit, egyedi jóváhagyást igényelnek.
8. INVARIANT_KERNEL_IMMUTABILITY: A motor kernel-szintű változtatása (prompt, agent, schema) soha nem automatikus — az mindig külön emberi review-t és verzióemelést igényel.
```

## 6. Formális Matematikai és Garanciális Modell

### 6.1 Kriptográfiai Execution Ledger (L2.1)

Minden esemény (`E_k`) hash-láncolatot képez a `.ai-sd-os/ledger/chain.json` fájlban:

```text
H_k = SHA256(H_(k-1) ∥ Timestamp_k ∥ AgentID_k ∥ Action_k ∥ PayloadHash_k)
```

### 6.2 Stratégiai Értékszámítás (L1.5)

A projekt elindítása előtti elutasítási kapu (`V_strategic < 15.0 ⟹ CANCEL`):

```text
V_strategic = (B_value × R_expected) / (C_maint × T_risk)
```

### 6.3 Kontextus Relevancia Pontozás (Context Compiler)

A kontextus-robbanás elkerülésére a `memory/` adatbázisból csak a legmagasabb `R_i` pontszámú elemek kerülnek be az ágens kontextusába:

```text
R_i = (w1 × S_tag) + (w2 × score_success) − (w3 × Δt)
```

### 6.4 Szemantikai Replay Ekvivalencia (Recovery)

A visszajátszás akkor sikeres (`E_semantic = TRUE`), ha az újragenerált kód AST-ben megegyezik az eredetivel, vagy átmegy a verifikációs teszteken:

```text
E_semantic = (AST(C_replay) ≡ AST(C_original)) ∨ (Tests(C_replay) = PASS)
```

## 7. Az Állapotgép (State Machine) és a HITL Kapuk

```text
INIT
  │
  ▼
DISCOVERY            ← README.md olvasás + CLI kérdések (+ meglévő projektnél: kódbázis felmérés)
  │
  ▼
SPEC                 ← SPEC_FORMAL.yaml generálva és validálva
  │
  ▼
WORK_PACKAGE         ← Sprint Backlog kiválasztva (prioritás + kapacitás alapján)
  │
  ▼
┌─────────────────────────────────────────┐
│ 🔒 SPRINT_PLANNING  — HUMAN GATE         │  ← "Ezt a scope-ot, ennyi taszkkal,
│    (jóváhagyás szükséges)                │     ezzel a Definition of Done-nal indítsam?"
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  AUTONÓM VÉGREHAJTÁSI ABLAK              │  ← Ember NEM avatkozik bele,
│  DEVELOPMENT ⇄ TEST (retry loop)         │     amíg a sprint fut.
│  max_retries-ig önállóan fut             │
└─────────────────────────────────────────┘
  │                              │
  │ retry kimerült                │ tesztek + coverage mapping zöld
  ▼                              ▼
┌─────────────────┐    ┌─────────────────────────────────────────┐
│ 🔒 BLOCKED        │    │ 🔒 SPRINT_REVIEW  — HUMAN GATE            │
│  (escalation,     │    │    (jóváhagyás szükséges)                 │
│   human dönt)     │    │    "Ez az increment elfogadható?"         │
└─────────────────┘    └─────────────────────────────────────────┘
  │                              │
  │ human döntés után             │ elfogadva
  ▼                              ▼
DEVELOPMENT / WORK_PACKAGE   PR_CREATED   ← Git commit + branch
  (újratervezés)                │
                                 ▼
                          RETROSPECTIVE   ← Sprint tanulságok (.ai-sd-os/retrospectives/)
                                 │
                                 ▼
                    ┌──── van még Sprint Backlog elem? ────┐
                    │ igen                         nem     │
                    ▼                                       ▼
              WORK_PACKAGE (köv. sprint)                  DONE ✓
```

## 8. Formális Szoftverszerződések és Sémák

### 8.1 `SPEC_FORMAL.yaml`

```yaml
id: "SPEC-001"
title: "Webarchívum Szolgáltatás"
description: "Weboldalak automatikus mentése és kereshető archiválása"
tech_stack:
  language: "python"
  framework: "fastapi"
  database: "sqlite"
requirements:
  - id: "FR-001"
    title: "URL archiválás API"
    description: "POST /archive endpoint URL-lel"
    priority: "HIGH"
    status: "PENDING"
  - id: "FR-002"
    title: "JWT Autentikáció"
    description: "Bearer tokenes védelem az API-hoz"
    priority: "HIGH"
    status: "PENDING"
```

### 8.2 `WORK_PACKAGE.yaml`

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

### 8.3 `CAPABILITY_REGISTRY.yaml`

```yaml
capabilities:
  code_generation:
    primary_provider: "ClaudeCodeCLI"
    fallback_providers: ["AiderAgent", "OpenAIAgent"]
    required_context_window: 64000
    timeout_seconds: 600

  security_audit:
    primary_provider: "SemgrepCLI"
    secondary_provider: "SecurityAgentLLM"
    mode: "hybrid"

  architecture_validation:
    primary_provider: "ArchitectAgent"
    fallback_providers: ["DeepSeekR1Agent"]
    decision_authority: "FROZEN_ADR_CHECK"
```

### 8.4 `ORGANIZATION_GENOME.yaml`

```yaml
organization_id: "ORG-ENTERPRISE-CORE"
total_projects_analyzed: 42
genome_version: "v4.2"

preferred_patterns:
  - pattern_id: "PAT-EVENT-DRIVEN"
    success_rate: 0.96
    domain_relevance: ["document_processing", "backend_platform"]
  - pattern_id: "PAT-CLEAN-ARCHITECTURE"
    success_rate: 0.91

forbidden_patterns:
  - pattern_id: "ANTI-GOD-CLASS"
    reason: "A korábbi projektek során az esetek 88%-ában tesztelhetőségi és karbantartási hibákhoz vezetett."
  - pattern_id: "ANTI-SHARED-DATABASE"
    reason: "Mikroszolgáltatások közötti adatmodell-törést okoz."
```

## 9. Discovery Mode — a "README-First" Megközelítés

A rendszer a projekt gyökerében található `README.md` fájlt tekinti az elsődleges információforrásnak.

### A Discovery Mátrix

| Állapot          | Van README.md                                                                 | Nincs README.md                                                                                      |
|------------------|----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Új Projekt       | Beolvassa a létező koncepciót és csak a hiányzó részekre kérdez rá.        | A CLI kérdések lefutnak, a rendszer megalkotja a `SPEC_FORMAL.yaml`-t és legyártja a kezdő README.md-t. |
| Meglévő Projekt  | Beolvassa a README-t és a kódot. Célzott tisztázó kérdéseket tesz fel.     | A felmérés után legyártja a hiányzó README.md-t és felveszi a technikai adósságok közé.                |

## 10. Kétszintű Tanulási Modell

### A) Projekt-szintű Tanulás (Automatikus)

A `RetrospectiveCollector` minden sprint végén rögzíti a tanulságot a `.ai-sd-os/retrospectives/SPRINT-XXX.yaml` fájlba. A `carry_forward_note` mező bekerül a következő sprint prompt kontextusába.

### B) Motor-szintű Lessons Learned (Emberi felülvizsgálattal)

A motor gyökerében lévő `lessons/lessons_learned.yaml` aggregálja a mintákat több projektből:

```yaml
entries:
  - pattern: "Időzóna-kezelésű követelmények"
    occurrences: 3
    projects:
      - "webarchivum / SPRINT-003"
    suggested_action: "Frissíteni a discovery fázis CLI kérdéseit"
    status: "PENDING_HUMAN_REVIEW"
```

A `suggested_action` mező csak javaslatot tesz — a motort kizárólag emberi PR és verzióemelés módosíthatja (Alkotmány 8. törvény).

## 11. Telepítés és Használat

### 1. Motor Telepítése

```bash
git clone https://github.com/yourorg/ai-sd-os.git /srv/projekts/ai-sd-os
cd /srv/projekts/ai-sd-os
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # .env szerkesztése: ANTHROPIC_API_KEY beállítása
```

### 2. Projekt Futtatása

```bash
cd /srv/projekts/webarchivum
python /srv/projekts/ai-sd-os/main.py
```

## 12. Függőségek (`requirements.txt`)

```text
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

## 13. Licenc

MIT License — szabad felhasználás, módosítás és terjesztés.

