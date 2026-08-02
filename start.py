#!/usr/bin/env python3
"""Startet parish-scribe: Datenbank anlegen, falls noetig, dann die Maske.

    python3 start.py            Maske auf http://127.0.0.1:8765
    python3 start.py --port 9000
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kirchenbuch import db, konfig            # noqa: E402
from kirchenbuch.web import app as webapp     # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()

    k = konfig.konfig()
    print(f"Gemeinde : {k.get('gemeinde', {}).get('name', '—')}")
    print(f"Register : {', '.join(konfig.register())}")
    bestand = konfig.bestand()
    print(f"Bestand  : {bestand if bestand else 'keiner — beginnt bei Null'}")

    con = db.verbinde()
    n = con.execute("SELECT count(*) FROM eintrag").fetchone()[0]
    print(f"Erfasst  : {n} Einträge\n")

    sys.argv = [sys.argv[0], "--port", str(a.port)]
    webapp.main()


if __name__ == "__main__":
    main()
