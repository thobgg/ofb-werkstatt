# Das Admin-Portal: Betreiber-Handgriffe im Browser

Stufe 5 des Mehrbenutzer-Bauplans (`naechste-sitzung.md`). Eine eigene
kleine App auf dem Wirt – eigener Port, eigenes Passwort, kein Login in
die Instanzen. Sie arbeitet über das **Dateisystem** der
Instanzverzeichnisse; wer eine Parochie kompromittiert, hat weiterhin
nur sie. Der Shell-Zugriff bleibt der Generalschlüssel und Rettungsweg.

## Gesamtbild

Ein OFB ist ein **Ordner auf dem Wirt**; Container, Proxy-Eintrag und
App sind nur die Bedienung dieses Ordners.

```
                         Internet
                            │
                   Reverse Proxy (einer für alles)
        ┌───────────────────┼───────────────────────┐
  haberschlacht.xyz    neipperg.xyz         portal.xyz (besser: nur LAN)
        │                   │                       │
  127.0.0.1:8770      127.0.0.1:8771          127.0.0.1:8767
  ┌─────▼──────┐      ┌─────▼──────┐          ┌─────▼──────┐
  │ Container   │      │ Container  │          │ Container  │
  │ Werkstatt   │      │ Werkstatt  │          │ Portal     │
  └─────┬──────┘      └─────┬──────┘          └─────┬──────┘
        │                   │                       │ liest/schreibt
  ══════▼═══════════════════▼═══════════════════════▼══ Dateisystem ══
  ofb-instanzen/
     haberschlacht/                 neipperg/
        daten/erfassung.sqlite  ◄── das OFB lebt hier
        daten/nutzer.txt            (Konten dieser Parochie)
        bilder/  quellen/  ausgabe/  sicherungen/
```

Daraus folgt alles Weitere: Der Container ist wegwerfbar, dem OFB
passiert dabei nichts. Backup eines OFB ist ein Ordner, Umzug auf einen
anderen Server ist Ordner kopieren. Das Repo `ofb-werkstatt` ist nur
der Bauplan; beim Anlegen kopiert das Portal den Code in den neuen
Ordner. Und das Portal geht nie über HTTP in die Instanzen, sondern
arbeitet direkt auf deren Ordnern - deshalb braucht es dort keinen
Login. Je neuem OFB bleiben drei Handgriffe: der Klick im Portal,
einmal `docker compose up`, eine Proxy-Zeile.

## Starten

```sh
OFB_PORTAL_PASSWORT=... python3 -m werkstatt.portal
OFB_PORTAL_PASSWORT=... python3 -m werkstatt.portal --wurzel ~/ofb-instanzen --port 8767
```

Ohne Passwort startet es nicht – das Portal legt Konten und Projekte
an. Gehört wird nur 127.0.0.1; nach außen kommt es über den Reverse
Proxy (eigener Hostname, Ziel `127.0.0.1:8767`), optional nur im LAN.
Jede Änderung steht in `portal.log` neben den Instanzen.

## Die vier Funktionen

**Projektliste.** Alle Instanzen unter der Wurzel, mit Stand aus deren
Dateien gelesen (nur lesend, `mode=ro`): Personen, Familien, Einträge,
offene Runden, letzter Zugriff, Konten, Verbrauch gegen Kontingent.

**Neues OFB anlegen.** Name, Kontext-GEDCOM (Upload, wird als
`beleg` eingelesen), erstes Redakteurskonto – Pflicht, sonst ginge die
Instanz ohne Anmeldung hinter den Proxy. Provisioniert wird über
`werkstatt/instanz.py`: Klon aus `git ls-files`, kurz gestartet und
über die eigene Web-Schnittstelle eingerichtet (derselbe Weg, den der
Browser nimmt), dann `daten/nutzer.txt` und Betriebsdateien mit
eigenem Port. Ports: 8765 Arbeitsplatz, 8766 Vorführinstanz, 8767
Portal, Instanzen ab 8770 (`betrieb/port`). Ab da verwaltet der
Redakteur seine Instanz selbst im Zahnrad.

Von der Kommandozeile geht dasselbe:

```sh
python3 -m werkstatt.instanz --neu Neipperg --gedcom bestand.ged --redakteur maria
python3 -m werkstatt.instanz --liste
```

**Nutzerverwaltung je Projekt.** Bearbeitet die `nutzer.txt` der
Instanz – dieselbe Datei wie der Zahnrad-Reiter des Redakteurs, nur
von oben, mit denselben Regeln (der letzte Redakteur bleibt).

**KI-Kontingent je Projekt.** Setzt `ki.budget_dollar` in der
Instanz-Datenbank. Geprüft wird **in der Instanz**
(`werkstatt/kontingent.py`), vor `plane`, `einlesen` und
`lesen-lassen`, gegen die Summe der verbuchten Auftragskosten
(`auftrag.dollar` – gemessen, nicht geschätzt). Testdaten zählen
nicht; der Abo-Weg zählt mit, denn in einer gehosteten Instanz läuft
er über das Konto des Betreibers. Keine Einstellung = kein Deckel; der
Einzelplatz des README merkt von alledem nichts.

## Betrieb auf dem NAS (und später dem Vereinsserver)

Die Betriebsdateien liegen in `betrieb/portal/` (Dockerfile,
compose.yaml). Der Wirt braucht drei Verzeichnisse:

    /volume1/docker/ofb/werkstatt      das Repo MIT .git (git clone oder
                                       tar inkl. .git) - Quelle der
                                       Provisionierung, nur lesend
    /volume1/docker/ofb-instanzen      Wurzel der Instanzen
    /volume1/docker/ofb-instanzen/<slug>   entsteht durch das Portal

Einrichten:

    # Repo und betrieb/portal aufs NAS bringen, Passwort in compose.yaml
    cd /volume1/docker/ofb/werkstatt/betrieb/portal
    sudo docker compose up -d          # Portal auf 127.0.0.1:8767

    # Reverse Proxy im DSM: eigener Hostname → HTTP 127.0.0.1:8767,
    # Proxy-Timeout 300 s (die Provisionierung importiert GEDCOM)

Das Portal legt Instanzen nur an. Ihren Container startet der Betreiber
einmalig selbst - `docker` braucht auf der Synology sudo, und ein
Portal, das Container starten dürfte, hätte den Generalschlüssel, den
der Bauplan ausdrücklich nicht will:

    cd /volume1/docker/ofb-instanzen/<slug>/betrieb
    sudo docker compose up -d
    # Proxy: <parochie>.example → 127.0.0.1:<port>  (steht in betrieb/port)

Ab da läuft alles im Browser: Der Redakteur lädt Scans hoch, lässt
lesen, korrigiert; Gäste schauen zu und hinterlassen Hinweise. Der
Shell-Zugriff bleibt Rettungsweg und wird für den Alltag nicht mehr
gebraucht.

## Support-Zugang: als Betreiber in eine Instanz

Der Betreiber hat kein stehendes Konto in den Instanzen. Braucht eine
Parochie Hilfe, gibt es im Portal je Projekt den Knopf
**Support-Zugang anlegen**: Er legt dort das Redakteurskonto `support`
mit einem Zufallspasswort an und zeigt das Passwort genau einmal.
Damit meldet man sich auf der Instanz-Seite an, behebt die Sache und
entfernt den Zugang mit demselben Knopf wieder.

Warum so und nicht als festes Admin-Konto: Das Konto steht sichtbar in
der Kontenliste der Instanz (der Redakteur sieht es), jeder Schritt
steht im `portal.log`, und ein geleaktes Passwort öffnet eine Parochie
statt alle. Der Komfort ist derselbe - ein Klick.

## Sicherung

Je Projekt im Portal: **Sicherung erstellen** packt eine ZIP-Datei mit
der Datenbank (als konsistenter Schnappschuss, nicht als Dateikopie),
der Kontenliste, beiden Konfigurationsdateien, den Kontextquellen und
den GEDCOM-Ausgaben nach `sicherungen/` in der Instanz. Die letzten
zehn bleiben liegen, alle sind im Portal herunterladbar - eine Kopie
gehört regelmäßig weg vom Wirt (Download genügt).

Die Scans sind nicht enthalten (groß, liegen beim Bearbeiter oder
kommen per Upload wieder); wer sie mitsichern will:
`python3 -m werkstatt.sicherung --mit-bildern` in der Instanz.

**Wiederherstellen** ist bewusst kein Knopf, sondern Kommandozeile mit
Rückfrage - es überschreibt den aktuellen Stand:

```sh
python3 -m werkstatt.sicherung --wiederherstellen sicherungen/NAME.zip
```

Die laufende Datenbank bleibt dabei als `.vorher` liegen, ein
Fehlgriff ist umkehrbar. Danach den Server neu starten. Zusätzlich
gilt auf einer Synology: Hyper Backup über die Instanzen-Wurzel
sichert auch die Sicherungen mit.

## Zugang für Interessierte

Anfangs per Mail an den Admin: Er legt das Projekt im Portal an und
schickt die Zugangsdaten des Redakteurskontos. Ein Anfrageformular
kommt später, wenn es gebraucht wird.
