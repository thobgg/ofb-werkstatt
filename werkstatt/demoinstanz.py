#!/usr/bin/env python3
"""Die vorführbare Instanz bauen, zurücksetzen, nachsehen.

    python3 -m werkstatt.demoinstanz --bauen
    python3 -m werkstatt.demoinstanz --zuruecksetzen
    python3 -m werkstatt.demoinstanz --zeigen

**Wozu.** Ein Fremder soll den Ansatz anklicken können, ohne etwas zu
installieren – Bildstreifen, Spaltenkopf, Ampel, Aktkarte, Korrigieren,
Übergeben, GEDCOM. Ein frischer Klon zeigt davon nichts: Er müsste erst
einrichten, planen, lesen. Drei Schritte vor dem Eigentlichen, und der
erste Eindruck ist ein leeres Formular.

Dieses Skript nimmt sie vorweg. Es baut denselben Klon wie
`probelauf.py`, fährt ihn über die Web-Schnittstelle durch – und hält
**vor dem Bestätigen der letzten Runde** an. Wer die Seite öffnet, steht
mitten in der Korrekturmaske, mit Bild, Ampel und Bestandstreffern.

**Warum zwei Runden trotzdem übergeben werden.** `runde.plane()` lässt
immer nur eine Runde offen; eine zweite zu planen, solange die erste
nicht auf `fertig` steht, verweigert es. „Alle drei gelesen" und „alle
drei auf `korrigieren`" schließen sich also aus. Also: Ehen und Tote ganz
durch, Taufen gelesen und offen. Das ist nicht bloß die Notlösung – es
ist auch der bessere Aufbau. Die übergebenen Runden liegen im Bestand,
wenn die Taufen gelesen werden, und genau daran zeigt sich der Anker:
Der Vater eines Täuflings ist grün, weil seine Ehe zwei Runden vorher
eingetragen wurde.

**Ohne KI.** Gelesen wird ausschließlich aus `daten/pilot.json`. Der
Bau läuft ohne `ANTHROPIC_API_KEY` in der Umgebung; betrieben wird die
fertige Instanz mit `OFB_DEMO=1`, was das Lesen im Programm sperrt (siehe
`konfig.demo`). Beides zusammen, nicht eines davon – die Umgebung eines
Dienstes lässt sich sauber halten, `claude` im Suchpfad nicht.

**Zurücksetzbar.** Neben der Arbeitsdatenbank liegt eine unberührte
Kopie. `--zuruecksetzen` spielt sie zurück, ohne den Server anzuhalten;
stündlich aufgerufen hat der zweite Besucher nicht die Korrekturen des
ersten vor sich.
"""
import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from . import konfig, testdaten
from .klon import Maske, ausnahmen, baue, frei, warte

# Bewusst **nicht** neben der Arbeitsinstallation. `testdaten.py` hat zwei
# Zweige: Liegt das Nachbarprojekt daneben, liest es dessen Datenbank;
# fehlt es, greift die mitgelieferte `daten/pilot.json`. In
# `~/Dokumente/Ahnenforschung/` liegt das Nachbarprojekt – eine Demo
# dort hätte die Arbeitsdatenbank des Betreibers ausgeliefert, und zwar
# lautlos. Beim ersten Bau ist genau das passiert; gemerkt hat man es
# nur daran, dass das Eheregister leer blieb.
ZIEL = Path("~/ofb-werkstatt-demo").expanduser()
PORT = 8766                    # die Arbeitsinstallation behält 8765

# Reihenfolge des Aufbaus. Die letzte Runde bleibt offen – sie ist die,
# in der der Besucher landet. Dass es die Taufen sind, ist Absicht: Nur
# dort liegen Zeilenstreifen, und drei Personen je Eintrag lassen sich
# überblicken, wo das Eheregister sechs hat.
DURCH = ("ehe", "tod")
OFFEN = "taufe"

DB = Path("daten") / "erfassung.sqlite"
URFASSUNG = Path("daten") / "urfassung.sqlite"


# --------------------------------------------------------------- Bauen
def _umgebung():
    """Die Umgebung, in der gebaut wird: ohne Schlüssel, ohne Demo-Sperre.

    Ohne Schlüssel, damit ein versehentlich gesetzter nichts kostet.
    Ohne `OFB_DEMO`, weil der Bau selbst `/api/einrichten` braucht – und
    genau das ist im Betrieb gesperrt.
    """
    u = dict(os.environ)
    u.pop("ANTHROPIC_API_KEY", None)
    u.pop("OFB_DEMO", None)
    return u


def _lies_runde(m, art, seiten=5):
    """Eine Runde planen und einlesen. Rückgabe: (runde_id, Einträge)."""
    r = m("/api/runde/plane",
          dict(register=art, seiten=seiten, quelle="testdaten"))
    rid = r.get("runde")
    if not rid:
        raise SystemExit(f"{art}: keine Runde – {r.get('fehler', r)}")
    m("/api/einlesen", dict(runde=rid))
    for _ in range(180):
        time.sleep(2)
        if m(f"/api/fortschritt?runde={rid}").get("stand") == "fertig":
            break
    else:
        raise SystemExit(f"{art}: das Einlesen wurde nicht fertig.")
    liste = m(f"/api/eintraege?runde={rid}")
    return rid, (liste if isinstance(liste, list)
                 else liste.get("eintraege", []))


def _bestaetige(m, eintraege):
    """Jeden Eintrag so speichern, wie er gelesen wurde, und bestätigen."""
    for e in eintraege:
        werte = {x["name"]: {"wert": x.get("wert") or ""}
                 for x in e.get("felder", [])
                 if (x.get("wert") or "").strip()}
        m("/api/speichern", dict(id=e["id"], felder=werte, bestaetigt=True))


def _nachbar(ziel):
    """Die Datei, die `testdaten.py` an diesem Platz statt pilot.json nähme.

    Abgeleitet aus `testdaten.PILOT`, nicht abgeschrieben: Verschiebt
    jemand das Nachbarprojekt, wandert die Prüfung mit.
    """
    return ziel.parent / testdaten.PILOT.relative_to(konfig.WURZEL.parent)


def bauen(ziel=ZIEL, port=PORT, ersetzen=False):
    n = _nachbar(ziel)
    if n.exists():
        raise SystemExit(
            f"An diesem Platz läge das Nachbarprojekt daneben:\n  {n}\n"
            f"`testdaten.py` würde dann dessen Datenbank auslesen statt der "
            f"mitgelieferten daten/pilot.json –\nund die Vorführinstanz "
            f"trüge die Arbeitsdaten des Betreibers ins Netz.\n"
            f"Ein anderes Ziel wählen, etwa {ZIEL}.")
    if ziel.exists():
        if not ersetzen:
            raise SystemExit(
                f"{ziel} gibt es schon.\nMit --ersetzen wird es neu gebaut; "
                f"alles darin geht dabei verloren.")
        shutil.rmtree(ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)

    # Direkt an den endgültigen Platz, nicht in ein Wegwerfverzeichnis mit
    # anschließendem Verschieben. Was die Werkstatt an Pfaden ablegt, ist
    # zwar relativ zur Wurzel – aber „zwar" ist keine Zusage, die ein
    # Umzug einlösen muss.
    n = baue(ziel)
    print(f"Klon: {n} Dateien in {ziel}")

    bau_port = frei()
    log = ziel / "bau.log"
    server = subprocess.Popen(
        [sys.executable, "start.py", "--port", str(bau_port), "--kein-browser"],
        cwd=ziel, stdout=log.open("w"), stderr=subprocess.STDOUT,
        text=True, env=_umgebung())
    try:
        if not warte(bau_port):
            raise SystemExit("Der Klon startet nicht.\n"
                             + log.read_text(encoding="utf-8")[-4000:])
        m = Maske(bau_port)
        print(f"baut auf 127.0.0.1:{bau_port}\n")

        a = m("/api/einrichten", dict(
            gemeinde="Haberschlacht", ort="Haberschlacht",
            religion="evangelisch", bestand=True,
            register=[dict(art=x, ordner=f"demo/bilder/{x}")
                      for x in ("taufe", "ehe", "tod")]))
        if not a.get("ok"):
            raise SystemExit(f"Einrichten schlug fehl: {a}")

        for art in DURCH:
            rid, liste = _lies_runde(m, art)
            _bestaetige(m, liste)
            z = m("/api/runde/uebergib", dict(runde=rid)).get("zahlen", {})
            print(f"  {art:6} {len(liste):3} Einträge bestätigt und übergeben"
                  f"  -> {z.get('personen_neu', 0)} Personen, "
                  f"{z.get('familien_gefunden', 0)} Familien gefunden")

        # Und hier wird angehalten. Kein Bestätigen, kein Übergeben –
        # das ist der Teil, den der Besucher selbst machen soll.
        rid, liste = _lies_runde(m, OFFEN)
        ampel = {"gruen": 0, "gelb": 0, "rot": 0}
        for e in liste:
            for f in e.get("felder", []):
                if f.get("ampel") in ampel:
                    ampel[f["ampel"]] += 1
        print(f"  {OFFEN:6} {len(liste):3} Einträge gelesen, Stand "
              f"'korrigieren' – grün {ampel['gruen']}, gelb {ampel['gelb']}, "
              f"rot {ampel['rot']}")
    finally:
        _halt(server)

    meldungen = ausnahmen(log)
    if meldungen:
        print(f"\nAchtung: {len(meldungen)} Ausnahme(n) beim Bau, erste:\n"
              f"  {meldungen[0][:200]}")

    shutil.copy2(ziel / DB, ziel / URFASSUNG)
    print(f"\nUnberührte Kopie: {URFASSUNG} "
          f"({(ziel / URFASSUNG).stat().st_size // 1024} kB)")
    _betriebsdateien(ziel, port)
    print(f"\nFertig. Starten mit:\n  {ziel}/starten.sh")
    return 0


def _halt(server):
    if server and server.poll() is None:
        server.terminate()
        try:
            server.wait(10)
        except subprocess.TimeoutExpired:
            server.kill()


# --------------------------------------------------------- Zurücksetzen
def zuruecksetzen(ziel=ZIEL, still=False):
    """Die unberührte Kopie zurückspielen, ohne den Server anzuhalten.

    Nicht `shutil.copy2`. Die Werkstatt öffnet je Aufruf eine eigene
    Verbindung; eine Datei unter einer offenen Verbindung auszutauschen
    geht meistens gut und irgendwann nicht. `Connection.backup()` nimmt
    stattdessen dieselben Sperren wie ein Schreibvorgang – ein Aufruf,
    der gerade mittendrin ist, wartet, statt auf halbem Stand zu lesen.
    """
    q, z = ziel / URFASSUNG, ziel / DB
    if not q.exists():
        raise SystemExit(f"Keine unberührte Kopie: {q}\n"
                         f"Erst bauen: python3 -m werkstatt.demoinstanz --bauen")
    quelle = sqlite3.connect(f"file:{q}?mode=ro", uri=True)
    ziel_con = sqlite3.connect(z, timeout=30)
    try:
        quelle.backup(ziel_con)
    finally:
        ziel_con.close()
        quelle.close()

    # Was ein Besucher ausgegeben hat, liegt als Datei daneben und gehört
    # nicht zum Anfangsstand. Die Datenbank allein zurückzusetzen ließe
    # den nächsten glauben, er habe schon ausgegeben.
    weg = 0
    aus = ziel / "ausgabe"
    if aus.is_dir():
        for f in aus.iterdir():
            if f.is_file() and f.suffix.lower() == ".ged":
                f.unlink()
                weg += 1
    if not still:
        print(f"Zurückgesetzt: {z.name} aus {q.name}"
              + (f", {weg} Ausgabedatei(en) entfernt" if weg else ""))
    return 0


# ---------------------------------------------------------------- Zeigen
def zeigen(ziel=ZIEL):
    z = ziel / DB
    if not z.exists():
        raise SystemExit(f"Keine Instanz in {ziel}.")
    con = sqlite3.connect(f"file:{z}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    print(f"Instanz  : {ziel}")
    for r in con.execute("SELECT nr, register, stand, seiten FROM runde "
                         "ORDER BY nr"):
        print(f"  Runde {r['nr']}  {r['register']:6} {r['stand']:12} "
              f"{r['seiten']} Seiten")
    n = con.execute("SELECT count(*) FROM eintrag").fetchone()[0]
    b = con.execute("SELECT count(*) FROM eintrag WHERE status='bestaetigt'"
                    ).fetchone()[0]
    p = con.execute("SELECT count(*) FROM person").fetchone()[0]
    print(f"  {n} Einträge, davon {b} bestätigt · {p} Personen im Bestand")
    con.close()
    q = ziel / URFASSUNG
    print(f"  Unberührte Kopie: "
          + (f"{q.name}, {q.stat().st_size // 1024} kB" if q.exists()
             else "fehlt – --bauen"))
    return 0


# -------------------------------------------------------- Betriebsdateien
STARTEN = """#!/bin/sh
# Die Vorführinstanz starten. Zwei Dinge macht dieses Skript, und beide
# sind der Grund, warum es überhaupt eines gibt:
#
#   OFB_DEMO=1        sperrt im Programm alles, was Claude anruft, und
#                     `POST /api/beenden`. Siehe werkstatt/konfig.py.
#   -u ANTHROPIC_...  nimmt einen Schlüssel aus der Umgebung, falls in
#                     der Sitzung des Betreibers einer steht.
#
# OFB_DEMO_PASSWORT setzt das gemeinsame Passwort der Eingeladenen;
# gesetzt lassen, ungesetzt ist die Instanz offen.
#
# Gehört bleibt 127.0.0.1. Nach außen kommt die Instanz nur über den
# Reverse Proxy.
cd "$(dirname "$0")" || exit 1
exec env -u ANTHROPIC_API_KEY OFB_DEMO=1 \\
     python3 start.py --port {port} --kein-browser
"""

ZURUECK = """#!/bin/sh
# Den Anfangsstand zurückspielen. Stündlich aus cron oder aus einem
# systemd-Timer; der Server darf dabei weiterlaufen.
cd "$(dirname "$0")" || exit 1
exec python3 -m werkstatt.demoinstanz --zuruecksetzen --ziel .
"""

DIENST = """[Unit]
Description=OFB-Werkstatt, Vorführinstanz
After=network.target

[Service]
Type=simple
WorkingDirectory={ziel}
Environment=OFB_DEMO=1
# Passwort der Eingeladenen; Zeile aktivieren und Wert setzen:
# Environment=OFB_DEMO_PASSWORT=...
UnsetEnvironment=ANTHROPIC_API_KEY
ExecStart=/usr/bin/env python3 start.py --port {port} --kein-browser
Restart=on-failure

[Install]
WantedBy=default.target
"""

DOCKERFILE = """# Die Vorführinstanz im Container – gedacht für die Synology
# (Container Manager), wo das System-Python zu alt ist und Pillow/numpy
# mühsam wären. Das Verzeichnis wird eingehängt, nicht eingebacken:
# `zuruecksetzen` und ein neues `--bauen` wirken dann ohne neues Image.
FROM python:3.12-slim
# gedcom7 ist freiwillig, im Container aber mit dabei: Sonst sieht der
# Betrachter dort den zweiten Ausgang nicht, den die README nennt.
RUN pip install --no-cache-dir pillow numpy gedcom7
WORKDIR /app
ENV OFB_DEMO=1
EXPOSE {port}
CMD ["python3", "start.py", "--port", "{port}", "--kein-browser"]
"""

COMPOSE = """# docker compose up -d   (oder im Container-Manager als Projekt anlegen)
#
# `network_mode: host`, kein Port-Mapping: Die App bindet 127.0.0.1, und
# ein gemappter Port käme am Loopback *des Containers* nie an – die
# Verbindung würde still verweigert. Im Host-Netz ist ihr 127.0.0.1 der
# des Wirts, und genau dort holt der Reverse Proxy der Synology sie ab
# (Ziel 127.0.0.1:{port}). Nach außen offen ist damit nichts.
# Das Passwort vor dem Start eintragen.
services:
  ofb-demo:
    build:
      context: ..
      dockerfile: betrieb/Dockerfile
    container_name: ofb-demo
    volumes:
      - ..:/app
    network_mode: host
    environment:
      OFB_DEMO_PASSWORT: "HIER-PASSWORT-EINTRAGEN"
    restart: unless-stopped

  # Der stündliche Rücksetzer, im selben Verzeichnis. Kein Aufgabenplaner
  # im DSM nötig; wer den Takt ändern will, ändert die 3600.
  ofb-demo-reset:
    build:
      context: ..
      dockerfile: betrieb/Dockerfile
    container_name: ofb-demo-reset
    volumes:
      - ..:/app
    entrypoint: ["sh", "-c",
      "while true; do sleep 3600; python3 -m werkstatt.demoinstanz --zuruecksetzen --ziel /app; done"]
    restart: unless-stopped
"""

TIMER_DIENST = """[Unit]
Description=OFB-Werkstatt Vorführinstanz zurücksetzen

[Service]
Type=oneshot
WorkingDirectory={ziel}
ExecStart=/usr/bin/env python3 -m werkstatt.demoinstanz --zuruecksetzen --ziel .
"""

TIMER = """[Unit]
Description=OFB-Werkstatt Vorführinstanz stündlich zurücksetzen

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
"""

LIESMICH = """# Vorführinstanz

Gebaut von `python3 -m werkstatt.demoinstanz --bauen`. Nicht von Hand
pflegen – ein erneutes `--bauen --ersetzen` wirft alles hier weg und
stellt den Anfangsstand wieder her.

## Stand

Eingerichtet, Beispielbestand eingelesen, Ehen und Tote gelesen,
bestätigt und übergeben. Die Taufrunde ist gelesen und steht auf
`korrigieren` – dort landet der Besucher.

## Betrieb auf der Synology (der vorgesehene Weg)

Das ganze Verzeichnis aufs NAS kopieren, etwa:

    rsync -a {ziel}/ nas:/volume1/docker/ofb-werkstatt-demo/

Dann in `betrieb/compose.yaml` das Passwort eintragen und den Ordner
`betrieb/` im Container-Manager als Projekt anlegen – oder per SSH:

    cd /volume1/docker/ofb-werkstatt-demo/betrieb && docker compose up -d

Das startet zwei Container: die Werkstatt auf `127.0.0.1:{port}` des NAS
und den stündlichen Rücksetzer. Beide teilen sich dieses Verzeichnis;
ein neues `--bauen` samt `rsync` genügt zum Aktualisieren, das Image
bleibt.

Reverse Proxy im DSM (Systemsteuerung → Anmeldeportal → Erweitert):

    Quelle  HTTPS  ofb-werkstatt.bgg-home.de  443
    Ziel    HTTP   127.0.0.1                  {port}

Das Zugangskontrollprofil bleibt „Nicht konfiguriert" – es kann nur
IP-Filter, keine Passwörter. Die Anmeldung macht die Werkstatt selbst:
`OFB_DEMO_PASSWORT` in `compose.yaml` ist das gemeinsame Passwort der
Eingeladenen (Benutzername im Anmeldefenster ist egal). In den
erweiterten Einstellungen des Proxys den **Proxy-Timeout auf 300 s**
stellen: Übergeben und Ausgeben rechnen über den ganzen Bestand und
brauchen bei größeren Runden mehr als die üblichen 60 Sekunden.

## Betrieb ohne Container (Linux-Rechner)

    ./starten.sh          hört auf 127.0.0.1:{port}
    ./zuruecksetzen.sh    Anfangsstand zurück, Server darf laufen

Als Dienst, wenn systemd da ist:

    mkdir -p ~/.config/systemd/user
    cp betrieb/*.service betrieb/*.timer ~/.config/systemd/user/
    systemctl --user daemon-reload
    systemctl --user enable --now ofb-demo.service ofb-demo-reset.timer
    loginctl enable-linger $USER      # damit es ohne Anmeldung läuft

Sonst per cron:

    0 * * * * {ziel}/zuruecksetzen.sh >/dev/null 2>&1

Das Passwort kommt aus `OFB_DEMO_PASSWORT` (in `starten.sh` bzw. der
systemd-Unit setzen); ungesetzt ist die Instanz offen.

## Was gesperrt ist

`OFB_DEMO=1` sperrt im Programm, nicht bloß in der Umgebung:

- alles, was Claude anruft – Lesen, Nachlesen, Gespräch, Anmelden
- `POST /api/beenden`
- Endpunkte, die einen Dateipfad vom Besucher entgegennehmen:
  `quelle`, `entpacken`, `einrichten`

Offen bleibt die Arbeit, die vorgeführt werden soll: Korrigieren,
Aktkarte, Dubletten, Perioden, Übergeben, Ausgeben. Alles davon fasst
nur die Datenbank an, und die wird stündlich zurückgesetzt.
"""


def _betriebsdateien(ziel, port):
    (ziel / "starten.sh").write_text(STARTEN.format(port=port),
                                     encoding="utf-8")
    (ziel / "zuruecksetzen.sh").write_text(ZURUECK, encoding="utf-8")
    (ziel / "starten.sh").chmod(0o755)
    (ziel / "zuruecksetzen.sh").chmod(0o755)
    b = ziel / "betrieb"
    b.mkdir(exist_ok=True)
    (b / "ofb-demo.service").write_text(
        DIENST.format(ziel=ziel, port=port), encoding="utf-8")
    (b / "ofb-demo-reset.service").write_text(
        TIMER_DIENST.format(ziel=ziel), encoding="utf-8")
    (b / "ofb-demo-reset.timer").write_text(TIMER, encoding="utf-8")
    (b / "Dockerfile").write_text(DOCKERFILE.format(port=port),
                                  encoding="utf-8")
    (b / "compose.yaml").write_text(COMPOSE.format(port=port),
                                    encoding="utf-8")
    (ziel / "LIESMICH-vorfuehrinstanz.md").write_text(
        LIESMICH.format(port=port, ziel=ziel), encoding="utf-8")
    print("Betriebsdateien: starten.sh, zuruecksetzen.sh, betrieb/ "
          "(Dockerfile, compose.yaml, systemd), LIESMICH-vorfuehrinstanz.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bauen", action="store_true")
    ap.add_argument("--zuruecksetzen", action="store_true")
    ap.add_argument("--zeigen", action="store_true")
    ap.add_argument("--ziel", type=Path, default=ZIEL)
    ap.add_argument("--port", type=int, default=PORT,
                    help=f"Port der fertigen Instanz (Vorgabe {PORT})")
    ap.add_argument("--ersetzen", action="store_true",
                    help="ein vorhandenes Zielverzeichnis wegwerfen")
    a = ap.parse_args()
    ziel = a.ziel.expanduser().resolve()
    if a.bauen:
        raise SystemExit(bauen(ziel, a.port, a.ersetzen))
    if a.zuruecksetzen:
        raise SystemExit(zuruecksetzen(ziel))
    if a.zeigen:
        raise SystemExit(zeigen(ziel))
    ap.print_help()


if __name__ == "__main__":
    main()
