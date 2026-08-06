# Windows 11: einmal von vorn

Was hier geprüft wird, ist nicht die Transkription, sondern der Einstieg —
also genau das, was ein fremder Nutzer beim ersten Start erlebt. Scans und
Datenbank braucht es dafür nicht; ein frisch geklontes Projekt startet als
Nullstart mit „Musterhausen" und leeren Registern.

Vor jedem Schritt steht, was passieren muss. Weicht etwas ab, ist das das
Ergebnis — bitte den Wortlaut notieren, nicht sinngemäß.

## 1. Python

Von `python.org/downloads` holen. Beim Installieren **„Add python.exe to
PATH" ankreuzen** — ohne das findet nachher nichts das Programm.

Prüfen, in der Eingabeaufforderung (Windows-Taste, `cmd`, Enter):

    py --version

→ eine Versionsnummer ab 3.10.

## 2. Das Projekt holen

Ohne Git am einfachsten über den Browser:
`github.com/thobgg/ofb-werkstatt` → grüner Knopf **Code** → **Download ZIP**
→ auspacken, etwa nach `C:\Users\<name>\ofb-werkstatt`.

Mit Git:

    git clone https://github.com/thobgg/ofb-werkstatt.git

## 3. Claude Code

Von `claude.com/download` das Windows-Installationsprogramm.
**Nicht anmelden** — die Anmeldung ist ja der Prüfgegenstand.

Prüfen:

    claude --version

→ eine Versionsnummer. Kommt „Der Befehl … ist falsch geschrieben", ist
Claude Code nicht im Suchpfad; dann bitte notieren, wohin es installiert
wurde.

## 4. Starten

Im Explorer in den Projektordner, Doppelklick auf

    OFB-Werkstatt starten (Windows).bat

→ Ein schwarzes Fenster geht auf, holt bei Bedarf Pillow, und der Browser
öffnet `http://127.0.0.1:8765`. Das schwarze Fenster **bleibt offen** — das
ist der Server.

Geht der Browser nicht auf: Adresse von Hand eingeben. Schließt sich das
Fenster sofort, den Inhalt abfotografieren.

## 5. Der Prüfgegenstand

Oben rechts das **Zahnrad**, dann zu **KI-Anbindung** blättern.

Dort muss stehen: *Claude Code ist installiert, aber nicht angemeldet* und
darunter der Knopf **Jetzt anmelden**.

- Steht dort „nicht installiert", obwohl Schritt 3 geklappt hat, findet die
  Werkstatt das Programm nicht — der interessanteste Fehlerfall.
- Steht dort eine grüne Zeile mit Konto, war doch schon eine Anmeldung da.

Knopf drücken. Erwartet:

1. ein Eingabeaufforderungs-Fenster geht auf und zeigt die Anmeldung
2. der Browser fragt nach dem Konto
3. **ohne Neuladen** wird aus dem Knopf eine grüne Zeile mit Konto und Abo

Schritt 3 ist der eigentliche Test — Fenster und Browser hängen an Windows,
das Umschalten hängt an der Werkstatt.

## 6. Noch zwei Handgriffe, wenn Zeit ist

**Ein zweiter Start** bei laufendem Server: Die `.bat` noch einmal
doppelklicken. Erwartet: „Die Werkstatt läuft schon", nur ein neues
Browserfenster, keine Fehlermeldung über einen belegten Port.

**Testdaten lesen.** Auf der Startseite Quelle *Testdaten*, „Lesen starten".
Das kostet nichts und braucht keine Scans. Erwartet: eine Runde entsteht,
die Korrekturmaske zeigt Einträge.

## Was zurückkommen soll

Je Schritt: geklappt oder nicht, und bei „nicht" der Wortlaut. Besonders
Schritt 5 — dort ist ungetesteter Code, alles davor ist gewöhnliche
Installation.
