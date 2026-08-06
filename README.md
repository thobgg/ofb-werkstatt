# OFB-Werkstatt

Werkstatt für ein **Ortsfamilienbuch**: Kirchenbuchseite lesen lassen, gegen
den vorhandenen Bestand abgleichen, anbinden oder neu anlegen — und als
GEDCOM ausgeben.

> **In Arbeit.** Gebaut und gemessen an einem echten Bestand: den
> Kirchenbüchern von Haberschlacht, Württemberg, ab 1808. Für Fremde noch
> nicht ohne Weiteres benutzbar — siehe [Ausprobieren](#ausprobieren).
>
> Gebaut für **eine Person**, die ihre eigene Parochie abschreibt. Kein
> Login, kein Hosting, kein Mehrbenutzerbetrieb. Wer ein Kirchenbuch
> abschreibt, tut das aus persönlichem Bezug zum Ort — das sind Einzelne,
> keine Crowd, und jeder hat sein eigenes Dorf, seinen eigenen Bestand,
> seine eigene Handschrift.

## Wofür

Ahnenblatt, Gramps und webtrees können einen Bestand gut **verwalten**, aber
nur mühsam **aus einer Quelle erweitern**. Jeder Registereintrag stellt
dieselbe Frage — *vorhandene Person übernehmen* oder *neu anlegen* —, und
sie zu beantworten kostet viele Klicks. Hier ist sie vorbeantwortet und muss
nur noch bestätigt werden.

## Der Durchlauf

Eine **Runde** ist eine Tranche: so und so viele Seiten eines Registers, die
zusammen gelesen, korrigiert und übergeben werden.

    geplant ──lesen──► korrigieren ──übergeben──► fertig

Die Reihenfolge **Ehen → Taufen → Tode** ist Bedingung, nicht Empfehlung:
Der Elternehe-Anker trägt im Taufjahr 1808 noch 94 %, 1813 noch 53 %, 1820
nur 18 % — es sei denn, die Ehen sind vorher übergeben. Dann wächst er mit.

Der Zustand liegt in der Datenbank, nicht im Prozess. Der Läufer arbeitet im
Hintergrund weiter, wenn das Browserfenster zugeht, und ein Abbruch
hinterlässt einen lesbaren Zustand statt eines Rätsels.

## Wie es arbeitet

**Nah an der Quelle erfassen, nicht nah an GEDCOM.** Eine Zeile je
Registereintrag, so wie es dasteht. Die GEDCOM-Ausgabe wird daraus
abgeleitet. So lässt sich eine Zuordnung korrigieren, ohne die Lesung
anzufassen — und umgekehrt.

**Journal statt Veränderung.** Der Ausgangsbestand wird nie verändert. Jede
Ergänzung und jede Korrektur ist ein festgehaltener Vorgang mit seinem
Beleg; die Ausgabedatei entsteht daraus. Rücknahme heißt, einen Vorgang zu
deaktivieren.

**Belege statt Urteile.** Nicht „Sicherheitsstufe A", sondern *woran* eine
Aussage hängt: `Elternehe F1149, oo 14.02.1798`. Das Urteil folgt aus dem
Beleg, nicht umgekehrt.

**Der Bestand wächst mit.** Ohne vorhandenes GEDCOM gleicht die Werkstatt
gegen die eigenen früheren Einträge ab: Die ersten hundert tragen die
nächsten tausend.

## Was gemessen ist

Kein Wert hier ist geschätzt. Wo etwas ungeprüft ist, steht das dabei.

| | |
|---|---|
| GEDCOM-Fortschreibung einer übergebenen Runde | 5.605 Records zeichengleich durchgereicht, 9 ergänzt, 57 neu — **0 verloren, 0 tote Verweise** |
| Leerlauftest | `3444327 Byte, zeichengleich` — die Vorlage kommt Byte für Byte aus der Datenbank zurück |
| Abgleich gegen geprüfte Wahrheit | 18 von 39 Verweisen wiedergefunden (46 %), **0 Falschzuordnungen** |
| Bestandsprüfung, 4.111 Personen | 29 Fehler, 630 Warnungen |
| Zeilenerkennung im Seitenraster | 22 von 22 bei ±40 px, 0 überzählige Vorschläge |
| Rohlesung des Modells (Pilotlauf) | **42 % der Familiennamen falsch** |

Der letzte Wert ist der wichtigste: **Das ist ein Abgleichsverfahren, kein
Leseverfahren.** Auf 13,4 % markierte Felder kam der Pilotlauf erst durch den
Abgleich gegen den vorhandenen Bestand. Was gut lesbar ist — Datum, Vornamen,
Beruf, Ort — trägt den Abgleich; die Nachnamen werden *durch* ihn bestimmt.

**Grün wird nur, was ein Anker bestätigt.** Weder die Selbsteinschätzung des
Modells noch die Häufigkeit im Bestand machen grün: Bei `Koch`/`Roth` war das
Modell viermal sicher und viermal falsch, und `Roth` kommt 59-mal vor.

⚠️ **Ungeprüft ist die Lesequalität selbst.** Alle Zahlen oben messen die
Verknüpfung, nicht das Lesen — die Testdaten enthalten bereits korrigierte
Lesungen. Dafür braucht es einen Lauf über die API gegen eine Seite mit
bekannter Wahrheit. Ebenso ungeprüft: der Nullstart ohne vorhandenen Bestand,
und eine zweite Handschrift.

## Stand

| | |
|---|---|
| ✅ | Datenbasis in SQLite, GEDCOM-Import verlustfrei, Round-Trip zeichengleich |
| ✅ | Äquivalenzklassen für Namensvarianten, samt Erkennung falscher Kanten |
| ✅ | Korrekturmaske im Browser: Bildstreifen, Autovervollständigung, Familienanbindung |
| ✅ | Rundenautomat mit Hintergrundläufer, Fehler je Seite statt je Lauf |
| ✅ | Abgleich mit Ampel, Herkunftsrang (was darf bestätigen, was nur ranken) |
| ✅ | GEDCOM-Ausgabe: Fortschreibung und Neuausgabe |
| ✅ | Bestandsprüfung nach Vorbild von Gramps und Ahnenblatt |
| 🚧 | Bedienschleife: ein Eintrag zur Zeit statt der ganzen Runde auf einer Seite |
| ⬜ | Batch-API — halbiert die Kosten, bei seitenweiser Verarbeitung der natürliche Modus |
| ⬜ | Kaskaden für Ehe und Tod (die für Taufe steht) |
| ⬜ | Bildausschnitt je Feld statt ganzem Zeilenstreifen |

## Ein Sprachmodell ist Voraussetzung, nicht Zubehör

Der ganze Sinn ist *Maschine liest zuerst, Mensch korrigiert*. Ohne das wäre
es eine gewöhnliche Eingabemaske — und die haben Ahnenblatt, Gramps und
webtrees längst.

**Beim Lesen verlassen die Kirchenbuchbilder den eigenen Rechner.** Sie gehen
an die Anthropic-API. Scans von Archion, Ancestry oder einem Archiv
unterliegen deren Nutzungsbedingungen; ob die eine Übermittlung an einen
Dienstleister decken, muss jeder für seine eigenen Quellen klären.

Alles Übrige bleibt lokal: Bestand, Erfassung und Ausgabe liegen in einer
SQLite-Datei und im Ordner `ausgabe/`. Der Server hört nur auf `127.0.0.1`.

Zwei Teile laufen ganz ohne Modell — die Bestandspflege (Dublettensuche,
Äquivalenzklassen, Plausibilitätsprüfung) und die GEDCOM-Ausgabe. Nützlich,
aber nicht der Grund, warum es das Projekt gibt.

## Ausprobieren

```sh
python3 start.py          # → http://127.0.0.1:8765
```

Ohne Fremdbibliotheken außer Pillow; `http.server` aus der Standardbibliothek
genügt.

⚠️ **Die mitgelieferte Testquelle läuft derzeit nur auf dem Rechner des
Autors** — sie sucht die 22 Piloteinträge in einem Nachbarverzeichnis, das im
Repo nicht enthalten ist. Wer klont, kann den Durchlauf also nur mit eigenem
`ANTHROPIC_API_KEY` und eigenen Scans erproben. Das ist der nächste Punkt,
der zu beheben wäre, falls jemand es wirklich versuchen will.

## Einrichten

Alles Ortsspezifische steht in `konfig.toml` — Registerarten, Felder,
Vorbelegungen. Eigene Pfade gehören nach `konfig.local.toml`; die steht in
`.gitignore`.

```toml
[register.taufe]
titel    = "Taufregister"
ordner   = "bilder/taufe"
personen = ["kind", "vater", "mutter"]

[[kontext]]
name      = "Eigenes Ortsfamilienbuch"
art       = "gedcom"
datei     = "quellen/OFB_Musterhausen.ged"
gilt      = "beleg"          # darf bestätigen → ein Treffer macht grün
parochien = ["Musterhausen"]
```

Der **Rang** einer Quelle ist die eine Angabe, die über die Ampel
entscheidet: `beleg` darf bestätigen, `vokabular` rankt nur. Keine Quelle
eingetragen heißt Nullstart — dann bleibt alles gelb und jedes Feld wird
vorgelegt. Langsam, aber nicht falsch.

Betriebswerte (Seitenzahl je Runde, Reihenfolge, Bildordner, Modell,
Plausibilitätsgrenzen) stehen unter **Einstellungen** in der Oberfläche, nicht
in der Datei.

## Rechtliches

Scans von Archion, Ancestry und ähnlichen Diensten **dürfen nicht
weiterverbreitet werden**. `bilder/` und `daten/` sind deshalb von der
Versionsverwaltung ausgenommen und gehören in kein öffentliches Repo.

## Sprache

Deutsch ist die Hauptsprache: Code, Kommentare, Konfigurationsschlüssel und
Oberfläche. Die Register, die abgeschrieben werden, sind deutsch — und die
Menschen, für die das gebaut ist, ebenso.

Anzeigetexte sollen vom Code getrennt werden, damit weitere Sprachen ohne
Eingriff in die Logik hinzukommen können. Noch nicht umgesetzt.

## Zum Nachlesen

Alle Entwurfsentscheidungen stehen mit ihren Messwerten in `doku/`:

| | |
|---|---|
| `doku/landkarte.md` | wo liegt was, welcher Bestand gilt wofür |
| `doku/ansatz.md` | Begründung aller Entwurfsentscheidungen |
| `doku/verknuepfung.md` | die Kaskade je Aktart — der anspruchsvollste Teil |
| `doku/workflow.md` | der Arbeitsablauf von der ersten Seite bis zur Ausgabe |
| `doku/naechste-sitzung.md` | Stand und offene Punkte |

Lizenz: MIT.

---

## In English

**OFB-Werkstatt** builds a German *Ortsfamilienbuch* (local family register)
from parish registers: a model transcribes the page, you correct it, and each
named person is matched against your existing dataset — or against your own
earlier entries, if you start from scratch. Output is GEDCOM.

It is **a matching tool with a reader attached**, not a transcription tool.
In the pilot run 42 % of surnames were read wrong; the usable result came
entirely from matching against an existing dataset. Existing tools (Transkribus
and others) do the reading well — what they do not do is decide which of the
six people in a marriage entry already exist in your data, and record why.

Built for a single researcher working on their own parish. Local, SQLite, no
service, no accounts. Requires an Anthropic API key for the reading step —
note that this sends your scans to a third party, which your image licence
may or may not permit.

The interface and documentation are in German; the registers are German, and
so are the people this is built for. Interface strings are to be moved into
language files — not done yet.
