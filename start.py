#!/usr/bin/env python3
"""Startet OFB-Werkstatt: Datenbank anlegen, falls noetig, dann die Maske.

    python3 start.py            Maske auf http://127.0.0.1:8765
    python3 start.py --port 9000
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from werkstatt import db, konfig            # noqa: E402
from werkstatt.web import app as webapp     # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()

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

    sys.argv = [sys.argv[0], "--port", str(a.port)]
    webapp.main()


if __name__ == "__main__":
    main()
