# Changelog

Ez a motor (`ai-sd-os/`) saját kiadási naplója — nem keverendő a motorral
generált projektek saját `CHANGELOG.md`-jével (azt a `GitDriver` írja, a
célprojekt könyvtárában).

> **Megjegyzés a korábbi tartalomra:** ez a fájl korábban 90+ egymást szó
> szerint ismétlő `[SPRINT-001] - Implement features: FR-001` bejegyzést
> tartalmazott. Ennek oka: a `GitDriver.update_changelog` feltétel nélkül
> appendelt minden pipeline-futáson, függetlenül attól, hogy történt-e valódi
> változás, és a motor egy ponton saját magán futtatta a projekt-pipeline-t
> (lásd `main.py` self-run védelme). Mindkét gyökérokot javítottuk — lásd
> lent —, a fájl itt egy tiszta állapotból folytatódik.

## [Unreleased]

### Fixed
- A `DeveloperAgent` eddig hardcode-olt sablonnal írt egyszerre implementációt
  és hozzá tautologikus, saját magára hivatkozó tesztet — a `TESTS_PASSED`
  emiatt semmit sem bizonyított. Az `ArchitectAgent` most a specifikációból
  írja meg az elfogadási teszteket, mielőtt a fejlesztés elkezdődne
  (spec-first / TDD), és a `DeveloperAgent` ténylegesen az AI providert hívja
  a kódgeneráláshoz.
- A `TestRunnerAgent` coverage-mapping ellenőrzése eddig csak szöveges
  egyezést nézett a tesztfájlban; most valódi `pytest -v` PASSED node-id-kat
  követel meg, és üres `coverage_mapping`-et automatikus bukásnak tekint.
- A `GitDriver` feltétel nélkül commitolt és bővítette a CHANGELOG-ot minden
  futáson — ez okozta a duplikált bejegyzéseket. Most csak akkor, ha van
  valódi diff.
- `main.py` a pipeline tényleges kimenetétől függetlenül DONE-ra állította a
  projekt állapotát; most a `PIPELINE_BLOCKED` eseményt figyeli, és csak
  valódi sikeres lezárás esetén jelez DONE-t.
- Pydantic és asyncio deprecation warningok javítva
  (`workspace/project_detector.py`, `kernel/event_bus/bus.py`).

### Added
- A motor elutasítja a futtatást, ha a munkakönyvtár a motor saját
  könyvtára — ez akadályozza meg, hogy a motor újra önmagán fusson (ez volt a
  fenti CHANGELOG/commit-spam gyökéroka).
- Egységes, egy helyen tárolt szemantikus verzió (`kernel/system/version.py`),
  amit a CLI banner is használ (korábban a banner "V5"-öt, a README
  "V6.1.0"-t írt).
- `answer.md` / `previous_answer.md` — a pipeline BLOCKED/DONE kimenete
  markdown fájlba is íródik, terminál-korlátozott környezetekhez.
- `.github/workflows/ci.yml` — pytest fut minden push/PR-en.
- `CONTRIBUTING.md` — a motor saját (kernel-szintű) fejlesztésének szabályai.
- Regressziós tesztek, amik bizonyítják, hogy a verifikáció ténylegesen tud
  hibát fogni (`tests/test_verification_is_honest.py`).

## [6.1.0] és korábbi

A korábbi, `SPRINT-001`-hez kötött duplikált bejegyzések itt törölve lettek —
ezek egy hibás, tartalom nélküli automatizált commit-ciklus termékei voltak,
nem valódi kiadási információ. A motor tényleges fejlesztési története a git
historyban követhető (`git log --oneline`).
