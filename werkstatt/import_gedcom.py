#!/usr/bin/env python3
"""GEDCOM in die Datenbasis einlesen.

Verlustfrei in zwei Stufen:

  `rec`                die ganze Datei, Record für Record, in Reihenfolge
  `person`/`familie`   Index darauf, plus Ereignisse und Namensformen

Die erste Stufe fehlte lange, und die Lücke war unsichtbar: `person.raw`
bewahrt jeden INDI-Record, aber eine GEDCOM-Datei besteht nicht nur daraus.
Gemessen am Bestand Haberschlacht – 5.615 Records, davon 4.111 INDI und
1.346 FAM, und 158 weitere, die niemand aufhob: HEAD, SUBM, 35 SOUR,
**120 _LOC** und TRLR. Auf die _LOC-Records zeigt jede Person mit
`3 _LOC @L1@`; ohne sie hätte die Ausgabe tote Verweise.

    python3 -m werkstatt.import_gedcom pfad/zur/datei.ged
    python3 -m werkstatt.import_gedcom --aus-konfig
    python3 -m werkstatt.import_gedcom --nur-rec datei.ged   nur nachtragen
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

    Ein INDI kann MEHRERE `1 NAME`-Bloecke tragen, jeder mit eigenem SURN –
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


def lies_datei(pfad):
    """Text plus die drei Eigenschaften, die eine Ausgabe wiederherstellen muss.

    BOM, Zeilenende und Schlussumbruch entscheiden über das erste und das
    letzte Byte. Ohne sie unterscheidet sich eine Ausgabe von der Vorlage,
    ohne dass ein einziges Feld anders wäre – und der Leerlauftest, der die
    Verlustfreiheit belegen soll, schlägt aus einem belanglosen Grund fehl.
    """
    roh = Path(pfad).read_bytes()
    bom = roh.startswith(b"\xef\xbb\xbf")
    if bom:
        roh = roh[3:]
    text = roh.decode("utf-8", errors="replace")
    crlf = "\r\n" in text
    if crlf:
        text = text.replace("\r\n", "\n")
    schluss = text.endswith("\n")
    return text.rstrip("\n"), dict(bom=int(bom),
                                   zeilenende="crlf" if crlf else "lf",
                                   schluss=int(schluss))


def merke_rec(con, hid, records, eigenschaften):
    """Die ganze Datei ablegen, Record für Record, in Reihenfolge."""
    con.execute("UPDATE herkunft SET bom=?, zeilenende=?, schluss=? WHERE id=?",
                (eigenschaften["bom"], eigenschaften["zeilenende"],
                 eigenschaften["schluss"], hid))
    con.execute("DELETE FROM rec WHERE herkunft=?", (hid,))
    con.executemany(
        "INSERT INTO rec (herkunft, seq, xref, typ, raw) VALUES (?,?,?,?,?)",
        [(hid, i, x, t, r) for i, (x, t, r) in enumerate(records)])
    con.commit()
    return len(records)


def nur_rec(pfad, con=None, still=False):
    """Nur die Recordtabelle nachtragen, sonst nichts anfassen.

    Für Bestände, die vor der Einführung von `rec` eingelesen wurden. Ein
    voller Neuimport wäre hier falsch: `ereignis` kennt kein OR IGNORE und
    würde sich verdoppeln.
    """
    pfad = Path(pfad)
    eigen = con is None
    con = con or db.verbinde()
    text, eig = lies_datei(pfad)
    row = con.execute("SELECT id FROM herkunft WHERE art='gedcom' AND datei=?",
                      (pfad.name,)).fetchone()
    if not row:
        raise SystemExit(f"{pfad.name} ist nicht als Herkunft eingetragen – "
                         "erst importieren")
    n = merke_rec(con, row["id"], zerlege(text), eig)
    if not still:
        print(f"{pfad.name}: {n} Records nachgetragen "
              f"(BOM {eig['bom']}, {eig['zeilenende']}, "
              f"Schlussumbruch {eig['schluss']})")
    if eigen:
        con.close()
    return n


def importiere(pfad, con=None, still=False):
    pfad = Path(pfad)
    text, eig = lies_datei(pfad)
    eigen = con is None
    con = con or db.verbinde()
    hid = db.herkunft_id(con, "gedcom", pfad.name,
                         f"{pfad}, {len(text)} Zeichen")

    records = zerlege(text)
    merke_rec(con, hid, records, eig)
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
    ap.add_argument("--nur-rec", action="store_true",
                    help="nur die Recordtabelle nachtragen, sonst nichts")
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
        (nur_rec if a.nur_rec else importiere)(z, con)
    con.close()


if __name__ == "__main__":
    main()
