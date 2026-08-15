# OFB-Werkstatt

Werkstatt für ein **Ortsfamilienbuch**: Kirchenbuchseite lesen lassen, gegen
den vorhandenen Bestand abgleichen, anbinden oder neu anlegen – und als
GEDCOM ausgeben.

> **In Arbeit.** Gebaut und gemessen an einem echten Bestand: den
> Kirchenbüchern von Haberschlacht, Württemberg, ab 1808. Für Fremde noch
> nicht ohne Weiteres benutzbar – siehe [Ausprobieren](#ausprobieren).
>
> Gebaut für **eine Person**, die ihre eigene Parochie abschreibt: ohne
> Login, ohne Hosting, ohne Mehrbenutzerbetrieb. Wer ein Kirchenbuch
> abschreibt, tut das aus persönlichem Bezug zum Ort; jeder hat sein eigenes
> Dorf, seinen eigenen Bestand, seine eigene Handschrift.

## Wofür

Ahnenblatt, Gramps und webtrees können einen Bestand gut **verwalten**, aber
nur mühsam **aus einer Quelle erweitern**. Jeder Registereintrag stellt
dieselbe Frage – *vorhandene Person übernehmen* oder *neu anlegen* –, und
sie zu beantworten kostet viele Klicks. Hier ist sie vorbeantwortet und muss
nur noch bestätigt werden.

## Der Durchlauf

Eine **Runde** ist eine Tranche: so und so viele Seiten eines Registers, die
zusammen gelesen, korrigiert und übergeben werden.

    geplant ──lesen──► korrigieren ──übergeben──► fertig

Die Reihenfolge **Ehen → Taufen → Tode** muss eingehalten werden.
Ein Bestand endet irgendwann; die Eltern einer Taufe von 1808 haben meist
vorher geheiratet und stehen noch drin, die von 1825 nicht mehr. Der
Elternehe-Anker versiegt also mit jedem Jahrgang – es sei denn, die Ehen
werden mit erfasst und vorher übergeben. Dann wächst er mit. Wer die Taufen
vorzieht, prüft sie später ein zweites Mal.

Der Zustand liegt in der Datenbank. Der Läufer arbeitet im Hintergrund
weiter, wenn das Browserfenster zugeht, und nach einem Abbruch ist ablesbar,
wie weit er gekommen ist.

## Wie es arbeitet

**Nah an der Quelle erfassen, nicht nah an GEDCOM.** Eine Zeile je
Registereintrag, so wie es dasteht; die GEDCOM-Ausgabe wird daraus
abgeleitet. So lässt sich eine Zuordnung korrigieren, ohne die Lesung
anzufassen – und umgekehrt.

**Der Ausgangsbestand bleibt unangetastet.** Jede Ergänzung und jede
Korrektur ist ein festgehaltener Vorgang mit seinem Beleg; die Ausgabedatei
entsteht daraus. Rücknahme heißt, einen Vorgang zu deaktivieren.

**Jede Zuordnung führt ihren Beleg mit.** Also `Elternehe F1149,
oo 14.02.1798` – woran die Aussage hängt, in nachprüfbarer Form. Wie sicher
sie ist, ergibt sich daraus.

**Der Bestand wächst mit.** Ohne vorhandenes GEDCOM gleicht die Werkstatt
gegen die eigenen früheren Einträge ab: Die ersten hundert tragen die
nächsten tausend.

## Wo die Arbeit liegt

Wie gut die Maschine liest, hängt an der Handschrift, am Erhaltungszustand
und an der Auflösung des Scans. Eine Trefferquote anzugeben wäre deshalb
irreführend: Sie gälte für ein Buch, eine Hand, einen Bestand. Der Teil, den
die Werkstatt beisteuert, ist der Schritt danach – die Entscheidung, welche
der sechs Personen eines Eheeintrags im Bestand schon stehen.

**Was gut lesbar ist, trägt den Abgleich – was schlecht lesbar ist, wird
durch ihn bestimmt.** Datum, Vornamen, Beruf und Ort sind auch in schwieriger
Kurrentschrift meist eindeutig; die Familiennamen sind es selten. Genau
deshalb dient der ganze Eintrag als Suchschlüssel.

**Grün wird nur, was ein Anker bestätigt.** Weder die Selbsteinschätzung des
Modells noch die Häufigkeit eines Namens im Bestand machen grün. Ein Name,
der hundertmal vorkommt, ist deshalb noch lange nicht der, der dasteht.

**Nichtfinden ist ein Ergebnis.** Zuzug, andere Parochie, Lücke im Buch –
das gehört vermerkt.

**Die Ausgabe ist verlustfrei.** Die Vorlage läuft Record für Record durch;
unberührte Records gehen zeichengleich hindurch. Belegt durch einen
Leerlauftest: ohne Änderungen muss die Ausgabe Byte für Byte der Vorlage
entsprechen.

Alle Messwerte aus der Entwicklung – samt dem, was daran ungeprüft ist –
stehen in `doku/`, wo auch dabeisteht, woran sie gemessen wurden.

## Für welche Bücher

Der Lese-Teil setzt **tabellarisch geführte Register** voraus. Über die
Eignung eines Bestandes entscheiden vier Eigenschaften der Vorlage:

| Bedingung | warum |
|---|---|
| Formular mit festen, gedruckten Spalten | sonst kein Spaltenraster, kein gezielter Bildausschnitt, keine Familienbuch-Nummer |
| ein Eintrag = ein abgrenzbarer Block | sonst fehlt schon die Zerlegung der Seite in Einträge |
| lesbare Datums- und Nummernspalte | die Chronologie ist der billigste Anker – sie prüft, ohne den Bestand zu brauchen |
| Scan und Handschrift geben Datum, Vornamen, Beruf her | auf diesen Feldern ruht der Abgleich |

In Württemberg sind diese Bedingungen ab **1808** erfüllt: Das Generalreskript
vom 15. November 1807 verordnete beiden Konfessionen feste Spalten und führte
zugleich die Familienregister ein. Andere Territorien haben ihre eigenen
Zeitpunkte – und auch ein spätes, aber schlampig geführtes oder schlecht
gescanntes Buch kann ungeeignet sein.

Ältere Fließtext-Register liest die Werkstatt **nicht**. Sie kommen als
vorhandene Transkription in den Bestand und werden beim Abgleich trotzdem
gefunden – der arbeitet auf Daten und ist vom Seitenlayout unabhängig.
Gemessen an Sterbeeinträgen 1750–1807 (`doku/verknuepfung.md`).

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
| ⬜ | Batch-API – halbiert die Kosten, bei seitenweiser Verarbeitung der natürliche Modus |
| ⬜ | Kaskaden für Ehe und Tod (die für Taufe steht) |
| ⬜ | Bildausschnitt je Feld statt ganzem Zeilenstreifen |

## Einblick

Die Stand-Seite mit der Ampel – grün ist nur, was ein Beleg bestätigt:

![Stand mit Ampel](doku/screenshots/stand.jpg)

Das Lesen läuft rundenweise über Claude Code; beantwortete Seiten werden
eingelesen, offene warten:

![Lesen](doku/screenshots/lesen.jpg)

Übergeben macht aus bestätigten Einträgen Personen und Familien – erst danach
kann die nächste Tranche gegen sie ankern:

![Übergeben](doku/screenshots/uebergeben.jpg)

Die GEDCOM-Ausgabe zeigt den Leerlauftest an: ohne Änderungen ist die Ausgabe
Byte für Byte die Vorlage:

![Ausgeben](doku/screenshots/ausgeben.jpg)

Die Seite **Formular** liest, was das Buch selbst über sich sagt: Aus den
gedruckten Spaltenköpfen jeder fünften Seite entstehen die Formularperioden,
darunter steht die Aktkarte mit den Feldern, die diese Registerart führt. Die
Schreiber fallen gratis aus den erfassten Einträgen – der taufende Geistliche
steht ja als eigene Spalte im Formular:

![Formular](doku/screenshots/formular.jpg)

Die Einstellungen liegen hinter fünf Reitern; hier die Kontextquellen mit
ihrem Rang – nur was *bestätigen* darf, macht grün:

![Einstellungen](doku/screenshots/einstellungen.jpg)

Die Korrekturmaske, ein Eintrag zur Zeit. Oben der gedruckte Spaltenkopf
und darunter, auf dieselbe Breite geschnitten, die Zeile des Originals –
über beide Buchseiten hinweg, denn ein Eintrag läuft über den Bund. Dann
was der Abgleich gesichert hat, was gelesen wurde, und die Felder, die
eine Entscheidung brauchen. *Ganze Seite* zeigt die Buchöffnung mit
markierter Zeile, *nochmal lesen* liest dieselbe Zeile ein zweites Mal und
stellt die Unterschiede gegenüber:

![Korrigieren](doku/screenshots/korrigieren.jpg)

*Bildstreifen: Evangelische Kirchengemeinde Haberschlacht, Taufregister
Bd. 4, Bild 1184798-00359, Eintrag Nr. 1 von 1808. Digitalisat über
Ancestry.*

## Das Sprachmodell ist Voraussetzung

Der ganze Sinn ist *Maschine liest zuerst, Mensch korrigiert*. Ohne das wäre
es eine gewöhnliche Eingabemaske – und die haben Ahnenblatt, Gramps und
webtrees längst.

**Beim Lesen verlassen die Kirchenbuchbilder den eigenen Rechner.** Sie gehen
an die Anthropic-API. Scans von Archion, Ancestry oder einem Archiv
unterliegen deren Nutzungsbedingungen; ob die eine Übermittlung an einen
Dienstleister decken, muss jeder für seine eigenen Quellen klären.

Zwei Klarstellungen dazu, weil hier viele hängenbleiben:

**Zum Training verwendet werden sie nicht.** Anthropic schreibt für die
kommerziellen Produkte: *„By default, we will not use your inputs or
outputs from our commercial products (e.g. Claude for Work, Anthropic API,
Claude Gov, etc.) to train our models."* Anders liegt es nur, wenn man
ausdrücklich Rückmeldung gibt oder der Nutzung zustimmt.

**Gespeichert werden sie aber.** Eine Aufbewahrungsfrist ist Sache des
Vertrags; ohne eigene Vereinbarung ist nicht zugesichert, dass die Bilder
nach der Verarbeitung verschwinden. Wer das braucht, muss es vereinbaren –
und wer es genau wissen will, liest die Bedingungen selbst, nicht diese
Zeile.

Die Übermittlung ist eine **Verarbeitung, keine Veröffentlichung** –
funktional wie eine Texterkennung, die auf fremder Hardware läuft. Das ist
eine Einordnung, keine Erlaubnis: Ob die eigenen Nutzungsbedingungen sie
decken, entscheidet nicht diese Datei.

Wer die Bilder gar nicht aus der Hand geben will, hat einen Weg: die
Testquelle braucht kein Modell, und die Bestandspflege und die
GEDCOM-Ausgabe laufen ohnehin ohne.

Alles Übrige bleibt lokal: Bestand, Erfassung und Ausgabe liegen in einer
SQLite-Datei und im Ordner `ausgabe/`. Der Server hört nur auf `127.0.0.1`.

Zwei Teile laufen ganz ohne Modell: die Bestandspflege (Dublettensuche,
Äquivalenzklassen, Plausibilitätsprüfung) und die GEDCOM-Ausgabe.

### Offen für ein lokales Modell

Das Lesen ist der einzige Teil, der ein Modell braucht, und es hängt an
einer einzigen Funktion: Bilder und Anweisung gehen als JSON an einen
Endpunkt. Wer statt der Anthropic-API einen lokalen Dienst ansprechen
will, tauscht diese Stelle aus; Ollama, llama.cpp und vLLM sprechen alle
denselben Dialekt. Abgleich, Ampel, Übergabe und Ausgabe merken davon
nichts. Für sie ist eine Lesung eine Lesung.

Auch eine reine **Handschrifterkennung** (TrOCR, Kraken, Transkribus)
lässt sich hier andocken. Die Seite wird ohnehin zeilenweise geschnitten,
und Zeilenbilder sind genau das, was solche Modelle erwarten. Sie liefern
allerdings Text, keine Felder. Für die Zuordnung „welcher Text gehört in
welche Spalte" bräuchte es ein verlässliches Spaltenraster, und das ist
derzeit die schwächste Stelle der Geometrie. Einmal je Buch von Hand
gezogen wäre der gangbare Weg.

**Versprochen wird nichts.** Ob ein offenes Modell Kurrent des 18. und
19. Jahrhunderts brauchbar liest, ist eine Messung und keine Meinung. Sie
ist mit dem machbar, was hier beiliegt: fünfzehn Seiten, 93 fertige
Lesungen als Vergleich, und der Knopf *nochmal lesen*, der zwei Lesungen
derselben Zeile nebeneinanderstellt. Wer ein lokales Modell anschließt,
sieht in einer Stunde, wo es abfällt.

Und für den Fall, dass es schlechter liest: Das macht die Werkstatt nicht
überflüssig, sondern nötiger. Ein schwächeres Modell verschiebt die Arbeit
zur Korrektur, und dafür ist die Maske gebaut. Der Ansatz ist gegenüber
der Lesegüte gleichgültig; sie bestimmt nur, wie viel Arbeit übrig bleibt.

## Ausprobieren

**Fünfzehn Beispielseiten liegen bei** – je fünf aus Tauf-, Ehe- und
Sterberegister der Pfarrei Haberschlacht, Jahrgänge ab 1808, dazu 93
Rohlesungen aus fünfzehn Seiten aller drei Register – so wie ein Modell
sie gelesen hat, vor jeder Korrektur. Damit läuft der ganze Durchlauf ohne eigene
Bücher und ohne API-Schlüssel: einrichten, unter **Lesen** die Quelle
*Testdaten* wählen, korrigieren, übergeben, GEDCOM ausgeben.

Zu sehen ist dabei, worauf es ankommt: der Bildstreifen je Eintrag mit
dem gedruckten Spaltenkopf darüber, der Knopf *ganze Seite* mit der
markierten Zeile, die Ampel, die Aktkarte, die Formularperioden.

### Was die Beispiele zeigen – und was nicht

Nicht dabei ist die geprüfte Wahrheit. Die von Hand geprüften
Personenverweise bleiben zurück, damit der Abgleich sie selbst
wiederfinden muss.

**Ein kleiner Bestand liegt bei**, sonst bliebe der Kern unsichtbar. Der
Elternehe-Anker trägt nur, wenn der Bestand die Zeit *vor* den Taufen
abdeckt – und die beiliegenden Eheseiten sind Trauungen von 1808, während
die Eltern der 1808 getauften Kinder vorher geheiratet haben. Wer nur sie
liest und übergibt, bekommt 38 Personen in den Bestand und trotzdem null
grün.

`demo/bestand.ged` schließt die Lücke: 23 Personen, 12 Familien und die
drei Quellen- und drei Ortsdefinitionen, auf die sie zeigen, 15 kB,
genau die, die zu den Beispielseiten gehören. Damit werden auf denselben
Seiten **10 Felder grün** – und der Beleg steht daneben:

    Nr 1  vater_name   Elternehe F3 über Vornamen beider Eltern, oo 26 NOV 1800

Die Einrichtung bietet den Auszug beim Anlegen an; wer ihn weglässt, sieht
den Nullstart, und der ist genauso richtig, nur langsamer.

Was sich damit prüfen lässt:

| | |
|---|---|
| Läuft der Durchlauf durch? | ja – lesen, korrigieren, übergeben, GEDCOM |
| Wann wird etwas grün, wann nicht? | ja – mit und ohne Auszug vergleichbar |
| Liest ein anderes Programm das Ergebnis? | ja – exportieren und in Gramps o. ä. importieren |
| Überleben die eigenen Tags den Wechsel? | ja, prüfbar – sie werden dort zu Notizen |
| Wie gut liest die Maschine? | nur mit eigenem Zugang, über *nochmal lesen* |
| Ist die Fortschreibung verlustfrei? | ja – der Auszug dient als Vorlage, 15.801 Byte zeichengleich |
| Wie oft liest die Maschine falsch? | **nicht** – dafür fehlt die korrigierte Fassung |

Diese Zahlen sind nachprüfbar, und zwar mit einem Befehl:

```
python3 -m werkstatt.probelauf
```

Der baut aus `git ls-files` einen Klon in ein Wegwerfverzeichnis, startet
ihn dort als eigenen Prozess und fährt den ganzen Durchlauf: einrichten,
drei Register lesen, bestätigen, übergeben, ausgeben. Am Ende stehen die
Zahlen dieser Seite, und wenn eine abweicht, sagt er welche. Aus einer
frischen venv aufgerufen prüft er zugleich, ob die genannten Pakete
wirklich reichen.

Das ist kein Zierrat: Die Demo lief lange nur auf dem Rechner des Autors
richtig, weil dort das Nachbarprojekt mit allen Bildern liegt und die
Testquelle deshalb einen anderen Zweig nahm als im Klon. Aufgefallen ist
das erst, als der Klon zum ersten Mal wirklich gebaut wurde.

Herkunft und Zitation der Beispielseiten stehen in `demo/QUELLE.md`.

Läuft unter Linux, Windows und macOS. Gebraucht wird Python ab 3.11,
alles Weitere holt das Startskript selbst:

| | |
|---|---|
| Windows | `OFB-Werkstatt starten (Windows).bat` doppelklicken – prüft der Reihe nach, was fehlt, und sagt es im Klartext. Ersteinrichtung Schritt für Schritt: `doku/windows-test.md` |
| Linux / macOS | `OFB-Werkstatt starten (Linux+Mac).command` anklicken, oder im Terminal `python3 start.py` |

Beides endet auf `http://127.0.0.1:8765` im Browser.

Zwei Fremdpakete: **Pillow** schneidet die Seitenbilder, **numpy** findet
darin die Zeilen. Beide holt `start.py` beim ersten Start selbst und sagt
dabei, was es tut; von Hand geht `python3 -m pip install -r
requirements.txt`. Der Rest ist Standardbibliothek, der Webserver ist
`http.server`.

Python 3.11 ist keine Willkür: Die Konfiguration wird mit `tomllib` gelesen,
und das kam erst mit 3.11. Ältere Fassungen halten wir nicht offen, dafür
prüft `start.py` die Version und sagt es im Klartext, statt abzustürzen.

## Einrichten

Alles Ortsspezifische steht in `konfig.toml` – Registerarten, Felder,
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
eingetragen heißt Nullstart – dann bleibt alles gelb und jedes Feld wird
vorgelegt. Langsam, aber nicht falsch.

Betriebswerte (Seitenzahl je Runde, Reihenfolge, Bildordner, Modell,
Plausibilitätsgrenzen) stehen unter **Einstellungen** in der Oberfläche, nicht
in der Datei.

## Rechtliches

Scans von Archion, Ancestry und ähnlichen Diensten **dürfen nicht
weiterverbreitet werden**. `bilder/` und `daten/` sind deshalb von der
Versionsverwaltung ausgenommen und gehören in kein öffentliches Repo.

Zwei Ausnahmen stehen hier bewusst und begründet:

**Der Bildstreifen** im Abschnitt *Einblick* belegt die beschriebene
Funktion – ohne ihn ist von der Arbeitsweise nichts zu sehen. Er ist ein
Ausschnitt mit Quellenangabe; die abgebildete Vorlage stammt aus 1808 und
ist gemeinfrei. Nach § 68 UrhG gilt das seit 2021 auch für originalgetreue
Reproduktionen gemeinfreier Werke.

**Die fünfzehn Beispielseiten** in `demo/bilder/` machen die Werkstatt ohne
eigene Bücher ausprobierbar. Herkunft, Bandangabe und Zitation stehen in
`demo/QUELLE.md`. Auch hier: Vorlagen von 1808/09, gemeinfrei, § 68 UrhG.

Ob die eigenen Zugangsbedingungen eine solche Verwendung decken, bleibt
Sache dessen, der sie eingeht – diese Datei nimmt die Entscheidung nicht
ab, sie legt nur offen, was hier liegt und warum.

**Die MIT-Lizenz gilt für den Code dieses Repos**, nicht für
Kirchenbuchdaten, Scans oder daraus erzeugte Transkriptionen. Für die
gelten die Bedingungen der jeweiligen Quelle.

## Sprache

Deutsch ist die Hauptsprache: Code, Kommentare, Konfigurationsschlüssel und
Oberfläche. Die Register, die abgeschrieben werden, sind deutsch – und die
Menschen, für die das gebaut ist, ebenso.

Anzeigetexte sollen vom Code getrennt werden, damit weitere Sprachen ohne
Eingriff in die Logik hinzukommen können. Noch nicht umgesetzt.

## Zum Nachlesen

Alle Entwurfsentscheidungen stehen mit ihren Messwerten in `doku/`:

| | |
|---|---|
| `doku/landkarte.md` | wo liegt was, welcher Bestand gilt wofür |
| `doku/ansatz.md` | Begründung aller Entwurfsentscheidungen |
| `doku/verknuepfung.md` | die Kaskade je Aktart – der anspruchsvollste Teil |
| `doku/workflow.md` | der Arbeitsablauf von der ersten Seite bis zur Ausgabe |
| `doku/naechste-sitzung.md` | Stand und offene Punkte |

Lizenz: MIT.

---

## In English

**OFB-Werkstatt** builds a German *Ortsfamilienbuch* (local family register)
from parish registers: a model transcribes the page, you correct it, and each
named person is matched against your existing dataset – or against your own
earlier entries, if you start from scratch. Output is GEDCOM.

The emphasis is on **matching**, with a reader attached. The reading step
presupposes tabular, pre-printed registers (in Württemberg the rule from 1808
onward); older free-text entries are left to dedicated HTR tools, and their
transcriptions can be imported and matched against. How well the machine
reads depends on the hand, the state of the book and the scan. What this tool
adds is the step afterwards: deciding which of the six people named in a
marriage entry already exist in your dataset, and recording the evidence for
each decision.

Built for a single researcher working on their own parish. Local, SQLite, no
service, no accounts. Requires an Anthropic API key for the reading step –
note that this sends your scans to a third party, which your image licence
may or may not permit.

The interface and documentation are in German; the registers are German, and
so are the people this is built for. Interface strings are to be moved into
language files – not done yet.
