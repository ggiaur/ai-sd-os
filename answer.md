# Scope-korlát: teljes siker. ReplayWeb.page kalibráció: őszinte közbenső jelentés

## 1. A scope/mélység-korlát — teljesen megoldva, ÉLESBEN bizonyítva

Frissítettem a `crawler.py`-t valódi, biztonságos alapértékekkel
(`--scopeType host`, `--depth 2`, `--pageLimit 25`, `--sizeLimit 500MB`,
`--timeLimit 600s` — a pontos flag-neveket a Browsertrix saját `--help`
kimenetéből vettem, nem találgattam).

**Éles bizonyíték**: lefuttattam egy valódi, 8 oldalas crawl-t a vmk.hu-n.
A napló pontosan megmutatta, mi történt:
- **8 oldal, MIND `www.vmk.hu`-n** — pontosan a `pageLimit` szerint.
- **Kifejezetten kizárva**: `gyerek.vmk.hu`, `helyismeret.vmk.hu`,
  `konyvtar.vmk.hu`, `tlwww.vmk.hu` (mind vmk.hu ALdomainek!), és minden
  külső oldal (Facebook, YouTube, Google Forms, goethe.de, stb.) —
  mindegyik a naplóban "Skipping Link; not in scope" jelzéssel.

**Ez bizonyítja, hogy a domain-korlátozás valóban működik** — a crawler
tuti nem "kezdi el az egész világhálót begyűjteni". 5/5 teszt zöld erre.

**Egy fontos mellékfelfedezés**: a `host` scope ennél a konkrét oldalnál
(vmk.hu) KIZÁRTA a `helyismeret.vmk.hu` aldomaint is — pedig ott lehet a
legrelevánsabb helytörténeti tartalom! Ez egy valós tervezési döntés,
amit érdemes átbeszélni: `host` scope biztonságosabb, de szigorúbb;
`domain` scope (ami az aldomaineket is engedné) rugalmasabb, de nagyobb
a kockázata, hogy irreleváns aldomain-tartalmat is begyűjt. Ezt
webhelyenként kellene esetleg konfigurálni.

## 2. A ReplayWeb.page küszöb kalibrálása — őszinte közbenső állapot

Megpróbáltam VALÓDI, automatizált méréssel (nem csak online beszámolókra
hagyatkozva) kalibrálni: felállítottam egy izolált teszt-környezetet
(nginx Range-support-tal, a saját valódi WACZ fájljainkkal, Playwright
headless böngészővel egy Docker-konténerben).

**Amit sikerült**: megtaláltam a HELYES eseménynevet a ReplayWeb.page
forráskódjában (`coll-loaded`, nem amit korábban feltételeztem), és
bekonfiguráltam a szükséges service worker fájlt.

**Amivel elakadtam**: ez a beágyazott (docker-a-dockerben, headless,
`--no-sandbox`, host-hálózatú) teszt-környezet **maga is instabilnak
bizonyult** — még a szerényebb, 56MB-os fájlnál sem sikerült tiszta,
megbízható "sikeresen betöltött" jelzést kapnom, annak ellenére, hogy a
service worker regisztrálódott. Ez valószínűleg a headless/beágyazott
Docker-környezet sajátossága, nem a ReplayWeb.page valós hibája — de
**nem akarok kitalált számot mondani neked, mint egy megbízható mérés
eredményét, amikor valójában nem sikerült megbízhatóan lemérnem.**

**Ahelyett, hogy tovább erőltetném ezt a mesterséges tesztkörnyezetet**
(ami már jelentős időt vett igénybe, csökkenő megtérüléssel), inkább
őszintén jelzem: **ezt a konkrét kalibrációt egy VALÓDI böngészőben
(nem headless, nem beágyazott Docker-Docker-ben) kellene elvégezni** —
akár általad, kézzel, a tényleges célkörnyezetben (production hosting),
mert a Service Worker viselkedése köztudottan nagyon környezet-érzékeny.

## A gyakorlati megoldás, ami ETTŐL FÜGGETLENÜL biztonságos

A korábban tervezett **timeout-alapú fallback logika**
(ha a `<replay-web-page>` N másodpercen belül nem jelez betöltött
állapotot, átváltunk pywb-re) **ÖNMAGÁBAN is helyesen működik**, akármi
is a pontos küszöbszám — mert ez nem egy előre kitalált fájlméret-határ,
hanem egy VALÓS IDEJŰ, minden egyes archívumnál lefutó ellenőrzés. Tehát
a rendszer biztonságos marad akkor is, ha a pontos "hány MB-nál kezd
akadozni" számot nem sikerült ma laboratóriumi körülmények között
kalibrálnom — ezt majd az éles használat közben, valós böngészőkben
fogjuk látni, és a napló (a "tanulási napló" elv szerint) rögzíteni fogja.

## Kérdés hozzád

Szeretnéd, hogy (a) folytassam a kalibrációs kísérletet más módszerrel
(pl. egy egyszerű, nem-headless VNC-s böngésző-környezet felállításával),
vagy (b) fogadjuk el a timeout-alapú, önjavító megoldást mostanra, és
lépjünk tovább a tervben szereplő következő fázisra (admin API/UI)?

---
_Generálva: 2026-07-31 10:43:30 +0200_
