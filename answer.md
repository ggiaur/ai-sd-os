# .env.example pótolva + "legyen a motor a system promptod" — megcsináltam

## 1. Miért nem volt .env.example?

Valódi hiányosság volt — a README setup-lépései hivatkoztak rá
("cp .env.example .env"), de a fájl SOSEM létezett a repóban. Most pótoltam
(`.env.example`), minden `KernelConfig` env-változóval, dokumentálva.

## 2. "Lehet a motor a system promptod?" — IGEN, és megcsináltam

Ez egy nagyon jó felismerés volt tőled. Ahelyett, hogy két külön dolgunk
lenne (a) direkt beszélgetünk, ad-hoc módon, vagy (b) elindítjuk a teljes
Python pipeline-t — **a motor FEGYELMÉT (nem a Python-gépezetét) rátettem
a saját munkamódomra**, egy `CLAUDE.md` fájl formájában.

**Hogyan működik ez technikailag:** a Claude Code automatikusan beolvassa a
`CLAUDE.md` fájlt egy adott könyvtárban, és kontextusként mindig figyelembe
veszi — pont úgy, mint egy system prompt kiegészítést, DE csak arra a
projektre nézve, ahol a fájl van. Két helyre írtam meg:

1. **`/srv/projects/ai-sd-os/CLAUDE.md`** — magának a motornak a repójára
   (amikor a motor kódján dolgozom, ez a szabály).
2. **`/srv/projects/ai-sd-os/templates/PROJECT_CLAUDE.md`** — egy
   ÁTMÁSOLHATÓ sablon, amit BÁRMELYIK más projektbe bedobhatsz
   (`cp .../templates/PROJECT_CLAUDE.md /path/to/projekt/CLAUDE.md`), és
   onnantól, valahányszor abban a könyvtárban dolgozom veled, automatikusan
   követem ugyanazt a fegyelmet, amit ma egész nap gyakoroltunk:

   - **Terv/spec előbb**, jóváhagyás, mielőtt implementálnék (ez az emberi
     kapu — nem hagyjuk ki, mert lassúnak tűnik)
   - **Teszt a kód ELŐTT**, a specifikációból, nem az implementációból
     visszafejtve (ez volt a mai nap #1 gyökérhibája, amit javítottunk)
   - **Sose írjunk felül/töröljünk meglévő fájlt** észrevétlenül
   - **Ne találgassunk időben változó tényeket** (modell-ID-k, verziók)
     memóriából — nézzünk utána (pont, ahogy a Sonnet 4.6-nál tettem)
   - **Valódi, független második ellenőrzés** implementálás után, nem csak
     "átmegy-e a saját tesztjén"
   - **Auditálható commit-üzenetek**, csak valós diff esetén
   - **Második emberi kapu**: megerősítés kérése push/commit előtt, ha
     valódi, nehezen visszafordítható következménye van

**Ez pontosan azt oldja meg, amit felvetettél:** megkapod a motor
fegyelmét és minőségi biztosítékait, DE a Python event-bus/state-machine/
YAML-szerződés overhead nélkül — mert az overhead-et most én, a
beszélgetésen keresztül, közvetlenül hordozom, nem egy külön futó program.

**Mostantól, ha egy másik projekten akarsz dolgozni velem:**
```
cp /srv/projects/ai-sd-os/templates/PROJECT_CLAUDE.md /srv/projects/<projekt>/CLAUDE.md
```
...és onnantól, amikor abban a könyvtárban beszélgetünk, automatikusan ezt
a fegyelmet követem — nem kell külön kérned minden alkalommal.

**93/93 teszt továbbra is zöld** (ez a kör csak dokumentáció volt, kódot
nem érintett), commitolva és pusholva (`a9ad5cd`).

---
_Generálva: 2026-07-31 08:54:05 +0200_
