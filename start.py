#!/usr/bin/env python3
"""Startet OFB-Werkstatt: Datenbank anlegen, falls noetig, dann die Maske.

    python3 start.py            Maske auf http://127.0.0.1:8765, oeffnet
                                den Browser von selbst
    python3 start.py --port 9000
    python3 start.py --kein-browser
"""
import argparse
import socket
import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from werkstatt import db, konfig            # noqa: E402
from werkstatt.web import app as webapp     # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--kein-browser", dest="browser", action="store_false",
                    help="nur den Server starten, kein Fenster oeffnen")
    a = ap.parse_args()
    url = f"http://127.0.0.1:{a.port}"

    # Laeuft schon eine Werkstatt, waere der Port belegt und der Start
    # bliebe mit einer Fehlermeldung stehen. Dann nur das Fenster oeffnen.
    if belegt(a.port):
        print(f"Die Werkstatt läuft schon — öffne {url}")
        webbrowser.open(url)
        return

    k = konfig.konfig()
    con = db.verbinde()
    db.kontext_anwenden(con)

    # Der Stand kommt aus der Datenbank, nicht aus konfig.toml. Die alte
    # Fassung meldete "Bestand: keiner", während 4.111 Personen darin lagen —
    # sie las den leeren gedcom-Eintrag der Konfiguration.
    z = db.stand(con)
    beleg = list(con.execute(
        "SELECT COALESCE(name, datei) t, "
        "(SELECT count(*) FROM person p WHERE p.herkunft=herkunft.id) n "
        "FROM herkunft WHERE gilt='beleg' ORDER BY n DESC"))
    print(f"Gemeinde : {k.get('gemeinde', {}).get('name', '—')}")
    print(f"Register : {', '.join(konfig.register())}")
    if beleg:
        for b in beleg:
            print(f"Beleg    : {b['t']}  ({b['n']} Personen)")
    else:
        print("Beleg    : keine Quelle darf bestätigen — Nullstart, "
              "alles wird vorgelegt")
    print(f"Bestand  : {z['person']} Personen, {z['familie']} Familien, "
          f"{z['ereignis']} Ereignisse")
    print(f"Erfasst  : {z['eintrag']} Einträge, {z['feld']} Felder")
    r = con.execute("SELECT nr, register, stand FROM runde "
                    "WHERE stand<>'fertig' ORDER BY id DESC LIMIT 1").fetchone()
    if r:
        print(f"Runde    : {r['nr']} ({r['register']}), Stand {r['stand']}")
    print()

    if a.browser:
        threading.Thread(target=warte_dann_oeffne, args=(a.port, url),
                         daemon=True).start()

    sys.argv = [sys.argv[0], "--port", str(a.port)]
    webapp.main()


def belegt(port):
    """Antwortet auf diesem Port schon jemand?"""
    s = socket.socket()
    s.settimeout(1)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def warte_dann_oeffne(port, url):
    """Erst oeffnen, wenn der Server auch antwortet.

    Ein festes `sleep` waere geraten — auf einem langsamen Rechner zu kurz,
    sonst zu lang. Also nachfragen, bis es klappt.
    """
    import time
    for _ in range(100):                     # bis zu zehn Sekunden
        if belegt(port):
            return webbrowser.open(url)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
