#!/usr/bin/env python3
"""Einen Klon bauen, starten und über die Web-Schnittstelle bedienen.

Zwei Aufgaben brauchen genau dasselbe: `probelauf.py` prüft, ob ein
frisch ausgepacktes Projekt durchläuft, und `demoinstanz.py` baut das
Schaustück fürs Netz. Beide fangen mit einem Klon aus `git ls-files` an,
starten ihn als eigenen Prozess und reden danach nur noch über HTTP mit
ihm – nie über Python-Aufrufe ins laufende Projekt hinein.

Dass es HTTP ist, ist der Punkt. Ein Aufruf von `runde.lauf()` aus dem
Prüfskript heraus liefe im Prozess des Prüfskripts, mit dessen Umgebung
und dessen Importen. Gemessen werden soll aber der Weg, den der Browser
nimmt.
"""
import json
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request

from . import konfig


def frei():
    """Ein Port, auf dem gerade niemand hört."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def baue(ziel, wurzel=None):
    """Nur was im Git liegt - also genau das, was ein Klon bekommt."""
    wurzel = wurzel or konfig.WURZEL
    dateien = subprocess.run(
        ["git", "ls-files", "-z"], cwd=wurzel,
        capture_output=True, text=True, check=True).stdout.split("\0")
    n = 0
    for f in dateien:
        if not f:
            continue
        q = wurzel / f
        if not q.is_file():
            continue
        z = ziel / f
        z.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(q, z)
        n += 1
    return n


class Maske:
    """Die Web-Schnittstelle, wie der Browser sie benutzt."""

    def __init__(self, port):
        self.b = f"http://127.0.0.1:{port}"

    def __call__(self, pfad, daten=None):
        r = urllib.request.Request(
            self.b + pfad, method="POST" if daten is not None else "GET")
        if daten is not None:
            r.add_header("Content-Type", "application/json")
        rumpf = json.dumps(daten).encode() if daten is not None else None
        try:
            with urllib.request.urlopen(r, rumpf, timeout=900) as f:
                return json.loads(f.read())
        except urllib.error.HTTPError as e:
            return {"HTTP": e.code, **json.loads(e.read() or b"{}")}


def warte(port, sekunden=30):
    for _ in range(sekunden * 5):
        s = socket.socket()
        s.settimeout(1)
        try:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        finally:
            s.close()
        time.sleep(0.2)
    return False


def ausnahmen(log):
    """Was der Server nach draußen gemeldet hat.

    Ein Lauf, der Zahlen liefert und dabei Ausnahmen wirft, ist nicht grün.
    """
    if not log.exists():
        return []
    return [z for z in log.read_text(encoding="utf-8").split("\n")
            if "Traceback" in z or "Error" in z or "Exception" in z]
