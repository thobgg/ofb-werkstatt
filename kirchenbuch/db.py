#!/usr/bin/env python3
"""Erfassungsschema für Kirchenbucheinträge ab 1808.

Registernah, nicht GEDCOM-nah: eine Zeile je Registereintrag, so wie es
dasteht. Die GEDCOM-Erzeugung ist eine spaetere Ableitung. Dadurch laesst
sich die Zuordnung korrigieren, ohne die Lesung anzufassen — und umgekehrt.

  eintrag  ein Registereintrag (Taufe, Ehe, Begraebnis)
  feld     ein Datenfeld darin, mit gelesenem und korrigiertem Wert

Der Status eines Feldes:
  gelesen      von mir transkribiert, unbestaetigt
  bestaetigt   vom Benutzer geprueft  -> gilt als fix
  strittig     Konflikt, braucht Klaerung

Nur 'bestaetigt' zaehlt als gesichert. Das ersetzt das Stufensystem:
statt eines Urteilsbuchstabens steht in 'beleg', WORAN die Aussage haengt.

Aufruf:
  python3 skripte/erfassung.py --init
  python3 skripte/erfassung.py --stand
"""
import argparse
import sqlite3
from pathlib import Path

from . import konfig as _k

ROOT = _k.WURZEL
DB = ROOT / "daten" / "erfassung.sqlite"


def FELDER(art=None):
    """Feldreihenfolge je Registerart — kommt aus konfig.toml."""
    from . import konfig as k
    if art:
        return k.felder(art)
    return {a: k.felder(a) for a in k.register()}

SCHEMA = """
CREATE TABLE IF NOT EXISTS eintrag (
  id        INTEGER PRIMARY KEY,
  register  TEXT NOT NULL,          -- taufe | ehe | begraebnis
  band      TEXT,
  bild      TEXT,                   -- z.B. '1184798-00361'
  nr        TEXT,                   -- laufende Nummer im Register
  jahr      INTEGER,
  ausschnitt TEXT,                  -- Pfad zum Bildstreifen, relativ zur Wurzel
  status    TEXT NOT NULL DEFAULT 'gelesen',
  bemerkung TEXT,
  UNIQUE(register, bild, nr)
);
CREATE TABLE IF NOT EXISTS feld (
  id         INTEGER PRIMARY KEY,
  eintrag_id INTEGER NOT NULL REFERENCES eintrag(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,         -- kind_vorname, vater_name, tauf_datum, ...
  gelesen    TEXT,                  -- meine Transkription
  korrigiert TEXT,                  -- vom Benutzer geaendert; NULL = uebernommen
  kb_form    TEXT,                  -- Kirchenbuchform, falls abweichend
  beleg      TEXT,                  -- woran die Aussage haengt
  ofb_id     TEXT,                  -- zugeordneter OFB-Record
  status     TEXT NOT NULL DEFAULT 'gelesen',
  reihe      INTEGER NOT NULL DEFAULT 0,
  UNIQUE(eintrag_id, name)
);
CREATE INDEX IF NOT EXISTS ix_feld_eintrag ON feld(eintrag_id);
CREATE VIEW IF NOT EXISTS wert AS
  SELECT e.register, e.bild, e.nr, e.jahr, f.name,
         COALESCE(f.korrigiert, f.gelesen) AS wert,
         f.kb_form, f.beleg, f.ofb_id, f.status
  FROM feld f JOIN eintrag e ON e.id = f.eintrag_id;
"""



def verbinde():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    return con


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--stand", action="store_true")
    a = ap.parse_args()
    con = verbinde()
    if a.stand:
        for r in con.execute(
                "SELECT register, count(*) n, "
                "sum(status='bestaetigt') fix FROM eintrag GROUP BY register"):
            print(f"  {r['register']:12} {r['n']:4} Einträge, {r['fix'] or 0} bestätigt")
        f = con.execute(
            "SELECT count(*) n, sum(status='bestaetigt') fix FROM feld").fetchone()
        print(f"  Felder gesamt: {f['n'] or 0}, davon bestätigt: {f['fix'] or 0}")
        return
    n = con.execute("SELECT count(*) FROM eintrag").fetchone()[0]
    print(f"Erfassung bereit: {DB.relative_to(ROOT)} ({n} Einträge)")


if __name__ == "__main__":
    main()
