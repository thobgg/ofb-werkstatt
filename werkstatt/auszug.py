#!/usr/bin/env python3
"""Einen kleinen Bestandsauszug schneiden — nur was zu bestimmten Seiten gehört.

    python3 -m werkstatt.auszug --runde 1 -o demo/bestand.ged

Ein Ortsfamilienbuch hat Tausende Personen; für eine Veranschaulichung
braucht es zwei Dutzend. Dieses Modul nimmt die Personen, die der Abgleich
auf den gewählten Seiten getroffen hat, holt ihre Ehepartner und Familien
dazu und schreibt die Records **wörtlich** aus der Recordtabelle — kein
Nachbau, sondern dieselben Zeilen wie im Original.

**Wozu.** Die Demo zeigte den Nullstart: keine Beleg-Quelle, also alles
gelb. Der Elternehe-Anker, der Kern des Verfahrens, blieb damit
unsichtbar. Gemessen an den beiliegenden Seiten: Wer nur die Ehen von 1808
liest und übergibt, bekommt trotzdem null grün — die Eltern der 1808
getauften Kinder haben vorher geheiratet. Es braucht Bestand aus früherer
Zeit, und genau den schneidet dieses Modul heraus.

**Was mitkommt.** Die Ortsdefinitionen (`_LOC`), auf die die Records
zeigen — ohne sie hat der Auszug tote Verweise. Der Kopfsatz wird neu
geschrieben und nennt die Herkunft.
"""
import argparse
import re
from pathlib import Path

from . import db, konfig

KOPF = """0 HEAD
1 SOUR OFB-Werkstatt
2 NAME OFB-Werkstatt, Auszug
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
1 NOTE {notiz}
"""


def betroffene(con, runde_id=None):
    """Personen und Familien, die zu den Einträgen gehören."""
    wo, par = ("WHERE f.person IS NOT NULL", [])
    if runde_id:
        wo += " AND e.runde=?"
        par = [runde_id]
    pids = {r["person"] for r in con.execute(
        "SELECT DISTINCT f.person FROM feld f "
        "JOIN eintrag e ON e.id=f.eintrag_id " + wo, par)}
    fam, mehr = set(), set()
    for p in list(pids):
        for r in con.execute("SELECT id, mann, frau FROM familie "
                             "WHERE mann=? OR frau=?", (p, p)):
            fam.add(r["id"])
            mehr |= {x for x in (r["mann"], r["frau"]) if x}
    return pids | mehr, fam


def _xrefs(con, tabelle, ids):
    if not ids:
        return []
    q = (f"SELECT xref FROM {tabelle} WHERE id IN "
         f"({','.join('?' * len(ids))}) AND xref IS NOT NULL")
    return [r["xref"] for r in con.execute(q, tuple(ids))]


def schneide(con, runde_id=None, notiz=None):
    """Gibt den Auszug als Text zurück."""
    pids, fam = betroffene(con, runde_id)
    xr = _xrefs(con, "person", pids) + _xrefs(con, "familie", fam)
    if not xr:
        raise SystemExit("nichts getroffen — erst abgleichen")
    q = (f"SELECT xref, typ, raw FROM rec WHERE xref IN "
         f"({','.join('?' * len(xr))}) ORDER BY seq")
    records = list(con.execute(q, tuple(xr)))
    # Die Ortsdefinitionen, auf die sie zeigen. Ohne sie zeigt jeder
    # `3 _LOC @L1@` ins Leere, und das faellt beim Import als Fehler auf.
    loc = set()
    for r in records:
        loc |= set(re.findall(r"_LOC @(\w+)@", r["raw"]))
    if loc:
        q = (f"SELECT raw FROM rec WHERE xref IN "
             f"({','.join('?' * len(loc))}) ORDER BY seq")
        orte = [r["raw"] for r in con.execute(q, tuple(loc))]
    else:
        orte = []
    z = [KOPF.format(notiz=notiz or "Auszug aus einem Ortsfamilienbuch")]
    z += orte
    z += [r["raw"] for r in records]
    z.append("0 TRLR")
    return "\n".join(x.rstrip("\n") for x in z) + "\n", dict(
        personen=len(_xrefs(con, "person", pids)),
        familien=len(_xrefs(con, "familie", fam)),
        orte=len(orte), records=len(records) + len(orte))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runde", type=int)
    ap.add_argument("-o", "--ziel", required=True)
    ap.add_argument("--notiz")
    a = ap.parse_args()
    text, z = schneide(db.verbinde(), a.runde, a.notiz)
    p = Path(a.ziel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    print(f"{konfig.kurz(p)}: {z['personen']} Personen, {z['familien']} "
          f"Familien, {z['orte']} Orte — {len(text) // 1024} kB")


if __name__ == "__main__":
    main()
