# Éles próba — előbb kell egy API-kulcs

Ellenőriztem: **nincs `ANTHROPIC_API_KEY` beállítva** ebben a környezetben
(sem környezeti változóként, sem `.env` fájlban sehol a `/srv/projects`
alatt). Valós (nem mock) módban a motor nem tud AI-hívást tenni enélkül.

## Kérlek, add meg biztonságosan

**NE illeszd be a kulcsot ide, a chatbe** — az bekerülne a beszélgetés
naplójába. Ehelyett az egyik:

1. **Te magad hozod létre a `.env` fájlt** a terminálban (nem rajtam
   keresztül), pl.:
   ```
   echo 'ANTHROPIC_API_KEY=sk-ant-...' > /srv/projects/<projekt-neve>/.env
   ```
   Utána csak szólj, hogy kész, és onnantól én már csak azt látom, hogy a
   fájl létezik, a tartalmát nem kell megosztanod velem szövegben.

2. **Környezeti változóként**, a `! export ANTHROPIC_API_KEY=...` paranccsal
   (a `!` előtag a te terminálodban futtatja, nem kerül a beszélgetésbe) —
   de ez csak az adott munkamenetre érvényes, minden újraindításnál
   újra kellene állítani, ezért az 1. opció (`.env` fájl a projektben)
   praktikusabb.

## Amit addig előkészítek

Amíg megadod a kulcsot, előkészítek egy kis, valóban alacsony tétű
teszt-projektet (`/srv/projects/`-ben, a webarchívumtól függetlenül), és
`auto_approve=False` móddal állítom be a futtatást, hogy a Sprint Planning
kapunál ténylegesen megálljon és átnézzük együtt, mielőtt bármit írna.

Szólj, ha kész a kulcs, és folytatjuk.

---
_Generálva: 2026-07-31 08:39:46 +0200_
