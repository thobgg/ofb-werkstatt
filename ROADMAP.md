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

## Tranchen — der Registerwechsel

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
| Der Anker wächst mit | Die Ehe von 1812 ankert die Taufe von 1819 — aber nur, wenn vorher erfasst |
| Fehler zeigen sich früh | Ein falsch gelesener Bräutigam fällt auf, wenn seine Kinder nicht anschließen |
| Dieselbe Hand | Innerhalb einer Tranche schreibt meist derselbe Pfarrer, der Fehlerkatalog passt |
| Früher Abbruch möglich | Nach Tranche 1 ist beurteilbar, ob es trägt — nicht erst nach 66 Ehe-Seiten |

**Reihenfolge innerhalb der Tranche** folgt den Ankern: Ehen liefern
Elternehen und tagesgenaue Geburtsdaten · Taufen nutzen sie · Tode nutzen
beide und schließen die Ketten.

**Tranchengröße ~12 Jahre.** Bei Haberschlacht etwa 35–40 Buchöffnungen über
alle drei Register.

### Der Übergabepunkt — bisher nur behauptet, nicht gebaut

Der Wechsel erzwingt etwas, das noch fehlt: **Die eigene Erfassung muss selbst
zum Bestand werden.** Bisher sucht `suche.py` nur gegen fremde Bestände
(kirchenbuch.db, OFB-GEDCOM). Nach jedem Register muss aus `eintrag`/`feld`
eine Person und ggf. eine Familie entstehen, sonst findet die nächste Tranche
sie nicht.

Das ist der Mechanismus „die ersten hundert tragen die nächsten tausend".
Ohne ihn ist die Tranchen-Reihenfolge wirkungslos.

## Reihenfolge

### erledigt: Verknüpfungskaskade Tod
59,8 % Treffer, ~¾ verwertbare Auskunft. `doku/verknuepfung.md`.

### erledigt: Bildsichtung
`werkstatt/seiten.py` — Lücken, Auflösung, Dubletten relativ zum Median.

### 1. `lesen.py` — die Modellanbindung  ← der fehlende Kern
Ganze Seite hinein, strukturierte Einträge heraus. Zunächst **ohne** Raster:
Das Modell findet die Einträge auf einer gedruckten Registerseite selbst, und
das Raster steckt bei 42 %. Damit hängt der Kern nicht an einem ungelösten
Vorschritt.

Mitzugeben: Nachbarzeilen als Kontext · Fehlerkatalog **je Hand** · Konfidenz
je Feld · Familienbuchnummer und laufende Nummer als Pflichtfelder.

### 2. Übergabepunkt Erfassung → Personenbasis
Bestätigte Einträge werden zu Personen und Familien, damit die nächste Tranche
gegen sie ankern kann. Ohne diesen Schritt bringt der Registerwechsel nichts.

### 3. Kaskaden für Taufe und Heirat
Nach dem Muster von Tod — kein zweites Konzept nötig, Fleißarbeit.

### 4. Raster für die Lupe
Erst jetzt nötig: für gezielte Bildausschnitte beim Korrigieren.
Papierabgrenzung robust machen (71 % wo sie gelingt, sonst 0 %).

### alt: Verknüpfungskaskade gegen kirchenbuch.db
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
