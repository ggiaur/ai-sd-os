# Modell-választás: Haiku vs Sonnet, kódoláshoz ÉS review-hoz is — KÉSZ

## Amit csináltam

1. **A hibás modellazonosítót kijavítottam.** `"claude-sonnet-4-6"` nem
   létező modell volt — helyette `KernelConfig.ai_model` alapértéke most
   `"claude-sonnet-5"`, és bekerült egy új `light_model` mező
   `"claude-haiku-4-5-20251001"` alapértékkel.

2. **Egyetlen közös heurisztika (`sdk/model_selector.py`), ami MINDKÉT
   helyen fut** — pont amit kértél: "nem csak a tesztre, a kódolásra is":
   - `DeveloperAgent` (a tényleges kódírás) — ha egy WorkPackage egyszerű
     (1 rövid feladat), Haiku-t használ; ha összetettebb (több feladat vagy
     hosszabb leírás), Sonnet-et.
   - `TestRunnerAgent` független review-lépése — ugyanezt a döntést kapja
     meg, ráadásul a review alapból a Haiku-t kapja preferáltan (egy
     kód-ellenőrzés egyszerűbb ítélet-feladat, mint a generálás).

3. **A modellválasztás nem csak a `KernelConfig.ai_model` mezőhöz van
   kötve** — mindhárom valódi adapter (Anthropic, ClaudeCodeCLI) most már
   elfogad egy per-hívásos felülbírálást (`context={"model": ...}"`), így a
   motor UGYANAZT a provider-objektumot használja, csak feladatonként más
   modellt kér tőle — nem kell külön adapter-példány minden modellhez.

4. **7 új teszt, ami TÉNYLEGESEN bizonyítja, hogy ez működik** — nem csak azt
   ellenőrzi, hogy a heurisztika-függvény jó választ ad izoláltan, hanem egy
   "figyelő" (capturing) provider-stub-bal azt is, hogy a `DeveloperAgent`
   és a `TestRunnerAgent` TÉNYLEG átadja a helyes modellnevet a hívásban.

**79/79 teszt zöld, élesben (mock módban) leellenőrizve, commitolva és
pusholva** (`bce5db1`).

## Mostantól hogyan állítod be

`.env`-ben (vagy környezeti változóként):
```
AI_MODEL=claude-sonnet-5        # erős modell, összetett feladatokhoz
LIGHT_MODEL=claude-haiku-4-5-20251001   # gyors/olcsó modell, egyszerű feladatokhoz + review-hoz
```

Nem kell semmit kikapcsolni vagy külön konfigurálni — ha valós (nem mock)
módban futtatod a motort, ez a döntés automatikusan megtörténik minden
egyes WorkPackage-nél, a heurisztika alapján.

## Amire figyelmeztetlek: ez egy KIINDULÓ heurisztika, nem tudomány

"1 feladat, rövid leírás = egyszerű" — ez egy ésszerű, de nyers becslés.
Ha azt látod, hogy rosszul dönt (pl. egy rövid leírású, de valójában
trükkös feladatot Haiku-ra küld, és az elbukik a review-n), a pipeline a
meglévő retry-mechanizmuson keresztül úgyis újrapróbálja — de ha
rendszeresen rossz döntéseket látsz, szólj, és finomítjuk a
`sdk/model_selector.py`-ban lévő küszöbértékeket.

---
_Generálva: 2026-07-31 08:11:00 +0200_
