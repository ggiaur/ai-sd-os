# A 3 provider részletesen — mikor melyiket, miért

Előbb egy státusz: **commitoltam és push-oltam a motor repóját GitHubra**
(`ce40f9a`), és beépítettem az automatikus push-ot a `GitDriver`-be minden
projekthez, amit a motor kezel (nem csak a motor saját repójához) — ez
mostantól minden sikeres sprint után lefut, ha van beállított `origin`
remote. A `previous_answer.md` mostantól garantáltan a motor saját
`write_answer()` függvényén keresztül rotálódik, és az időbélyeg mostantól
GMT+2-ben van (nem a szerver UTC idejében).

## Mi a "provider" egyáltalán?

A motor `AIProvider` interfésze (`sdk/provider_adapter.py`) egy csere-
szabvány: bármi implementálhatja, ami tud `generate()` (kódot írni),
`review()` (kódot ellenőrizni), `analyze()` (elemezni) és `embed()`
(vektorizálni). A `DeveloperAgent`/`TestRunner`/stb. sosem tudja, ÉPPEN
melyik implementáció fut mögötte — ez teszi lehetővé, hogy projektenként
más-más "motort" válassz a tényleges munkához.

## 1. `MockProviderAdapter` — amit ma, teszteléshez használunk

**Mi ez:** nincs mögötte semmilyen valódi AI. Egy Python regex kiolvassa a
promptból, milyen függvényt kell írni és mit kell visszaadnia, és
begépeli — determinisztikus, 0 másodperc, 0 Ft, nincs internet vagy API
kulcs szükséges hozzá.

**Előny:**
- **Villámgyors és ingyenes** — ezért fut le a teljes 66 tesztes suite 4
  másodperc alatt, API kulcs nélkül. Ez teszi lehetővé, hogy a CI (GitHub
  Actions) minden push-nál újra tudja futtatni az egészet, ingyen.
- **Determinisztikus** — mindig ugyanazt adja ugyanarra a bemenetre, ezért
  lehet rá red/green regressziós tesztet írni (pl.
  `test_verification_is_honest.py`), ami MINDIG ugyanúgy fut le, sosem
  "néha véletlenül máshogy viselkedik az LLM".

**Hátrány:** **nem valódi AI** — nem tud semmit, amit nem kódoltam bele
explicit szabályként. Éles projekten, valódi funkcióhoz **használhatatlan**,
csak fejlesztői/teszt célra való.

**Mikor ezt:** kizárólag a motor SAJÁT tesztjeihez, és amikor ki akarod
próbálni a pipeline vezérlését (állapotgép, HITL kapuk, git-flow) anélkül,
hogy AI-hívásokért fizetnél.

## 2. `AnthropicAdapter` — ma is létezik, de gyenge codegen-módban

**Mi ez:** egyetlen, "egylövéses" hívás a Claude API-nak
(`anthropic.AsyncAnthropic().messages.create()`). Küldünk egy szöveges
promptot, kapunk egy szöveges választ, amiből regex-szel kiszedjük a kódot.

**Előny:**
- **Egyszerű, gyors, olcsó** — egyetlen API-hívás work package-enként, nincs
  agentic loop overhead, alacsony latencia és token-fogyasztás.
- **Valódi AI** — ténylegesen a Claude modell dönt a kódról, nem egy fix
  szabály.
- **Könnyen skálázható** — sok kis work package-et párhuzamosan is el lehet
  intézni (a swarm-orchestrator pont erre való).

**Hátrány — ez a lényeg, amire rákérdeztél:**
- **Nincs fájlrendszer-hozzáférése.** Nem tudja megnézni a projekt többi
  fájlját, a meglévő kódstílust, a függőségeket — csak azt látja, amit a
  promptba beírunk neki kézzel.
- **Nem tud tesztet futtatni és a saját hibájából tanulni EGY híváson
  belül.** Ha rossz kódot ír, azt csak a MI `TestRunner`-ünk veszi észre
  utólag (ez működik, a retry-loop megoldja), de a modell maga nem lát
  visszajelzést menet közben — "vakon" ír egy próbálkozást.
- **Egy work package = egy fájl, egyszerű esetekre jó.** Ha egy funkció
  több fájlt érint (pl. backend endpoint + frontend hívás + migráció),
  ez az adapter nem tudja ezt egyben, koherensen megoldani — külön
  hívásokra kellene szétszabdalni, amiket nekünk kellene manuálisan
  összehangolni.

**Mikor ezt:** kis, jól körülhatárolt, egyfájlos feladatokhoz, ahol a
formális `SPEC_FORMAL`/`WorkPackage` már eleve minden szükséges infót
tartalmaz, és nincs szükség arra, hogy a modell "körülnézzen" a projektben.

## 3. `ClaudeCodeCLIAdapter` — amit javasoltam, MÉG NINCS megcsinálva

**Mi lenne ez:** a motor a `claude` CLI-t hívná meg subprocess-ként,
nem-interaktív módban (pl. `claude -p "<feladat leírása>" --output-format
json` jellegű hívással), ugyanazzal az agentic loop-pal, amit MOST is
használsz velem beszélgetve.

**Előny — miért különb, mint az #2:**
- **Fájlrendszer-hozzáférése van.** Ténylegesen be tudja olvasni a projekt
  meglévő kódját, stílusát, függőségeit, mielőtt írna — nem "vakon" dolgozik.
- **Tud iterálni EGY feladaton belül.** Meg tudja írni a kódot, le tudja
  futtatni rá a tesztet, ha bukik, saját maga javítja — mindezt egyetlen
  work package-en belül, mielőtt visszaadná az irányítást a mi
  `TestRunner`-ünknek. Ez ELVILEG kevesebb retry-kört jelentene a mi
  pipeline-unk szintjén, mert a hibák nagy részét a CLI már saját magában
  kiszűri.
- **Több fájlt érintő, komplex feladatokra alkalmas** — pont az, amire a
  #2-es adapter NEM jó.

**Hátrány:**
- **Lassabb és drágább work package-enként** — egy teljes agentic session
  (több tool-hívás, több oda-vissza a modellel) drágább és lassabb, mint
  egyetlen API-hívás. Egy triviális, egysoros funkcióhoz ez túlzás lenne.
- **Nehezebb determinisztikusan tesztelni** — a motor SAJÁT tesztjeihez
  (a 66-ból amit most futtatunk) ez nem helyettesítené a Mock-ot, mert
  minden CLI-hívás valódi, nem-determinisztikus AI-választ adna, API
  kulcsot igényelne, és lassítaná a CI-t. A Mock ezért MINDENKÉPP maradna,
  csak MÁSRA (a motor saját tesztelésére), nem az éles kódgenerálásra.
- **Process-kezelési komplexitás** — subprocess indítás, timeout-kezelés,
  jogosultsági módok (permission mode) beállítása, kimenet parse-olása —
  ez tényleges implementációs munka, nem triviális "csak hívjuk meg".

**Mikor ezt:** komplex, több fájlt érintő, valódi projekt-kontextust igénylő
munkákhoz — pontosan az, amit a webarchívumon vagy bármilyen éles
projekten csinálnál, ha egyszer tényleg rááengeded a motort.

## Az ajánlásom lényege

A három NEM egymást kizáró, hanem **egymást kiegészítő** eszköz, projektenként
és feladatonként választható (`KernelConfig`-ban egy `provider` mező):
- `Mock` → csak a motor saját tesztjeihez, sosem éles munkához.
- `Anthropic` → gyors, olcsó, kis egyfájlos feladatokhoz.
- `ClaudeCodeCLI` → komplex, több fájlt érintő, valódi projekt-kontextust
  igénylő munkákhoz (ez lenne az, amit egy éles projektnél, pl. a
  webarchívumnál használnál).

**Ha szeretnéd, hogy megcsináljam a `ClaudeCodeCLIAdapter`-t, szólj — jelezd
külön, mert ez egy új fejlesztési kör lenne, nem ráértő "unatkozom" munka.**

---
_Generálva: 2026-07-31 07:50:24 +0200_
