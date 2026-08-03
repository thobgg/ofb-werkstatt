# Ansatz

Festgehalten am 3. August 2026, nach einem Pilotlauf über 22 Taufeinträge
(Haberschlacht 1808/09). Die Zahlen darin sind gemessen, nicht geschätzt.

## Arbeitsteilung: Modell schlägt vor, Skript entscheidet

| Aufgabe | LLM | deterministisches Skript |
|---|---|---|
| Handschrift lesen | ✓ | — |
| Kandidaten erkennen, Plausibilität einschätzen | ✓ | — |
| Abgleich gegen den Bestand | — | ✓ |
| Regelentscheidungen | — | ✓ |
| Daten verändern, zusammenlegen, exportieren | — | ✓ |

**Begründung aus dem Pilotlauf.** Acht doppelt angelegte Ehepaare wurden zuerst
einzeln diskutiert — langsam und ohne belastbares Ergebnis. Eine fünfzeilige
Regel entschied danach sechs davon allein und legte zwei zur Handprüfung.
Umgekehrt hätte kein Skript erkannt, dass `Roßin` in Wahrheit `Kochin` heißt.

**Sicherheitsregel:** Was Daten verändert, muss reproduzierbar sein. Ein Modell
entscheidet bei jedem Durchlauf womöglich anders. Also schlägt das Modell
Vorgänge vor, das Skript führt sie aus, das Journal hält beides fest.

## Dreischritt

    1  Transkribieren   Modell liest, markiert Unsicheres
                        Mensch ergänzt/korrigiert mit Bild daneben
                        Ergebnis: vollständiger Eintrag, noch ungeprüft

    2  Matching         der GANZE Eintrag als Suchschlüssel
                        Ergebnis: Zuordnungsvorschlag samt Begründung

    3  Bestätigen       Mensch entscheidet find-and-use oder create
                        erst hier wird etwas als gesichert markiert

**Warum erst vollständig lesen, dann matchen.** Die Anker, die im Pilotlauf
tatsächlich trafen, liefen fast nie über den Nachnamen:

| Eintrag | Treffer über | falsch gelesen war |
|---|---|---|
| Taufe 8/00361 | Vornamen der Frau (*Felicitas Heinrika*) | Nachname des Mannes |
| Taufe 7/00364 | Beruf *Schneidermeister* + *Eleonora Catharina* | Nachname des Mannes |
| Taufe 14/00365 | Beruf *Ratsverwandter* + *Maria Agnes* | Nachname des Mannes |
| Taufe 3/00363 | Beruf *Wirt und Gerichtsverwandter* | Nachname des Vaters |

> **Was gut lesbar ist — Vornamen, Datum, Beruf, Ort — trägt das Matching.
> Was schlecht lesbar ist — die Familiennamen — wird durch das Matching bestimmt.**

Feldweises Ankern während des Lesens würde beim falsch gelesenen Nachnamen
steckenbleiben.

## Ampel — Ergebnis des Matchings, keine Eigenschaft der Lesung

| Signal | Farbe | Folge |
|---|---|---|
| Anker bestätigt, Vornamen passen unabhängig | grün | still übernommen, eingeklappt |
| gelesen, aber nichts bestätigt es | gelb | Maske springt hin |
| unsicher gelesen, mehrere Kandidaten | rot | mit Bildausschnitt |

**Die Selbsteinschätzung des Modells darf nicht grün machen.** Bei `Koch`/`Roth`
war das Modell viermal sicher und viermal falsch — der Buchstabe ist eindeutig
lesbar, nur eben als der falsche.

**Vokabular und Häufigkeit machen ebenfalls nicht grün.** `Roth` kommt 59-mal im
Bestand vor und hätte jeden Plausibilitätstest bestanden.

### Kalibrierung nach Feldtyp (gemessen)

    Datum, Ort, Beruf, Formeln, Vornamen    praktisch fehlerfrei
    Familiennamen                           42 % falsch gelesen

Ein Familienname startet daher gelb, auch wenn er sauber lesbar wirkt.

## Anker je Registerart

    Taufe        Eltern      → Elternehe im Bestand
    Ehe          Brautleute  → Geburtsdatum + Ort (tagesgenau, der stärkste)
                 Eltern      → über die Herkunftsfamilie der Brautleute
    Begräbnis    Verstorbener→ Name + Alter → Geburtsjahr rückgerechnet
                 Kinder      → genannter Vater → Elternfamilie
                 "weyl."     → Ehepartner

**Die Register verweisen aufeinander.** Der Täufling von 1809 ist der Bräutigam
von 1835 und der Verstorbene von 1880. Sind alle drei erfasst, schließen sich
die Ketten — ein stärkerer Anker als jeder Einzelabgleich, weil er unabhängige
Quellen verknüpft.

Der Elternehe-Anker verliert mit der Zeit an Kraft, wenn man **ein** Register
isoliert bearbeitet: Bei einem Bestand, der 1807 endet, tragen die Ehen im
Taufjahr 1808 noch 94 %, 1813 noch 53 %, 1820 nur 18 %. Werden die Ehen ab 1808
mit erfasst, versiegt er nicht — er wächst mit.

## Namensebenen

| Ebene | Beispiel | Zweck |
|---|---|---|
| gelesen | `Roßin` | Rohlesung, bleibt erhalten auch wenn falsch |
| Kirchenbuchform | `Kochin` | was dasteht, bestätigt → `_KB_NAME` |
| kanonisch | `Koch` | normalisiert, für Suche und Verknüpfung → `NAME` |

Die Rohlesung wegzuwerfen wäre ein Verlust — nur so lässt sich messen, wo die
Erkennung schlecht ist. Der `Koch`/`Roth`-Befund entstand genau daraus.

**Das Glattziehen darf die Kirchenbuchform nie überschreiben.** Sonst
verschwindet, dass dort `Krönich` steht und nicht `Kröneck`.

Der kanonische Name kommt beim Matching meist geschenkt: wird `I3037` zugeordnet,
ist deren `NAME` bereits `Bierle`.

## Wann der Mensch gefragt werden muss

    Match eindeutig        ein Kandidat, Anker stimmt          → durchlaufen
    Match mehrdeutig       zwei plausible Personen             → fragen
    Match widersprüchlich  beide Eltern da, keine gemeinsame
                           Familie                             → fragen (gefährlich)
    kein Match             kanonische Form festlegen           → vorschlagen, bestätigen

Nur der letzte Fall verlangt eine echte Namensentscheidung — und jede solche
Bestätigung ist eine neue Kante im Klassengraphen: gilt `Bührlin` einmal als
`Bierle`, gilt es fortan.

**Vorsicht dabei: Die Relation ist nicht transitiv.** Eine einzige falsche Kante
(`Bührle → Müller`, ein Beleg) verschmolz im Pilotbestand zwei fremde Familien
zu einer Klasse von 231 Personen. Bestätigte Kanten brauchen dieselbe Prüfung
wie importierte: Schreibnähe plus Belegzahl.

## Gezielter Bildausschnitt statt ganzer Seite

Der eigentliche Geschwindigkeitshebel: Bei jeder unsicheren Stelle wird genau
dieser Ausschnitt geschnitten und neben das Eingabefeld gelegt.

    heute      grosses Bild -> Stelle suchen -> hin und her -> tippen
    Ziel       kleiner Ausschnitt direkt am Feld -> tippen

**Nicht ueber Bounding Boxes des Modells** — die sind ungenau; beim Pilotlauf
traf die geschaetzte Position mehrfach daneben. Stattdessen deterministisch:

    Spaltenraster (einmal je Buch, von Hand gezogen)  -> horizontaler Bereich
    Zeilengrenze  (je Eintrag, ohnehin vorhanden)     -> vertikaler Bereich
    Modellhinweis (welche Textzeile in der Zelle)     -> Feinjustierung

Kirchenbuchformulare haben feste, gedruckte Spalten. Sind deren Grenzen einmal
bestimmt, ist fuer jedes Feld bekannt, wo es liegt — fuer den ganzen Band, oft
ueber Jahrzehnte. Das Raster einmal geführt ziehen (sechs bis neun senkrechte
Linien auf der Seitenuebersicht) kostet Minuten und ersetzt jede Automatik.
Automatische Zeilen- und Spaltenerkennung ist im Projekt bereits zweimal
gescheitert.

Sicherheitsnetz: grosszuegiger Rand, und ein Klick blendet den ganzen Streifen
ein, falls der Ausschnitt danebenliegt.

## Zwei Rollen, nicht zwei Betriebsarten

Transkribieren und Korrigieren sind verschiedene Taetigkeiten und duerfen nicht
derselben Person zugemutet werden.

| Rolle | wo | braucht |
|---|---|---|
| **Bearbeiter** | lokal, mit API-Schluessel | Seiten vorbereiten, transkribieren lassen, Matching, Export |
| **Korrektor** | Browser, Login | nur Ausschnitt anschauen und tippen |

**Die Korrekturoberflaeche braucht kein Modell.** Das Vorlesen ist vorher
passiert, zentral und im Batch. Damit entfallen fuer Mitarbeitende saemtliche
Huerden: keine Installation, kein Python, keine Konfigurationsdatei, kein
eigener API-Schluessel. Die Kosten bleiben beim Bearbeiter und damit
kontrollierbar.

Auch die Bildrechte entschaerfen sich: verbreitet werden keine ganzen Scans,
sondern Ausschnitte von wenigen Quadratzentimetern.

Stufenweise, jede Stufe fuer sich nuetzlich:

    1  lokal, nur der Bearbeiter    Transkription + Matching + Korrektur
    2  + Export                     der Bestand waechst
    3  + Korrekturoberflaeche       Helfer bekommen Zugang

Voraussetzung fuer Stufe 3 ist lediglich eine `benutzer`-Spalte von Anfang an —
sonst wird daraus eine Migration statt eines Aufsatzes.

## Eine Datenbasis, viele Eingangstüren

    GEDCOM ─┐
    XLSX   ─┤
    CSV    ─┼──►  person / familie  ◄── eigene Erfassung
    DOCX   ─┘            ▲
                         └── find-and-use sucht ausschließlich hier

Import ist ein Vorgang, kein Dauerzustand. Die Suche kennt keine Herkunft.
Damit ist kein Startbestand nötig: Wer bei Null anfängt, füllt die Tabelle durch
Erfassen — die ersten hundert Einträge tragen die nächsten tausend.

Erhalten bleiben muss die **Quelle je Person und je Feld**, sonst lässt sich
später weder gewichten noch zurückverfolgen, und beim Export nicht unterscheiden,
was neu ist und was schon da war.
