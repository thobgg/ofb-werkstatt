# Mehrbenutzer: mehrere Bearbeiter, einer ist Redakteur

*Stand 17. August 2026. Eine Datei schaltet alles ein; ohne sie bleibt
die Werkstatt der Einzelplatz ohne Anmeldung aus dem README.*

## Einschalten

Konten anlegen - das erste als Redakteur:

    python3 -m werkstatt.nutzer --anlegen thomas --rolle redakteur
    python3 -m werkstatt.nutzer --anlegen anna
    python3 -m werkstatt.nutzer --anlegen bernd
    python3 -m werkstatt.nutzer --liste

Das Passwort wird verdeckt abgefragt (mindestens 8 Zeichen) und als
PBKDF2-Hash in `daten/nutzer.txt` abgelegt - lesbar, ohne Klartext,
ausserhalb von Git. Sobald die Datei Konten enthaelt, verlangt der
Server Anmeldung (Basic Auth, Name und Passwort). `--weg NAME` entfernt
ein Konto.

Ab dem ersten Konto geht es auch **im Browser**: Zahnrad, Reiter
**Nutzer** - anlegen, Rolle aendern, entfernen. Sichtbar nur fuer den
Redakteur (und am Einzelplatz fuer das allererste Konto, das immer
Redakteur wird). Der letzte Redakteur laesst sich weder entfernen noch
degradieren - sonst spertte man sich aus der Verwaltung aus.

## Rollen

| | redakteur | bearbeiter |
|---|---|---|
| Korrigieren, Bestaetigen | ja | ja |
| Runden planen, lesen lassen, Nachlesen, Fragen | ja | nur nach Freigabe* |
| Uebergeben (Erfassung wird Bestand) | ja | nein |
| Ausgeben (GEDCOM 5.5.1 und 7) | ja | nein |
| Einstellungen, Quellen, Aktkarten, Einrichtung | ja | nein |

*Freigabe: Einstellung `rollen.bearbeiter_liest` auf `1` (im Zahnrad
unter Eigene Werte oder per POST /api/einstellungen). Das Lesen laeuft
ueber den API-Schluessel der Instanz - deshalb entscheidet der
Redakteur einmal bewusst, ob Bearbeiter auf Instanzrechnung lesen.

Das Uebergeben ist der Redaktionsentscheid: erst damit wird Erfassung
zu Bestand. Dasselbe Muster wie in den Crowdsourcing-Projekten - viele
schlagen vor, einer uebernimmt gegen die Quelle.

## Parallel arbeiten

Je Register darf eine Runde offen sein: Taufen, Ehen und Tote laufen
gleichzeitig, drei Bearbeiter arbeiten nebeneinander. Alle ankern gegen
dieselbe Datenbank; die Dublette aus getrennter Erfassung (zwei
Bestaende, hinterher verschmelzen) kann so nicht entstehen.

- Die Startseite verlinkt alle offenen Runden.
- `/korrektur?runde=N` oeffnet eine bestimmte Runde; ohne Parameter
  gilt die juengste.
- Im selben Register bleibt die Reihenfolge Pflicht - die zweite
  Tranche muss gegen die uebergebene erste ankern koennen.

Nach **jeder Uebergabe** werden alle noch offenen Runden automatisch
gegen den gewachsenen Bestand neu abgeglichen: Die Ampeln der Kollegen
werden frisch, ohne dass jemand etwas tut; bestaetigte Entscheidungen
bleiben unangetastet.

## Wer hat was getan

Jede Speicherung und Bestaetigung traegt den Kontonamen
(`eintrag.bearbeiter`); das Zugriffslog der Vorfuehrinstanz zeigt ihn
als Suffix der Adresse: `84.44.1.2(anna)`.

## Abgrenzung

Eine Instanz je Parochie (eigene Datenbank, eigener Container) - das
Anlegen weiterer Projekte ist Provisionierung, kein Datenmodell - das
macht das Admin-Portal des Betreibers (`doku/portal.md`). Kein
gleichzeitiges Bearbeiten desselben Eintrags, keine Sperrlogik: die
Registertrennung ersetzt sie. Offene Stufen (Gast mit Hinweis-Stift,
Scan-Upload) stehen in `doku/naechste-sitzung.md`.
