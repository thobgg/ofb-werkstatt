# Windows: einrichten und ausprobieren

Für Leute, die mit GitHub nichts zu tun haben. Es braucht keinen Account,
kein Git und keine Kommandozeile – bis auf eine einzige Zeile, mit der
geprüft wird, ob Python da ist.

Gebraucht wird: Windows 10 oder 11, etwa 100 MB Platz, zehn Minuten.
Scans, Datenbank und ein Schlüssel für die KI sind **nicht** nötig; die
Beispielseiten und fertige Lesungen liegen bei.

---

## 1. Python holen

`python.org/downloads` → der große gelbe Knopf lädt die aktuelle Fassung.
Beim Installieren unten **„Add python.exe to PATH" ankreuzen**. Ohne das
Häkchen findet Windows das Programm später nicht.

Gebraucht wird **3.11 oder neuer**. Prüfen: Windows-Taste drücken, `cmd`
tippen, Enter, dann

    py --version

Erwartet: eine Zahl wie `Python 3.13.1`. Kommt „Der Befehl … ist falsch
geschrieben", fehlt das Häkchen – Python noch einmal installieren und die
Zeile *Modify* → *Add to PATH* wählen.

## 2. Das Programm holen

Im Browser auf **github.com/thobgg/ofb-werkstatt**. Dort der grüne Knopf
**„Code"**, darin **„Download ZIP"**.

Die Datei landet in `Downloads` und heißt `ofb-werkstatt-main.zip`.
Rechtsklick → **„Alle extrahieren"** → als Ziel etwa
`C:\Users\<dein Name>\Dokumente` wählen.

> Danach liegt dort ein Ordner `ofb-werkstatt-main`, und **darin noch
> einmal** einer gleichen Namens. Der innere ist der richtige: In ihm
> liegen `start.py` und die beiden Startdateien.

## 3. Starten

In diesem Ordner doppelt anklicken:

    OFB-Werkstatt starten (Windows).bat

Ein schwarzes Fenster geht auf. Beim allerersten Mal steht dort „Es fehlt
noch etwas, das hole ich" und es lädt zwei Zusatzpakete (Pillow und numpy,
zusammen etwa 30 MB) – das dauert eine halbe Minute. Danach öffnet der
Browser `http://127.0.0.1:8765`.

**Das schwarze Fenster bleibt offen** – das ist das Programm. Wer es
schließt, schaltet die Werkstatt ab. Zum Beenden gibt es in der Maske
unten den Knopf *Beenden*.

Zwei Dinge, die Windows dazwischenfunken kann:

- **„Der Computer wurde durch Windows geschützt"** – SmartScreen kennt
  die Datei nicht. *Weitere Informationen* → *Trotzdem ausführen*.
- **Der Browser geht nicht auf** – dann die Adresse
  `http://127.0.0.1:8765` von Hand eintippen.

Schließt sich das schwarze Fenster sofort wieder, steht der Grund darin.
Dann besser über die Eingabeaufforderung starten, da bleibt die Meldung
stehen: `cmd` öffnen, in den Ordner wechseln und `py start.py` eingeben.

## 4. Einrichten

Beim ersten Start fragt die Maske nach Gemeinde und Registern.

- **Gemeinde**: irgendein Name, für den Versuch etwa `Haberschlacht`.
- **Register**: Taufen, Ehen, Tode stehen zur Wahl. Die Bildordner sind
  schon vorbelegt – sie zeigen auf die mitgelieferten Beispielseiten in
  `demo\bilder`. So lassen.
- **Beispielbestand**: ankreuzen. Das sind 23 Personen aus dem gedruckten
  Ortsfamilienbuch. Ohne sie bleibt beim Abgleich alles gelb, weil es
  nichts gibt, wogegen geprüft werden könnte.

## 5. Der Durchlauf

Auf der Startseite unter **Lesen** als Quelle **Testdaten** wählen. Das
kostet nichts und braucht keinen Schlüssel: Die Lesungen liegen fertig
bei, so wie ein Modell sie geliefert hat, **vor jeder Korrektur**.

Dann der Reihe nach:

1. **Runde beginnen** – die Werkstatt schlägt ein Register vor.
2. **Lesen** – geht bei den Testdaten in Sekunden.
3. **Korrigieren** – die Maske zeigt je Eintrag den Bildstreifen mit dem
   gedruckten Spaltenkopf darüber. Daneben die Felder mit der Ampel:
   grün heißt, es gibt einen Beleg im Bestand; gelb heißt, das Wort ist
   bekannt, aber nichts bestätigt es; rot heißt, kein Treffer.
4. **Übergeben** – erst damit wandert der Eintrag in den Bestand.
5. **Ausgeben** – GEDCOM, das sich in Gramps, Ahnenblatt und andere
   Programme laden lässt.

Was dabei herauskommen soll, wenn alles läuft:

| | |
|---|---|
| Einträge | 81 auf dreizehn Seiten (Taufe 23, Ehe 19, Tod 39) |
| grün | 10 Felder, alle über die Elternehe im Bestand |
| Ausgabe | rund 64 kB, 244 Personen, 96 Familien |
| Leerlauf | ohne eigene Änderung zeichengleich zur Vorlage |

Die Zahlen weichen ab, wenn nur ein Teil bestätigt wurde – das ist kein
Fehler, sondern die Rechnung: Übergeben wird nur, was bestätigt ist.

---

## Für den, der es genauer wissen will

Ein Befehl fährt den ganzen Weg von selbst ab, in einem Wegwerfordner,
und vergleicht das Ergebnis mit den Zahlen oben:

    py -m werkstatt.probelauf

Am Ende steht entweder „Alles wie in der README beschrieben" oder es wird
aufgezählt, was abweicht.

---

## Was hier noch ungeprüft ist

Der Weg oben ist unter Linux gemessen, unter Windows **geschrieben, aber
nicht gefahren**. Wer ihn geht, hilft am meisten mit dem Wortlaut dessen,
was schiefging – bitte nicht sinngemäß.

Am wenigsten geprüft ist die **Anmeldung an Claude Code**, also der Weg,
eigene Seiten lesen zu lassen statt der Testdaten. Wer den mitnehmen will:

1. Von `claude.com/download` das Windows-Programm installieren.
2. In der Eingabeaufforderung `claude --version` – erwartet eine Nummer.
3. In der Werkstatt oben rechts das **Zahnrad**, dann **KI-Anbindung**.
   Dort soll stehen: *Claude Code ist installiert, aber nicht angemeldet*,
   darunter der Knopf **Jetzt anmelden**.
4. Knopf drücken. Erwartet: ein Eingabeaufforderungs-Fenster geht auf, der
   Browser fragt nach dem Konto, und danach wird **ohne Neuladen** aus dem
   Knopf eine grüne Zeile mit Konto und Abo.

Schritt 4 ist der eigentliche Prüfpunkt. Fenster und Browser hängen an
Windows, das Umschalten hängt an der Werkstatt.

Steht dort „nicht installiert", obwohl Schritt 2 geklappt hat, findet die
Werkstatt das Programm nicht – der interessanteste Fehlerfall. Dann bitte
notieren, wohin es installiert wurde.

**Noch ein Handgriff, wenn Zeit ist:** die `.bat` bei laufendem Server ein
zweites Mal doppelklicken. Erwartet: „Die Werkstatt läuft schon", ein
neues Browserfenster, keine Meldung über einen belegten Port.
