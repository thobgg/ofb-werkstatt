#!/usr/bin/env python3
"""Datenbasis: eine Struktur, viele Eingangstüren.

GEDCOM, Tabellen und die eigene Erfassung schreiben in dieselben Tabellen.
Die Suche kennt keine Herkunft, nur den Inhalt.

    python3 -m werkstatt.db --init
    python3 -m werkstatt.db --stand
"""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import konfig as _k

ROOT = _k.WURZEL
DB = ROOT / "daten" / "erfassung.sqlite"
SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def verbinde():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    return con


def felder(art=None):
    """Feldreihenfolge je Registerart — kommt aus konfig.toml."""
    if art:
        return _k.felder(art)
    return {a: _k.felder(a) for a in _k.register()}


def herkunft_id(con, art, datei, notiz=None):
    """Herkunftseintrag anlegen oder finden."""
    jetzt = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con.execute(
        "INSERT OR IGNORE INTO herkunft (art, datei, angelegt, notiz) "
        "VALUES (?,?,?,?)", (art, datei, jetzt, notiz))
    return con.execute(
        "SELECT id FROM herkunft WHERE art=? AND datei IS ?",
        (art, datei)).fetchone()["id"]


def stand(con):
    z = {}
    for t in ("herkunft", "person", "namensform", "familie", "kind",
              "ereignis", "eintrag", "feld"):
        z[t] = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--stand", action="store_true")
    a = ap.parse_args()
    con = verbinde()
    if a.stand:
        for t, n in stand(con).items():
            print(f"  {t:12} {n:7}")
        print()
        for r in con.execute(
                "SELECT h.art, h.datei, count(p.id) n FROM herkunft h "
                "LEFT JOIN person p ON p.herkunft=h.id GROUP BY h.id"):
            print(f"  {r['art']:10} {(r['datei'] or ''):44} {r['n']:6} Personen")
        return
    print(f"Datenbank bereit: {DB.relative_to(ROOT)}")
    for t, n in stand(con).items():
        print(f"  {t:12} {n:7}")


if __name__ == "__main__":
    main()
