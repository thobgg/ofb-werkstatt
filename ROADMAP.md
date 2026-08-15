# Roadmap

Abgeglichen am 6. August 2026 mit dem Stand im README. Die konzeptionellen
Grundlagen stehen in `doku/ansatz.md` und `doku/verknuepfung.md`; der jeweils
letzte Arbeitsstand in `doku/naechste-sitzung.md`.

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

## Offen – Reihenfolge

### 1. Bedienschleife (in Arbeit)
Ein Eintrag zur Zeit statt der ganzen Runde auf einer Seite.

### 2. Kaskaden für Ehe und Tod anschließen
`kaskade_tod.py` liegt fertig vor (59,8 % Treffer gemessen gegen
`kirchenbuch.db`, siehe `doku/verknuepfung.md`), ist aber nicht an den
Durchlauf angeschlossen – der Abgleich rankt bei Ehe und Tod bisher nur
Nachnamen und macht nie grün. Die Ehe-Kaskade nach demselben Muster.

### 3. Batch-API
Halbiert die Kosten; bei seitenweiser Verarbeitung der natürliche Modus.
Der Rundenautomat ist bereits die Struktur, die Batch braucht.

### 4. Bildausschnitt je Feld (Lupe)
`feld.bild_x/y/w/h` stehen im Schema und werden nie gefüllt. Arbeitsteilung:
Modell sagt Zeile und Spalte, die Geometrie liefert die Pixel; Koordinaten
schätzen zu lassen ist zweimal gescheitert. Spalten bleiben Handarbeit,
einmal je Buch – der Rastereditor dafür fehlt. Papierabgrenzung robust
machen (71 % wo sie gelingt, sonst 0 %).

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
