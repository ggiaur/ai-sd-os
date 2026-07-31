# ClaudeCodeCLIAdapter elkészült + "mi az a provider" — lépésről lépésre

## Kész: `ClaudeCodeCLIAdapter`

Megvan, `sdk/provider_adapter.py`-ban. **72/72 teszt zöld** (6 új teszt csak
erre). Fontos biztonsági döntés: a tesztek NEM hívják meg a valódi `claude`
parancsot — lecseréltem (mock-oltam) a subprocess-hívást, mert egy valódi
beágyazott Claude Code munkamenet indítása a teszt-suite-ból lassú, pénzbe
kerülne, és kockázatos lenne (egy agent elindít egy másik agentet a
tesztfutás közben — ezt tudatosan elkerültem).

## Milyen modellel futna?

Amit a `KernelConfig.ai_model` mond — ma ennek az alapértéke
`"claude-sonnet-4-6"`. Ez ugyanaz a mező, amit az `AnthropicAdapter` is
használ, tehát egy helyen állítod be, és mindkét adapter ugyanazt a modellt
kapja. A CLI-hívás konkrétan így néz ki (a kód ezt rakja össze):

```
claude -p "<a feladat szövege>" --model claude-sonnet-4-6 \
       --output-format text --permission-mode acceptEdits
```

Ha másik modellt akarsz (pl. Opus egy komplexebb projekthez), csak a
`KernelConfig.ai_model`-t kell átírni — a `.env`-ben `AI_MODEL=...`
környezeti változóval, kód módosítása nélkül.

## "Mi az a provider" — most tényleg lépésről lépésre, konkrét kóddal

**A probléma, amit megold:** ha a `DeveloperAgent` kódjába direktben
beleírnánk "hívd meg az Anthropic API-t", akkor ha egyszer ki akarnád
próbálni a Claude CLI-t helyette, át kellene írnod a `DeveloperAgent`
kódját. Ez rossz — a "ki írja a kódot" döntésnek KÜLÖN kellene lennie
attól, "hogyan vezetem a sprintet".

**A megoldás: egy közös "szerződés" (interfész).** Az `AIProvider` egy
Python absztrakt osztály (`sdk/provider_adapter.py`), ami ennyit mond:
"bármi, ami engem implementál, KÖTELES tudni 4 dolgot: `generate()`,
`review()`, `embed()`, `analyze()`". Ennyi. Nem mondja meg, HOGYAN — csak
hogy legyen ilyen nevű függvénye, ami ezt-és-ezt a bemenetet veszi, és
ezt-és-ezt adja vissza.

Ma **4 különböző implementáció** létezik ehhez a szerződéshez:

| Implementáció | `generate()` mit csinál valójában |
|---|---|
| `MockProviderAdapter` | Regex-szel kiolvassa a promptból, mit kell visszaadni, begépeli. 0 mp. |
| `AnthropicAdapter` | Egy API-hívás a `anthropic` Python csomaggal. |
| `ClaudeCodeCLIAdapter` | Elindítja a `claude` parancssori programot subprocess-ként. |
| `OpenAIAdapter` | (ma még csak váz, GPT API-t hívna) |

**A lényeg, amit a `DeveloperAgent` kódjában látsz** (`agents/developer_agent.py`):

```python
response = await self.provider.generate(prompt, context={"work_package_id": wp.id})
```

Ez a sor **szó szerint ugyanígy néz ki**, függetlenül attól, hogy melyik
implementáció fut mögötte. A `DeveloperAgent` sosem írja ki, hogy
"AnthropicAdapter" vagy "ClaudeCodeCLIAdapter" — csak annyit tud, hogy
`self.provider`-nek VAN egy `generate()` metódusa, és azt meghívja. Hogy
`self.provider` ÉPPEN melyik konkrét objektum, azt **máshol, egy helyen**
dől el — a `main.py`-ban, az `EngineRunner.__init__`-ben:

```python
if config.mock_mode:
    self.provider = MockProviderAdapter()
elif config.provider == "claude_code_cli":
    self.provider = ClaudeCodeCLIAdapter(model=config.ai_model, cwd=cwd)
elif config.api_key:
    self.provider = AnthropicAdapter(api_key=config.api_key, model=config.ai_model)
```

Ez az egész "provider" dolog **csereszabatosság**. Olyan, mint egy
villásdugó-szabvány: a `DeveloperAgent` egy konnektor, aminek mindegy, MILYEN
készülék van bedugva bele (Mock/Anthropic/ClaudeCodeCLI/OpenAI), amíg az a
készülék illik a szabványba (van neki `generate()`, `review()`, stb.
metódusa, ami a megfelelő típusú választ adja vissza).

**Miért jó ez neked konkrétan:** amikor most azt kérdezted, "ne CLI-t
használjon Python helyett" — a válasz az volt, hogy EZ MÁR EGY VÁLASZTÁS,
nem egy beépített, megváltoztathatatlan tulajdonság. Most, hogy elkészült a
`ClaudeCodeCLIAdapter`, a `.env`-ben (vagy `KernelConfig`-ban) beállítod:

```
AI_SD_OS_PROVIDER=claude_code_cli
```

...és mostantól minden projekten, amit a motorral futtatsz, a
`DeveloperAgent`/`TestRunner` review-lépése ténylegesen a Claude Code
CLI-t hívja a Python API helyett — **a `DeveloperAgent` kódjában egyetlen
sort sem kellett módosítani ehhez.** Ez a "provider absztrakció" konkrét,
kézzelfogható haszna.

## Mikor melyiket válaszd — most már a konfigurálás is megvan

- `MOCK_MODE=true` → mindig `Mock`, a motor saját tesztjeihez.
- `AI_SD_OS_PROVIDER` nincs beállítva (vagy `anthropic`) + van
  `ANTHROPIC_API_KEY` → `AnthropicAdapter` (gyors, egyszerű feladatokhoz).
- `AI_SD_OS_PROVIDER=claude_code_cli` → `ClaudeCodeCLIAdapter` (komplex,
  több fájlt érintő, projekt-kontextust igénylő munkákhoz — pl. a
  webarchívum-szintű projektekhez, ha egyszer arra rááengeded a motort).

---
_Generálva: 2026-07-31 07:59:42 +0200_
