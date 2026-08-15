#!/usr/bin/env python3
"""Einen kleinen Bestandsauszug schneiden – nur was zu bestimmten Seiten gehört.

    python3 -m werkstatt.auszug --runde 1 -o demo/bestand.ged

Ein Ortsfamilienbuch hat Tausende Personen; für eine Veranschaulichung
braucht es zwei Dutzend. Dieses Modul nimmt die Personen, die der Abgleich
auf den gewählten Seiten getroffen hat, holt ihre Ehepartner und Familien
dazu und schreibt die Records **wörtlich** aus der Recordtabelle – kein
Nachbau, sondern dieselben Zeilen wie im Original.

**Wozu.** Die Demo zeigte den Nullstart: keine Beleg-Quelle, also alles
gelb. Der Elternehe-Anker, der Kern des Verfahrens, blieb damit
unsichtbar. Gemessen an den beiliegenden Seiten: Wer nur die Ehen von 1808
liest und übergibt, bekommt trotzdem null grün – die Eltern der 1808
getauften Kinder haben vorher geheiratet. Es braucht Bestand aus früherer
Zeit, und genau den schneidet dieses Modul heraus.

**Was mitkommt.** Die Ortsdefinitionen (`_LOC`) und die Quellen (`SOUR`),
auf die die Records zeigen. Was darüber hinaus nach außen zeigt, wird
gekappt: Ein Auszug kennt die Eltern seiner Personen nicht und nicht alle
Kinder seiner Familien, und ein stehengebliebener Zeiger auf `@F472@` ist
beim Import ein Fehler, keine Information. Der Kopfsatz wird neu
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


def _zeiger(text):
    """Alle Verweise `@X1@`, die in Zeigerstellung stehen."""
    z = set()
    for zeile in text.split("\n"):
        m = re.match(r"^\d+ (?:@[^@]+@ )?\w+ (@[A-Za-z0-9_]+@)\s*$", zeile)
        if m:
            z.add(m.group(1).strip("@"))
    return z


def _kappe(text, vorhanden):
    """Zeilen entfernen, deren Verweis nicht mitkommt, samt Unterzeilen.

    Ein Auszug reisst Verbindungen ab: Die Eltern der herausgeschnittenen
    Person stehen in einer Familie, die nicht dabei ist, und eine Familie
    hat Kinder, die nicht dabei sind. Bleiben die Zeiger stehen, meldet
    jedes Programm beim Import tote Verweise und legt Platzhalter an.
    Also weg damit. Alles Uebrige bleibt Zeichen fuer Zeichen wie im
    Original; gekappt wird nur, was ohnehin ins Leere zeigte.
    """
    raus, weg, tiefe = [], 0, None
    for zeile in text.split("\n"):
        m = re.match(r"^(\d+) ", zeile)
        if not m:
            raus.append(zeile)
            continue
        lvl = int(m.group(1))
        if tiefe is not None and lvl > tiefe:
            continue                     # Unterzeile einer gekappten Zeile
        tiefe = None
        p = re.match(r"^(\d+) (?:@[^@]+@ )?\w+ (@[A-Za-z0-9_]+@)\s*$", zeile)
        if p and p.group(2).strip("@") not in vorhanden:
            tiefe, weg = lvl, weg + 1
            continue
        raus.append(zeile)
    return "\n".join(raus), weg


def schneide(con, runde_id=None, notiz=None):
    """Gibt den Auszug als Text zurück."""
    pids, fam = betroffene(con, runde_id)
    xr = _xrefs(con, "person", pids) + _xrefs(con, "familie", fam)
    if not xr:
        raise SystemExit("nichts getroffen – erst abgleichen")
    q = (f"SELECT xref, typ, raw FROM rec WHERE xref IN "
         f"({','.join('?' * len(xr))}) ORDER BY seq")
    records = list(con.execute(q, tuple(xr)))
    # Was mitkommen muss, damit kein Zeiger ins Leere geht: die
    # Ortsdefinitionen (`3 _LOC @L1@`) und die Quellen (`2 SOUR @S35@`).
    # Beides sind wenige, kleine Records; ohne sie faellt der Auszug beim
    # Import als fehlerhaft auf. Personen und Familien zieht der Auszug
    # dagegen nicht nach, sonst haengt am Ende das ganze Buch daran.
    gebraucht = set()
    for r in records:
        gebraucht |= _zeiger(r["raw"])
    beiwerk = []
    if gebraucht:
        q = (f"SELECT raw FROM rec WHERE xref IN "
             f"({','.join('?' * len(gebraucht))}) "
             f"AND typ IN ('_LOC','SOUR','NOTE','OBJE','REPO','SUBM') "
             f"ORDER BY seq")
        beiwerk = [r["raw"] for r in con.execute(q, tuple(gebraucht))]
    text = "\n".join(x.rstrip("\n")
                     for x in beiwerk + [r["raw"] for r in records])
    vorhanden = set(re.findall(r"^0 @([A-Za-z0-9_]+)@", text, re.M))
    text, gekappt = _kappe(text, vorhanden)
    z = [KOPF.format(notiz=notiz or "Auszug aus einem Ortsfamilienbuch"),
         text, "0 TRLR"]
    return "\n".join(x.rstrip("\n") for x in z) + "\n", dict(
        personen=len(_xrefs(con, "person", pids)),
        familien=len(_xrefs(con, "familie", fam)),
        beiwerk=len(beiwerk), gekappt=gekappt,
        records=len(records) + len(beiwerk))


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
          f"Familien, {z['beiwerk']} Quellen/Orte, {z['gekappt']} Zeiger "
          f"gekappt – {len(text) // 1024} kB")


if __name__ == "__main__":
    main()
