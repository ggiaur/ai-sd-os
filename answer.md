# 4 kérdésed — sorban

## 1. "Ez legyen a te mérlegelésed és a tesztek finomítsák" — megcsináltam

A `DeveloperAgent` mostantól, ha egy WorkPackage-et a heurisztika
"egyszerűnek" ítélt (Haiku-ra küldte), de az ELSŐ próbálkozás elbukott a
verifikáción, ezt **rögzíti** a motor már meglévő "lessons learned"
rendszerében (`lessons/lessons_learned.yaml`, `status:
PENDING_HUMAN_REVIEW`) — pont úgy, ahogy a motor Alkotmánya előírja: a
kernel-viselkedést (itt: a `sdk/model_selector.py` küszöbértékeit) **soha
nem hangolja automatikusan**, csak bizonyítékot gyűjt, amit egy ember (vagy
én, ha rákérdezel) tud felhasználni a döntéshez. **93/93 teszt zöld**,
2 új teszt igazolja, hogy ez a napló-bejegyzés ténylegesen megtörténik,
commitolva/pusholva (`c7d784a`).

Vagyis: ha rendszeresen rossz döntéseket látsz, nem kell "szólnod" — a motor
saját maga gyűjti a bizonyítékot, és ha átnézed a `lessons_learned.yaml`-t
(vagy megkérsz, hogy nézzem át), onnantól tudatosan finomíthatjuk a
küszöböt, nem találgatásból.

## 2. Mikor indulhatunk másik projekten? — Fontos tisztázás előbb

**Két teljesen különböző üzemmódról van szó, és eddig csak az egyiket
csináltuk:**

- **A) Amit EDDIG csináltunk (ezen a beszélgetésen keresztül):** ÉN,
  Claude Code, közvetlenül dolgoztam a motor kódján — olvastam, írtam,
  teszteltem, commitoltam, veled egyeztetve minden lépésnél. Ez NEM az
  ai-sd-os motor pipeline-ja — ez simán "veled dolgozom, mint fejlesztő".
- **B) Az ai-sd-os motor ÖNÁLLÓ pipeline-ja** (`main.py`): ez egy
  automatizált rendszer, ami emberi jóváhagyási kapukkal (HITL gates) fut,
  saját ágensekkel generál kódot, saját maga futtatja a teszteket és
  commitol/pushol — **ezt még sosem próbáltuk ki éles (nem mock) módban.**

A B) mód értéke ott van, amikor **felügyelet nélkül, autonóm módon** akarod,
hogy dolgozzon (pl. "fusson éjszaka, reggelre legyen kész X"). Ha viszont
most, veled beszélgetve akarsz egy funkciót megcsináltatni egy projekten —
azt egyszerűen ÉN direktben megcsinálom, ahogy eddig is, gyorsabb és
átláthatóbb, mint a pipeline-on keresztül.

**Javaslatom az induláshoz, ha a B) módot (önálló pipeline) akarod
kipróbálni:**
1. NE a webarchívumon kezdjük — az egy komplex, valós, értékes projekt.
   Válasszunk egy kis, alacsony téttel járó, jól körülhatárolt feladatot
   (akár egy vadonatúj, üres projekt, akár a webarchívum egy triviális,
   elszigetelt részfeladata).
2. Először **csak a Discovery/SPEC szakaszig** fusson (`auto_approve=False`,
   valós API-kulccsal, de a Sprint Planning kapunál MEGÁLLUNK, átnézzük,
   mit tervez, mielőtt bármit írna).
3. Csak ez után engedjük tovább a fejlesztési fázisba.

## 3. A könyvtár-kérdés — nem számít, amit gondoltál

**Nem kell átjelentkezned semmilyen mappába, és nekem sem kell onnan
indulnom.** Ennek az oka egyszerű: a motor `main.py`-ja azt nézi, hogy MELYIK
KÖNYVTÁRBAN FUT ÉPPEN A PARANCS (a `cd project && python3 main.py`
mintában) — ez teljesen független attól, hogy a Claude Code munkamenetem
honnan indult. Bizonyíték: ebben a beszélgetésben már dolgoztam a
webarchívumon, a demo-project-en, az existing-demo-n — mindegyik más
könyvtár, anélkül hogy újra kellett volna indítanod engem onnan. Egyszerűen
`cd`-elek oda, ahova kell, parancsonként.

Az egyetlen dolog, aminek ELVILEG jelentősége LEHETNE: ha a Claude Code
saját fájlhozzáférési engedélyei szigorúan a indítási könyvtárra lennének
korlátozva. De ezt már cáfolta a gyakorlat — hozzáfértem a
`/srv/projects/webarchivum`-hoz simán, pedig a munkamenet nem onnan indult.
**Tehát: nem kell átjelentkezned, nyugodtan maradhatsz ott, ahol most vagy.**

## 4. Gemini (vagy más provider) integrálása kvóta-kiesés esetére

**Igen, technikailag egyszerű** — az `AIProvider` interfész pont erre való
(lásd a korábbi részletes magyarázatot arról, "mi az a provider"). Egy
`GeminiAdapter` ugyanúgy megírható, mint az `OpenAIAdapter` (ami ma még csak
váz, de a minta megvan).

**Amit érdemes hozzá építeni, ha csináljuk:** nem elég egy önálló
`GeminiAdapter` — kell egy **`FallbackProviderAdapter`** wrapper is, ami:
1. Megpróbálja a fő providert (pl. Anthropic).
2. Ha kvóta/rate-limit hibát kap (nem akármilyen hibát — konkrétan
   erőforrás-kimerülést), automatikusan átvált a másodlagos providerre
   (pl. Gemini).
3. Ezt logolja (és a fenti lessons-learned mechanizmussal jelzi, hogy
   fallback történt — átláthatóság, nem csendes csere).

Ez egy VALÓDI, önálló fejlesztési kör lenne (új függőség — Gemini SDK —,
API-kulcs-kezelés, hibatípus-felismerés kvóta vs. egyéb hiba
megkülönböztetésére). Nincs itt Gemini API-kulcsom, hogy éles tesztet
futtassak rajta, de mock-olt teszteléssel (ahogy a ClaudeCodeCLIAdapter-nél
is tettem) meg tudom írni és bizonyítani, hogy a fallback-logika helyesen
működik.

**Kérdés hozzád:** ez most jöjjön, vagy előbb a 2. pontban javasolt "kis,
alacsony téttel járó éles próba" a pipeline-nal? Mindkettő értelmes
következő lépés, de mindkettőt egyszerre nem érdemes csinálni.

---
_Generálva: 2026-07-31 08:31:36 +0200_
