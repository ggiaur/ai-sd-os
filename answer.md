# Igazad volt — Sonnet 4.6 valóban létezik. Javítva, profibb megoldással.

## Amit rosszul csináltam, és amit utánanéztem

Korábban **hibásan** "javítottam" az `ai_model` alapértékét
`"claude-sonnet-5"`-re, mert azt hittem, a `"claude-sonnet-4-6"` egy
elgépelés vagy nem létező modell. Tévedtem — utánanéztem hivatalos
forrásokból (Anthropic hivatalos bejelentés, AWS Bedrock model card), és:

- **Sonnet 4.6 valóban létezik**, 2026. február 17-én jelent meg, a valós
  API modell-azonosítója szó szerint `claude-sonnet-4-6`, ára $3/$15
  (input/output, millió tokenenként).
- **Sonnet 5** ennél KÉSŐBB, 2026. június 30-án jelent meg — jelenleg
  bevezető áron $2/$10 (2026.08.31-ig), utána $3/$15-re emelkedik.
- **Haiku 4.5**: `claude-haiku-4-5-20251001`, $1/$5 — a legolcsóbb.

Vagyis a sorrend időben: **Haiku 4.5 → Sonnet 4.6 → Sonnet 5**, és jelenleg
a Sonnet 5 bevezető ára miatt NEM egyértelműen drágább, mint a 4.6 — ez
augusztus 31. után változik. Ez pontosan mutatja, miért veszélyes
hardcode-olni: az árstruktúra és az elérhető modellek listája HÓNAPRÓL
HÓNAPRA változik.

**Forrás:**
- [Introducing Sonnet 4.6 — Anthropic hivatalos bejelentés](https://www.anthropic.com/news/claude-sonnet-4-6)
- [Claude Sonnet 4.6 — AWS Bedrock model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-sonnet-4-6.html)
- [Claude Sonnet 5 pricing — OpenRouter](https://openrouter.ai/anthropic/claude-sonnet-5)
- [Claude Haiku 4.5 — Anthropic hivatalos oldal](https://www.anthropic.com/claude/haiku)
- [Model IDs and versioning — Claude Platform Docs](https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions)

## A profi megoldás, amit építettem: ESCALATION, nem találgatás

A korábbi megközelítésem (leírás-hossz alapján megbecsülni, "ez bonyolult
lesz, vigyük Sonnet-re") pontosan az volt, amit kritizáltál — egy találgatás,
amit nem lehet megbízhatóan "felmérni" előre. Az iparágban erre a valódi,
bevált mintázat: **escalation-on-failure** — csak akkor lépünk drágább
modellre, ha a olcsóbb TÉNYLEGESEN, bizonyítottan elbukott, nem mert
"úgy néz ki, hogy bonyolult lesz."

Az új, 3-szintű létra (`sdk/model_selector.py`):

1. **1. próbálkozás, egyszerű feladat** (1 rövid task) → **Haiku 4.5**
2. **1. próbálkozás, összetettebb feladat, VAGY bármelyik köztes retry** →
   **Sonnet 4.6** (ez a valódi munkaló modell, nem a Haiku és nem a Sonnet 5)
3. **CSAK az utolsó retry**, mielőtt a pipeline feladná → **Sonnet 5** — és
   KIZÁRÓLAG akkor, ha a Sonnet 4.6 már bizonyítottan, ismételten elbukott
   ugyanazon a feladaton.

Ez pontosan azt csinálja, amit írtál: "sonnet 5 csak bonyolult
feladatoknál, ahol a 4.6 nem boldogul" — de a "nem boldogul"-t TÉNYLEGES,
mért kudarc dönti el (a mi saját, kétrétegű verifikációnk: pytest + független
review — lásd korábbi köröket), nem egy előzetes találgatás.

## A másik kérésed: mi van, ha egy modell megszűnik?

**`sdk/model_validator.py`** — a motor induláskor (nem minden work
package-nél, csak egyszer, hogy ne legyen felesleges API-hívás-pazarlás)
ténylegesen lekérdezi az Anthropic API-tól (`client.models.retrieve(model_id)`)
mindhárom konfigurált modellt (light/ai/escalation), és ha valamelyik
elavult/átnevezett/nem létezik, **hangosan figyelmeztet**, ahelyett hogy
csendben, egy zavaros API-hibával futna el a pipeline közepén. Ez nem
automatikusan cserél le semmit — az automatikus "találjunk ki egy pótlást"
kockázatosabb lenne, mint egy világos figyelmeztetés + link a dokumentációra.

**91/91 teszt zöld** (17 új/frissített teszt csak erre a körre — az
escalation-létra minden ágára, plusz egy hamisított Anthropic-klienssel a
validátorra, hogy sose hívjunk valódi API-t a teszteléshez). Élesben
leellenőrizve, commitolva és pusholva (`f0c0554`).

## Amire figyelmeztetlek

Ez a rendszer NEM garantálja, hogy sose kell kézzel beavatkoznod — ha
Anthropic hónapok múlva kivezeti a Sonnet 4.6-ot, a validátor jelezni fogja
(hangos warning induláskor), de nem fog magától új modellt választani
helyette. Ez tudatos döntés: egy automatikusan "kitalált" modellcsere
kockázatosabb lenne, mint hogy te nézd át és döntsd el kézzel, a
`.env`-ben (`AI_MODEL`, `LIGHT_MODEL`, `ESCALATION_MODEL`).

---
_Generálva: 2026-07-31 08:25:41 +0200_
