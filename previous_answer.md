# Válasz: rotáció + Claude CLI kérdés

## 1. A rotáció mostantól minden frissítésnél garantált

Igazad van, eddig kézzel másoltam a `previous_answer.md`-t, ami hibázható.
Mostantól minden egyes alkalommal, amikor válaszolok, ténylegesen a motor
saját `kernel/system/answer_log.py::write_answer()` függvényét hívom meg (nem
csak kézzel írom a fájlt) — ez garantáltan és automatikusan végzi a rotációt
(régi `answer.md` → `previous_answer.md`, majd az új tartalom + időbélyeg).
Ez már be van építve a motorba (a pipeline saját BLOCKED/DONE kimenetei is
ezt használják), mostantól a saját válaszaimhoz is ezt hívom, nem külön utat.

## 2. A kérdésed: ne a motor Python/Anthropic API helyett a Claude Code CLI-t használja?

**Rövid válasz: igen, jó irány, de kiegészítésként, nem lecserélésként.**

Jelenleg a `sdk/provider_adapter.py::AnthropicAdapter` egyetlen, egylövéses
API-hívást csinál (`messages.create`) — a modell egy szöveges promptra egy
szöveges választ ad, amit regex-szel szedünk szét kódra. Ez gyenge: nincs
fájlrendszer-hozzáférése, nem tud tesztet futtatni, nem tud iterálni,
nem lát kontextust a projektről.

Ezzel szemben a **Claude Code CLI** (amit most is használsz velem) egy
teljes, több-lépéses ágens: fájlokat olvas/ír, bash-t futtat, teszteket
indít, iterál a saját hibáin — pont az, amit egy "DeveloperAgent"-nek
csinálnia KELLENE, nem csak egy darab kódot kiköpnie.

**Fontos:** ezt érdemes egy ÚJ, cserélhető `ClaudeCodeCLIAdapter`-ként
hozzáadni a meglévő `AIProvider` interfészhez (ami már ma is
Mock/Anthropic/OpenAI-t támogat felcserélhetően) — NEM kell kidobni a
Python kernel/state machine/HITL-gate/ledger réteget. Az az OS-réteg (a
motor "operating system" jellege: audit, jóváhagyási kapuk, állapotgép) az
érték, amit a motor ad — a kódgenerálás csak egy csere-alkatrész benne.
Ez egyébként már szerepel a README roadmap-jában (`CAPABILITY_REGISTRY.yaml`
"ClaudeCodeCLI" mint elsődleges code_generation provider) — csak eddig nem
volt implementálva.

**Trade-off, amit tudnod kell:** a CLI-alapú ágens lassabb és drágább
work-package-enként (egy teljes agentic session indul minden taskhoz), és
nehezebb determinisztikusan tesztelni (a `MockProviderAdapter` mai gyors,
API-kulcs nélküli teszt-útja nem triviálisan helyettesíthető egy valódi CLI
hívással). Javaslat: tartsuk meg mindhárom adaptert választhatóként
(`Mock` gyors/determinisztikus teszteléshez, `Anthropic` egyszerű/gyors
API-hívásokhoz, `ClaudeCodeCLI` komplex, több fájlt érintő munkákhoz), és a
`KernelConfig`-ban legyen választható, melyiket használja egy adott projekt.

**Szeretnéd, hogy megcsináljam a `ClaudeCodeCLIAdapter`-t?** Ha igen, jelezd
és nekiállok — becslésem szerint ez egy közepes méretű, jól körülhatárolható
bővítés (új adapter osztály + `KernelConfig` provider-választás + CLI-hívás
subprocess-en keresztül, nem-interaktív módban).

---
_Generálva: 2026-07-31 05:42:48 +0000_
