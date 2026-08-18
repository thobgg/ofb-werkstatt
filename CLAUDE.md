# OFB-Werkstatt

Werkstatt für ein **Ortsfamilienbuch**: Kirchenbuchseite lesen lassen, korrigieren,
gegen den Bestand abgleichen, anbinden oder neu anlegen, am Ende GEDCOM ausgeben.

**Funktioniert mit und ohne vorhandenen Bestand.** Wer eines fortschreibt, ankert
gegen sein GEDCOM; wer bei Null anfängt, gegen die eigenen früheren Einträge –
die ersten hundert tragen die nächsten tausend. Zwei der vier Ankertypen
(Chronologie, Kontext) brauchen überhaupt keinen Bestand.

⚠️ Der Nullstart ist **nie getestet** – alle bisherigen Messwerte stammen aus
einem Lauf gegen ein reiches Ortsfamilienbuch mit 4.111 Personen.

**Vor der Arbeit lesen – in dieser Reihenfolge:**
1. `doku/landkarte.md` – wo liegt was, welcher Bestand gilt wofür, **wann Thomas
   gefragt wird und wie**
2. `doku/ansatz.md` – Begründung aller Entwurfsentscheidungen, mit Messwerten
3. `doku/verknuepfung.md` – die Kaskade je Aktart, der anspruchsvollste Teil
4. `doku/naechste-sitzung.md` – Stand und offene Punkte

## Die drei Regeln der Zusammenarbeit

1. **Erst Regel, dann Ausnahmen.** Nie Einzelfälle abarbeiten, solange eine
   Regel möglich ist. Am 3.8. wurden acht Doppelehen einzeln diskutiert, bis
   Thomas bremste – die anschließende fünfzeilige Regel entschied sechs davon
   allein.
2. **Fragen sammeln.** Zweifelsfälle einer Runde am Stück vorlegen.
3. **Mit Empfehlung fragen.** Nicht „was soll ich tun", sondern „ich würde X,
   weil Y – einverstanden?"

⚠️ `~/ofb-ki/` wird **nur lesend** angefasst. Kein Eingriff ins Live-System.

## Verzeichnis

```
werkstatt/     Paket: db, konfig, suche, import_gedcom, raster, klassen, web/
konfig.toml      Registerarten, Felder, Vorbelegungen – alles Ortsspezifische
bilder/{ehe,taufe,tod}/   Scans je Aktart (nie einchecken)
daten/           erfassung.sqlite (nie einchecken)
doku/            ansatz.md, naechste-sitzung.md
start.py         python3 start.py → http://127.0.0.1:8765
```

## Die wichtigsten Regeln

**Dreischritt, nicht vermischen.** Erst vollständig transkribieren, dann matchen,
dann bestätigen. Feldweises Ankern während des Lesens bleibt beim falsch
gelesenen Nachnamen stecken.

**Was gut lesbar ist, trägt das Matching.** Vornamen, Datum, Beruf, Ort sind
praktisch fehlerfrei; Familiennamen waren im Pilotlauf zu 42 % falsch. Die
Nachnamen werden *durch* den Abgleich bestimmt, nicht umgekehrt.

**Selbsteinschätzung des Modells macht nicht grün.** Bei `Koch`/`Roth` war das
Modell viermal sicher und viermal falsch. Vokabular und Häufigkeit ebenso wenig –
`Roth` kommt 59-mal vor und hätte jeden Plausibilitätstest bestanden. Grün wird
nur, was ein Anker bestätigt.

**Kontext ist Teil der Information.** Ausschnitte nie isoliert zeigen oder ans
Modell schicken – weder in der Oberfläche noch im Prompt. Dieselbe Hand schreibt
in jedem Eintrag `B. u. Weingärtner in Haberschlacht`; daran eicht man die
Buchstaben.

**Modell schlägt vor, Skript entscheidet.** Alles, was Daten verändert, muss
reproduzierbar sein. Das Modell liest und schätzt ein; Abgleich, Regelentscheidung
und Änderung laufen deterministisch und landen im Journal.

**Kirchenbuchform nie überschreiben.** Drei Ebenen je Name: `gelesen` (Rohlesung,
bleibt erhalten auch wenn falsch), `kb_form` (wörtlich, → `_KB_NAME`), `kanonisch`
(normalisiert, → `NAME`).

## Frontend liegt in static/, nicht in Python-Strings

HTML, CSS und JavaScript der Maske liegen als echte Dateien in
`werkstatt/web/static/`; die Module `web/start.py` und `web/seite.py`
sind nur noch Lader. Anzeigecode nicht wieder in Python-Strings
anwachsen lassen - das war Davids berechtigter Einwand im Forum:
Strings haben kein Highlighting, kein Linting und unlesbare Diffs.
Neue Dateien in static/ gehören sofort in Git, sonst fehlen sie jedem
Klon (git ls-files ist die Quelle von Probelauf und Demo-Bau).

## Anker, nach Preis geordnet

| Anker | braucht | trägt ab |
|---|---|---|
| Chronologie – Datum zwischen Vorgänger und Nachfolger | nichts | erster Seite |
| Kontext der Nachbarzeilen | nichts | erster Seite |
| Bestand: Person, Elternehe, Beruf | vorhandenes GEDCOM | sofort |
| Verweise zwischen Tauf-, Ehe- und Totenregister | mehrere Register | nach Jahrgängen |

## Nicht bauen

Login, Hosting, Upload, Mehrbenutzerbetrieb, Web-Framework, Paket zum Doppelklick.
Zielgruppe ist **eine Person**, die ihre eigene Parochie abschreibt und Python
bedienen kann. `http.server` genügt.

Gleich mitnehmen, weil später teuer: Anzeigetexte in Sprachdateien (Deutsch
Standard, Englisch zweite Datei) und die `herkunft`-Spalte je Datensatz.

## Der Durchlauf

Eine **Runde** ist eine Tranche: so und so viele Seiten EINES Registers, die
zusammen gelesen, korrigiert und übergeben werden. Der Zustand liegt in der
Datenbank, nicht im Prozess – der Läufer arbeitet weiter, wenn das Browser-
fenster zugeht, und ein Abbruch hinterlässt einen lesbaren Zustand.

    geplant ──lesen──► korrigieren ──übergeben──► fertig
                            │
                            └── die Maske zeigt genau diese Runde

    /            Stand und der nächste Schritt als EIN Knopf
    /lesen       Tranche planen, Fortschritt je Seite
    /korrektur   Maske, auf die Runde eingeschränkt
    /uebergabe   Probelauf zeigen, auf zweiten Klick schreiben

Auf der Kommandozeile dasselbe:

```sh
python3 -m werkstatt.runde --stand
python3 -m werkstatt.runde --plane taufe --seiten 4 --quelle testdaten
python3 -m werkstatt.runde --lies 1
python3 -m werkstatt.runde --uebergib 1 --schreib
python3 -m werkstatt.runde --verwirf 1      # rückstandslos zurücknehmen
```

**Zwei Lesequellen.** `--quelle testdaten` spielt die 22 Piloteinträge ein
und braucht keinen API-Schlüssel. Das ist keine Bequemlichkeit: Die Maske war
seit dem Schemawechsel kaputt (`ofb_id` gegen `person`) und niemandem
aufgefallen, weil sie nur zwei Zustände kannte – leer, oder Schlüssel und
echtes Geld. Was nur gegen Bezahlung sichtbar wird, wird nicht geprüft.

Die Testquelle liefert **nur die Rohlesung**; die 39 geprüften Verweise
bleiben als Maßstab zurück (`werkstatt.abgleich --messe`). Wer sie mitliefert,
misst hinterher nur, dass er sie mitgeliefert hat.

⚠️ Ihre `gelesen`-Werte sind bereits die *korrigierten* Lesungen des
Pilotlaufs. Sie prüfen den Durchlauf, nicht die Lesequalität.

## Einstellungen: Struktur gegen Betrieb

    konfig.toml   Registerarten, Felder, Rollen, Kontextquellen
                  -> Struktur. Einmal beim Einrichten.
    einstellung   Seitenzahl je Register, Reihenfolge, Bildordner,
                  Autopilot, Lebensgrenzen
                  -> Betrieb. Beim Arbeiten, über /einstellungen.

Betriebswerte in die TOML-Datei zurückzuschreiben hieße, sie bei jedem Klick
neu zu erzeugen und dabei ihre Kommentare zu verlieren. Was in `einstellung`
fehlt, kommt weiterhin aus `konfig.toml`.

```sh
python3 -m werkstatt.einstellungen
python3 -m werkstatt.einstellungen --setze seiten.ehe 10
python3 -m werkstatt.einstellungen --setze reihenfolge ehe,taufe,tod
```

**Seitenzahlen ungleich mit Absicht:** Ehe 10, Taufe 20, Tod 20. Ein
Eheeintrag nennt sechs Personen, ein Taufeintrag drei.

**PDFs sind Behälter, keine Bilder.** Ein Archion-Download enthält oft den
halben Band. `seiten.entpacken()` zerlegt sie einmal mit `pdftoppm` (300 dpi)
nach `entpackt/`; danach zählen sie wie gewöhnliche Bilder. Ohne
poppler-utils meldet die Einstellungsseite das.

## KI-Anbindung

Modell, Bildkante und Tokengrenze stehen unter `/einstellungen`, nicht mehr
im Code. Preise je Million Token, Stand August 2026 – die Batch-API halbiert
beide:

| Modell | ein | aus | Bildkante |
|---|---|---|---|
| Opus 5 `claude-opus-5` | 5,00 $ | 25,00 $ | 2576 px |
| Sonnet 5 `claude-sonnet-5` | 3,00 $ | 15,00 $ | 2576 px |
| Haiku 4.5 `claude-haiku-4-5` | 1,00 $ | 5,00 $ | 1568 px |
| Fable 5 `claude-fable-5` | 10,00 $ | 50,00 $ | 2576 px |

**Die Bildkante ist der Hebel für die Lesequalität.** Sie stand auf 1568 px
mit dem Vermerk „größer bringt nichts, kostet nur Tokens" – das galt für die
damaligen Modelle. Opus 5 und Sonnet 5 nehmen **2576 px**. Bei Kurrentschrift
zählt genau das, und die eigene Messung sagt es: „Ancestry-JPG (24 MP) gegen
Archion-PDF (14 MP) löste Eheeintrag Nr. 4 auf, der vorher unlesbar war."
Der Preis ist klein – 1.600 auf 4.784 Bildtoken, bei Opus 5 rund zwei Cent
je Seite gegen gemessene 0,13 $.

Das Modell stand außerdem auf `claude-opus-4-5`. Jetzt `claude-opus-5`.

**Der Schlüssel wird nie angezeigt**, nur ob `ANTHROPIC_API_KEY` gesetzt ist.
Der Verbrauch kommt aus der Auftragstabelle – gemessen, nicht geschätzt.

### Zweiter Weg: über das eigene Abonnement

Quelle `datei` legt die Seiten ab und lässt sie von `claude -p` lesen. Das
läuft über den Zugang des Bearbeiters, kostet also keine zweite Rechnung.
**Es gibt dabei keinen Chat, an den sich die Werkstatt hängt** – jeder Aufruf
ist eine eigene, kurze Sitzung ohne Verlauf. Wer angemeldet ist, entscheidet
allein `claude auth login`; die Werkstatt hält keine Anmeldedaten und fragt
über `vorlage.bereitschaft()` nur `claude auth status` ab.

Im Zahnrad steht das Konto samt Abo, und wenn keines da ist, ein Knopf
„Jetzt anmelden" (`vorlage.anmelden()`). Er öffnet ein Terminalfenster mit
`claude auth login` – die Anmeldung schickt in den Browser und wartet auf
Rückmeldung, blind im Hintergrund geht sie nicht. Die Seite pollt danach
`/api/anmeldestand` und schaltet von selbst auf grün.

**Am 6. August 2026 unter Linux/XFCE ganz durchgelaufen**: abgemeldet, Server
neu gestartet, Knopf gedrückt, Fenster ging auf, Anmeldung im Browser, Seite
schaltete von selbst auf grün.

○ **Ungetestet bleiben Windows und macOS** – die Zweige für `cmd` und
Terminal.app. Zum Prüfen muss man sich abmelden, was die begleitende
Claude-Code-Sitzung mit beendet; also allein testen, nicht nebenher. Greift
`claude auth logout` nicht, hilft
`mv ~/.claude/.credentials.json ~/.claude/.credentials.json.aus`.

**Starten:** `python3 start.py` genügt – wartet auf den Server und öffnet den
Browser (`--kein-browser` schaltet das ab), und bei belegtem Port wird nur
das Fenster geöffnet. Die beiden Dateien zum Doppelklick reichen bloß durch.
Ein laufender Server merkt Codeänderungen nicht: nach dem Bearbeiten
`pkill -f "python3 start.py"`, sonst misst man den alten Stand – genau daran
ist der erste Anmeldetest gescheitert.

○ **Batch fehlt.** Halbiert die Kosten und ist bei seitenweiser Verarbeitung
der natürliche Modus. Der Rundenautomat ist bereits die Struktur, die Batch
braucht: eine Liste eingereichter Einheiten mit Zustand.

## Kontextquellen: was darf bestätigen

`[[kontext]]` in `konfig.toml`, eigene Pfade in `konfig.local.toml` (in
`.gitignore`). Jede Quelle trägt ihren Rang:

    gilt = "beleg"       darf bestätigen  → ein Treffer macht grün
    gilt = "vokabular"   rankt nur        → ein Treffer bleibt gelb

Der Rang landet in `herkunft.gilt`; damit ist die Ampelregel eine Abfrage und
keine Sonderlogik. Keine Quelle eingetragen = Nullstart: alles bleibt gelb,
die Maske legt jedes Feld vor. Langsam, aber nicht falsch.

## Stand – gemessen 4. August 2026

Fertig: Datenbasis mit Herkunftsrang, GEDCOM-Import verlustfrei, Suche mit
Äquivalenzklassen, Familienanbindung, Rundenautomat mit Hintergrundläufer,
Abgleich mit Ampel, Übergabe je Runde, vier Seiten Oberfläche.

Voller Durchlauf gegen die Testquelle, 4 Seiten Taufregister:

| | |
|---|---|
| gelesen | 22 Einträge, 102 gefüllte Felder |
| Ampel | 20 grün · 18 gelb · 6 rot · 58 grau |
| vorgelegt | 24 Felder von 102 brauchen eine Entscheidung |
| übergeben | 45 Personen neu, 20 verknüpft, 22 Familien, 22 Kinder |
| Abgleich gegen die geprüfte Wahrheit | **18 von 39 wiedergefunden (46 %), 0 falsch** |

Die 46 % sind die Untergrenze: Die Piloteinträge enthalten nur Nachnamen,
keine Vornamen und keine Daten – der Abgleich hat nur Nachname+Nachname+Ehe.

**Ein Falschtreffer, den die Messung gefunden hat.** Der Taufe Nr. 12 von 1809
wurde ein Paar zugeordnet, das 1699 und 1703 geboren wurde und dessen Frau
1767 starb – einziger gemeinsamer Nachname im Bestand, kein Trauungsdatum,
und damit **grün**. Seither prüft `abgleich._plausibel()` Lebensgrenzen, und
ohne ein Datum, das die Familie zeitlich einordnet, wird nichts mehr grün.

## Ausgabe – der Weg nach draußen

```sh
python3 -m werkstatt.ausgabe --leerlauf        Verlustfreiheit belegen
python3 -m werkstatt.ausgabe --fort -o x.ged   Fortschreibung
python3 -m werkstatt.ausgabe --neu  -o x.ged   Neuausgabe
```

`rec` bewahrt die Quelldatei vollständig und in Reihenfolge – **nicht nur
INDI und FAM.** Der Import verwarf vorher 158 Records: HEAD, SUBM, 35 SOUR,
120 `_LOC` und TRLR. Auf die `_LOC` zeigt jede Person mit `3 _LOC @L1@`.
Nachtragen für alte Bestände: `import_gedcom --nur-rec datei.ged`.

Der **Leerlauftest** ist der Beleg, nicht die Behauptung: Ohne Änderungen muss
die Ausgabe Byte für Byte der Vorlage entsprechen. Bei Abweichung nennt er die
Bytestelle.

**Was noch fehlt:** Bildausschnitte je Feld, und die Auswertung des
Journals beim Fortschreiben (nötig erst, wenn Records nicht nur ergänzt,
sondern geändert werden). Die Kaskaden für Ehe und Tod sind seit dem
18. August angeschlossen (`abgleich.register_anker`).

## Stand 6. August 2026 – was an diesem Tag entstand

Die App ist bedienbar geworden. Der Reihe nach:

**Anmeldung ohne Terminal.** Zahnrad zeigt Konto und Abo; ist niemand
angemeldet, steht dort ein Knopf, der ein Fenster mit `claude auth login`
öffnet und danach von selbst auf grün schaltet. Unter Linux/XFCE einmal
ganz durchgelaufen; Windows und macOS sind geschrieben und ungetestet
(`doku/windows-test.md` führt durch die Prüfung).

**Einrichtung.** Ein frisch ausgepacktes Projekt zeigt beim ersten Start
drei Fragen statt „Musterhausen" und schreibt `konfig.local.toml` selbst.
Ein Projekt bleibt ein Ordner.

**Quellen im Zahnrad.** Hinzufügen und Entfernen per Pfadfeld, kein
TOML-Bearbeiten mehr. Neu ist `import_wortschatz.py`: `.csv .tsv .txt
.xlsx .ods .docx` und ganze Ordner, Spalten aus der Kopfzeile erkannt,
Rang immer `vokabular`. Nach jedem Import werden die gemerkten Listen
verworfen und alles noch nicht Bestätigte neu abgeglichen.

**Arbeitskopie nach jeder Übergabe.** `ausgabe/<Gemeinde>_arbeitskopie.ged`,
vorige Fassung als `.vorher.ged`. Nicht erst am Ende – zwei getrennt
gewachsene Bestände hinterher zu verschmelzen bekommt niemand mehr sauber
hin.

**Gesprächsfenster unter jedem Eintrag.** Der Bearbeiter fragt, das Modell
antwortet mit Eintrag, Bildausschnitt und Bestandstreffern vor Augen –
und ändert nichts. Der Verlauf bleibt stehen.

**Randvermerk wird zum Sterbeereignis** (`randvermerk.py`), samt der
Zählmonate 7ber/8ber/9ber/Xber. Zwei von sechs Einträgen der Runde 1
tragen einen Tod am Rand.

**Feldkatalog** (`katalog.py`) – der eigentliche Umbau. Je Aktart steht
jetzt fest, was vorkommen *kann*, nicht was jemand nachgetragen hat:

    Taufe 16 -> 34 Felder · Ehe 22 -> 36 · Tod 10 -> 29

Jedes Feld weiß, ob es eine Kirchenbuchform hat und wohin beide Formen
gehören. Jedes Ziel ist eingestuft – GEDCOM 5.5.1, gebräuchlicher eigener
Tag, hauseigener Tag. Etwa ein Drittel ist hauseigen und übersteht einen
Programmwechsel nicht; dagegen steht `volltext`. Die Aktkarten sind im
Zahnrad bedienbar: abschalten, Ziele umhängen, eigene Felder ergänzen
(`feldwahl`).

**Bauplan aus dem Katalog.** `uebergabe` hatte eine zweite, von Hand
gepflegte Feldliste – und kannte das Sterbedatum nicht. Ereignisse werden
jetzt abgeleitet, alles Übrige landet in der neuen Tabelle `merkmal` und
von dort unverändert ins GEDCOM.

### Drei Fehler, die dabei herauskamen

- **Die zweite Ausgabe verlor die erste.** `fortschreiben` hängte nur an,
  was gerade eine Kennung bekommen hatte. Die Arbeitskopie der zweiten
  Runde hätte die erste stillschweigend weggeworfen. „Neu" heißt jetzt
  „steht nicht in der Vorlage".
- In der Ehe bekam der Bräutigam den Geburtsort der Braut – beide Felder
  zielen auf `BIRT.PLAC`.
- Ein Bildordner außerhalb des Projekts riss die Startseite ab
  (`relative_to` wirft dort). Dafür jetzt `konfig.kurz()`.

### Wo die Arbeit morgen ansetzt

**Runde 1 steht offen** (Seite 00359, sechs Einträge, Stand
`korrigieren`). Sie wurde vor dem Katalog gelesen und hat nur die alten
16 Felder – *geborene*, *Personenstand*, *Paten*, *Volltext* fehlen dort,
weil beim Lesen niemand danach gefragt hat.

Vorschlag: **Runde 1 verwerfen und 00359–00365 mit dem neuen Katalog neu
lesen.** Das ist zugleich der erste echte Durchlauf und bringt die
Stichprobe von 24 auf rund 68 Namensfelder – damit wird der Grenzfall von
29 % markiert entscheidbar. Kostet Abo-Zeit, keine Rechnung.

## Nächste Schritte

1. ~~Papierabgrenzung in `raster.py`~~ – **erledigt.** Nicht über Helligkeit
   (die Unterlage ist so hell wie das Papier), sondern über die gedruckten
   Linien. 22/22 Zeilenlinien bei ±40 px, 0 überzählige Vorschläge.
   Messung: `python3 -m werkstatt.messung`, Sollwerte in `daten/soll_zeilen.json`.
2. ~~**GEDCOM-Ausgabe**~~ – **erledigt.** `werkstatt/ausgabe.py`, zwei Arten:
   **Fortschreibung** reicht die Vorlage Record für Record durch (5.605
   zeichengleich, 9 ergänzt, 57 neu, 0 verloren, 0 tote Verweise) und belegt
   das mit dem **Leerlauftest**: `3444327 Byte, zeichengleich`. **Neuausgabe**
   schreibt alles aus den eigenen Tabellen – aber nur 31 % der Dateigröße,
   weil Quellen, Notizen, Paten und Ortsdefinitionen dabei wegfallen. Deshalb
   ist Durchreichen die Voreinstellung.
3. **Kaskaden für Ehe und Tod** – nach dem Muster von Taufe. `kaskade_tod.py`
   liegt fertig vor und ist noch nicht angeschlossen.
4. **Bildausschnitte je Feld.** Arbeitsteilung statt Entweder-Oder: Das Modell
   sagt, *welche* Zeile und *welche* Spalte (das braucht keine Pixel, weil
   Einträge und Zeilenbänder dieselbe Reihenfolge haben), die Geometrie
   liefert die Pixel. Koordinaten schätzen zu lassen ist zweimal gescheitert.
   `feld.bild_x/y/w/h` stehen im Schema und werden nie gefüllt.
5. **Registernamen aus dem Code lösen.** `ansatz.md` verspricht, ein
   englischsprachiger Nutzer könne sein Register frei benennen. Teilweise
   gelöst: `uebergabe` leitet den Bauplan jetzt aus dem Katalog ab. Verdrahtet
   bleiben `katalog.KATALOG`, `PAAR`, `KIND` und die Maske
   (`vater`/`mutter`/`braeutigam`).
6. **Katalogfelder in die Maske.** Die Aktkarte kennt 34 Felder, die
   Korrekturmaske zeigt Personenrollen, Datumsfelder und „alle Felder" –
   für Paten, Volltext und Unleserliches gibt es noch keine eigene Stelle.
7. **Kirchenbuchform beim Eintragen.** `feld.kb_form` wird gelesen und
   ausgegeben, aber in der Maske gibt es nur unter „alle Felder" ein
   Eingabefeld dafür.

**Spaltenraster bleibt Handarbeit.** Die Zeilen sitzen jetzt, die Spalten
nicht: die äußerste Randlinie fehlt teils (00365 beginnt bei x=1264 statt
1160). Einmal je Buch ziehen ist ohnehin der vorgesehene Weg.

## Nicht erneut versuchen

Automatische Zeilenerkennung per Textprojektion, proportional übertragene
Zeilenraster, Bounding Boxes vom Modell schätzen lassen. Messwerte in
`raster.py`.
