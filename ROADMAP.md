# Roadmap

Abgeglichen am 15. August 2026 mit dem Stand im README. Die konzeptionellen
Grundlagen stehen in `doku/ansatz.md` und `doku/verknuepfung.md`.

## Was NICHT gebaut wird – weil ofb-ki es hat

| | liegt in |
|---|---|
| Personen- und Familienbestand | `kirchenbuch.db`, `ofb.db` |
| GEDCOM-Import und -Export des Live-Systems | `ofb-ki/ingest/`, `ofb/` |
| Namens-, Orts-, Berufsmappings | `mapping_*` (21.565 Familiennamen) |
| Wissensspeicher, Musterpflege | `kb_muster`, `pruefe_wissensspeicher.py` |
| Web-Anzeige, Crowd-Korrekturen | `app.py`, `stats.db`, kies.bgg-home.de |

Die Werkstatt liest `kirchenbuch.db` **nur lesend** – als Vokabular und Anker.
Sie schreibt in ihre eigene kleine Datei und liefert am Ende ab. Kein Eingriff
ins Live-System, keine Deploy-Kette, kein Risiko für die 240.000 Einträge.

## Tranchen – der Registerwechsel

Nicht „erst alle Ehen bis 1855, dann alle Taufen", sondern **Tranchen nach
Zeitraum, innerhalb der Tranche alle drei Register**:

    Tranche 1808–1820      Tranche 1821–1832      …
      1. Ehen                1. Ehen
      2. Taufen              2. Taufen
      3. Tode                3. Tode
         ↓                      ↓
      Übergabe in die        Übergabe
      Personenbasis

**Warum verzahnt statt registerweise:**

| | |
|---|---|
| Der Anker wächst mit | Die Ehe von 1812 ankert die Taufe von 1819 – aber nur, wenn vorher erfasst |
| Fehler zeigen sich früh | Ein falsch gelesener Bräutigam fällt auf, wenn seine Kinder nicht anschließen |
| Dieselbe Hand | Innerhalb einer Tranche schreibt meist derselbe Pfarrer, der Fehlerkatalog passt |
| Früher Abbruch möglich | Nach Tranche 1 ist beurteilbar, ob es trägt – nicht erst nach 66 Ehe-Seiten |

**Reihenfolge innerhalb der Tranche** folgt den Ankern: Ehen liefern
Elternehen und tagesgenaue Geburtsdaten · Taufen nutzen sie · Tode nutzen
beide und schließen die Ketten. Der Rundenautomat erzwingt diese Reihenfolge
und schlägt beim leeren Bestand „ehe" vor.

**Tranchengröße ~12 Jahre.** Bei Haberschlacht etwa 35–40 Buchöffnungen über
alle drei Register.

## Gebaut (Stand siehe README)

- **Lesen** – Modellanbindung (`lesen.py`) im Rundenautomaten mit
  Hintergrundläufer; Fehler je Seite statt je Lauf. Testquelle ohne
  API-Schlüssel für den kostenlosen Durchlauf.
- **Übergabepunkt** – bestätigte Einträge werden zu Personen und Familien
  (`uebergabe.py`), Arbeitskopie nach jeder Übergabe; damit ankert die
  nächste Tranche gegen die eigene Erfassung („die ersten hundert tragen
  die nächsten tausend").
- **Abgleich mit Ampel und Herkunftsrang** – `herkunft.gilt` entscheidet,
  was bestätigen darf (`beleg`) und was nur rankt (`vokabular`);
  Plausibilitätsprüfung über Lebensgrenzen. Kaskade für die **Taufe** steht.
- **GEDCOM-Ausgabe** – Fortschreibung (unberührte Records zeichengleich,
  Leerlauftest byte-identisch) und Neuausgabe für den Nullstart.
- **Korrekturmaske** – Bildstreifen, Autovervollständigung,
  Familienanbindung; Bestandsprüfung nach Vorbild von Gramps und Ahnenblatt.
- **Bildsichtung** – `seiten.py`: Lücken, Auflösung, Dubletten relativ zum
  Median. Zeilenraster-Messung: 22/22 Linien bei ±40 px (`messung.py`).
- **Elternzeilen zerlegen** – Ehe- und Sterberegister führen die Eltern in
  einer Zeile mit Beruf, Ort und „weiland" darin. `personenzeile.py` trennt
  das; gemessen an 142 Zeilen der Demo: 142 Namen, 74 Orte, 63 Berufe, 34
  Sterbevermerke, 25 Geburtsnamen, kein Fall mit Beruf oder Ort im Namen.
  Erst dadurch sind die Eltern der Brautleute Personen, gegen die der
  Abgleich etwas finden kann.
- **Normalform nachrechnen** – `normalform.py` prüft, was das Modell an den
  Namen still normalisiert (771 von 885 Kirchenbuchformen weichen ab).
  Vier Urteile: belegt, regelhaft, frei, widerspruch. Ändert nichts,
  markiert nur.
- **Admin-Portal und Provisionierung** – `verein/portal.py` (Projektliste,
  neues OFB mit GEDCOM-Upload und Redakteurskonto, Nutzerverwaltung,
  KI-Kontingent) über `instanz.py --neu`; der Deckel `ki.budget_dollar`
  wird in der Instanz geprüft (`kontingent.py`). Siehe `doku/portal.md`.
- **Probelauf** – `werkstatt/probelauf.py` baut aus `git ls-files` einen
  Klon, startet ihn und fährt den ganzen Durchlauf; meldet jede Abweichung
  von den Zahlen der README. Damit ist die Demo nicht mehr davon abhängig,
  was zufällig auf dem Rechner des Autors liegt.

## Offen – Reihenfolge

### 1. ~~Bedienschleife~~ – erledigt
Ein Eintrag zur Zeit ist der Standard der Korrekturmaske (Fokus-Karte,
Blättern mit Pfeiltasten/j/k, Enter-Fluss durch die Felder, „Fertig ·
weiter" springt zum nächsten offenen Eintrag); die Listenansicht bleibt
als Ausweich. Der Aufwand je Eintrag (Tasten, Klicks, Sekunden) wird
dabei still mitgezählt.

### 2. ~~Kaskaden für Ehe und Tod anschließen~~ – erledigt 18. August
Die registereigenen Anker stecken jetzt in `abgleich.register_anker`,
nach dem Punkteschema des Machbarkeitsnachweises `kaskade_tod.py`:
Geburtsdatum der Brautleute (Spalte 6, taggenau), Alter → errechnetes
Geburtsdatum, Ehegatten-Umweg für verheiratete Frauen, genannte Eltern
als zweiter Beleg. Grün nur bei taggenauem Datum plus Vorname aus einer
Beleg-Quelle; Ortswiderspruch schließt aus. Probelauf: 21 statt 18 grün,
u. a. „Zoller, 64 J 1 M 18 T → geb. 10.06.1744" taggenau auf Zöller.
Offen bleibt die Proklamation als Plausibilitätsprüfung der Trauung.

### 3. Batch-API
Halbiert die Kosten; bei seitenweiser Verarbeitung der natürliche Modus.
Der Rundenautomat ist bereits die Struktur, die Batch braucht.

### 4. Bildausschnitt je Feld (Lupe)
`feld.bild_x/y/w/h` stehen im Schema und werden nie gefüllt. Arbeitsteilung:
Modell sagt Zeile und Spalte, die Geometrie liefert die Pixel; Koordinaten
schätzen zu lassen ist zweimal gescheitert. Spalten bleiben Handarbeit,
einmal je Buch – der Rastereditor dafür fehlt. Papierabgrenzung robust
machen (71 % wo sie gelingt, sonst 0 %).

*Zeilenraster erledigt:* `zeilenraster.py` passt ein Modell ein, statt
Linien abzuzählen. 22 von 22 Linien auf ±40 px gegen die geprüften
Seiten; über die dreizehn Beispielseiten 10 vollständig gemessen statt
vorher 6. Das Spaltenraster bleibt offen.

### 5. Registernamen aus dem Code lösen
`uebergabe.BAUPLAN` und die Maske sind auf `ehe`/`taufe`/`tod` und deutsche
Feldnamen verdrahtet; das Versprechen „Rollen statt Feldnamen" aus
`ansatz.md` ist gemessen noch nicht eingelöst. Zuordnung Rolle → Ereignisart
gehört in `konfig.toml`; `sprache/` existiert noch nicht.

## Offen – Wissenslücken (keine Bauschritte)

- **Der Nullstart ist nie gemessen.** Er ist inzwischen ein *definierter*
  Zustand (keine Beleg-Quelle → alles gelb, jedes Feld wird vorgelegt) –
  langsam, aber nicht falsch. Was fehlt, ist die Messung, wie schnell die
  eigene Erfassung als Anker zu tragen beginnt.
- **Eine andere Handschrift.** Die Variable mit dem größten Einfluss, nie
  getestet. Pfarrerwechsel in Haberschlacht 1827.
- **Lesequalität auf voller Seitenbreite.** Alle bisherigen Zahlen messen den
  Durchlauf oder den Abgleich, nicht das Lesen; der Qualitätstest gegen eine
  bekannte Eheseite (Bild 1184798-00917) steht aus.
- **Kostenrechnung.** Ob 0,13 $/Seite bei 42 % Rohfehlern die richtige
  Rechnung ist; Batch halbiert den Preis.
- **Verlässlichkeit je Herkunft.** `kirchenbuch.db` ist für Haberschlacht und
  Neipperg `beleg`, für die übrigen 32 Parochien nur `vokabular` – die
  Regel ist im Schema, die Erfahrung außerhalb der Pilotparochie fehlt.
