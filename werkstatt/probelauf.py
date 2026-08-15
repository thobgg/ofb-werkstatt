#!/usr/bin/env python3
"""Die Demo so durchspielen, wie ein Fremder sie bekommt.

    python3 -m werkstatt.probelauf

**Wozu.** Auf dem Rechner des Autors funktioniert die Demo aus den
falschen Gruenden. `testdaten.py` hat zwei Zweige: liegt das Nachbar-
projekt daneben, liest es dessen Datenbank; fehlt es, greift die
mitgelieferte `daten/pilot.json`. Hier lief immer der erste Zweig. Der
zweite, den jeder Klon nimmt, war nie gelaufen. Genauso mit numpy:
installiert ist installiert, auch wenn es nirgends deklariert steht.

Dieses Skript baut deshalb einen Klon aus dem, was `git ls-files`
ausliefert, in ein Wegwerfverzeichnis, startet ihn dort als eigenen
Prozess und fahrt den ganzen Durchlauf ueber die Web-Schnittstelle:
einrichten, alle drei Register lesen, bestaetigen, uebergeben, ausgeben.
Am Ende steht eine Tabelle mit Zahlen, die sich mit der README
vergleichen laesst - und der Hinweis, wenn eine davon abweicht.

Gepruefte Fremdpakete werden **nicht** nachinstalliert: Das Skript nimmt
das Python, mit dem es aufgerufen wurde. Wer wissen will, ob ein nacktes
System reicht, ruft es aus einer frischen venv auf.
"""
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import konfig

# Was die README behauptet. Weicht der Lauf ab, wird es gemeldet -
# entweder stimmt die Zahl nicht mehr, oder es ist etwas kaputt.
ERWARTET = dict(eintraege=81, gruen=10, ohne_bild=0, tote_zeiger=0,
                leerlauf=True)


def _frei():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _klon(ziel):
    """Nur was im Git liegt - also genau das, was ein Klon bekommt."""
    dateien = subprocess.run(
        ["git", "ls-files", "-z"], cwd=konfig.WURZEL,
        capture_output=True, text=True, check=True).stdout.split("\0")
    n = 0
    for f in dateien:
        if not f:
            continue
        q = konfig.WURZEL / f
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


def _warte(port, sekunden=30):
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


def _tote_zeiger(datei):
    import re
    t = Path(datei).read_text(encoding="utf-8")
    da = set(re.findall(r"^0 @([A-Za-z0-9_]+)@", t, re.M))
    tot = 0
    for zeile in t.split("\n"):
        m = re.match(r"^\d+ (?:@[^@]+@ )?\w+ (@[A-Za-z0-9_]+@)\s*$", zeile)
        if m and m.group(1).strip("@") not in da:
            tot += 1
    return tot


def lauf(behalten=False):
    ordner = Path(tempfile.mkdtemp(prefix="ofb-probelauf-"))
    port = _frei()
    server = None
    try:
        n = _klon(ordner)
        print(f"Klon: {n} Dateien in {ordner}")
        server = subprocess.Popen(
            [sys.executable, "start.py", "--port", str(port), "--kein-browser"],
            cwd=ordner, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True)
        if not _warte(port):
            aus = ""
            if server.poll() is not None:
                aus = server.communicate()[0]
            raise SystemExit(f"Der Klon startet nicht.\n{aus}")
        m = Maske(port)
        print(f"laeuft auf 127.0.0.1:{port}\n")

        a = m("/api/einrichten", dict(
            gemeinde="Haberschlacht", ort="Haberschlacht",
            religion="evangelisch", bestand=True,
            register=[dict(art=x, ordner=f"demo/bilder/{x}")
                      for x in ("taufe", "ehe", "tod")]))
        if not a.get("ok"):
            raise SystemExit(f"Einrichten schlug fehl: {a}")

        gruen = gelb = rot = eintraege = ohne_bild = 0
        for art in ("taufe", "ehe", "tod"):
            r = m("/api/runde/plane",
                  dict(register=art, seiten=5, quelle="testdaten"))
            rid = r.get("runde")
            if not rid:
                print(f"  {art:6} keine Runde: {r.get('fehler', r)}")
                continue
            m("/api/einlesen", dict(runde=rid))
            f = {}
            for _ in range(180):
                time.sleep(2)
                f = m(f"/api/fortschritt?runde={rid}")
                if f.get("stand") == "fertig":
                    break
            liste = m(f"/api/eintraege?runde={rid}")
            liste = liste if isinstance(liste, list) else liste.get("eintraege", [])
            zaehler = {"gruen": 0, "gelb": 0, "rot": 0}
            for ein in liste:
                for x in ein.get("felder", []):
                    if x.get("ampel") in zaehler:
                        zaehler[x["ampel"]] += 1
                if not ein.get("ausschnitt") and not ein.get("streifen"):
                    ohne_bild += 1
                werte = {x["name"]: {"wert": x.get("wert") or ""}
                         for x in ein.get("felder", [])
                         if (x.get("wert") or "").strip()}
                m("/api/speichern", dict(id=ein["id"], felder=werte,
                                         bestaetigt=True))
            gruen += zaehler["gruen"]
            gelb += zaehler["gelb"]
            rot += zaehler["rot"]
            eintraege += len(liste)
            z = m("/api/runde/uebergib", dict(runde=rid)).get("zahlen", {})
            print(f"  {art:6} {f.get('seiten_fertig')}/{f.get('seiten_gesamt')} "
                  f"Seiten  {len(liste):3} Eintraege   "
                  f"gruen {zaehler['gruen']:3} gelb {zaehler['gelb']:3} "
                  f"rot {zaehler['rot']:3}   -> {z.get('personen_neu', 0)} Personen, "
                  f"{z.get('familien_gefunden', 0)} Familien gefunden")

        vor = m("/api/ausgabe")
        aus = m("/api/ausgabe", {})
        ged = ordner / aus.get("datei", "")
        tot = _tote_zeiger(ged) if ged.is_file() else -1

        gemessen = dict(eintraege=eintraege, gruen=gruen, ohne_bild=ohne_bild,
                        tote_zeiger=tot, leerlauf=bool(vor.get("leerlauf")))
        print(f"\n{eintraege} Eintraege - gruen {gruen}, gelb {gelb}, rot {rot}")
        print(f"Leerlauf: {vor.get('leerlauf_text')}")
        print(f"Ausgabe : {aus.get('bytes')} Byte, "
              f"{aus.get('zahlen', {}).get('neu_personen')} neue Personen, "
              f"{aus.get('zahlen', {}).get('neu_familien')} neue Familien, "
              f"{tot} tote Zeiger")

        abweichung = {k: (v, gemessen[k]) for k, v in ERWARTET.items()
                      if gemessen[k] != v}
        if abweichung:
            print("\nAbweichung von der README:")
            for k, (soll, ist) in abweichung.items():
                print(f"  {k}: erwartet {soll}, gemessen {ist}")
            return 1
        print("\nAlles wie in der README beschrieben.")
        return 0
    finally:
        if server and server.poll() is None:
            server.terminate()
            try:
                server.wait(10)
            except subprocess.TimeoutExpired:
                server.kill()
        if behalten:
            print(f"\nKlon bleibt stehen: {ordner}")
        else:
            shutil.rmtree(ordner, ignore_errors=True)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--behalten", action="store_true",
                    help="das Wegwerfverzeichnis stehen lassen")
    a = ap.parse_args()
    raise SystemExit(lauf(a.behalten))


if __name__ == "__main__":
    main()
