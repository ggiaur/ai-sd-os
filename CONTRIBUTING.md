# Hozzájárulás a motorhoz (`ai-sd-os/`)

Ez a dokumentum a **motor saját** fejlesztésére vonatkozik — nem a motorral
generált projektekre. A motor és a generált projektek soha nem élnek ugyanabban
a Git repóban (lásd README, "Kritikus Tervezési Alapelvek"); `main.py`
elutasítja a futtatást, ha a munkakönyvtár a motor saját könyvtára.

## Az alapszabály (Alkotmány 8. törvénye)

> INVARIANT_KERNEL_IMMUTABILITY: A motor kernel-szintű változtatása (prompt,
> agent, schema) soha nem automatikus — az mindig külön emberi review-t és
> verzióemelést igényel.

Ez a gyakorlatban a következőt jelenti minden PR-re, amely a `kernel/`,
`agents/`, `contracts/`, `sdk/`, `runtime/`, `security/` mappák bármelyikét
módosítja:

1. **A tesztek zöldek maradnak.** `python3 -m pytest -q` a PR benyújtása előtt.
   Ha a változtatás új viselkedést vezet be (pl. új invariáns, új ellenőrzés),
   ahhoz **új teszt is tartozik**, ami megbukna a régi kód mellett — ne csak a
   régi tesztek maradjanak zöldek, hanem legyen bizonyíték, hogy az új
   viselkedés ténylegesen működik. (Lásd `tests/test_verification_is_honest.py`
   mintaként: red/green pár, ami bizonyítja, hogy egy ellenőrzés valóban
   különbséget tesz helyes és hibás eset között.)
2. **Verzióemelés.** `kernel/system/version.py` `__version__` mezője
   semver szerint emelkedik:
   - PATCH: bugfix, nincs viselkedésváltozás kifelé (pl. a GitDriver
     idempotencia-javítása).
   - MINOR: új, visszafelé kompatibilis képesség (pl. új ágens, új esemény
     típus, amit a régi projektek figyelmen kívül hagyhatnak).
   - MAJOR: séma- vagy állapotgép-változás, ami a `.ai-sd-os/` alatti meglévő
     projekt-állapotokat inkompatibilissé teszi. Ehhez `MIGRATION.md`
     bejegyzés is kell.
3. **CHANGELOG.md bejegyzés** a motor gyökerében — ez a motor saját kiadási
   naplója, nem keverendő a generált projektek saját `CHANGELOG.md`-jével
   (amit a `GitDriver` ír, a projekt könyvtárában).
4. **Emberi review.** Ágens nem mergelheti a saját kernel-szintű
   változtatását automatikusan.

## Mit jelent ez a gyakorlatban egy új ágens vagy esemény hozzáadásakor

- Ha új `EventType`-ot vezetsz be, regisztrálj hozzá payload sémát is a
  `contracts/events/registry.py`-ban — validálatlan event type csak warningot
  kap, nem hibát, szándékosan (lásd `EventBus.publish`), de ez nem felmentés
  az alól, hogy legyen sémája.
- Ha egy ágens új módon hívja a `provider`-t (LLM), és a `MockProviderAdapter`
  nem tudja értelmesen szimulálni, bővítsd a mockot is — a motor saját
  tesztjeinek mock módban kell futniuk, API kulcs nélkül.
- Ha egy `Contract` (Pydantic modell) mezőt kötelezővé teszel (mint pl. a
  `TaskItem.expected_output`), az minden meglévő hívási helyet érint — futtasd
  végig a teljes tesztkészletet, ne csak az érintett fájlt.

## Amit SOHA nem szabad tenni

- Ne futtasd a `main.py`-t a motor saját könyvtárában (ez ellen most már
  explicit védelem is van, de a szabály attól még érvényes).
- Ne commitolj `__pycache__/`, `.pyc` fájlokat.
- Ne bővítsd a README-t olyan modullal, ami nem létezik a kódban — ha
  tervezett, jelöld egyértelműen "Roadmap"-ként.
