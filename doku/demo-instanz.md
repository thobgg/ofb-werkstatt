# Auftrag: eine vorführbare Instanz

*Für eine eigene Sitzung. Stand 17. August 2026.*

## Was gebraucht wird

Eine Instanz der Werkstatt, die unter `ofb-werkstatt.bgg-home.de` erreichbar
ist und die ein Fremder anklicken kann, **ohne** etwas zu installieren.
Sie soll den Ansatz zeigen: Bildstreifen, Spaltenkopf, Ampel, Aktkarte,
Korrigieren, Übergeben, GEDCOM.

## Die vier Bedingungen

**Ohne KI.** Quelle ausschließlich *Testdaten* (`daten/pilot.json`, 93
fertige Lesungen). Kein `ANTHROPIC_API_KEY` in der Umgebung, kein `claude`
im Pfad. Sonst liest ein Besucher auf Rechnung des Betreibers – gemessen:
7 Seiten über Claude Code = 10,43 $ Gegenwert.

**Vorbereitet.** Einrichtung, Beispielbestand und alle drei Runden schon
gelesen, Stand `korrigieren`. Wer die Seite öffnet, steht sofort in der
Maske. Ein Klon muss sonst erst einrichten, planen, lesen – drei Schritte
vor dem Eigentlichen.

**Getrennt.** Eigenes Verzeichnis, eigene SQLite, eigener Port. Die
Arbeitsinstallation in `~/Dokumente/Ahnenforschung/ofb-werkstatt` bleibt
unberührt und läuft weiter.

**Zurücksetzbar.** Eine unberührte Kopie der Datenbank daneben; ein
Aufruf spielt sie zurück. Stündlich per cron, sonst hat der zweite
Besucher die Korrekturen des ersten vor sich.

## Nachtrag 18. August: Zuschauen ohne Passwort

Gemessen an der Wirklichkeit: Mehrere Besucher haben die Instanz
aufgerufen und bei der Passwortabfrage wieder aufgelegt, statt nach dem
Passwort zu fragen – die Hemmschwelle war höher als die Neugier. Für ein
Schaustück ist eine Tür, hinter der man nichts erkennen kann, die
falsche Tür.

Seither gilt: **Zuschauen ohne Passwort, Mitarbeiten mit.**
Eingeschaltet über `OFB_DEMO_OFFEN=1` (Umgebung) oder die Datei
`daten/demo-offen`; ohne den Schalter bleibt alles wie zuvor.

    lesen (GET)     ohne Anmeldung – Seiten, Bildstreifen, Ampel,
                    Belege, Übergabe-Probelauf, GEDCOM-Vorschau
    ändern (POST)   401 – Korrigieren, Bestätigen, Übergeben,
                    Ausgeben, Hinweis-Stift
    /stats          401 – das Zugriffslog geht Besucher nichts an

Die Oberfläche sagt es oben in einem Band („Sie schauen zu …") und
schaltet alle Bedienelemente ab; der Link *anmelden* führt auf
`/anmelden`, das für Zuschauer 401 liefert und damit die Passwortabfrage
auslöst – ein `fetch` täte das nicht, eine Navigation schon.

Der Hinweis-Stift bleibt dem angemeldeten Zugang vorbehalten: Er
schreibt in die Datenbank und stünde sonst jedem Vorbeikommenden offen.

## Was der Betrieb noch braucht

- **Basic Auth** am Proxy, solange es um einen kleinen Kreis
  Eingeladener geht.
- `POST /api/beenden` **sperren** – sonst schaltet der erste Besucher den
  Server ab. Vorschlag: Umgebungsvariable `OFB_DEMO=1`, die den Endpunkt
  verweigert.
- Die App hört nur auf `127.0.0.1` und soll das bleiben; der Proxy
  verbindet sich lokal.

## Was **nicht** gebaut wird

Kein Mehrbenutzerbetrieb, keine Anmeldung, keine Migration auf MariaDB.
Die Werkstatt ist Einzelplatz von der Bauart her – eine Datenbank, eine
Runde. Wenn mehrere arbeiten sollen, bekommt **jeder seine eigene
Instanz**; das gemeinsame Ergebnis entsteht in webtrees, nicht in der
Werkstatt.

## Bausteine, die schon da sind

`werkstatt/probelauf.py` baut bereits einen Klon aus `git ls-files`,
startet ihn als eigenen Prozess und fährt den ganzen Durchlauf über die
Web-Schnittstelle. Für die Demo-Instanz muss er **vor** dem Bestätigen
anhalten und das Verzeichnis stehenlassen.

## Prüfstein

```
python3 -m werkstatt.probelauf
```

muss danach unverändert grün bleiben: 81 Einträge, 24 grün, Leerlauf
zeichengleich, 0 tote Zeiger.
