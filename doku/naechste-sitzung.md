# Quintessenz für einen Neustart

Stand 4. August 2026, abends. Wer diese Datei und `ansatz.md` liest, kann
ohne Vorwissen weitermachen. Zahlen hier sind gemessen, nicht geschätzt.

## Sofort loslegen — 30 Sekunden

```sh
cd ~/Dokumente/Ahnenforschung/ofb-werkstatt
python3 start.py                     # → http://127.0.0.1:8765
```

Erwartete Ausgabe:

```
Gemeinde : Haberschlacht
Register : ehe, taufe, tod
Beleg    : OFB Haberschlacht (kuratiert)  (4111 Personen)
Bestand  : 4111 Personen, 1346 Familien, 8974 Ereignisse
Erfasst  : 0 Einträge, 0 Felder
```

Dann im Browser: **Lesen** → Register „Taufregister", Quelle „Testdaten",
*Lesen starten*. Es läuft ohne API-Schlüssel und kostet nichts. Danach
**Korrigieren**, dann **Übergeben**.

Alles rückgängig machen:

```sh
python3 -m werkstatt.runde --verwirf 1
```

Geprüft: danach stehen die Zahlen exakt wieder auf 4.111 / 1.346 / 2.520.
Beliebig oft wiederholbar.

## Was der Durchlauf ist

Eine **Runde** ist eine Tranche: so und so viele Seiten EINES Registers, die
zusammen gelesen, korrigiert und übergeben werden.

    geplant ──lesen──► korrigieren ──übergeben──► fertig

Der Zustand liegt in der Datenbank (`runde`, `auftrag`, `auftrag_seite`),
nicht im Prozess. Folge: Der Läufer arbeitet weiter, wenn das Browserfenster
zugeht; ein Abbruch hinterlässt einen lesbaren Zustand; und die Einschränkung
der Maske auf die gerade gelesene Tranche ist ein `WHERE` statt eines
Sonderfalls.

Dieselben Schritte auf der Kommandozeile:

```sh
python3 -m werkstatt.runde --stand
python3 -m werkstatt.runde --plane taufe --seiten 4 --quelle testdaten
python3 -m werkstatt.runde --lies 1
python3 -m werkstatt.runde --uebergib 1 --schreib
python3 -m werkstatt.abgleich --messe
```

## Gemessen am 4. August — voller Durchlauf, 4 Seiten Taufregister

| | |
|---|---|
| gelesen | 22 Einträge, 102 gefüllte Felder |
| Ampel nach dem selbsttätigen Abgleich | 20 grün · 18 gelb · 6 rot · 58 grau |
| vorgelegt | **24 von 102 Feldern** brauchen eine Entscheidung |
| übergeben | 45 Personen neu, 20 verknüpft, 22 Familien, 22 Kinder |
| Abgleich gegen die 39 geprüften Verweise | **18 wiedergefunden (46 %), 0 falsch** |

**Die 46 % messen NICHT die Lesequalität.** Die Piloteinträge enthalten nur
Nachnamen — keine Vornamen, keine Daten, keine Familienbuchnummern. Der
Abgleich hatte Nachname + Nachname + Ehe, sonst nichts. Und die
`gelesen`-Werte der Testquelle sind bereits die *korrigierten* Lesungen des
Pilotlaufs. Geprüft ist der Durchlauf, nicht das Lesen.

**Die 45 neu angelegten Personen sind die Kehrseite.** Aus 44 Elternplätzen
entstehen bei 46 % Trefferquote rund 24 Personen, die es im OFB vermutlich
schon gibt. Mit Vornamen und Taufdaten aus der vollen Seitenbreite sollte das
deutlich besser werden — geprüft ist es nicht.

## Drei Funde, nach denen niemand gesucht hat

**1. Die Maske war kaputt.** Sie las `f["ofb_id"]`, die Spalte heißt im
Werkstatt-Schema `person` — `IndexError`, sobald ein einziger Eintrag
existierte. Seit dem Schemawechsel, unbemerkt, weil sie nur zwei Zustände
kannte: leer, oder ein API-Schlüssel und echtes Geld. **Daraus die Regel:
Was nur gegen Bezahlung sichtbar wird, wird nicht geprüft.** Deshalb gibt es
die Testquelle.

**2. `eintrag` fehlten `fam_reg` und `schreiber`.** Beide standen seit
Längerem in `schema.sql` und waren in der laufenden Datenbank nicht
angekommen — `CREATE TABLE IF NOT EXISTS` erweitert keine bestehende Tabelle.
`fam_reg` ist nach `verknuepfung.md` der stärkste Anker überhaupt: Die Spalte
war da, wo man sie liest, und fehlte da, wo man sie schreibt. `db.wandere()`
vergleicht jetzt gegen die Schemadatei; eine von Hand gepflegte Liste hätte
genau das wieder übersehen.

**3. Ein stiller Falschtreffer.** Der Taufe Nr. 12 von **1809** wurde ein Paar
zugeordnet, das 1699 und 1703 geboren wurde und dessen Frau 1767 starb —
einziger gemeinsamer Nachname im Bestand, kein Trauungsdatum, und damit nach
der ersten Fassung der Regel **grün**. Gefunden hat ihn nur die Messung gegen
die geprüfte Wahrheit; von innen sah er wie ein Erfolg aus.

`abgleich._plausibel()` prüft seither Lebensgrenzen (Mutter 14–50, Vater
16–70, Todesjahr), und ohne ein Datum, das die Familie zeitlich einordnet,
wird gar nichts mehr grün. Wirkung: Treffer unverändert 18, Falschzuordnungen
von 1 auf 0.

## Kontextquellen — der Rang entscheidet über die Ampel

Neu im Schema: `herkunft.gilt` und `herkunft.parochien`. Sie tragen die Regel,
die bisher nur in `landkarte.md` stand:

    gilt = "beleg"       darf bestätigen  → ein Treffer macht grün
    gilt = "vokabular"   rankt nur        → ein Treffer bleibt gelb

Damit ist die Ampelregel eine Verbundabfrage statt einer Sonderlogik, und der
**Nullstart ist kein zweiter Betriebsmodus, sondern der Fall „null Quellen"**:
alles bleibt gelb, die Maske legt jedes Feld vor. Langsam, aber nicht falsch.

Quellen kommen aus `[[kontext]]` in `konfig.toml`. Eigene Pfade stehen in
**`konfig.local.toml`** — die ist in `.gitignore` (geprüft) und enthält
derzeit das kuratierte OFB als `beleg`, `kirchenbuch.db` als `beleg` für
Haberschlacht und Neipperg, den Namensatlas als `vokabular`.

`konfig.local.toml` ist die Datei, die es erlaubt, das Repo zu veröffentlichen,
ohne fremde Bestände oder Pfade mitzuliefern.

## Zustand der Dateien

| | |
|---|---|
| `daten/erfassung.sqlite` | 4.111 Personen, 1.346 Familien, 8.974 Ereignisse, **0 Einträge** — sauberer Ausgangszustand |
| Runden | 0 — der Probelauf wurde verworfen |
| `konfig.local.toml` | angelegt, gitignoriert, drei Kontextquellen |
| `bilder/taufe/zeilen/` | 22 Zeilenstreifen aus dem Pilotlauf, für die Maske |
| Git | 26 Commits, alles eingecheckt, nichts offen |

Die Datenbank ist aus dem GEDCOM reproduzierbar (`werkstatt/import_gedcom.py`),
falls doch etwas schiefgeht. Der OFB in `Transkription-1808/quellen/` ist
schreibgeschützt und wurde nicht angefasst.

## Was als Nächstes ansteht

**1. GEDCOM-Ausgabe — die einzige Stelle, an der die Werkstatt nichts hergibt.**

`gedcom_export.py` ist das falsche Werkzeug: Es liest `rec`, `vorgang`, `meta`
aus dem Haberschlacht-Index, die es im Werkstatt-Schema nicht gibt, und bricht
sofort ab (`TypeError: expected str … not NoneType`). Zwei Arten sind nötig:

| | für wen | wie |
|---|---|---|
| Fortschreibung | wer ein OFB hat | unberührte Records zeichengleich aus `person.raw` — bei **4.111 von 4.111** vorhanden, Familien 1.346/1.346. Leerlauftest: leeres Journal → byte-identisch |
| Neuausgabe | Nullstart | aus `person`/`familie`/`ereignis`, mit `_KB_NAME`, `_BERUF_KB`, `_NOTE_TAUFE` |

Dazu gehört: **das Journal in dieselbe Datenbank holen.** `journal.py` schreibt
nach `daten/aenderung.sqlite` — eine zweite Datei, die es gar nicht gibt. Über
zwei Dateien hinweg kann ein Bestätigen nicht Feld *und* Vorgang in einer
Transaktion schreiben.

**2. Kaskaden für Ehe und Tod.** `kaskade_tod.py` liegt fertig vor (59,8 %
Treffer gemessen) und ist an den Durchlauf nicht angeschlossen. Der Abgleich
kennt bisher nur die Taufe; für Ehe und Tod rankt er nur Nachnamen und macht
nie grün.

**3. Bildausschnitte je Feld.** `feld.bild_x/y/w/h` stehen im Schema und
werden nie gefüllt — deshalb zeigt die Maske ganze Zeilenstreifen, keine Lupe.
Vereinbarte Arbeitsteilung: **Das Modell sagt, welche Zeile und welche Spalte**
(das braucht keine Pixel, weil Einträge und Zeilenbänder dieselbe Reihenfolge
haben — es muss nur sagen, wie viele Bänder ein Eintrag belegt), **die
Geometrie liefert die Pixel.** Koordinaten schätzen zu lassen ist zweimal
gescheitert. Wo kein Raster existiert, schätzt das Modell eine Box mit
großzügigem Rand — Rückfall, nicht Normalfall.

Spalten bleiben Handarbeit, einmal je Buch. Der Rastereditor dafür fehlt.

**4. Registernamen aus dem Code lösen.** `ansatz.md` verspricht, ein
englischsprachiger Nutzer könne sein Register frei benennen, „solange die
Rollen stimmen". Gemessen stimmt das nicht:

```
uebergabe.BAUPLAN.get('marriage')  →  None
Ergebnis:  {'uebersprungen': 'kein Bauplan für marriage'}
```

`BAUPLAN` ist auf `ehe`/`taufe`/`tod` und deutsche Feldnamen
(`trauung_datum`, `sterbe_datum`) verdrahtet, die Maske auf
`vater`/`mutter`/`braeutigam`/`braut`. `sprache/` existiert nicht.
Die Zuordnung Rolle → Ereignisart gehört in dieselbe `konfig.toml`, in der
die Felder schon stehen.

## Zwei Dinge, die daneben liegen und im Blick bleiben

**Der Qualitätstest.** Eine Eheseite lesen und gegen die Wahrheit halten.
Braucht `ANTHROPIC_API_KEY`. Bild **1184798-00917** eignet sich, weil die
Seite bekannt ist (1808, Einträge 1–5). Das ist die erste Messung, die etwas
über die **Lesequalität** sagen würde statt über den Durchlauf — mit dem
Rundenautomaten läuft sie jetzt über die Oberfläche statt über Wegwerfskripte.

**Das Haberschlacht-Projekt** liegt separat und ist unberührt:
`Transkription-1808/` mit den 22 geprüften Einträgen, dem Fehlerkatalog in
`wissen/haberschlacht.md` und dem bereinigten GEDCOM.

## Weiterhin ungelöst

- **Der Nullstart ist nie gemessen.** Alle Zahlen stammen aus Läufen gegen ein
  OFB mit 4.111 Personen. Neu ist immerhin: Er ist jetzt ein *definierter*
  Zustand (keine Beleg-Quelle → alles gelb) statt eines unbedachten Falls.
- **Ob das Verfahren ohne reichen Bestand trägt.** Bei Nachbarorten ohne
  eigenes OFB (Bönnigheim, Löchgau, Michelbach) war der Pilotlauf chancenlos.
- **Eine andere Handschrift.** Die Variable mit dem größten Einfluss, nie
  getestet. Pfarrerwechsel in Haberschlacht 1827.
- **Ob 0,13 $/Seite bei 42 % Rohfehlern die richtige Rechnung ist.** Die
  Batch-API halbiert das; der Rundenautomat ist die Struktur, die Batch
  ohnehin braucht — eine Liste eingereichter Einheiten mit Zustand. Wer
  synchron baut und später Batch nachrüstet, baut sie zweimal.

## Belegte Fehllesungen (Hand M. Deurlin, bis zum Pfarrerwechsel 1827)

Gilt unverändert und ist noch **nicht** in die Datenbank importiert — der
Fehlerkatalog speist sich bisher nur aus eigenen Korrekturen.

| gelesen | tatsächlich | Häufigkeit |
|---|---|---|
| `Roth` / `Roßin` | **`Koch`** | 4 von 5 Vorkommen falsch |
| `Kräßin`, `Bierlin` | **`Käserin`** | 2× — die K-Anfangsschleife |
| `Weißhardt` | `Weissert` | Normalisierungsfrage, kein Lesefehler |
| `Straub` | `Brudi` · `Hubelz` → `Häberlen` · `Grumbaldts` → `Rembold` | je 1× |

`Roth` kommt 59-mal im Bestand vor, `Koch` 36-mal. **Vokabular und Häufigkeit
bestätigen diesen Fehler, statt ihn zu finden** — das ist der Grund für den
Herkunftsrang und dafür, dass Häufigkeit niemals grün macht.

## Der Elternehe-Anker und sein Verfallsdatum

Gerechnet aus 1.397 Kind-Ereignissen, Bestand endet 1807:

    Taufjahr 1808  94 %   1813  53 %   1820  18 %   1827  3 %

Ab 1813 trägt er die Mehrheit nicht mehr — **es sei denn, die Ehen ab 1808
werden mit erfasst.** Deshalb erzwingt der Rundenautomat die Reihenfolge
Ehen → Taufen → Tode und schlägt beim leeren Bestand „ehe" vor: *„erste Runde
— Ehen zuerst, sie bauen den Anker"*.
