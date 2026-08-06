#!/usr/bin/env python3
"""Änderungsjournal: was die Werkstatt am Bestand tut, als Vorgangsliste.

    python3 -m werkstatt.journal --liste
    python3 -m werkstatt.journal --zurueck 17     Vorgang deaktivieren

Die Vorlage in `quellen/` bleibt unangetastet. Jede Ergänzung und jede
Korrektur wird hier festgehalten; `werkstatt.ausgabe --fort` wendet die
Vorgänge auf die unveränderten Records an und erzeugt daraus die Ausgabe.

Damit gilt:
  - der Ausgangszustand ist jederzeit rekonstruierbar
  - jeder Vorgang trägt seinen Beleg, nicht bloß ein Urteil
  - Rücknahme = `aktiv=0`, kein Datenverlust

Die Tabelle liegt in **derselben** Datei wie alles andere. Vorher stand sie
in `daten/aenderung.sqlite`; über zwei Dateien hinweg lässt sich ein
Bestätigen nicht in einer Transaktion schreiben — bricht es dazwischen ab,
stimmen Feld und Vorgang nicht mehr überein.
"""
import argparse
import json
from datetime import datetime, timezone

from . import db


def notiere(con, art, ziel=None, ziel2=None, daten=None, quelle=None,
            beleg=None, bemerkung=None):
    """Einen Vorgang festhalten. Gibt seine Nummer zurück."""
    cur = con.execute(
        "INSERT INTO vorgang (art, ziel, ziel2, daten, quelle, beleg, "
        "bemerkung, angelegt) VALUES (?,?,?,?,?,?,?,?)",
        (art, ziel, ziel2,
         json.dumps(daten, ensure_ascii=False) if daten is not None else None,
         quelle, beleg, bemerkung,
         datetime.now(timezone.utc).isoformat(timespec="seconds")))
    return cur.lastrowid


def vorgaenge(con, nur_aktive=True):
    q = "SELECT * FROM vorgang" + (" WHERE aktiv=1" if nur_aktive else "")
    return [dict(r) for r in con.execute(q + " ORDER BY id")]


def zuruecknehmen(con, nummer):
    con.execute("UPDATE vorgang SET aktiv=0 WHERE id=?", (nummer,))
    con.commit()
    return con.execute("SELECT changes()").fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--liste", action="store_true")
    ap.add_argument("--alle", action="store_true", help="auch zurückgenommene")
    ap.add_argument("--zurueck", type=int, metavar="NR")
    a = ap.parse_args()
    con = db.verbinde()

    if a.zurueck:
        zuruecknehmen(con, a.zurueck)
        print(f"Vorgang {a.zurueck} zurückgenommen")
        return

    rows = vorgaenge(con, nur_aktive=not a.alle)
    if not rows:
        print("Journal ist leer.")
        return
    for r in rows:
        marke = "" if r["aktiv"] else "  (zurückgenommen)"
        print(f"[{r['id']:4}] {r['art']:12} {r['ziel'] or '':8} "
              f"{(r['quelle'] or ''):38} {r['beleg'] or ''}{marke}")
    print(f"\n{len(rows)} Vorgänge")


if __name__ == "__main__":
    main()
