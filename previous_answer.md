# Két őszinte válasz — az egyik lehet, hogy nem az, amit vársz

## Előbb: mennyire megbízható a modell-önhangolás ma?

**Őszintén: nem tudom, mert nincs még valós adat.** A 3-szintű létra
(Haiku → Sonnet 4.6 → Sonnet 5) egy ÉSSZERŰ tervezési döntés, amit
tesztekkel bizonyítottam, hogy A LOGIKÁJA helyesen működik (a helyes
modellt választja a megfelelő helyzetben) — de ez szintetikus, kitalált
tesztadatokon fut. Arra, hogy "a leírás-hossz alapú egyszerűség-becslés
mennyire jó előrejelzője a valódi nehézségnek", **nulla valós adatom van**,
mert még egyetlen igazi feladat sem futott át rajta. A lessons-learned
mechanizmus pont azért létezik, hogy EGYSZER, ha lesz elég valós futás,
legyen mit átnézni — de ma még üres. Ez nem "kész és bevizsgált", hanem
"jól megtervezett és készen áll arra, hogy tanuljon" — ez fontos
különbség, és nem akarok többet állítani, mint amit tudok.

## A nagyobb kérdésed: van-e egyáltalán értelme a pipeline-nak?

**Őszinte válasz: a mostani, egyszemélyes, veled-egyeztetős munkamódra —
valószínűleg NEM éri meg annyira, mint amennyit gondoltál.**

Nézzük meg pontosan, mit ad hozzá a pipeline (B mód) ahhoz képest, amit
most csinálunk (A mód, direkt veled dolgozom):

### Amiben a pipeline TÉNYLEG jobb, mint a direkt beszélgetés

1. **Felügyelet nélküli, autonóm munka.** Ha azt akarod, hogy "fusson
   éjszaka, amíg alszol, reggelre legyen kész X" — erre a direkt Claude
   Code beszélgetés nem alkalmas (nekem is "jelen kell lennem" a
   beszélgetésben), a pipeline viszont igen, mert a HITL-kapuk mentén
   önállóan halad, és csak a kapuknál áll meg.
2. **Sok projekt egyidejű, egységes kezelése.** Ha 5-10 projekted lenne, és
   mindegyiken ugyanazt a szigorú folyamatot (spec-first, kettős
   verifikáció, audit-napló) akarnád kikényszeríteni anélkül, hogy minden
   egyes alkalommal külön beszélgetést kezdenél — a pipeline ezt
   strukturálisan kikényszeríti, a beszélgetés-alapú munka nem.
3. **Formális audit/megfelelőségi nyomvonal.** A titkosított ledger,
   traceability matrix, Definition of Done — ez akkor számít, ha egyszer
   valakinek (auditornak, csapatnak) BIZONYÍTANOD kell, mi történt és miért,
   nem csak emlékezned kell rá egy chat-előzményből.

### Amiben a direkt beszélgetés (amit MOST csinálunk) egyszerűen JOBB

1. **Gyorsabb.** Nincs esemény-busz, állapotgép, YAML-szerződés-generálás —
   egyenesen nekiállok a feladatnak.
2. **Rugalmasabb és okosabb.** Széles kontextust látok, tudok ítélkezni,
   alkalmazkodni menet közben — a pipeline `DeveloperAgent`-je ma egyetlen,
   szűk promptot kap egyetlen WorkPackage-hez, nincs igazi oda-vissza
   iterációja (kivéve, ha a `ClaudeCodeCLIAdapter`-t használod, ami
   valójában... egy ilyen munkamenetet indítana el, mint ez itt).
3. **Valószínűleg jobb minőségű**, mert TE közvetlenül átnézed minden
   lépésemet — ez pont az, amit ma egész végig csináltunk, és pont ez adta
   a magas minőséget (a sok valódi hibát, amit együtt találtunk meg).

### A lényeg, amit ki kell mondanom

A pipeline igazi értéke NEM az, hogy "jobb munkát végez, mint amikor
beszélgetünk" — hanem hogy **automatizálja és skálázza** azt, amit most
kézzel, felügyelettel csinálunk. Ha a te valós használati eseted az, hogy
**leülsz velem, és együtt dolgozunk** — akkor őszintén, a pipeline overhead-je
(állapotgép, YAML-szerződések, esemény-busz) ma nem ad annyi értéket, mint
amennyi munkát igényelt megépíteni.

**A javaslatom:** ha nincs konkrét igényed a "felügyelet nélküli, autonóm
futtatásra" vagy a "sok projekt egységes kezelésére", akkor NE erőltessük
tovább a pipeline éles kipróbálását — inkább folytassuk úgy, ahogy ma
csináltuk: te elmondod, mit akarsz egy adott projekten, és én direktben
megcsinálom, ugyanazzal a minőségi igényességgel (két független
ellenőrzés-gondolkodással, tesztekkel, óvatossággal), amit ma a motorba
építettünk. A motor kódja addig is megmarad — ha egyszer tényleg
felmerül az autonóm/skálázási igény, készen áll.

**Ha viszont van olyan konkrét helyzeted, amikor tényleg felügyelet nélkül
kellene futnia** (pl. sok kis, ismétlődő feladat, vagy amikor nem vagy
elérhető) — szólj, és akkor van értelme folytatni az éles pipeline-tesztet.

---
_Generálva: 2026-07-31 08:46:26 +0200_
