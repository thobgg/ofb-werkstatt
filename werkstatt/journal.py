#!/usr/bin/env python3
"""Änderungsjournal für den OFB.

Der OFB in quellen/ bleibt unangetastet. Jede Ergänzung und jede Korrektur
wird hier als Vorgang festgehalten; sqlite2ged.py wendet das Journal auf die
verlustfreien raw-Records an und erzeugt daraus die Ausgabedatei.

Damit gilt:
  - der Ausgangszustand ist jederzeit rekonstruierbar
  - jeder Vorgang traegt seinen Beleg, nicht bloss ein Urteil
  - Ruecknahme = Vorgang deaktivieren, kein Datenverlust

Aufruf:
  python3 skripte/journal.py --init          Journal anlegen
  python3 skripte/journal.py --liste         Vorgaenge zeigen
"""
import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOURNAL = ROOT / "daten" / "aenderung.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS vorgang (
  id        INTEGER PRIMARY KEY,
  art       TEXT NOT NULL,      -- neu_person | neu_familie | merge | feld | kind
  ziel      TEXT,               -- betroffene Record-ID (bei neu_*: die vergebene)
  ziel2     TEXT,               -- zweite ID (merge: der aufgehende Record)
  daten     TEXT,               -- JSON: Feldwerte bzw. Parameter
  quelle    TEXT,               -- z.B. 'Taufreg. Bd. 4 Bild 00361 Nr. 11'
  beleg     TEXT,               -- woran es haengt, im Klartext
  bemerkung TEXT,
  aktiv     INTEGER NOT NULL DEFAULT 1,
  angelegt  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_vorgang_ziel ON vorgang(ziel);
CREATE INDEX IF NOT EXISTS ix_vorgang_art  ON vorgang(art);
"""


def verbinde():
    con = sqlite3.connect(JOURNAL)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--liste", action="store_true")
    a = ap.parse_args()

    con = verbinde()
    if a.init:
        n = con.execute("SELECT count(*) FROM vorgang").fetchone()[0]
        print(f"Journal bereit: {JOURNAL.relative_to(ROOT)} ({n} Vorgänge)")
        return
    if a.liste:
        rows = list(con.execute(
            "SELECT * FROM vorgang WHERE aktiv=1 ORDER BY id"))
        if not rows:
            print("Journal ist leer.")
            return
        for r in rows:
            print(f"[{r['id']:4}] {r['art']:12} {r['ziel'] or '':8} "
                  f"{(r['quelle'] or ''):38} {r['beleg'] or ''}")
        print(f"\n{len(rows)} aktive Vorgänge")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
