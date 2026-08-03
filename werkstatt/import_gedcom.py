#!/usr/bin/env python3
"""GEDCOM in die Datenbasis einlesen.

Verlustfrei: der vollständige Quellrecord bleibt in `raw` erhalten, die
Spalten sind ein Index darauf. Damit ist ein zeichengleicher Export möglich
und nichts geht unterwegs verloren.

    python3 -m werkstatt.import_gedcom pfad/zur/datei.ged
    python3 -m werkstatt.import_gedcom --aus-konfig
"""
import argparse
import re
import sys
from pathlib import Path

from . import db, konfig

MONAT = {m: i + 1 for i, m in enumerate(
    "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
UNGENAU = re.compile(r"\b(BEF|AFT|ABT|CAL|EST|BET|FROM|TO)\b", re.I)

# Ereignisse, die als eigene Zeile gespeichert werden
EREIGNIS = {"BIRT", "CHR", "BAPM", "DEAT", "BURI", "MARR", "DIV",
            "OCCU", "RESI", "EVEN", "CENS", "CONF"}


def jahr_von(datum):
    if not datum:
        return None
    m = re.search(r"\b(\d{3,4})\b", datum)
    return int(m.group(1)) if m else None


def zerlege(text):
    """GEDCOM-Datei in Records zerlegen: (xref, typ, rohtext)."""
    zeilen = text.split("\n")
    rec, aktuell = [], None
    for z in zeilen:
        if z.startswith("0 "):
            if aktuell:
                rec.append(aktuell)
            m = re.match(r"0 (?:@([^@]+)@ )?(\w+)", z)
            aktuell = [m.group(1) if m else None,
                       m.group(2) if m else "?", [z]]
        elif aktuell:
            aktuell[2].append(z)
    if aktuell:
        rec.append(aktuell)
    return [(x, t, "\n".join(zs)) for x, t, zs in rec]


def unterzeilen(raw, ebene=1):
    """Record in Blöcke der angegebenen Ebene zerlegen."""
    bloecke, aktuell = [], None
    for z in raw.split("\n"):
        if z.startswith(f"{ebene} "):
            if aktuell:
                bloecke.append(aktuell)
            aktuell = [z]
        elif aktuell is not None and not re.match(rf"^[0-{ebene}] ", z):
            aktuell.append(z)
        elif aktuell is not None and re.match(r"^0 ", z):
            bloecke.append(aktuell)
            aktuell = None
    if aktuell:
        bloecke.append(aktuell)
    return bloecke


def wert(block, tag, ebene=2):
    for z in block:
        m = re.match(rf"^{ebene} {tag}(?: (.*))?$", z)
        if m:
            return (m.group(1) or "").strip()
    return None


def nachname_aus(voll):
    """Nachname aus 'Vorname /Nachname/' ziehen."""
    teile = (voll or "").split("/")
    return teile[1].strip() if len(teile) > 2 else None


def lies_person(raw):
    """Namensfelder und abweichende Formen aus einem INDI-Record.

    Ein INDI kann MEHRERE `1 NAME`-Bloecke tragen, jeder mit eigenem SURN —
    das sind Schreibvarianten desselben Namens (Bierle / Buehrlen). Alle
    Nachnamensformen werden als `namensform` mit art='surn' abgelegt, damit
    die Suche sie findet.
    """
    daten = dict(name=None, givn=None, surn=None, sex=None, formen=[])
    for b in unterzeilen(raw):
        kopf = b[0]
        if kopf.startswith("1 NAME "):
            voll = kopf[7:].strip()
            surn = wert(b, "SURN") or nachname_aus(voll)
            if daten["name"] is None:
                daten["name"] = voll.replace("/", "").strip()
                daten["givn"] = wert(b, "GIVN") or voll.split("/")[0].strip()
                daten["surn"] = surn
            else:
                daten["formen"].append(("variante", voll))
            if surn:
                daten["formen"].append(("surn", surn))
            for z in b[1:]:
                m = re.match(r"^2 _KB_NAME (.+)$", z)
                if m:
                    kb = m.group(1).strip()
                    daten["formen"].append(("kb", kb))
                    n = nachname_aus(kb)
                    if n:
                        daten["formen"].append(("surn", n))
                m = re.match(r"^2 _RUFNAME (.+)$", z)
                if m:
                    daten["formen"].append(("rufname", m.group(1).strip()))
        elif kopf.startswith("1 SEX "):
            daten["sex"] = kopf[6:].strip()
    return daten


def lies_ereignisse(raw):
    raus = []
    for b in unterzeilen(raw):
        m = re.match(r"^1 (\w+)(?: (.*))?$", b[0])
        if not m or m.group(1) not in EREIGNIS:
            continue
        art = m.group(1)
        datum = wert(b, "DATE")
        seite = None
        for z in b:
            s = re.match(r"^3 PAGE (.+)$", z)
            if s:
                seite = s.group(1).strip()
                break
        raus.append(dict(
            art=art, datum=datum, jahr=jahr_von(datum),
            exakt=0 if (datum and UNGENAU.search(datum)) else 1,
            ort=wert(b, "PLAC"), wert=(m.group(2) or "").strip() or None,
            quelle=seite))
    return raus


def importiere(pfad, con=None, still=False):
    pfad = Path(pfad)
    text = pfad.read_text(encoding="utf-8-sig", errors="replace")
    eigen = con is None
    con = con or db.verbinde()
    hid = db.herkunft_id(con, "gedcom", pfad.name,
                         f"{pfad}, {len(text)} Zeichen")

    records = zerlege(text)
    idx_person, idx_familie = {}, {}

    # 1. Durchgang: Personen und Familien anlegen
    for xref, typ, raw in records:
        if typ == "INDI":
            d = lies_person(raw)
            cur = con.execute(
                "INSERT OR IGNORE INTO person "
                "(xref,name,givn,surn,sex,herkunft,raw) VALUES (?,?,?,?,?,?,?)",
                (xref, d["name"], d["givn"], d["surn"], d["sex"], hid, raw))
            pid = con.execute(
                "SELECT id FROM person WHERE herkunft=? AND xref=?",
                (hid, xref)).fetchone()["id"]
            idx_person[xref] = pid
            for art, w in d["formen"]:
                con.execute(
                    "INSERT OR IGNORE INTO namensform (person,art,wert) "
                    "VALUES (?,?,?)", (pid, art, w))
        elif typ == "FAM":
            con.execute(
                "INSERT OR IGNORE INTO familie (xref,herkunft,raw) VALUES (?,?,?)",
                (xref, hid, raw))
            idx_familie[xref] = con.execute(
                "SELECT id FROM familie WHERE herkunft=? AND xref=?",
                (hid, xref)).fetchone()["id"]

    # 2. Durchgang: Verknüpfungen und Ereignisse
    for xref, typ, raw in records:
        if typ == "INDI":
            pid = idx_person.get(xref)
            for e in lies_ereignisse(raw):
                con.execute(
                    "INSERT INTO ereignis "
                    "(person,art,datum,jahr,exakt,ort,wert,quelle) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (pid, e["art"], e["datum"], e["jahr"], e["exakt"],
                     e["ort"], e["wert"], e["quelle"]))
        elif typ == "FAM":
            fid = idx_familie.get(xref)
            mann = frau = None
            for z in raw.split("\n"):
                m = re.match(r"^1 (HUSB|WIFE|CHIL) @([^@]+)@", z)
                if not m:
                    continue
                p = idx_person.get(m.group(2))
                if p is None:
                    continue
                if m.group(1) == "HUSB":
                    mann = p
                elif m.group(1) == "WIFE":
                    frau = p
                else:
                    con.execute(
                        "INSERT OR IGNORE INTO kind (familie,person) VALUES (?,?)",
                        (fid, p))
            con.execute("UPDATE familie SET mann=?, frau=? WHERE id=?",
                        (mann, frau, fid))
            for e in lies_ereignisse(raw):
                con.execute(
                    "INSERT INTO ereignis "
                    "(familie,art,datum,jahr,exakt,ort,wert,quelle) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (fid, e["art"], e["datum"], e["jahr"], e["exakt"],
                     e["ort"], e["wert"], e["quelle"]))
    con.commit()

    if not still:
        z = db.stand(con)
        print(f"{pfad.name}")
        print(f"  Records gelesen : {len(records)}")
        print(f"  Personen        : {len(idx_person)}")
        print(f"  Familien        : {len(idx_familie)}")
        print(f"  Bestand gesamt  : {z['person']} Personen, {z['familie']} "
              f"Familien, {z['ereignis']} Ereignisse, {z['namensform']} Namensformen")
    if eigen:
        con.close()
    return len(idx_person), len(idx_familie)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("datei", nargs="*")
    ap.add_argument("--aus-konfig", action="store_true",
                    help="die in konfig.toml eingetragene Bestandsdatei lesen")
    a = ap.parse_args()
    ziele = list(a.datei)
    if a.aus_konfig:
        b = konfig.bestand()
        if not b:
            sys.exit("in konfig.toml ist unter [bestand] keine Datei eingetragen")
        ziele.append(b)
    if not ziele:
        sys.exit(__doc__)
    con = db.verbinde()
    for z in ziele:
        importiere(z, con)
    con.close()


if __name__ == "__main__":
    main()
