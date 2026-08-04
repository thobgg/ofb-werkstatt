# OFB-Werkstatt

Werkstatt für ein **Ortsfamilienbuch**: Kirchenbuchseite lesen lassen, korrigieren,
gegen den Bestand abgleichen, anbinden oder neu anlegen, am Ende GEDCOM ausgeben.

**Funktioniert mit und ohne vorhandenen Bestand.** Wer eines fortschreibt, ankert
gegen sein GEDCOM; wer bei Null anfängt, gegen die eigenen früheren Einträge —
die ersten hundert tragen die nächsten tausend. Zwei der vier Ankertypen
(Chronologie, Kontext) brauchen überhaupt keinen Bestand.

⚠️ Der Nullstart ist **nie getestet** — alle bisherigen Messwerte stammen aus
einem Lauf gegen ein reiches Ortsfamilienbuch mit 4.111 Personen.

**Vor der Arbeit lesen — in dieser Reihenfolge:**
1. `doku/landkarte.md` — wo liegt was, welcher Bestand gilt wofür, **wann Thomas
   gefragt wird und wie**
2. `doku/ansatz.md` — Begründung aller Entwurfsentscheidungen, mit Messwerten
3. `doku/verknuepfung.md` — die Kaskade je Aktart, der anspruchsvollste Teil
4. `doku/naechste-sitzung.md` — Stand und offene Punkte

## Die drei Regeln der Zusammenarbeit

1. **Erst Regel, dann Ausnahmen.** Nie Einzelfälle abarbeiten, solange eine
   Regel möglich ist. Am 3.8. wurden acht Doppelehen einzeln diskutiert, bis
   Thomas bremste — die anschließende fünfzeilige Regel entschied sechs davon
   allein.
2. **Fragen sammeln.** Zweifelsfälle einer Runde am Stück vorlegen.
3. **Mit Empfehlung fragen.** Nicht „was soll ich tun", sondern „ich würde X,
   weil Y — einverstanden?"

⚠️ `~/ofb-ki/` wird **nur lesend** angefasst. Kein Eingriff ins Live-System.

## Verzeichnis

```
werkstatt/     Paket: db, konfig, suche, import_gedcom, raster, klassen, web/
konfig.toml      Registerarten, Felder, Vorbelegungen — alles Ortsspezifische
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
Modell viermal sicher und viermal falsch. Vokabular und Häufigkeit ebenso wenig —
`Roth` kommt 59-mal vor und hätte jeden Plausibilitätstest bestanden. Grün wird
nur, was ein Anker bestätigt.

**Kontext ist Teil der Information.** Ausschnitte nie isoliert zeigen oder ans
Modell schicken — weder in der Oberfläche noch im Prompt. Dieselbe Hand schreibt
in jedem Eintrag `B. u. Weingärtner in Haberschlacht`; daran eicht man die
Buchstaben.

**Modell schlägt vor, Skript entscheidet.** Alles, was Daten verändert, muss
reproduzierbar sein. Das Modell liest und schätzt ein; Abgleich, Regelentscheidung
und Änderung laufen deterministisch und landen im Journal.

**Kirchenbuchform nie überschreiben.** Drei Ebenen je Name: `gelesen` (Rohlesung,
bleibt erhalten auch wenn falsch), `kb_form` (wörtlich, → `_KB_NAME`), `kanonisch`
(normalisiert, → `NAME`).

## Anker, nach Preis geordnet

| Anker | braucht | trägt ab |
|---|---|---|
| Chronologie — Datum zwischen Vorgänger und Nachfolger | nichts | erster Seite |
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
Datenbank, nicht im Prozess — der Läufer arbeitet weiter, wenn das Browser-
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
aufgefallen, weil sie nur zwei Zustände kannte — leer, oder Schlüssel und
echtes Geld. Was nur gegen Bezahlung sichtbar wird, wird nicht geprüft.

Die Testquelle liefert **nur die Rohlesung**; die 39 geprüften Verweise
bleiben als Maßstab zurück (`werkstatt.abgleich --messe`). Wer sie mitliefert,
misst hinterher nur, dass er sie mitgeliefert hat.

⚠️ Ihre `gelesen`-Werte sind bereits die *korrigierten* Lesungen des
Pilotlaufs. Sie prüfen den Durchlauf, nicht die Lesequalität.

## Kontextquellen: was darf bestätigen

`[[kontext]]` in `konfig.toml`, eigene Pfade in `konfig.local.toml` (in
`.gitignore`). Jede Quelle trägt ihren Rang:

    gilt = "beleg"       darf bestätigen  → ein Treffer macht grün
    gilt = "vokabular"   rankt nur        → ein Treffer bleibt gelb

Der Rang landet in `herkunft.gilt`; damit ist die Ampelregel eine Abfrage und
keine Sonderlogik. Keine Quelle eingetragen = Nullstart: alles bleibt gelb,
die Maske legt jedes Feld vor. Langsam, aber nicht falsch.

## Stand — gemessen 4. August 2026

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
keine Vornamen und keine Daten — der Abgleich hat nur Nachname+Nachname+Ehe.

**Ein Falschtreffer, den die Messung gefunden hat.** Der Taufe Nr. 12 von 1809
wurde ein Paar zugeordnet, das 1699 und 1703 geboren wurde und dessen Frau
1767 starb — einziger gemeinsamer Nachname im Bestand, kein Trauungsdatum,
und damit **grün**. Seither prüft `abgleich._plausibel()` Lebensgrenzen, und
ohne ein Datum, das die Familie zeitlich einordnet, wird nichts mehr grün.

**Was noch fehlt:** GEDCOM-Ausgabe aus den eigenen Tabellen (siehe unten),
Kaskaden für Ehe und Tod, Bildausschnitte je Feld.

## Nächste Schritte

1. ~~Papierabgrenzung in `raster.py`~~ — **erledigt.** Nicht über Helligkeit
   (die Unterlage ist so hell wie das Papier), sondern über die gedruckten
   Linien. 22/22 Zeilenlinien bei ±40 px, 0 überzählige Vorschläge.
   Messung: `python3 -m werkstatt.messung`, Sollwerte in `daten/soll_zeilen.json`.
2. **GEDCOM-Ausgabe** — `gedcom_export.py` ist das falsche Werkzeug: Es liest
   `rec`/`vorgang`/`meta` aus dem Haberschlacht-Index, die es hier nicht gibt,
   und bricht mit `TypeError` ab. Zwei Arten sind nötig: **Fortschreibung**
   (unberührte Records zeichengleich aus `person.raw` — bei 4.111 von 4.111
   vorhanden; Leerlauftest byte-identisch) und **Neuausgabe** aus
   `person`/`familie`/`ereignis` mit `_KB_NAME`, `_BERUF_KB`, `_NOTE_TAUFE`.
3. **Kaskaden für Ehe und Tod** — nach dem Muster von Taufe. `kaskade_tod.py`
   liegt fertig vor und ist noch nicht angeschlossen.
4. **Bildausschnitte je Feld.** Arbeitsteilung statt Entweder-Oder: Das Modell
   sagt, *welche* Zeile und *welche* Spalte (das braucht keine Pixel, weil
   Einträge und Zeilenbänder dieselbe Reihenfolge haben), die Geometrie
   liefert die Pixel. Koordinaten schätzen zu lassen ist zweimal gescheitert.
   `feld.bild_x/y/w/h` stehen im Schema und werden nie gefüllt.
5. **Registernamen aus dem Code lösen.** `ansatz.md` verspricht, ein
   englischsprachiger Nutzer könne sein Register frei benennen. Gemessen
   stimmt das nicht: `uebergabe.BAUPLAN` ist auf `ehe`/`taufe`/`tod` und
   deutsche Feldnamen verdrahtet, die Maske auf `vater`/`mutter`/`braeutigam`.
   `[register.marriage]` liefert „kein Bauplan für marriage".

**Spaltenraster bleibt Handarbeit.** Die Zeilen sitzen jetzt, die Spalten
nicht: die äußerste Randlinie fehlt teils (00365 beginnt bei x=1264 statt
1160). Einmal je Buch ziehen ist ohnehin der vorgesehene Weg.

## Nicht erneut versuchen

Automatische Zeilenerkennung per Textprojektion, proportional übertragene
Zeilenraster, Bounding Boxes vom Modell schätzen lassen. Messwerte in
`raster.py`.
