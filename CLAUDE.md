# OFB-Werkstatt

Werkstatt für ein **Ortsfamilienbuch**: Kirchenbuchseite lesen lassen, korrigieren,
gegen den Bestand abgleichen, anbinden oder neu anlegen, am Ende GEDCOM ausgeben.

**Funktioniert mit und ohne vorhandenen Bestand.** Wer eines fortschreibt, ankert
gegen sein GEDCOM; wer bei Null anfängt, gegen die eigenen früheren Einträge —
die ersten hundert tragen die nächsten tausend. Zwei der vier Ankertypen
(Chronologie, Kontext) brauchen überhaupt keinen Bestand.

⚠️ Der Nullstart ist **nie getestet** — alle bisherigen Messwerte stammen aus
einem Lauf gegen ein reiches Ortsfamilienbuch mit 4.111 Personen.

**Ausführliche Begründung aller Entwurfsentscheidungen: `doku/ansatz.md`.
Stand und offene Punkte: `doku/naechste-sitzung.md`. Beide vor der Arbeit lesen.**

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

## Stand

Fertig: Datenbasis (`person`/`familie`/`ereignis`/`namensform` mit Herkunft),
GEDCOM-Import verlustfrei, Suche mit Äquivalenzklassen, Familienanbindung,
Sichten `wert`/`fehlerkatalog`/`chronologie`.

**Der Kern fehlt:** API-Client und Transkriptionsprompt. Das Vorlesen geschieht
bisher von Hand außerhalb des Werkzeugs.

## Nächste Schritte

1. **Papierabgrenzung in `raster.py`** — Buchdeckel/Falz/Papier robust trennen.
   Wo sie gelingt, findet die Zeilenerkennung 71 % der Grenzen, sonst 0 %.
   Feste Helligkeitsschwelle 140 durch einen Wert relativ zum Papiermaximum ersetzen.
2. **Rastereditor** — Vorschläge anzeigen, fehlende Linien von Hand nachziehen,
   Folgeseiten erben das Raster.
3. **API-Client und Prompt** — mit Fehlerkatalog aus der Sicht `fehlerkatalog`
   und den Nachbarzeilen als Kontext.
4. **Matching anschließen** — Logik liegt fertig in `suche.py`.

## Nicht erneut versuchen

Automatische Zeilenerkennung per Textprojektion, proportional übertragene
Zeilenraster, Bounding Boxes vom Modell schätzen lassen. Messwerte in
`raster.py`.
