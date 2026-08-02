# kirchenbuch

Werkzeug zum **Fortschreiben** eines genealogischen Bestands aus Kirchenbüchern:
Registerseite lesen, gegen den vorhandenen Bestand abgleichen, anbinden oder neu
anlegen — und am Ende als GEDCOM ausgeben.

> **Work in Progress.** Entsteht gerade an einem echten Bestand
> (Kirchenbücher Haberschlacht ab 1808). Noch nicht benutzbar für Fremde.

## Wozu

Ahnenblatt, Gramps und webtrees sind gut im *Verwalten* eines Bestands, aber
mühsam im *Fortschreiben aus einer Quelle*. Für jeden Registereintrag stellt
sich dieselbe Frage — **find and use** oder **create** — und die kostet dort
viele Klicks. Genau die soll hier vorbeantwortet und nur noch bestätigt werden.

## Ansatz

**Registernah erfassen, nicht GEDCOM-nah.** Eine Zeile je Registereintrag, so
wie es dasteht. Die GEDCOM-Erzeugung ist eine Ableitung daraus. Dadurch lässt
sich die Zuordnung korrigieren, ohne die Lesung anzufassen — und umgekehrt.

**Änderungsjournal statt Mutation.** Der Ausgangsbestand wird nie verändert.
Jede Ergänzung und Korrektur ist ein Vorgang mit Beleg; die Ausgabedatei wird
daraus erzeugt. Rücknahme heißt Vorgang deaktivieren.

**Belege statt Urteile.** Nicht „Stufe A", sondern *woran* eine Aussage hängt:
`Ehe-Anker F1149, oo 14.02.1798`. Die Bewertung ist daraus ableitbar, umgekehrt
nicht.

**Der Bestand wächst mit.** Ohne vorhandenes GEDCOM läuft find-and-use gegen die
eigene bisherige Erfassung: die ersten hundert Einträge erzeugen das Vokabular
für die nächsten tausend.

## Stand

| | |
|---|---|
| ✅ | GEDCOM-Index in SQLite, verlustfreier Round-Trip (byte-identisch) |
| ✅ | Äquivalenzklassen von Namensvarianten samt Erkennung falscher Zuordnungen |
| ✅ | Dublettenerkennung über Ehepaar-Signatur |
| ✅ | Erfassungsmaske im Browser mit Bildstreifen, Autovervollständigung, Familienanbindung |
| 🚧 | Generalisierung: Konfiguration statt fest verdrahteter Felder |
| 🚧 | Ablauf Register wählen → Seiten wählen → arbeiten |
| ⬜ | GEDCOM-Export der Neuerfassung |
| ⬜ | Paket zum Doppelklick, ohne Python-Installation |

## Rechtliches

Kirchenbuch-Scans von Archion, Ancestry o. ä. dürfen **nicht weiterverbreitet**
werden. `bilder/` und `daten/` sind deshalb von der Versionsverwaltung
ausgenommen und gehören nicht in ein öffentliches Repository.
