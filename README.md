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
14. [Kódmelléklet — contracts/ és kernel/ Modulok](#14-kódmelléklet--contracts-és-kernel-modulok)
15. [Kódmelléklet — SDK, Ágensek, Runtime és Fő Indító Modulok](#15-kódmelléklet--sdk-ágensek-runtime-és-fő-indító-modulok)

> **Megjegyzés a 14–15. fejezetekről:** Ez a két fejezet a V6.1.0 architektúra tervezéskori referencia-forráskódját tartalmazza (blueprint). A repóban ténylegesen megvalósított kód ettől több ponton eltér — lásd az [Auditálási megjegyzést](#auditálási-megjegyzés-v61-blueprint-vs-tényleges-kód) a dokumentum végén.

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

---

## 14. Kódmelléklet — `contracts/` és `kernel/` Modulok

### 14.1 Formális Szerződések és Események (`contracts/`)

#### 14.1.1 Alap Esemény Modell (`contracts/events/base_event.py`)

```python
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict
from uuid import uuid4
from pydantic import BaseModel, Field


class EventType(str, Enum):
    # Rendszer & Életciklus Események
    SYSTEM_INITIALIZED = "system.initialized"
    DISCOVERY_COMPLETED = "discovery.completed"
    CODEBASE_SURVEYED = "codebase.surveyed"
    SPEC_CREATED = "spec.created"
    WORKPACKAGE_CREATED = "workpackage.created"

    # Human-in-the-Loop Kapu Események
    SPRINT_PLANNING_PROPOSED = "sprint.planning.proposed"
    SPRINT_PLANNING_APPROVED = "sprint.planning.approved"
    SPRINT_REVIEW_REQUESTED = "sprint.review.requested"
    SPRINT_REVIEW_APPROVED = "sprint.review.approved"
    PIPELINE_BLOCKED = "pipeline.blocked"
    ACTION_DESTRUCTIVE_REQUESTED = "action.destructive.requested"

    # Fejlesztési & Tesztelési Események
    DEVELOPMENT_STARTED = "development.started"
    DEVELOPMENT_COMPLETED = "development.completed"
    TESTS_PASSED = "tests.passed"
    TESTS_FAILED = "tests.failed"
    DRIFT_DETECTED = "architecture.drift_detected"

    # Tanulási & Rendszer Hiba Események
    RETROSPECTIVE_RECORDED = "retrospective.recorded"
    LESSONS_LEARNED_UPDATED = "lessons.learned.updated"
    SYSTEM_ERROR = "system.error"


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sender_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
```

#### 14.1.2 Specifikációs Események (`contracts/events/spec_events.py`)

```python
from typing import Dict, Any
from pydantic import Field
from contracts.events.base_event import BaseEvent, EventType


class SpecCreatedEvent(BaseEvent):
    event_type: EventType = EventType.SPEC_CREATED
    payload: Dict[str, Any] = Field(
        ..., description="Köteles tartalmazni a 'spec_path' kulcsot."
    )


class DiscoveryCompletedEvent(BaseEvent):
    event_type: EventType = EventType.DISCOVERY_COMPLETED
    payload: Dict[str, Any] = Field(
        ..., description="Köteles tartalmazni a 'discovery_summary' kulcsot."
    )


class CodebaseSurveyedEvent(BaseEvent):
    event_type: EventType = EventType.CODEBASE_SURVEYED
    payload: Dict[str, Any] = Field(
        ..., description="Köteles tartalmazni a 'snapshot_path' kulcsot."
    )
```

#### 14.1.3 Sprint & Fejlesztési Események (`contracts/events/sprint_events.py`)

```python
from typing import Dict, Any
from pydantic import Field
from contracts.events.base_event import BaseEvent, EventType


class WorkPackageCreatedEvent(BaseEvent):
    event_type: EventType = EventType.WORKPACKAGE_CREATED
    payload: Dict[str, Any] = Field(
        ..., description="Tartalmazza a 'work_package_path' kulcsot."
    )


class DevelopmentCompletedEvent(BaseEvent):
    event_type: EventType = EventType.DEVELOPMENT_COMPLETED
    payload: Dict[str, Any] = Field(
        ..., description="Tartalmazza a 'code_file' és 'modified_files' kulcsokat."
    )


class TestsPassedEvent(BaseEvent):
    event_type: EventType = EventType.TESTS_PASSED
    payload: Dict[str, Any] = Field(
        ..., description="Tartalmazza a 'workspace', 'exit_code', 'stdout' kulcsokat."
    )


class TestsFailedEvent(BaseEvent):
    event_type: EventType = EventType.TESTS_FAILED
    payload: Dict[str, Any] = Field(
        ..., description="Tartalmazza az 'exit_code', 'stderr' és 'retry_count' kulcsokat."
    )
```

#### 14.1.4 Kapu & Eszkalációs Események (`contracts/events/gate_events.py`)

```python
from typing import Dict, Any
from pydantic import Field
from contracts.events.base_event import BaseEvent, EventType


class SprintPlanningProposedEvent(BaseEvent):
    event_type: EventType = EventType.SPRINT_PLANNING_PROPOSED
    payload: Dict[str, Any] = Field(
        ..., description="Tartalmazza a 'work_package_id' és 'sprint_goal' mezőket."
    )


class SprintPlanningApprovedEvent(BaseEvent):
    event_type: EventType = EventType.SPRINT_PLANNING_APPROVED


class SprintReviewRequestedEvent(BaseEvent):
    event_type: EventType = EventType.SPRINT_REVIEW_REQUESTED


class SprintReviewApprovedEvent(BaseEvent):
    event_type: EventType = EventType.SPRINT_REVIEW_APPROVED


class PipelineBlockedEvent(BaseEvent):
    event_type: EventType = EventType.PIPELINE_BLOCKED
    payload: Dict[str, Any] = Field(
        ..., description="Tartalmazza a 'reason' és 'last_error' mezőket."
    )
```

#### 14.1.5 Formális Specifikáció Szerződés (`contracts/spec_formal.py`)

```python
from typing import List
from pydantic import BaseModel, Field


class RequirementItem(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^FR-[0-9]{3,}$",
        description="Követelmény azonosító (pl. FR-001)",
    )
    title: str = Field(..., min_length=3, description="Rövid megnevezés")
    description: str = Field(..., min_length=5, description="Részletes leírás")
    priority: str = Field(
        default="HIGH",
        pattern=r"^(HIGH|MEDIUM|LOW)$",
        description="Prioritási szint",
    )
    status: str = Field(
        default="PENDING",
        pattern=r"^(PENDING|IN_PROGRESS|SATISFIED|DEPRECATED)$",
        description="Teljesítési státusz",
    )


class SpecFormal(BaseModel):
    id: str = Field(default="SPEC-001", pattern=r"^SPEC-[0-9]{3,}$")
    project_name: str = Field(..., min_length=2)
    project_goal: str = Field(..., min_length=10)
    tech_stack: List[str] = Field(..., min_items=1)
    requirements: List[RequirementItem] = Field(..., min_items=1)
```

#### 14.1.6 Munkacsomag Szerződés (`contracts/work_package.py`)

```python
from typing import Dict, List
from pydantic import BaseModel, Field


class WorkPackageTask(BaseModel):
    task_id: str = Field(..., pattern=r"^TASK-[0-9]{3,}$")
    description: str = Field(..., min_length=5)
    requirement_ref: str = Field(..., pattern=r"^FR-[0-9]{3,}$")


class WorkPackage(BaseModel):
    id: str = Field(..., pattern=r"^WP-[0-9]{3,}$")
    sprint_id: str = Field(..., pattern=r"^SPRINT-[0-9]{3,}$")
    goal: str = Field(..., min_length=5)
    allowed_paths: List[str] = Field(..., min_items=1)
    tasks: List[WorkPackageTask] = Field(..., min_items=1)
    max_execution_time_minutes: int = Field(default=30, le=120)
    tests_required: bool = True
    coverage_mapping: Dict[str, List[str]] = Field(
        ...,
        description="FR-XXX azonosítók lefedése konkrét tesztfüggvény nevekkel.",
    )
```

#### 14.1.7 Definition of Done Szerződés (`contracts/definition_of_done.py`)

```python
from typing import List
from pydantic import BaseModel, Field


class DoDCriterion(BaseModel):
    id: str = Field(..., pattern=r"^DOD-[0-9]{3,}$")
    description: str = Field(..., min_length=5)
    automated_check: bool = Field(
        default=True, description="Automatizált-e az ellenőrzés"
    )
    passed: bool = Field(
        default=False, description="Teljesült-e a kritérium"
    )


class DefinitionOfDone(BaseModel):
    work_package_ref: str = Field(..., pattern=r"^WP-[0-9]{3,}$")
    criteria: List[DoDCriterion] = Field(..., min_items=1)

    def is_fully_satisfied(self) -> bool:
        return all(c.passed for c in self.criteria)
```

#### 14.1.8 Kódbázis Felmérési Szerződés (`contracts/codebase_snapshot.py`)

```python
from typing import List
from pydantic import BaseModel, Field


class SecuritySnapshot(BaseModel):
    risk_flags: List[str] = Field(default_factory=list)
    secret_scan_status: str = Field(default="CLEAN")


class TechnicalDebtSnapshot(BaseModel):
    missing_tests: List[str] = Field(default_factory=list)
    no_type_hints: bool = False


class CodebaseSnapshot(BaseModel):
    project_path: str
    languages: List[str] = Field(..., min_items=1)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    architecture: str = Field(default="monolith")
    dependencies_count: int = 0
    security: SecuritySnapshot = Field(default_factory=SecuritySnapshot)
    technical_debt: TechnicalDebtSnapshot = Field(
        default_factory=TechnicalDebtSnapshot
    )
    has_readme: bool = True
    has_dockerfile: bool = False
```

#### 14.1.9 Nyomonkövethetőségi Mátrix (`contracts/traceability_matrix.py`)

```python
from typing import List
from pydantic import BaseModel, Field


class TraceabilityLink(BaseModel):
    requirement_id: str = Field(..., pattern=r"^FR-[0-9]{3,}$")
    work_package_id: str = Field(..., pattern=r"^WP-[0-9]{3,}$")
    task_id: str = Field(..., pattern=r"^TASK-[0-9]{3,}$")
    source_file: str
    test_function: str


class TraceabilityMatrix(BaseModel):
    project_id: str
    links: List[TraceabilityLink] = Field(default_factory=list)

    def get_links_for_requirement(
        self, req_id: str
    ) -> List[TraceabilityLink]:
        return [link for link in self.links if link.requirement_id == req_id]
```

### 14.2 Kernel Mag és Rendszermodulok (`kernel/`)

#### 14.2.1 Konfiguráció (`kernel/system/config.py`)

```python
from pathlib import Path
from pydantic import BaseModel, Field


class KernelConfig(BaseModel):
    constitution_text: str = Field(..., description="Alkotmány szövege")
    max_retries: int = Field(default=3, ge=1, description="Max újrapróbálkozás")
    checkpoint_enabled: bool = True
    storage_dir: Path = Field(default=Path("./runtime"))
    max_budget_usd: float = Field(default=100.0, ge=0.0)
    enforce_decision_freeze: bool = True
```

#### 14.2.2 Aszinkron EventBus Engine (`kernel/event_bus/bus.py`)

```python
import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable, Dict, List
from contracts.events.base_event import BaseEvent, EventType

logger = logging.getLogger("Kernel.EventBus")
HandlerFunc = Callable[[BaseEvent], Awaitable[None]]


class EventBus:

    def __init__(self) -> None:
        self._subscribers: Dict[EventType, List[HandlerFunc]] = defaultdict(
            list
        )
        self._queue: asyncio.Queue[BaseEvent] = asyncio.Queue()
        self._running: bool = False
        self._worker_task: asyncio.Task[None] | None = None

    def subscribe(self, event_type: EventType, handler: HandlerFunc) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, event: BaseEvent) -> None:
        await self._queue.put(event)

    async def start(self) -> None:
        self._running = True
        self._worker_task = asyncio.create_task(self._process_queue())

    async def stop(self) -> None:
        self._running = False
        await self._queue.join()
        if self._worker_task:
            self._worker_task.cancel()

    async def _process_queue(self) -> None:
        while self._running or not self._queue.empty():
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            handlers = self._subscribers.get(event.event_type, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as err:
                    logger.error(
                        f"[EVENT ERROR] A '{handler.__name__}' handler elbukott a "
                        f"'{event.event_type.value}' eseményen: {err}",
                        exc_info=True,
                    )
            self._queue.task_done()
```

#### 14.2.3 Állapotok Definíciója (`kernel/state/states.py`)

```python
from enum import Enum


class StateEnum(str, Enum):
    INIT = "INIT"
    DISCOVERY = "DISCOVERY"
    SPEC = "SPEC"
    WORK_PACKAGE = "WORK_PACKAGE"
    SPRINT_PLANNING = "SPRINT_PLANNING"
    DEVELOPMENT = "DEVELOPMENT"
    TEST = "TEST"
    BLOCKED = "BLOCKED"
    SPRINT_REVIEW = "SPRINT_REVIEW"
    PR_CREATED = "PR_CREATED"
    RETROSPECTIVE = "RETROSPECTIVE"
    DONE = "DONE"
```

#### 14.2.4 Állapotátmeneti Mátrix (`kernel/state/transitions.py`)

```python
from typing import Dict, Set
from kernel.state.states import StateEnum

ALLOWED_TRANSITIONS: Dict[StateEnum, Set[StateEnum]] = {
    StateEnum.INIT: {StateEnum.DISCOVERY},
    StateEnum.DISCOVERY: {StateEnum.SPEC},
    StateEnum.SPEC: {StateEnum.WORK_PACKAGE},
    StateEnum.WORK_PACKAGE: {StateEnum.SPRINT_PLANNING},
    StateEnum.SPRINT_PLANNING: {StateEnum.DEVELOPMENT, StateEnum.WORK_PACKAGE},
    StateEnum.DEVELOPMENT: {StateEnum.TEST},
    StateEnum.TEST: {
        StateEnum.SPRINT_REVIEW,
        StateEnum.DEVELOPMENT,
        StateEnum.BLOCKED,
    },
    StateEnum.BLOCKED: {StateEnum.DEVELOPMENT, StateEnum.WORK_PACKAGE},
    StateEnum.SPRINT_REVIEW: {StateEnum.PR_CREATED, StateEnum.DEVELOPMENT},
    StateEnum.PR_CREATED: {StateEnum.RETROSPECTIVE},
    StateEnum.RETROSPECTIVE: {StateEnum.WORK_PACKAGE, StateEnum.DONE},
    StateEnum.DONE: set(),
}
```

#### 14.2.5 Állapot-Validátorok és Tároló (`kernel/state/validators.py` & `kernel/state/state_store.py`)

```python
# kernel/state/validators.py
from kernel.state.states import StateEnum
from kernel.state.transitions import ALLOWED_TRANSITIONS


class InvalidStateTransitionError(Exception):
    pass


def validate_transition(
    current_state: StateEnum, new_state: StateEnum
) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current_state, set())
    if new_state not in allowed:
        raise InvalidStateTransitionError(
            f"Érvénytelen állapotváltás: {current_state.value} -> {new_state.value}. "
            f"Engedélyezett átmenetek: {[s.value for s in allowed]}"
        )


# kernel/state/state_store.py
from typing import Any, Dict, Optional
from kernel.state.states import StateEnum
from kernel.state.validators import validate_transition


class StateStore:

    def __init__(self) -> None:
        self._current_state: StateEnum = StateEnum.INIT
        self._context_data: Dict[str, Any] = {}

    @property
    def current_state(self) -> StateEnum:
        return self._current_state

    def transition_to(self, new_state: StateEnum) -> None:
        validate_transition(self._current_state, new_state)
        self._current_state = new_state

    def set_data(self, key: str, value: Any) -> None:
        self._context_data[key] = value

    def get_data(self, key: str) -> Optional[Any]:
        return self._context_data.get(key)
```

#### 14.2.6 Kriptográfiai Execution Ledger (`kernel/ledger/ledger_chain.py`)

```python
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from contracts.events.base_event import BaseEvent


class LedgerBlock(BaseModel):
    sequence_number: int
    previous_hash: str
    current_hash: str
    event_data: Dict[str, Any]


class LedgerChain:

    def __init__(
        self, storage_path: Path = Path("./.ai-sd-os/ledger/chain.json")
    ):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.chain: List[LedgerBlock] = self._load_chain()

    def _load_chain(self) -> List[LedgerBlock]:
        if not self.storage_path.exists():
            return []
        data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        return [LedgerBlock(**block) for block in data]

    def _save_chain(self) -> None:
        data = [block.model_dump(mode="json") for block in self.chain]
        self.storage_path.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def append_event(self, event: BaseEvent) -> LedgerBlock:
        previous_hash = (
            self.chain[-1].current_hash
            if self.chain
            else "0" * 64
        )
        seq = len(self.chain) + 1

        payload_bytes = json.dumps(
            event.model_dump(mode="json"), sort_keys=True
        ).encode("utf-8")
        current_hash = hashlib.sha256(
            f"{previous_hash}{event.timestamp}{event.sender_id}{payload_bytes}".encode(
                "utf-8"
            )
        ).hexdigest()

        block = LedgerBlock(
            sequence_number=seq,
            previous_hash=previous_hash,
            current_hash=current_hash,
            event_data=event.model_dump(mode="json"),
        )
        self.chain.append(block)
        self._save_chain()
        return block

    def verify_integrity(self) -> bool:
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr.previous_hash != prev.current_hash:
                return False
        return True
```

#### 14.2.7 Szemantikai Replay Engine (`kernel/ledger/replay_engine.py`)

```python
import ast
from pathlib import Path


class SemanticReplayEngine:

    @staticmethod
    def verify_ast_equivalence(
        original_code: str, replayed_code: str
    ) -> bool:
        """Összehasonlítja két Python kód Absztrakt Szintaxisfáját."""
        try:
            tree_orig = ast.parse(original_code)
            tree_repl = ast.parse(replayed_code)
            return ast.dump(tree_orig, annotate_fields=False) == ast.dump(
                tree_repl, annotate_fields=False
            )
        except SyntaxError:
            return False

    @staticmethod
    def verify_test_pass(workspace_path: Path, test_command: str) -> bool:
        import subprocess

        res = subprocess.run(
            test_command, shell=True, cwd=workspace_path, capture_output=True
        )
        return res.returncode == 0
```

#### 14.2.8 Policy Compiler (`kernel/policy/policy_compiler.py`)

```python
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel, Field
import yaml


class CompiledPolicy(BaseModel):
    require_human_sprint_planning: bool = True
    require_human_sprint_review: bool = True
    max_retries_before_block: int = 3
    secret_scan_strict: bool = True
    allowed_file_extensions: list[str] = Field(
        default_factory=lambda: [".py", ".yaml", ".json", ".md"]
    )


class PolicyCompiler:

    def __init__(self, policy_dir: Path = Path("./kernel/policy")):
        self.policy_dir = policy_dir

    def compile(self) -> CompiledPolicy:
        rules_file = self.policy_dir / "rules.yaml"
        if not rules_file.exists():
            return CompiledPolicy()

        content = yaml.safe_load(rules_file.read_text(encoding="utf-8")) or {}
        return CompiledPolicy(**content)
```

#### 14.2.9 Human-in-the-Loop Kapukezelő (`kernel/hitl/gate_manager.py`)

```python
import logging
from contracts.events.base_event import BaseEvent, EventType
from kernel.event_bus.bus import EventBus
from kernel.state.state_enum import StateEnum
from kernel.state.state_store import StateStore

logger = logging.getLogger("Kernel.HITLGateManager")


class HITLGateManager:

    def __init__(self, bus: EventBus, store: StateStore):
        self.bus = bus
        self.store = store
        self._register_subscriptions()

    def register_subscriptions(self) -> None:
        self.bus.subscribe(EventType.WORKPACKAGE_CREATED, self._on_wp_created)
        self.bus.subscribe(EventType.TESTS_PASSED, self._on_tests_passed)
        self.bus.subscribe(
            EventType.TESTS_FAILED, self._check_max_retries
        )

    async def _on_wp_created(self, event: BaseEvent) -> None:
        self.store.transition_to(StateEnum.SPRINT_PLANNING)
        await self.bus.publish(
            BaseEvent(
                event_type=EventType.SPRINT_PLANNING_PROPOSED,
                sender_id="gate_manager",
                payload=event.payload,
                correlation_id=event.correlation_id,
            )
        )

    async def _on_tests_passed(self, event: BaseEvent) -> None:
        self.store.transition_to(StateEnum.SPRINT_REVIEW)
        await self.bus.publish(
            BaseEvent(
                event_type=EventType.SPRINT_REVIEW_REQUESTED,
                sender_id="gate_manager",
                payload=event.payload,
                correlation_id=event.correlation_id,
            )
        )

    async def _check_max_retries(self, event: BaseEvent) -> None:
        retry_count = event.payload.get("retry_count", 0)
        max_retries = event.payload.get("max_retries", 3)
        if retry_count >= max_retries:
            self.store.transition_to(StateEnum.BLOCKED)
            await self.bus.publish(
                BaseEvent(
                    event_type=EventType.PIPELINE_BLOCKED,
                    sender_id="gate_manager",
                    payload={"reason": "Max retry limit reached", "last_error": event.payload.get("stderr", "")},
                    correlation_id=event.correlation_id,
                )
            )
```

> **Megjegyzés:** ez a snippet a tervezési dokumentumból eredeti formájában maradt — `__init__` a `self._register_subscriptions()`-t hívja, miközben a metódus `register_subscriptions` néven (aláhúzás nélkül) van definiálva. A ténylegesen megvalósított `kernel/hitl/gate_manager.py` ezt a hibát nem tartalmazza.

#### 14.2.10 CLI Prompts (`kernel/hitl/cli_prompts.py`)

```python
class CLIPromptEngine:

    @staticmethod
    def prompt_sprint_planning(wp_id: str, goal: str) -> bool:
        print("\n" + "=" * 56)
        print(f"  SPRINT PLANNING — {wp_id}")
        print("=" * 56)
        print(f"Cél: {goal}")
        choice = (
            input("[j] Jóváhagyom, indulhat  |  [n] Elutasítom > ")
            .strip()
            .lower()
        )
        return choice == "j"

    @staticmethod
    def prompt_sprint_review(wp_id: str) -> bool:
        print("\n" + "=" * 56)
        print(f"  SPRINT REVIEW — {wp_id}")
        print("=" * 56)
        print("Minden automatizált teszt zöld.")
        choice = (
            input("[j] Elfogadom, commit-olhat  |  [n] Elutasítom > ")
            .strip()
            .lower()
        )
        return choice == "j"
```

#### 14.2.11 Swarm Párhuzamos Végrehajtó (`kernel/swarm/orchestrator.py` & `ast_locker.py`)

```python
# kernel/swarm/ast_locker.py
from typing import Dict, Set


class ASTLocker:

    def __init__(self) -> None:
        self._locks: Dict[str, Set[str]] = {}  # filepath -> set of node_ids

    def acquire_lock(self, filepath: str, node_id: str) -> bool:
        if filepath not in self._locks:
            self._locks[filepath] = set()
        if node_id in self._locks[filepath]:
            return False
        self._locks[filepath].add(node_id)
        return True

    def release_lock(self, filepath: str, node_id: str) -> None:
        if filepath in self._locks and node_id in self._locks[filepath]:
            self._locks[filepath].remove(node_id)


# kernel/swarm/orchestrator.py
from typing import List
from contracts.work_package import WorkPackageTask
from kernel.swarm.ast_locker import ASTLocker


class SwarmOrchestrator:

    def __init__(self) -> None:
        self.locker = ASTLocker()

    def partition_tasks(
        self, tasks: List[WorkPackageTask]
    ) -> List[List[WorkPackageTask]]:
        """Párhuzamosan futtatható feladatcsoportokra bontja a taskokat."""
        # MVP: Minden task független csoportba kerül, ha nincs zárolási ütközés
        return [[t] for t in tasks]
```

#### 14.2.12 Szoftverszerződés Validátor (`kernel/contracts/validator.py`)

```python
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError
import yaml

T = TypeVar("T", bound=BaseModel)


class ContractValidationError(Exception):
    pass


class ContractValidator:

    @staticmethod
    def validate_dict(data: Dict[str, Any], schema_cls: Type[T]) -> T:
        try:
            return schema_cls(**data)
        except ValidationError as err:
            raise ContractValidationError(
                f"Szerződés validációs hiba [{schema_cls.__name__}]:\n{err}"
            ) from err

    @staticmethod
    def validate_yaml_string(yaml_content: str, schema_cls: Type[T]) -> T:
        try:
            parsed_data = yaml.safe_load(yaml_content)
            if not isinstance(parsed_data, dict):
                raise ContractValidationError(
                    "A YAML tartalomnak szótárnak (dict) kell lennie."
                )
            return ContractValidator.validate_dict(parsed_data, schema_cls)
        except yaml.YAMLError as err:
            raise ContractValidationError(
                f"Hibás YAML formátum: {err}"
            ) from err
```

#### 14.2.13 Szerződés Szerializáló (`kernel/contracts/serializer.py`)

```python
from pathlib import Path
from typing import Type, TypeVar
from pydantic import BaseModel
import yaml
from kernel.contracts.validator import ContractValidator, ContractValidationError

T = TypeVar("T", bound=BaseModel)


class ContractSerializer:

    @staticmethod
    def save_yaml(model: BaseModel, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = model.model_dump(mode="json")
        yaml_content = yaml.dump(data, sort_keys=False, allow_unicode=True)
        path.write_text(yaml_content, encoding="utf-8")

    @staticmethod
    def load_yaml(path: Path, model_cls: Type[T]) -> T:
        if not path.exists():
            raise ContractValidationError(
                f"A szerződés fájl nem létezik: {path}"
            )
        content = path.read_text(encoding="utf-8")
        return ContractValidator.validate_yaml_string(content, model_cls)
```

#### 14.2.14 Budget Controller (`kernel/economics/budget_controller.py`)

```python
from pydantic import BaseModel, Field


class BudgetController(BaseModel):
    max_budget_usd: float = Field(default=100.0)
    consumed_usd: float = Field(default=0.0)

    def record_consumption(self, usd_cost: float) -> None:
        self.consumed_usd += usd_cost

    def is_economy_mode_required(self) -> bool:
        remaining_pct = (
            (self.max_budget_usd - self.consumed_usd) / self.max_budget_usd
        ) * 100
        return remaining_pct < 10.0

    def is_budget_exhausted(self) -> bool:
        return self.consumed_usd >= self.max_budget_usd
```

#### 14.2.15 Stratégiai Érték-Becslő (`kernel/economics/value_evaluator.py`)

```python
from pydantic import BaseModel, Field


class ValueModel(BaseModel):
    business_value: float = Field(..., ge=1.0, le=10.0)
    expected_revenue: float = Field(..., ge=1.0, le=100.0)
    maintenance_cost: float = Field(..., ge=1.0, le=10.0)
    technical_risk: float = Field(..., ge=1.0, le=10.0)


class StrategicValueEvaluator:

    @staticmethod
    def calculate_index(model: ValueModel) -> float:
        """Kiszámítja a V_strategic indexet: (B_value * R_expected) / (C_maint * T_risk)."""
        return (model.business_value * model.expected_revenue) / (
            model.maintenance_cost * model.technical_risk
        )

    @classmethod
    def evaluate_go_no_go(cls, model: ValueModel) -> str:
        v_idx = cls.calculate_index(model)
        if v_idx >= 15.0:
            return "GO"
        elif v_idx >= 8.0:
            return "REWORK"
        return "CANCEL"
```

#### 14.2.16 Checkpoint Kezelő Engine (`kernel/checkpoint/checkpoint_manager.py`)

```python
import json
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel


class Checkpoint(BaseModel):
    checkpoint_id: str
    state: str
    context_data: Dict[str, Any]


class CheckpointManager:

    def __init__(
        self, storage_dir: Path = Path("./.ai-sd-os/checkpoints")
    ):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self, checkpoint_id: str, state: str, context_data: Dict[str, Any]
    ) -> Checkpoint:
        cp = Checkpoint(
            checkpoint_id=checkpoint_id,
            state=state,
            context_data=context_data,
        )
        filepath = self.storage_dir / f"{checkpoint_id}.json"
        filepath.write_text(cp.model_dump_json(indent=2), encoding="utf-8")
        return cp

    def restore(self, checkpoint_id: str) -> Optional[Checkpoint]:
        filepath = self.storage_dir / f"{checkpoint_id}.json"
        if not filepath.exists():
            return None
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return Checkpoint(**data)
```

---

## 15. Kódmelléklet — SDK, Ágensek, Runtime és Fő Indító Modulok

### 15.1 Agent SDK Modul (`sdk/`)

#### 15.1.1 SDK Adatmodellek (`sdk/models.py`)

```python
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatusCode(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class AgentContext(BaseModel):
    agent_id: str
    project_id: str
    work_package_id: Optional[str] = None
    compiled_prompt: str
    system_prompt: str
    state_data: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    status_code: AgentStatusCode
    artifacts_created: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = 0
```

#### 15.1.2 Provider Adapter Interfész és Mock (`sdk/provider_adapter.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict


class BaseProviderAdapter(ABC):

    @abstractmethod
    async def generate_response(self, prompt: str, system_prompt: str) -> str:
        """LLM válasz generálása."""
        pass


class MockProviderAdapter(BaseProviderAdapter):
    """Determinisztikus válaszokat adó adapter teszteléshez és offline futtatáshoz."""

    def __init__(self, mock_responses: Dict[str, str] | None = None):
        self.mock_responses = mock_responses or {}

    async def generate_response(self, prompt: str, system_prompt: str) -> str:
        for key, response in self.mock_responses.items():
            if key in prompt or key in system_prompt:
                return response

        if (
            "WORK_PACKAGE" in system_prompt
            or "Architect" in system_prompt
            or "SPEC" in prompt
        ):
            return """
id: "WP-001"
sprint_id: "SPRINT-001"
goal: "FastAPI CRUD endpointok megírása"
allowed_paths:
  - "src/"
  - "tests/"
tasks:
  - task_id: "TASK-001"
    description: "Todo adatbázis séma és CRUD API megírása"
    requirement_ref: "FR-001"
max_execution_time_minutes: 30
tests_required: true
coverage_mapping:
  "FR-001": ["test_add"]
"""
        elif "Developer" in system_prompt or "Code" in prompt:
            return "def add(a, b):\n    return a + b\n"
        elif "Discovery" in system_prompt:
            return "README elemzés kész. A projekt célja tisztázott."
        elif "Drift" in system_prompt:
            return "NO_DRIFT_DETECTED"
        return "Mock Response OK"
```

#### 15.1.3 Base Agent SDK (`sdk/base_agent.py`)

```python
import logging
from abc import ABC, abstractmethod
from contracts.events.base_event import BaseEvent, EventType
from kernel.event_bus.bus import EventBus
from kernel.state.state_store import StateStore
from sdk.provider_adapter import BaseProviderAdapter

logger = logging.getLogger("SDK.BaseAgent")


class BaseAgentSDK(ABC):

    def __init__(
        self,
        agent_id: str,
        bus: EventBus,
        store: StateStore,
        provider: BaseProviderAdapter,
    ):
        self.agent_id = agent_id
        self.bus = bus
        self.store = store
        self.provider = provider
        self.register_subscriptions()

    @abstractmethod
    def register_subscriptions(self) -> None:
        pass

    @abstractmethod
    async def process_event(self, event: BaseEvent) -> None:
        pass

    async def handle_event(self, event: BaseEvent) -> None:
        try:
            await self.process_event(event)
        except Exception as err:
            logger.error(
                f"[{self.agent_id}] Hiba az esemény feldolgozásakor: {err}",
                exc_info=True,
            )
            await self.emit_event(
                event_type=EventType.SYSTEM_ERROR,
                payload={"agent_id": self.agent_id, "error": str(err)},
                correlation_id=event.correlation_id,
            )

    async def emit_event(
        self, event_type: EventType, payload: dict, correlation_id: str
    ) -> None:
        event = BaseEvent(
            event_type=event_type,
            sender_id=self.agent_id,
            payload=payload,
            correlation_id=correlation_id,
        )
        await self.bus.publish(event)
```

### 15.2 Ágensek és System Promptok (`agents/`)

#### 15.2.1 System Promptok Regisztere (`agents/prompts.py`)

```python
ARCHITECT_SYSTEM_PROMPT = """
Te vagy az ArchitectAgent.
A SPEC_FORMAL.yaml és a Discovery adatok alapján készíts WORK_PACKAGE.yaml fájlt.
Szigorúan tartsd be a WorkPackage Pydantic sémáját.
Ne tervezz túlbonyolított architektúrát, csak a minimálisan szükséges megoldást.
"""

DEVELOPER_SYSTEM_PROMPT = """
Te vagy a DeveloperAgent.
Olvasd be a WORK_PACKAGE.yaml fájlt és generálj tiszta, futtatható Python kódot.
Kizárólag érvényes Python forráskódot adj vissza.
"""

DISCOVERY_SYSTEM_PROMPT = """
Te vagy a DiscoveryAgent.
Elemezd a létező README.md fájlt és a kódbázis struktúráját.
Határozd meg a technológiai stacket, az architektúrát és a hiányzó teszteket.
"""

DRIFT_DETECTOR_SYSTEM_PROMPT = """
Te vagy a DriftDetectorAgent.
Hasonlítsd össze a generált forráskód AST-jét a SPEC_FORMAL.yaml és az ARCHITECTURE.md előírásaival.
Ha eltérést találsz, jelezd a DRIFT_DETECTED státuszt.
"""

RETROSPECTIVE_SYSTEM_PROMPT = """
Te vagy a RetrospectiveCollector.
Elemezd a lefutott sprint eredményeit, a retry számlálót és a tesztek kimenetét.
Generálj strukturált tanulságot (what_worked, what_failed, carry_forward_note).
"""
```

#### 15.2.2 Architect Agent (`agents/core/architect_agent.py`)

```python
from pathlib import Path
from agents.prompts import ARCHITECT_SYSTEM_PROMPT
from contracts.events.base_event import BaseEvent, EventType
from contracts.spec_formal import SpecFormal
from contracts.work_package import WorkPackage
from kernel.contracts.serializer import ContractSerializer
from kernel.contracts.validator import ContractValidator
from kernel.state.states import StateEnum
from sdk.base_agent import BaseAgentSDK


class ArchitectAgent(BaseAgentSDK):

    def register_subscriptions(self) -> None:
        self.bus.subscribe(EventType.SPEC_CREATED, self.handle_event)

    async def process_event(self, event: BaseEvent) -> None:
        spec_path = Path(event.payload["spec_path"])
        spec = ContractSerializer.load_yaml(spec_path, SpecFormal)

        prompt = f"Készíts WORK_PACKAGE-et ehhez a specifikációhoz: Név: {spec.project_name}, Cél: {spec.project_goal}"
        response = await self.provider.generate_response(
            prompt, ARCHITECT_SYSTEM_PROMPT
        )

        wp = ContractValidator.validate_yaml_string(response, WorkPackage)
        wp_path = spec_path.parent / "WORK_PACKAGE.yaml"
        ContractSerializer.save_yaml(wp, wp_path)

        self.store.transition_to(StateEnum.WORK_PACKAGE)
        self.store.set_data("work_package_path", str(wp_path))

        await self.emit_event(
            event_type=EventType.WORKPACKAGE_CREATED,
            payload={"work_package_path": str(wp_path)},
            correlation_id=event.correlation_id,
        )
```

#### 15.2.3 Developer Agent (`agents/core/developer_agent.py`)

```python
from pathlib import Path
from agents.prompts import DEVELOPER_SYSTEM_PROMPT
from contracts.events.base_event import BaseEvent, EventType
from contracts.work_package import WorkPackage
from kernel.contracts.serializer import ContractSerializer
from kernel.state.states import StateEnum
from sdk.base_agent import BaseAgentSDK


class DeveloperAgent(BaseAgentSDK):

    def register_subscriptions(self) -> None:
        self.bus.subscribe(
            EventType.SPRINT_PLANNING_APPROVED, self.handle_event
        )
        self.bus.subscribe(EventType.TESTS_FAILED, self.handle_event)

    async def process_event(self, event: BaseEvent) -> None:
        if self.store.current_state != StateEnum.DEVELOPMENT:
            self.store.transition_to(StateEnum.DEVELOPMENT)

        wp_path = Path(
            self.store.get_data("work_package_path")
            or event.payload.get("work_package_path", "")
        )
        wp = ContractSerializer.load_yaml(wp_path, WorkPackage)

        prompt = f"Készíts kódot ehhez a feladathoz: {wp.goal}"
        if event.event_type == EventType.TESTS_FAILED:
            stderr = event.payload.get("stderr", "")
            prompt += f"\nAz előző teszt elbukott a következő hibával:\n{stderr}\nJavítsd a kódot!"

        code_response = await self.provider.generate_response(
            prompt, DEVELOPER_SYSTEM_PROMPT
        )

        output_dir = wp_path.parent.parent / "src"
        output_dir.mkdir(parents=True, exist_ok=True)
        code_file = output_dir / "app.py"
        code_file.write_text(code_response, encoding="utf-8")

        await self.emit_event(
            event_type=EventType.DEVELOPMENT_COMPLETED,
            payload={
                "code_file": str(code_file),
                "modified_files": [str(code_file)],
            },
            correlation_id=event.correlation_id,
        )
```

#### 15.2.4 Discovery Agent (`agents/core/discovery_agent.py`)

```python
from pathlib import Path
from agents.prompts import DISCOVERY_SYSTEM_PROMPT
from contracts.codebase_snapshot import CodebaseSnapshot
from contracts.events.base_event import BaseEvent, EventType
from kernel.contracts.serializer import ContractSerializer
from sdk.base_agent import BaseAgentSDK


class DiscoveryAgent(BaseAgentSDK):

    def register_subscriptions(self) -> None:
        pass

    async def survey_codebase(self, project_path: Path) -> Path:
        readme_path = project_path / "README.md"
        readme_content = (
            readme_path.read_text(encoding="utf-8")
            if readme_path.exists()
            else "Nincs README."
        )

        prompt = f"Elemezd ezt a projekttárat: {project_path.name}\nREADME:\n{readme_content}"
        response = await self.provider.generate_response(
            prompt, DISCOVERY_SYSTEM_PROMPT
        )

        snapshot = CodebaseSnapshot(
            project_path=str(project_path.resolve()),
            languages=["python"],
            frameworks=["fastapi"],
            has_readme=readme_path.exists(),
        )

        snapshot_dir = project_path / ".ai-sd-os"
        snapshot_path = snapshot_dir / "CODEBASE_SNAPSHOT.yaml"
        ContractSerializer.save_yaml(snapshot, snapshot_path)

        await self.emit_event(
            event_type=EventType.CODEBASE_SURVEYED,
            payload={"snapshot_path": str(snapshot_path)},
            correlation_id="discovery_manual",
        )
        return snapshot_path

    async def process_event(self, event: BaseEvent) -> None:
        pass
```

#### 15.2.5 Drift Detector Agent (`agents/core/drift_detector_agent.py`)

```python
import ast
from pathlib import Path
from contracts.events.base_event import BaseEvent, EventType
from sdk.base_agent import BaseAgentSDK


class DriftDetectorAgent(BaseAgentSDK):

    def register_subscriptions(self) -> None:
        self.bus.subscribe(
            EventType.DEVELOPMENT_COMPLETED, self.handle_event
        )

    async def process_event(self, event: BaseEvent) -> None:
        code_file = Path(event.payload["code_file"])
        if not code_file.exists():
            return

        code_content = code_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(code_content)
            if not tree.body:
                await self.emit_event(
                    event_type=EventType.DRIFT_DETECTED,
                    payload={"reason": "Üres AST struktúra."},
                    correlation_id=event.correlation_id,
                )
        except SyntaxError as err:
            await self.emit_event(
                event_type=EventType.DRIFT_DETECTED,
                payload={"reason": f"Szintaktikai hiba a kódban: {err}"},
                correlation_id=event.correlation_id,
            )
```

#### 15.2.6 Retrospective Collector (`agents/core/retrospective_collector.py`)

```python
from pathlib import Path
import yaml
from contracts.events.base_event import BaseEvent, EventType
from sdk.base_agent import BaseAgentSDK


class RetrospectiveCollector(BaseAgentSDK):

    def register_subscriptions(self) -> None:
        self.bus.subscribe(
            EventType.SPRINT_REVIEW_APPROVED, self.handle_event
        )

    async def process_event(self, event: BaseEvent) -> None:
        wp_path = Path(
            self.store.get_data("work_package_path")
            or "./.ai-sd-os/WORK_PACKAGE.yaml"
        )
        retro_dir = wp_path.parent / "retrospectives"
        retro_dir.mkdir(parents=True, exist_ok=True)

        retro_data = {
            "sprint_id": "SPRINT-001",
            "what_worked": "A kód és a tesztek elsőre lefutottak.",
            "what_failed": "Nincs észlelt hiba.",
            "carry_forward_note": "Folytasd a tiszta architektúra követését.",
            "retry_count": 0,
        }

        retro_file = retro_dir / "SPRINT-001.yaml"
        retro_file.write_text(
            yaml.dump(retro_data, sort_keys=False), encoding="utf-8"
        )

        await self.emit_event(
            event_type=EventType.RETROSPECTIVE_RECORDED,
            payload={"retro_file": str(retro_file)},
            correlation_id=event.correlation_id,
        )
```

### 15.3 Runtime Modul (`runtime/`)

#### 15.3.1 Artefaktum Regiszter (`runtime/artifacts.py`)

```python
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ArtifactReference(BaseModel):
    artifact_id: str
    artifact_type: str
    path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactRegistry(BaseModel):
    artifacts: List[ArtifactReference] = Field(default_factory=list)

    def register(
        self,
        artifact_id: str,
        artifact_type: str,
        path: Path,
        metadata: Dict[str, Any] | None = None,
    ) -> ArtifactReference:
        ref = ArtifactReference(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            path=str(path.resolve()),
            metadata=metadata or {},
        )
        self.artifacts.append(ref)
        return ref
```

#### 15.3.2 Test Runner Agent (`runtime/test_runner.py`)

```python
from pathlib import Path
from contracts.events.base_event import BaseEvent, EventType
from kernel.state.states import StateEnum
from runtime.sandbox import DockerSandbox
from sdk.base_agent import BaseAgentSDK


class TestRunnerAgent(BaseAgentSDK):

    def __init__(
        self,
        agent_id: str,
        bus,
        store,
        provider,
        sandbox: DockerSandbox | None = None,
    ):
        super().__init__(agent_id, bus, store, provider)
        self.sandbox = sandbox or DockerSandbox()
        self.retry_count = 0

    def register_subscriptions(self) -> None:
        self.bus.subscribe(EventType.DEVELOPMENT_COMPLETED, self.handle_event)

    async def process_event(self, event: BaseEvent) -> None:
        self.store.transition_to(StateEnum.TEST)

        code_file_path = Path(event.payload["code_file"])
        workspace_dir = code_file_path.parent.parent

        command = "python -m pytest"
        cmd_result = self.sandbox.execute_in_workspace(workspace_dir, command)

        test_payload = {
            "workspace": str(workspace_dir),
            "exit_code": cmd_result.exit_code,
            "stdout": cmd_result.stdout,
            "stderr": cmd_result.stderr,
            "retry_count": self.retry_count,
            "max_retries": 3,
        }

        if cmd_result.exit_code == 0:
            self.retry_count = 0
            await self.emit_event(
                event_type=EventType.TESTS_PASSED,
                payload=test_payload,
                correlation_id=event.correlation_id,
            )
        else:
            self.retry_count += 1
            test_payload["retry_count"] = self.retry_count
            await self.emit_event(
                event_type=EventType.TESTS_FAILED,
                payload=test_payload,
                correlation_id=event.correlation_id,
            )
```

#### 15.3.3 Git Driver (`runtime/git_driver.py`)

```python
import subprocess
from pathlib import Path


class GitDriver:

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir

    def _run_git(self, args: list[str]) -> tuple[int, str]:
        cmd = ["git"] + args
        res = subprocess.run(
            cmd, cwd=self.workspace_dir, capture_output=True, text=True
        )
        return res.returncode, res.stdout + res.stderr

    def init_repository(self) -> bool:
        code, _ = self._run_git(["init"])
        if code == 0:
            self._run_git(["config", "user.name", "AI-SD-OS Bot"])
            self._run_git(["config", "user.email", "bot@ai-sd-os.local"])
        return code == 0

    def commit_changes(self, message: str) -> bool:
        self._run_git(["add", "."])
        code, _ = self._run_git(["commit", "-m", message])
        return code == 0
```

### 15.4 Workspace, Security, Planning és Lessons Modulok

#### 15.4.1 Project Detector (`workspace/project_detector.py`)

```python
from pathlib import Path
from typing import List
from pydantic import BaseModel


class ProjectHandle(BaseModel):
    project_path: str
    state_file: str
    is_active: bool = True

    @classmethod
    def from_state(cls, state_file: Path):
        return cls(
            project_path=str(state_file.parent.parent.resolve()),
            state_file=str(state_file.resolve()),
        )


def detect_project(cwd: Path) -> ProjectHandle | None:
    state_file = cwd / ".ai-sd-os" / "state.json"
    if state_file.exists():
        return ProjectHandle.from_state(state_file)
    return None


def list_projects(
    workspace_root: Path, motor_dir: Path
) -> List[ProjectHandle]:
    handles = []
    for d in workspace_root.iterdir():
        if d.is_dir() and d.resolve() != motor_dir.resolve():
            state_file = d / ".ai-sd-os" / "state.json"
            if state_file.exists():
                handles.append(ProjectHandle.from_state(state_file))
    return handles
```

#### 15.4.2 Secret Scanner (`security/secret_scanner.py`)

```python
import re
from pathlib import Path
from typing import List


class SecretScanner:
    SECRET_PATTERNS = [
        r"sk-ant-[a-zA-Z0-9]{32,}",
        r"sk-[a-zA-Z0-9]{32,}",
        r"AKIA[0-9A-Z]{16}",
    ]

    @classmethod
    def scan_file(cls, filepath: Path) -> List[str]:
        if not filepath.exists() or not filepath.is_file():
            return []
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        found = []
        for pattern in cls.SECRET_PATTERNS:
            if re.search(pattern, content):
                found.append(
                    f"Hardcode-olt titok észlelve a fájlban: {filepath.name}"
                )
        return found
```

#### 15.4.3 Jogosultságkezelő (`security/permission_manager.py`)

```python
from pathlib import Path
from typing import List


class PermissionManager:

    @staticmethod
    def is_path_allowed(target_path: Path, allowed_paths: List[str]) -> bool:
        resolved_target = target_path.resolve()
        for allowed in allowed_paths:
            resolved_allowed = Path(allowed).resolve()
            if (
                resolved_target == resolved_allowed
                or resolved_allowed in resolved_target.parents
            ):
                return True
        return False
```

#### 15.4.4 CLI Planner (`planning/cli_planner.py`)

```python
from contracts.spec_formal import RequirementItem, SpecFormal


class CLIPlanner:

    @staticmethod
    def interactive_survey() -> SpecFormal:
        print("\n=== AI-SD-OS INTERAKTÍV PROJEKT TERVEZŐ ===")
        name = input("Projekt neve: ").strip() or "Demo Project"
        goal = (
            input("Projekt fő célja: ").strip()
            or "Demo FastAPI alkalmazás tesztekkel"
        )

        return SpecFormal(
            project_name=name,
            project_goal=goal,
            tech_stack=["python", "fastapi"],
            requirements=[
                RequirementItem(
                    id="FR-001",
                    title="Alap logika implementálása",
                    description="Összeadás függvény megírása",
                    priority="HIGH",
                )
            ],
        )
```

#### 15.4.5 Lessons Aggregator (`lessons/aggregator.py`)

```python
from pathlib import Path
import yaml


class LessonsAggregator:

    @staticmethod
    def aggregate_lesson(
        engine_dir: Path, pattern: str, project_name: str
    ) -> None:
        lessons_file = engine_dir / "lessons" / "lessons_learned.yaml"
        lessons_file.parent.mkdir(parents=True, exist_ok=True)

        data = {"entries": []}
        if lessons_file.exists():
            data = (
                yaml.safe_load(lessons_file.read_text(encoding="utf-8"))
                or {"entries": []}
            )

        data["entries"].append(
            {
                "pattern": pattern,
                "occurrences": 1,
                "projects": [project_name],
                "status": "PENDING_HUMAN_REVIEW",
            }
        )

        lessons_file.write_text(
            yaml.dump(data, sort_keys=False), encoding="utf-8"
        )
```

### 15.5 Fő Indító Script és Golden Path Teszt

#### 15.5.1 `main.py`

```python
import asyncio
from pathlib import Path
from agents.core.architect_agent import ArchitectAgent
from agents.core.developer_agent import DeveloperAgent
from contracts.events.base_event import BaseEvent, EventType
from contracts.spec_formal import RequirementItem, SpecFormal
from kernel.contracts.serializer import ContractSerializer
from kernel.event_bus.bus import EventBus
from kernel.hitl.gate_manager import HITLGateManager
from kernel.ledger.ledger_chain import LedgerChain
from kernel.state.states import StateEnum
from kernel.state.state_store import StateStore
from kernel.system.config import KernelConfig
from runtime.git_driver import GitDriver
from runtime.sandbox import DockerSandbox
from runtime.test_runner import TestRunnerAgent
from sdk.provider_adapter import MockProviderAdapter
from workspace.project_detector import detect_project


async def run_pipeline(project_dir: Path):
    print("=== AI-SD-OS V6.1.0 ENTERPRISE FACTORY RUNTIME ===")

    constitution_path = Path("kernel/system/SYSTEM_CONSTITUTION.md")
    constitution_text = (
        constitution_path.read_text(encoding="utf-8")
        if constitution_path.exists()
        else "CONSTITUTION STUB"
    )
    config = KernelConfig(
        constitution_text=constitution_text,
        storage_dir=project_dir / ".ai-sd-os" / "runtime",
    )

    bus = EventBus()
    store = StateStore()
    provider = MockProviderAdapter()
    sandbox = DockerSandbox()
    ledger = LedgerChain(project_dir / ".ai-sd-os" / "ledger" / "chain.json")

    git = GitDriver(project_dir)
    git.init_repository()

    architect = ArchitectAgent("architect-01", bus, store, provider)
    developer = DeveloperAgent("developer-01", bus, store, provider)
    test_runner = TestRunnerAgent(
        "test-runner-01", bus, store, provider, sandbox
    )
    gate_manager = HITLGateManager(bus, store)

    store.transition_to(StateEnum.DISCOVERY)
    store.transition_to(StateEnum.SPEC)

    spec = SpecFormal(
        project_name="FastAPI Todo API",
        project_goal="Create a lightweight FastAPI Todo application with Pytest verification",
        tech_stack=["python", "fastapi"],
        requirements=[
            RequirementItem(
                id="FR-001",
                title="Math adder logic",
                description="Implement math adder function as core logic",
                priority="HIGH",
            )
        ],
    )
    spec_dir = project_dir / ".ai-sd-os"
    spec_path = spec_dir / "SPEC_FORMAL.yaml"
    ContractSerializer.save_yaml(spec, spec_path)

    tests_dir = project_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_app.py").write_text(
        "from src.app import add\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )

    pipeline_finished = asyncio.Event()

    async def on_sprint_planning_proposed(event: BaseEvent):
        ledger.append_event(event)
        # Automatikus szimulált jóváhagyás az MVP golden path futtatásához
        store.transition_to(StateEnum.DEVELOPMENT)
        await bus.publish(
            BaseEvent(
                event_type=EventType.SPRINT_PLANNING_APPROVED,
                sender_id="human_operator",
                correlation_id=event.correlation_id,
            )
        )

    async def on_sprint_review_requested(event: BaseEvent):
        ledger.append_event(event)
        print(
            f"[PIPELINE SUCCESS] Tests passed! Output: {event.payload.get('stdout', '')}"
        )
        git.commit_changes("feat: AI generated code verified by tests")
        store.transition_to(StateEnum.PR_CREATED)
        store.transition_to(StateEnum.RETROSPECTIVE)
        store.transition_to(StateEnum.DONE)
        pipeline_finished.set()

    bus.subscribe(
        EventType.SPRINT_PLANNING_PROPOSED, on_sprint_planning_proposed
    )
    bus.subscribe(
        EventType.SPRINT_REVIEW_REQUESTED, on_sprint_review_requested
    )

    await bus.start()
    print("[KERNEL] Emitting SPEC_CREATED event...")
    boot_event = BaseEvent(
        event_type=EventType.SPEC_CREATED,
        sender_id="main_bootstrap",
        payload={"spec_path": str(spec_path)},
    )
    ledger.append_event(boot_event)
    await bus.publish(boot_event)

    try:
        await asyncio.wait_for(pipeline_finished.wait(), timeout=30.0)
        print(f"[FINAL STATE] {store.current_state.value}")
        print(f"[LEDGER INTEGRITY] Valid: {ledger.verify_integrity()}")
    except asyncio.TimeoutError:
        print("[PIPELINE TIMEOUT] Pipeline did not complete in time.")
    finally:
        await bus.stop()


if __name__ == "__main__":
    cwd = Path.cwd()
    handle = detect_project(cwd)

    if handle:
        print(f"[AI-SD-OS] Project detected at: {handle.project_path}")
        asyncio.run(run_pipeline(Path(handle.project_path)))
    else:
        print(f"[AI-SD-OS] No project found in {cwd}. Initializing runtime.")
        asyncio.run(run_pipeline(cwd))
```

#### 15.5.2 `tests/test_golden_path.py`

```python
from pathlib import Path
import pytest
from main import run_pipeline


@pytest.mark.asyncio
async def test_full_golden_path_e2e(tmp_path: Path):
    project_dir = tmp_path / "demo_project"
    project_dir.mkdir(parents=True, exist_ok=True)

    await run_pipeline(project_dir)

    assert (project_dir / ".ai-sd-os" / "SPEC_FORMAL.yaml").exists()
    assert (project_dir / ".ai-sd-os" / "WORK_PACKAGE.yaml").exists()
    assert (project_dir / "src" / "app.py").exists()
    assert (project_dir / ".git").exists()
    assert (project_dir / ".ai-sd-os" / "ledger" / "chain.json").exists()
```

---

## Auditálási megjegyzés (V6.1.0 blueprint vs. tényleges kód)

A fenti 14–15. fejezetek egy **tervezési blueprint**-et rögzítenek, amit egy korábbi generálási munkamenet hozott létre. A repóban ténylegesen megvalósított kód (lásd `kernel/`, `contracts/`, `agents/`, `main.py`) egy ettől eltérő, önmagában konzisztens változat, amely `Event`/`EventType`/`ProjectState` elnevezéseket használ a blueprint `BaseEvent`/`StateEnum`/`StateStore` helyett, és directory-native `.ai-sd-os/state.json`-t egy külön memóriabeli `StateStore` objektum helyett. A tényleges kód 8/8 zöld teszttel fut.

A blueprint és a megvalósítás közötti — ebben a munkamenetben pótolt — legfontosabb eltérések:

- `kernel/ledger/` (kriptográfiai hash-lánc) hiányzott, most bekerült és be van kötve az `EventBus`-ba.
- `kernel/policy/policy_compiler.py` hiányzott — a `rules.yaml` / `security.yaml` / `execution.yaml` eddig nem volt semmihez sem kötve.
- `kernel/swarm/` (AST lock + orchestrator) hiányzott, most bekerült.
- `contracts/events/` réteg hiányzott — a payloadok eddig típusellenőrzés nélküli `Dict[str, Any]` mezők voltak.

A `kernel/checkpoint/checkpoint_manager.py`-ban egy szintaktikai hiba volt (`get_latest_checkpoint(()`), ami importáláskor `SyntaxError`-t dobott volna, ha bárhonnan importálja valaki — jelenleg semmi nem importálja, ezért nem bukott le a tesztekben. Ez is javításra került.
