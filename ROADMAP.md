# Roadmap

Angepasst nach dem Fund von `~/ofb-ki/kirchenbuch.db` (823.627 Personen,
34 Parochien) und der Klärung, dass die **Verknüpfung** die eigentliche
OFB-Arbeit ist, nicht das Lesen.

## Was NICHT gebaut wird — weil ofb-ki es hat

| | liegt in |
|---|---|
| Personen- und Familienbestand | `kirchenbuch.db`, `ofb.db` |
| GEDCOM-Import und -Export | `ofb-ki/ingest/`, `ofb/` |
| Namens-, Orts-, Berufsmappings | `mapping_*` (21.565 Familiennamen) |
| Wissensspeicher, Musterpflege | `kb_muster`, `pruefe_wissensspeicher.py` |
| Web-Anzeige, Crowd-Korrekturen | `app.py`, `stats.db`, kies.bgg-home.de |

Die Werkstatt liest `kirchenbuch.db` **nur lesend** — als Vokabular und Anker.
Sie schreibt in ihre eigene kleine Datei und liefert am Ende ab. Kein Eingriff
ins Live-System, keine Deploy-Kette, kein Risiko für die 240.000 Einträge.

## Was gebaut wird — vier Bausteine

    1  Zerlegen      Seitenraster, Zeilenstreifen, gezielte Ausschnitte
    2  Vorlesen      API-Aufruf mit Kontext und Fehlerkatalog
    3  VERKNÜPFEN    die Kaskade je Aktart  ← der anspruchsvollste Teil
    4  Korrigieren   Maske: nur offene Felder, Lupe daneben

Baustein 3 ist der eigentliche Wert. Siehe `doku/verknuepfung.md`.

## Reihenfolge

### 1. Verknüpfungskaskade gegen kirchenbuch.db  ← zuerst
Lässt sich **ohne Bilder und ohne API** bauen und prüfen, weil die Testdaten
schon da sind: 115.418 Taufen, 39.040 Heiraten, 89.422 Tode.

- Taufe: Vater → dessen Ehe → Mutter → Familie
- Heirat: Brautleute über Geburtsdatum + Ort
- Tod: Alter → Geburtsdatum → Taufe; bei Verheirateten erst die Ehe
- Pflichtregel: **zwei übereinstimmende Merkmale, eines davon nicht der Nachname**

Prüfbar an Fällen mit bekannter Wahrheit (Pilotlauf 22 Taufeinträge).

### 2. Seitenraster
Papierabgrenzung robust machen — Buchdeckel, Falz, Papier. Wo sie gelingt,
findet die Zeilenerkennung 71 % der Grenzen, sonst 0 %. Rest von Hand,
Folgeseiten erben das Raster.

### 3. API-Anbindung
Transkriptionsprompt mit Nachbarzeilen als Kontext und Fehlerkatalog aus
`kb_muster` — aber getrennt gehalten: Schreibvarianten des Schreibers und
Lesefehler des Modells sind zweierlei.

### 4. Maske fertigstellen
Existiert bereits: Autovervollständigung, Familienanbindung, Tastaturbedienung.
Fehlt: Ampel aus dem Matching, Lupe statt ganzem Streifen.

### 5. Abliefern
Format offen — GEDCOM oder direkt in die `*_voll`-Struktur von ofb-ki.
Entscheidung erst, wenn 1 bis 4 stehen.

## Offen

- **Nullstart nie getestet.** Alle Messwerte stammen aus einem Lauf gegen
  reiche Bestände. Ob es ohne trägt, ist unbekannt.
- **Verlässlichkeit je Herkunft.** kirchenbuch.db ist für Haberschlacht und
  Neipperg belastbar, für die übrigen 32 Parochien nur Vokabular — darf dort
  also ranken, aber nie bestätigen.
- **Ersterfassung vs. Bulk-Korrektur.** Der 9-Schritt-Workflow von ofb-ki ist
  für Massenkorrekturen gedacht, nicht für „Seite 7 von 50". Die Werkstatt
  braucht einen leichten eigenen Pfad.
