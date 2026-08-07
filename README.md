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

Die Reihenfolge **Ehen → Taufen → Tode** ist Bedingung, nicht Empfehlung.
Ein Bestand endet irgendwann; die Eltern einer Taufe von 1808 haben meist
vorher geheiratet und stehen noch drin, die von 1825 nicht mehr. Der
Elternehe-Anker versiegt also mit jedem Jahrgang — es sei denn, die Ehen
werden mit erfasst und vorher übergeben. Dann wächst er mit, statt zu
verfallen. Wer die Taufen vorzieht, prüft sie später ein zweites Mal.

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

## Ein Abgleichsverfahren, kein Leseverfahren

Wie gut die Maschine liest, hängt an der Handschrift, am Erhaltungszustand
und an der Auflösung des Scans — nicht am Werkzeug. Eine Trefferquote
anzugeben wäre deshalb irreführend: Sie gälte für ein Buch, eine Hand, einen
Bestand.

Worauf es stattdessen ankommt:

**Was gut lesbar ist, trägt den Abgleich — was schlecht lesbar ist, wird
durch ihn bestimmt.** Datum, Vornamen, Beruf und Ort sind auch in schwieriger
Kurrentschrift meist eindeutig; die Familiennamen sind es selten. Genau
deshalb wird der ganze Eintrag als Suchschlüssel benutzt und nicht Feld für
Feld geraten.

**Grün wird nur, was ein Anker bestätigt.** Weder die Selbsteinschätzung des
Modells noch die Häufigkeit eines Namens im Bestand machen grün. Ein Name,
der hundertmal vorkommt, ist deshalb noch lange nicht der, der dasteht.

**Nichtfinden ist ein Ergebnis, kein Fehler.** Zuzug, andere Parochie, Lücke
im Buch — das gehört vermerkt, nicht weggedrückt.

**Die Ausgabe ist verlustfrei.** Die Vorlage läuft Record für Record durch;
unberührte Records gehen zeichengleich hindurch. Belegt durch einen
Leerlauftest: ohne Änderungen muss die Ausgabe Byte für Byte der Vorlage
entsprechen. Das ist eine Eigenschaft des Codes, keine der Handschrift.

Alle Messwerte aus der Entwicklung — samt dem, was daran ungeprüft ist —
stehen in `doku/`, wo auch dabeisteht, woran sie gemessen wurden.

## Für welche Bücher

Der Lese-Teil setzt **tabellarisch geführte Register** voraus. Ob ein Bestand
geeignet ist, entscheidet nicht die Jahreszahl, sondern die Vorlage:

| Bedingung | warum |
|---|---|
| Formular mit festen, gedruckten Spalten | sonst kein Spaltenraster, kein gezielter Bildausschnitt, keine Familienbuch-Nummer |
| ein Eintrag = ein abgrenzbarer Block | sonst fehlt schon die Zerlegung der Seite in Einträge |
| lesbare Datums- und Nummernspalte | die Chronologie ist der billigste Anker — sie prüft, ohne den Bestand zu brauchen |
| Scan und Handschrift geben Datum, Vornamen, Beruf her | auf diesen Feldern ruht der Abgleich |

In Württemberg sind diese Bedingungen ab **1808** erfüllt: Das Generalreskript
vom 15. November 1807 verordnete beiden Konfessionen feste Spalten und führte
zugleich die Familienregister ein. Andere Territorien haben ihre eigenen
Zeitpunkte — und auch ein spätes, aber schlampig geführtes oder schlecht
gescanntes Buch kann ungeeignet sein.

Ältere Fließtext-Register liest die Werkstatt **nicht**. Sie kommen als
vorhandene Transkription in den Bestand und werden beim Abgleich gefunden —
Verknüpfen braucht kein Lesen; gemessen an Sterbeeinträgen 1750–1807
(`doku/verknuepfung.md`).

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

## Einblick

Die Stand-Seite mit der Ampel — grün ist nur, was ein Beleg bestätigt:

![Stand mit Ampel](doku/screenshots/stand.jpg)

Das Lesen läuft rundenweise über Claude Code; beantwortete Seiten werden
eingelesen, offene warten:

![Lesen](doku/screenshots/lesen.jpg)

Übergeben macht aus bestätigten Einträgen Personen und Familien — erst danach
kann die nächste Tranche gegen sie ankern:

![Übergeben](doku/screenshots/uebergeben.jpg)

Die GEDCOM-Ausgabe zeigt den Leerlauftest an: ohne Änderungen ist die Ausgabe
Byte für Byte die Vorlage:

![Ausgeben](doku/screenshots/ausgeben.jpg)

Kontextquellen und Aktkarten in den Einstellungen:

![Einstellungen](doku/screenshots/einstellungen.jpg)

Die Korrekturmaske, ein Eintrag zur Zeit: oben der Bildstreifen des
Originaleintrags, darunter was der Abgleich gesichert hat, was gelesen wurde,
und die Felder, die eine Entscheidung brauchen. Das Nachfragen-Feld stellt
Fragen direkt am Eintrag („steht da Möß oder Wöß?"):

![Korrigieren](doku/screenshots/korrigieren.jpg)

*Bildstreifen: Taufregister Haberschlacht 1808, Digitalisat via Archion.*

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
Einzelne Ausschnitte mit Quellenangabe — wie der Bildstreifen oben im
Einblick — sind von den Archion-Bedingungen gedeckt; die Regel gilt den
Beständen, nicht dem einzelnen Beleg.

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
The reading step presupposes tabular, pre-printed registers (in Württemberg
the rule from 1808 onward); older free-text entries are not read by the tool,
but existing transcriptions of them can be imported and matched against.
How well the machine reads depends on the hand, the state of the book and the
scan — not on the tool. What the tool contributes is the step afterwards:
deciding which of the six people named in a marriage entry already exist in
your dataset, and recording the evidence for each decision. Dedicated HTR
tools do the reading well; that decision is not what they are for.

Built for a single researcher working on their own parish. Local, SQLite, no
service, no accounts. Requires an Anthropic API key for the reading step —
note that this sends your scans to a third party, which your image licence
may or may not permit.

The interface and documentation are in German; the registers are German, and
so are the people this is built for. Interface strings are to be moved into
language files — not done yet.
