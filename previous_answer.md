# A terv — a válaszaid alapján

## Hibrid ReplayWeb.page/pywb kérdésedre — igen, ez a helyes megoldás

Utánanézve: nincs hivatalos "failure event" API a ReplayWeb.page-ben, de
két gyakorlati, mérhető jel van a váltásra:
1. **Fájlméret-küszöb** (a dokumentált problémás eset 963MB volt — egy
   biztonságos küszöb pl. 200-300MB alatt).
2. **Betöltési timeout** — ha a `<replay-web-page>` komponens N másodpercen
   belül nem jelez kész állapotot, feltételezzük, hogy elakadt.

**Ez pontosan ugyanaz a minta**, amit ma reggel az AI modell-választásnál
építettünk (Haiku→Sonnet 4.6→Sonnet 5 escalation, csak akkor drágább
eszközre váltva, ha az olcsóbb ténylegesen elbukik) — itt: ReplayWeb.page
az alapértelmezett (gyors, szerver nélküli), és CSAK akkor esik vissza
pywb-re (szerver-oldali, megbízhatóbb nagy fájloknál), ha ténylegesen
elakad. Konzisztens tervezési elv az egész projektben.

## A válaszaidból kirajzolódó architektúra

**Bővítés-first, de swappable**: a meglévő legacy archívumot bővítjük, de
úgy építjük a komponenseket (ReplayWeb.page, admin UI), hogy alkalmasak
legyenek arra is, hogy idővel ez legyen a fő rendszer.

**A kulcs új elem, amit kérsz**: egy **admin jóváhagyási felület**, ahol
egy ember dönt minden automatikusan felfedezett jelöltről ÉS minden
küszöb alatti minőségű archívumról.

## A pontos folyamat (a válaszaid alapján összeállítva)

```
1. discovery.py → jelölt oldalak (helyi-kötődés szűrővel)
        │
        ▼
2. ADMIN FELÜLET: "Jelölt oldalak" lista
   → ember jóváhagyja VAGY elutasítja
        │ (jóváhagyva)
        ▼
3. crawler.py → valódi Browsertrix crawl → WACZ
        │
        ▼
4. quality_index.py → pontszám (archivált vs élő)
        │
        ├─ pontszám ≥ QUALITY_THRESHOLD (env var, alapból 96%)
        │  → automatikus elfogadás, publikálás
        │
        ├─ pontszám < QUALITY_THRESHOLD, ELSŐ próbálkozás
        │  → automatikus ÚJRA-crawl (1x)
        │
        └─ pontszám < QUALITY_THRESHOLD, MÁSODIK próbálkozás után is
           → ADMIN FELÜLET: "Minőségi eltérések" lista
             → ember dönt: elfogadja / elutasítja / újrapróbálja
        │
        ▼
5. Elfogadás után: pywb collection-be töltés (wb-manager) + ReplayWeb.page
   (fallback: pywb) a nyilvános oldalon
        │
        ▼
6. MINDEN emberi döntés (jóváhagyás/elutasítás, elfogadás/elutasítás
   küszöb alatt) → naplózva, később áttekinthető ("tanulási napló") —
   UGYANAZ a minta, mint a mai `lessons_learned.yaml` a motorban: soha
   nem automatikusan hangolja magát a szűrő/küszöb, csak bizonyítékot
   gyűjt, amit egy ember (vagy én, ha kéred) használ fel a finomításhoz.
```

## Konkrét technikai terv

### Hova épüljön be? — újrahasznosítjuk a meglévő vázat, nem építünk párhuzamosat

A `fewa-v3-backend` (FastAPI + Postgres) már tartalmaz jogosultság-kezelést
("archivist" szerepkör), jobs API vázat (`/api/admin/ingest`,
`/api/admin/jobs`) — **ezt bővítjük**, nem építünk mellé egy harmadik
rendszert. A `arq_worker.py` szimulált függvényei helyére a ma megépített,
valódi `fewa-automation` modulok (crawler.py, quality_index.py,
discovery.py) kerülnek.

### Új adatbázis-táblák (Postgres, a meglévő séma mellé)
- `discovery_candidates`: talált jelölt oldalak (URL, cím, snippet,
  egyező helynevek, státusz: PENDING/APPROVED/REJECTED, döntő admin, időpont)
- `quality_reviews`: küszöb alatti archívumok (WorkPackage/job id,
  pontszám, ok, státusz: PENDING/ACCEPTED/REJECTED/RETRY, döntő admin)
- `curation_decisions` (a "tanulási napló"): minden emberi döntés
  archívuma, később elemezhető

### Új backend végpontok
- `GET /api/admin/candidates` — jelölt lista
- `POST /api/admin/candidates/{id}/approve` / `/reject`
- `GET /api/admin/quality-reviews` — küszöb alatti eltérések listája
- `POST /api/admin/quality-reviews/{id}/decide`

### Konfiguráció
- `QUALITY_THRESHOLD` env var (alapérték: 96)
- `MAX_QUALITY_RETRIES` env var (alapérték: 1)

### Admin UI (fewa-v3-frontend, a már tervezett `/admin/dashboard` alá)
- **"Jelölt oldalak"** oldal — lista, minden jelölthöz a talált helynevek,
  jóváhagyás/elutasítás gombokkal
- **"Minőségi eltérések"** oldal — küszöb alatti archívumok, pontszám,
  konkrét eltérés-okok (a `quality_index.py` már ma is visszaadja ezt),
  és egy **oldal-melletti összehasonlítás** (archivált szöveg vs élő
  szöveg kiemelt különbségekkel) — ezt gondoltam ki, mert "találd ki"
  kérted: enélkül a döntéshozó ember vakon dönt egy puszta százalék alapján.

### Nyilvános visszajátszás
- `<replay-web-page>` alapértelmezett, fájlméret- és timeout-alapú
  automatikus pywb-fallback-kel (iframe a helyi/production pywb-re)

## Fázisterv (ezzel indulnék neki)

1. **Adatbázis-séma bővítés** (2 új tábla) + a valós `fewa-automation`
   modulok bekötése az `arq_worker.py`-ba a szimuláció helyett
2. **Admin API végpontok** (jelölt jóváhagyás, minőségi döntés)
3. **Admin UI** (2 új oldal a `/admin` alatt)
4. **Nyilvános visszajátszó oldal** (ReplayWeb.page + pywb fallback)
5. **Tanulási napló** (a döntések naplózása — a tényleges "tanulás"/
   kritérium-finomítás explicit KÉSŐBBI fejlesztés, ahogy te is jelezted)

Minden fázishoz valódi tesztek (ahogy egész nap most is), és a meglévő
legacy rendszert egyetlen ponton sem érintjük.

**Mehetek?** Ha igen, az 1. fázissal kezdek.

---
_Generálva: 2026-07-31 10:23:36 +0200_
