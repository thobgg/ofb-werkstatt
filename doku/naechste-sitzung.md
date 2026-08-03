# Quintessenz für einen Neustart

Stand 3. August 2026. Diese Datei ersetzt die Sitzungshistorie — wer sie und
`ansatz.md` liest, kann ohne Vorwissen weitermachen.

## Was gesichert ist

**Der Pilotlauf ist positiv entschieden.** 67 Namensfelder kumuliert, 9 markiert
= 13,4 %, klar unter der vorab vereinbarten Abbruchschwelle von 25 %.

**Aber:** Die Rohlesung war bei 42 % der Felder falsch. Die guten Zahlen
entstehen vollständig durch den Abgleich gegen den vorhandenen Bestand.
Das Verfahren ist ein **Abgleichsverfahren, kein Leseverfahren**. Alles Weitere
folgt daraus.

**Belegte Fehllesungen** (Hand M. Deurlin, gilt bis zum Pfarrerwechsel 1827):

| gelesen | tatsächlich | Häufigkeit |
|---|---|---|
| `Roth` / `Roßin` | **`Koch`** | 4 von 5 Vorkommen falsch |
| `Weißhardt` | `Weissert` | Normalisierungsfrage, kein Lesefehler |
| `Kräßin`, `Bierlin` | **`Käserin`** | 2× — die K-Anfangsschleife |
| `Straub` | `Brudi` · `Hubelz` → `Häberlen` · `Grumbaldts` → `Rembold` | je 1× |

`Roth` kommt 59-mal im Bestand vor, `Koch` 36-mal. **Vokabular und Häufigkeit
bestätigen diesen Fehler, statt ihn zu finden.**

## Der Elternehe-Anker

Eltern der Taufen von 1808 heirateten fast alle vor 1807 — ihre Ehe steht also
noch im Bestand. Damit wird erstmals auch der *Mutter*name prüfbar.

Prüfregel, damit der Anker nicht selbst zum Fehler wird:
1. Vorname(n) des Vaters passen,
2. Vornamen der Mutter passen **unabhängig** zum Registereintrag,
3. Heiratsdatum liegt vor dem Bestandsende.

Punkt 2 trägt die Beweislast. In vier von 22 Fällen war der Vatername falsch
gelesen und der Treffer kam allein über die Vornamen der Mutter.

**Verfallsdatum** (gerechnet aus 1.397 Kind-Ereignissen, Bestand endet 1807):

    Taufjahr 1808  94 %   1813  53 %   1820  18 %   1827  3 %

Ab 1813 trägt er die Mehrheit nicht mehr, ab 1820 ist er praktisch weg —
**es sei denn, die Ehen ab 1808 werden mit erfasst.** Dann wächst er mit.
Deshalb: Heiratsregister vor die späten Taufen ziehen.

## Zustand der Daten

| | |
|---|---|
| `Transkription-1808/daten/erfassung.sqlite` | 22 Taufeinträge, 396 Felder, keiner bestätigt |
| `Transkription-1808/daten/aenderung.sqlite` | 18 Merge-Vorgänge, rücknehmbar |
| `Transkription-1808/ausgabe/OFB_..._bereinigt.ged` | 6 Doppelfamilien zusammengelegt, 0 tote Verweise |
| `Transkription-1808/wissen/pilot4_ergebnisse.md` | Belege je Eintrag |

**Fehlt in den 22 Einträgen:** Geburtsdatum, Taufdatum, Paten, Geschlecht —
ausgewertet wurde nur der linke Blockder Seite. Bildstreifen über die volle
Zeilenbreite liegen bereits in `scans/zeilen/`.

**Offen im Bestand:** Staib-Doppelehe (doppeltes Kind 1793), von Westen
(echte Zweitehe, nicht anfassen), 6 Personendubletten mit identischem
Sterbedatum.

## Was zuerst gebaut werden muss

Die Reihenfolge ist wichtig — das Werkzeug hat derzeit alles **außer** dem Kern.

1. **API-Client und Transkriptionsprompt.** Ohne ihn ist es eine gewöhnliche
   Eingabemaske. Der Prompt existiert faktisch schon, verteilt über
   `ansatz.md` und die Fehlerkataloge.
2. **Spaltenraster einmal je Buch, geführt gezogen.** Voraussetzung für die
   gezielten Bildausschnitte. Nicht automatisieren — ist zweimal gescheitert.
3. **Matching anschließen.** Die Logik liegt fertig vor
   (`Transkription-1808/skripte/paar.py`, `suche.py`, `klassen.py`).

Erst danach lohnen Generalisierung, Oberflächenpolitur und die Frage nach
Hosting.

## Ungelöst

- **Seitenzerlegung** — bisher nur von Hand gemacht.
- **Ob das Verfahren ohne reichen Bestand trägt.** Bei Nachbarorten ohne
  eigenes Ortsfamilienbuch (Bönnigheim, Löchgau, Michelbach) war der Pilotlauf
  chancenlos.
- **Ob 0,13 $/Seite bei 42 % Rohfehlern die richtige Rechnung ist.**
