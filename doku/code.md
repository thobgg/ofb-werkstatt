# Der Code: ein Weg hindurch

47 Module sind zu viele zum Draufschauen. Sieben davon tragen die Arbeit,
der Rest ist Zubehör. Diese Seite sagt, welche sieben das sind, in welcher
Reihenfolge sie drankommen und wo man eingreift.

Wer nur eine Sache lesen will: den Abschnitt *Der Weg einer Seite*. Danach
kennt man den Durchlauf und kann den Rest ignorieren, bis man ihn braucht.

## In zehn Minuten zum ersten Eingriff

```sh
python3 start.py                    # Maske auf http://127.0.0.1:8765
python3 -m werkstatt.probelauf      # der Wächter: fährt den ganzen Durchlauf
python3 -m unittest discover tests   # die schnellen Prüfungen
```

Der **Probelauf** ist das wichtigste Werkzeug. Er baut aus `git ls-files`
einen Klon in ein Wegwerfverzeichnis, fährt dort Lesen, Abgleich, Übergabe
und Ausgabe über die Web-Schnittstelle und vergleicht das Ergebnis mit den
Zahlen im README: 57 Einträge, 21 grün, Fortschreibung zeichengleich, 0 tote
Zeiger. Wer etwas ändert und diese vier Zahlen behält, hat den Durchlauf
nicht beschädigt. Er braucht kein Modell und kostet nichts.

## Der Weg einer Seite

Ein Scan wird zu GEDCOM. Das ist der ganze Zweck, und diese sieben Module
sind die Stationen:

    bilder/taufe/*.jpg
      │
      │  seiten.py        sichten: Dubletten, Lücken, Auflösung
      │                   nummer() liest die Seitenzahl aus dem Dateinamen
      ▼
      │  bloecke.py       je Zeile zwei Ausschnitte, links und rechts vom
      │  (raster.py)      Bund, dazu der Spaltenkopf. Grund: eine ganze
      │                   Seite kommt verkleinert an und die schmalen
      │                   Spalten sind dann unlesbar.
      ▼
      │  lesen.py         die Modellanbindung. Ausschnitte plus Prompt
      │                   hinein, JSON mit Feldern heraus. Die einzige
      │                   Stelle, die mit einem Anbieter spricht.
      ▼
      │  runde.py         der Läufer. Arbeitet eine Tranche Seiten ab,
      │                   schreibt eintrag und feld, hält den Stand fest.
      │                   Läuft im Hintergrund weiter, wenn der Browser
      │                   zugeht.
      ▼
      │  abgleich.py      das Herz. Sucht zu jeder Person einen Anker im
      │                   Bestand und setzt die Ampel. Grün heißt: ein
      │                   Beleg bestätigt, nicht "das Modell war sicher".
      ▼
      │  uebergabe.py     bestätigte Erfassung wird Bestand. Schreibt
      │                   Vorgänge, keine Records: Rücknahme heißt
      │                   aktiv=0, nicht löschen.
      ▼
      │  ausgabe.py       GEDCOM 5.5.1 fortschreiben. Unberührte Records
      │  (ausgabe7.py)    gehen zeichengleich durch, das prüft der
      │                   Leerlauftest bei jedem Export.
      ▼
    ausgabe/*.ged

Dazwischen liegt die Maske: `web/app.py` beantwortet rund 40 Routen,
`web/static/start.html` und `korrektur.html` zeichnen sie. Die Maske
entscheidet nichts, sie ruft die Module oben auf.

## Was dabei in der Datenbank entsteht

Eine einzige Datei, `daten/erfassung.sqlite`, angelegt aus
`werkstatt/schema.sql`. Die Tabellen in der Reihenfolge ihres Auftritts:

| Tabelle | wofür |
|---|---|
| `rec` | der Ausgangsbestand, GEDCOM-Zeilen wörtlich. Wird nie verändert. |
| `person`, `familie`, `kind` | derselbe Bestand, aufgeschlüsselt zum Suchen |
| `runde`, `auftrag`, `auftrag_seite` | ein Lauf und sein Stand, Seite für Seite |
| `eintrag`, `feld` | was gelesen wurde, ein Datensatz je Registerzeile |
| `vorgang` | jede Ergänzung als Journalzeile, mit Beleg |
| `einstellung` | Betriebswerte, die sich im Arbeiten ändern |

Die Trennlinie zu `konfig.toml`: Dort steht die **Struktur** (Registerarten,
Felder, Kontextquellen), in `einstellung` der **Betrieb** (Seiten je Runde,
Modell, Deckel). Struktur ändert man einmal beim Einrichten, Betrieb ständig.

`SELECT raw FROM rec ORDER BY seq` gibt die Ausgangsdatei zeichengleich
zurück. Das ist keine Zierde, sondern die Zusage, auf der die ganze
Fortschreibung steht.

## Das Zubehör, gruppiert

Vierzig Module, die man beim ersten Lesen überspringen kann. Sie stehen
hier, damit man sie wiederfindet, nicht damit man sie liest:

| Gruppe | Module | wann relevant |
|---|---|---|
| Infrastruktur | `konfig`, `db`, `einstellungen`, `katalog` | ständig, aber unauffällig |
| Bildvorbereitung | `raster`, `zeilenraster`, `spaltenraster`, `streifen`, `perioden`, `dubletten`, `soll_streifen`, `messung` | wenn der Zuschnitt klemmt |
| Namen und Formen | `normalform`, `klassen`, `personenzeile`, `randvermerk`, `suche` | wenn der Abgleich danebengreift |
| Einlesen | `import_gedcom`, `import_wortschatz`, `bestand` | beim Einrichten eines Bestands |
| Andere Lesewege | `vorlage` (Sitzung), `testdaten`, `nachlesen`, `gespraech` | Alternativen zur API |
| Mehrbenutzer | `nutzer`, `instanz`, `portal`, `wirt`, `kontingent`, `sicherung`, `zugriffe` | nur im Vereinsbetrieb |
| Demo und Prüfung | `probelauf`, `klon`, `demoinstanz`, `musterbuch`, `auszug`, `pruefung`, `journal` | beim Vorführen und Prüfen |

## Wo ändere ich was

| Vorhaben | Datei |
|---|---|
| anderes Modell, anderer Anbieter | `lesen.py`, dort `MODELLE`, `frage()`, `bild_teil()` |
| Prompt, Leseregeln | `lesen.py`, die Textbausteine `BASIS`, `AUSGABE` |
| welche Felder eine Aktart hat | `konfig.toml`, dann `katalog.py` |
| wann die Ampel grün wird | `abgleich.py` |
| was beim Übergeben entsteht | `uebergabe.py`, Tabelle `vorgang` |
| Aussehen und Bedienung | `web/static/start.html`, `korrektur.html` |
| neue Route | `web/app.py`, die `if pfad == ...`-Kette |
| Bildzuschnitt | `bloecke.py`, `raster.py` |

## Die Regeln, gegen die man nicht bauen sollte

Drei Zusagen tragen das Vertrauen in die Ausgabe. Wer sie bricht, macht aus
dem Werkzeug ein Risiko:

1. **Der Ausgangsbestand bleibt unangetastet.** Ergänzungen sind Vorgänge,
   Rücknahme ist `aktiv=0`. Kein `UPDATE` auf `rec`.
2. **Grün wird nur, was ein Beleg bestätigt.** Die Selbsteinschätzung des
   Modells und die Häufigkeit eines Namens dürfen ranken, nie bestätigen.
   Der Fall, an dem das hängt: `Koch` wurde viermal von vier Modellen als
   `Roth` gelesen, und `Roth` steht 59mal im Bestand.
3. **Die Ausgabe ist verlustfrei.** Unberührte Records gehen zeichengleich
   durch. Der Leerlauftest prüft das bei jedem Export.

## Prüfen, bevor man committet

```sh
python3 -m unittest discover tests   # Sekunden
python3 -m werkstatt.probelauf      # ein bis zwei Minuten
```

Der Probelauf muss unverändert 57 Einträge, 21 grün, zeichengleich und
0 tote Zeiger melden. Weicht eine der vier Zahlen ab, ist das kein
Messrauschen, sondern eine Änderung am Verhalten.
