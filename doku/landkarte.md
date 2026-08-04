# Landkarte und Arbeitsteilung

Zwei Zwecke: den Überblick behalten, wenn es unübersichtlich wird — und klären,
wann Thomas gefragt wird und wann nicht.

## Wo liegt was

    ~/ofb-ki/                          Kies-Projekt, LEBT, live unter kies.bgg-home.de
      kirchenbuch.db      400 MB       823.627 Personen, 34 Parochien, 247k Einträge
                                       taufe_voll 115k · heirat_voll 39k · tod_voll 89k
                                       mapping_* (Namen, Orte, Berufe), kb_muster
      ofb.db              127 MB       berechnete OFB-Tabellen (Alpha)
      stats.db (NAS)                   Crowd-Korrekturen — NIE lokal überschreiben
      app.py                           Web-App, 47 Routen
      → NUR LESEND anfassen. Kein Eingriff, keine Deploy-Kette.

    ~/Dokumente/Ahnenforschung/
      OFB/OFB-Haberschlacht/Transkription-1808/
        quellen/          Archion/Ancestry-Scans
        daten/            ofb_haberschlacht.sqlite (kuratiert, 4.111 Pers.)
                          erfassung.sqlite (22 Pilot-Einträge)
                          aenderung.sqlite (18 Merge-Vorgänge)
        wissen/           haberschlacht.md — Fehlerkatalog dieser Hand, bis 1827
        ausgabe/          OFB_Haberschlacht_bereinigt.ged
        skripte/          paar.py, klassen.py, pruefe_ofb.py, maske.py …
      OFB/Kirchenbücher Zabergäu/      136 Kies-DOCX (Rohquelle von kirchenbuch.db)
      ofb-werkstatt/                   DIESES Projekt

## Welcher Bestand gilt wofür

| Frage | zuerst | dann | nie |
|---|---|---|---|
| Person in Haberschlacht? | `ofb_haberschlacht.sqlite` (vollständiger) | kirchenbuch.db | — |
| Person in Neipperg? | kirchenbuch.db (belastbar) | — | — |
| Person in den übrigen 32 Parochien? | — | — | **als Beleg** — nur Vokabular |
| Namensvariante, Ort, Beruf? | `mapping_*` in kirchenbuch.db | Atlas-CSV | — |
| Fehllesung dieser Hand? | `wissen/haberschlacht.md` | — | — |

**Merksatz:** kirchenbuch.db ist außerhalb von Haberschlacht und Neipperg
Vokabular, kein Beweis. Es darf ranken, nie bestätigen.

## Arbeitsteilung

### Claude entscheidet allein
Technische Umsetzung, Datenstrukturen, Reihenfolge innerhalb einer Runde,
Bildzuschnitte, Schwellenwerte, Refactoring. Fehler hier sind billig und
umkehrbar.

### Thomas wird gefragt — weil er es besser weiß
| Anlass | warum |
|---|---|
| Paläographie im Zweifel | er liest die Hand besser; belegt: `30. Sept.`, `Löbichin` |
| Lokalgeschichte, Familienzusammenhänge | Ortskenntnis |
| Welche Quelle im Konflikt gilt | er kennt die Entstehung seiner Bestände |
| Prioritäten, Reihenfolge, Umfang | seine Zeit, seine Kosten |
| Alles, was nach außen wirkt | Veröffentlichung, Rechte, Hosting |

### Gemeinsam
Mehrdeutige Matches, widersprüchliche Bestände, Fälle, in denen die Regel
nicht greift.

## Wie gefragt wird — die Lehre aus dem 3. August

**Gebündelt, nicht einzeln.** An dem Tag wurden acht Doppelehen einzeln
diskutiert, bis Thomas bremste: *„wir drehen uns im Kreis"*. Die anschließende
fünfzeilige Regel entschied sechs davon allein und legte zwei sauber vor.

    FALSCH   Fall 1 besprechen, Fall 2 besprechen, Fall 3 besprechen …
    RICHTIG  Regel formulieren, anwenden, die Ausnahmen gesammelt vorlegen

Daraus drei Regeln für die Zusammenarbeit:

1. **Erst Regel, dann Ausnahmen.** Nie Einzelfälle abarbeiten, solange eine
   Regel möglich ist. Die Ausnahmeliste ist das Ergebnis, nicht der Anfang.
2. **Fragen sammeln.** Zweifelsfälle einer Runde am Stück vorlegen, nicht
   einzeln nachfragen.
3. **Mit Empfehlung fragen.** Nicht „was soll ich tun", sondern „ich würde X,
   weil Y — einverstanden?"

## Ablauf je Runde

    1  Vorbereiten    Dubletten aussortieren, Raster, Streifen
    2  Lesen          Modell, mit Fehlerkatalog und Nachbarzeilen
    3  Verknüpfen     Kaskade je Aktart gegen die Bestände
    4  Vorlegen       Maske: nur offene Felder; Zweifelsfälle gesammelt
    5  Festhalten     Stand in die DB, Auffälligkeiten in wissen/

Nach jeder Runde ein kurzer Stand: wie viele Einträge, wie viele bestätigt,
wie viele offen, was ist aufgefallen. **Keine Detailberichte ohne Anlass.**

## Reihenfolge des Gesamtvorhabens

Begründet in `doku/ansatz.md` (Anker-Verfallskurve):

    1  Heiraten 1808–1829     ~25 Seiten   baut den Anker für alles Weitere
    2  Tode     1808–1829     ~75 Seiten   Kaskade läuft bereits
    3  Taufen   1808–1829     ~90 Seiten   mit dann vollem Anker

Taufen zuletzt, obwohl die Bilder zuerst da waren: Ohne die Ehen verliert der
Elternehe-Anker ab 1814 die Mehrheit und ab 1820 fast alles (94 % → 18 %).
Wer die Taufen vorzieht, prüft sie später ein zweites Mal.

## Woran der Fortschritt abgelesen wird

    python3 -m werkstatt.db --stand        Erfasstes, Bestätigtes je Register
    SELECT * FROM fehlerkatalog            was das Modell wo falsch liest
    SELECT * FROM chronologie WHERE …      Datumslücken und Reihenfolgebrüche

Zahlenstände gehören in die Datenbank, nicht in Markdown — sonst veralten sie
unbemerkt. (Regel aus ofb-ki übernommen.)
