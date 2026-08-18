#!/usr/bin/env python3
"""Der Wirt: alle Instanzen als Prozesse in einem Container.

Der Monolith gehört auf die Prozess-Ebene, nicht in die Daten: Statt je
Parochie ein Container läuft EIN Container (oder ein Rechner), darin je
Instanz ein Werkstatt-Prozess auf ihrem Port - gestartet, überwacht und
gestoppt vom Portal. Die Ordner-Architektur bleibt: jede Parochie ihre
eigene Datenbank, ihr eigenes Verzeichnis, ihre eigene Kontenliste.

Damit entfällt das `docker compose up` je Parochie. Was je neuem OFB
bleibt, ist der Klick im Portal und die eine Zeile im Reverse Proxy.

Abgestürzte Instanzen werden neu gestartet (mit Abstand, kein
Schnellfeuer); bewusst gestoppte bleiben gestoppt. Jede Instanz
schreibt ihr Log nach `<instanz>/wirt.log`.
"""
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from . import instanz

# name -> dict(prozess, port, seit, gewollt). `gewollt=False` heißt: der
# Betreiber hat gestoppt, die Überwachung lässt die Instanz in Ruhe.
PROZESSE = {}
_SCHLOSS = threading.Lock()
NEUSTART_ABSTAND = 10        # Sekunden zwischen Absturz und Neustart


def _umgebung():
    import os
    u = dict(os.environ)
    u.pop("OFB_PORTAL_PASSWORT", None)   # geht die Instanz nichts an
    u.pop("OFB_DEMO", None)
    return u


def _port(pfad):
    f = Path(pfad) / "betrieb" / "port"
    try:
        return int(f.read_text().strip())
    except (OSError, ValueError):
        return None


def _belegt(port):
    import socket
    s = socket.socket()
    s.settimeout(0.5)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def laeuft(pfad):
    """Antwortet die Instanz - egal ob eigener Prozess oder externer
    Container? Der Portal-Anzeige ist das gleich; dem Stopp-Knopf nicht."""
    e = PROZESSE.get(Path(pfad).name)
    if e and e["prozess"].poll() is None:
        return True
    port = _port(pfad)
    return bool(port and _belegt(port))


def starte(pfad):
    """Eine Instanz starten. Rückgabe: Port, oder None mit Grund im Log."""
    pfad = Path(pfad)
    name = pfad.name
    port = _port(pfad)
    if not port or not (pfad / "start.py").is_file():
        return None
    with _SCHLOSS:
        e = PROZESSE.get(name)
        if e and e["prozess"].poll() is None:
            return e["port"]                     # läuft schon
        if _belegt(port):
            # Da antwortet schon jemand - etwa ein eigener Container aus
            # dem alten Betriebsmodell. Nicht dagegen anstarten.
            return port
        log = (pfad / "wirt.log").open("a")
        zeit = datetime.now(timezone.utc).isoformat(timespec="seconds")
        log.write(f"\n--- Start {zeit} auf Port {port}\n")
        log.flush()
        p = subprocess.Popen(
            [sys.executable, "start.py", "--port", str(port),
             "--kein-browser"],
            cwd=pfad, stdout=log, stderr=subprocess.STDOUT,
            env=_umgebung())
        PROZESSE[name] = dict(prozess=p, port=port, gewollt=True,
                              seit=time.time())
    return port


def stoppe(name):
    with _SCHLOSS:
        e = PROZESSE.get(name)
        if not e:
            return False
        e["gewollt"] = False
        p = e["prozess"]
    if p.poll() is None:
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            p.kill()
    return True


def status(name):
    """laeuft | gestoppt | None (nie gestartet)."""
    e = PROZESSE.get(name)
    if not e:
        return None
    return "laeuft" if e["prozess"].poll() is None else "gestoppt"


def alle_starten(wurzel):
    """Alle Instanzen unter der Wurzel hochfahren. Rückgabe: Anzahl."""
    n = 0
    for i in instanz.liste(wurzel):
        if starte(Path(i["verzeichnis"])):
            n += 1
    return n


def alle_stoppen():
    for name in list(PROZESSE):
        stoppe(name)


def ueberwachung(wurzel):
    """Abgestürzte Instanzen neu starten - als Daemon-Thread."""
    def lauf():
        while True:
            time.sleep(NEUSTART_ABSTAND)
            with _SCHLOSS:
                tote = [n for n, e in PROZESSE.items()
                        if e["gewollt"] and e["prozess"].poll() is not None]
            for name in tote:
                starte(Path(wurzel) / name)
    t = threading.Thread(target=lauf, daemon=True, name="wirt-ueberwachung")
    t.start()
    return t
