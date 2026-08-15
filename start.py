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

# Fehlt eine Voraussetzung, kommt sonst ein Traceback aus der Tiefe der
# Importkette – nicht falsch, aber niemand liest daraus ab, was zu tun ist.
BRAUCHT = [("PIL", "Pillow", "Bilder öffnen und zuschneiden"),
           ("numpy", "numpy", "Zeilen im Seitenbild finden")]


def voraussetzungen():
    """Python-Version und Fremdpakete prüfen, bevor irgendetwas importiert wird."""
    from importlib.util import find_spec
    if sys.version_info < (3, 11):
        v = ".".join(str(x) for x in sys.version_info[:3])
        sys.exit(f"OFB-Werkstatt braucht Python 3.11 oder neuer, hier läuft "
                 f"{v}.\nDie Konfiguration wird mit tomllib gelesen, und das "
                 f"gibt es erst ab 3.11.")
    fehlt = [(paket, wofuer) for modul, paket, wofuer in BRAUCHT
             if find_spec(modul) is None]
    if fehlt:
        z = "\n".join(f"  {p:8} {w}" for p, w in fehlt)
        sys.exit(f"Es fehlen Pakete:\n{z}\n\nHolen mit:\n  "
                 f"{Path(sys.executable).name} -m pip install "
                 f"{' '.join(p for p, _ in fehlt)}")


voraussetzungen()

from werkstatt import db, einstellungen, konfig   # noqa: E402
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
        print(f"Die Werkstatt läuft schon unter {url}")
        if a.browser:
            webbrowser.open(url)
        return

    k = konfig.konfig()
    con = db.verbinde()
    db.kontext_anwenden(con)

    # Der Stand kommt aus der Datenbank, nicht aus konfig.toml. Die alte
    # Fassung meldete "Bestand: keiner", während 4.111 Personen darin lagen –
    # sie las den leeren gedcom-Eintrag der Konfiguration.
    z = db.stand(con)
    beleg = list(con.execute(
        "SELECT COALESCE(name, datei) t, "
        "(SELECT count(*) FROM person p WHERE p.herkunft=herkunft.id) n "
        "FROM herkunft WHERE gilt='beleg' ORDER BY n DESC"))
    print(f"Gemeinde : {k.get('gemeinde', {}).get('name', '–')}")
    print(f"Register : {', '.join(konfig.register())}")
    if beleg:
        for b in beleg:
            print(f"Beleg    : {b['t']}  ({b['n']} Personen)")
    else:
        print("Beleg    : keine Quelle darf bestätigen – Nullstart, "
              "alles wird vorgelegt")
    print(f"Bestand  : {z['person']} Personen, {z['familie']} Familien, "
          f"{z['ereignis']} Ereignisse")
    print(f"Erfasst  : {z['eintrag']} Einträge, {z['feld']} Felder")
    r = con.execute("SELECT nr, register, stand FROM runde "
                    "WHERE stand<>'fertig' ORDER BY id DESC LIMIT 1").fetchone()
    if r:
        print(f"Runde    : {r['nr']} ({r['register']}), Stand {r['stand']}")
    print()

    # Ein zweiter Tab beim Start kommt fast immer daher, dass der Browser
    # die letzte Sitzung wiederherstellt – die Werkstatt war beim
    # Schliessen ja offen – und unseren Aufruf zusaetzlich bekommt. Wer das
    # nicht mag, schaltet das Oeffnen ab: dauerhaft hier, einmalig mit
    # --kein-browser.
    if a.browser and einstellungen.wert(con, "browser.oeffnen", "1") == "1":
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

    Ein festes `sleep` waere geraten – auf einem langsamen Rechner zu kurz,
    sonst zu lang. Also nachfragen, bis es klappt.
    """
    import time
    for _ in range(100):                     # bis zu zehn Sekunden
        if belegt(port):
            return webbrowser.open(url)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
