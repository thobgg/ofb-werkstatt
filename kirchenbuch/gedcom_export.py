#!/usr/bin/env python3
"""Erzeugt aus dem OFB-Index plus Änderungsjournal eine GEDCOM-Datei.

Unveraenderte Records werden zeichengleich aus rec.raw durchgereicht.
Nur Records, die ein Vorgang beruehrt, werden neu geschrieben.

Leerlauf-Test: bei leerem Journal muss die Ausgabe BYTE-IDENTISCH zur
Quelldatei sein.

Merge-Semantik:
  1. alle Zeilen des aufgehenden Records, die im Zielrecord fehlen,
     werden dort ergaenzt (Identitaetszeilen ausgenommen)
  2. jeder Verweis @alt@ wird global durch @neu@ ersetzt
  3. der aufgehende Record entfaellt
  4. dadurch entstehende Doppelzeilen werden entfernt
Damit verwaist kein Verweis und es geht keine Angabe verloren.

Aufruf:
  python3 skripte/sqlite2ged.py --pruefe
  python3 skripte/sqlite2ged.py --diff
  python3 skripte/sqlite2ged.py -o ausgabe/OFB_erweitert.ged
"""
import argparse
import difflib
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "daten" / "ofb_haberschlacht.sqlite"
JOURNAL = ROOT / "daten" / "aenderung.sqlite"

# Zeilen, die die Identitaet des aufgehenden Records ausmachen und
# nicht in den Zielrecord uebernommen werden duerfen.
IDENTITAET = ("0 @", "1 RIN ", "1 CHAN", "2 DATE ", "3 TIME ")


def lade_vorgaenge():
    if not JOURNAL.exists():
        return []
    con = sqlite3.connect(JOURNAL)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(
            "SELECT * FROM vorgang WHERE aktiv=1 ORDER BY id")]
    except sqlite3.OperationalError:
        return []


def entdoppeln(zeilen):
    """Entfernt exakte Wiederholungen einzelner Verweiszeilen."""
    gesehen = set()
    raus = []
    for z in zeilen:
        if re.match(r"^1 (FAMS|FAMC|CHIL|HUSB|WIFE) @", z):
            if z in gesehen:
                continue
            gesehen.add(z)
        raus.append(z)
    return raus


def in_bloecke(raw):
    """Record in Bloecke der Ebene 1 zerlegen (jeder mit seinen Unterzeilen)."""
    bloecke = []
    aktuell = None
    for z in raw.split("\n"):
        if z.startswith("0 @"):
            continue
        if z.startswith("1 "):
            if aktuell:
                bloecke.append(aktuell)
            aktuell = [z]
        elif aktuell is not None:
            aktuell.append(z)
    if aktuell:
        bloecke.append(aktuell)
    return bloecke


def merge_bloecke(ziel_raw, quell_raw):
    """Bloecke aus quell_raw, die im Zielrecord fehlen, anhaengen.

    Verglichen wird der GANZE Block, nicht einzelne Zeilen: ein OCCU-Block
    mit anderem Datum ist neu, auch wenn seine Unterzeilen (PLAC, MAP, ...)
    anderswo schon vorkommen. Umgekehrt wird ein identischer Block nicht
    zweimal aufgenommen.

    Voraussetzung: in quell_raw sind die IDs bereits auf die Zielwerte
    umgeschrieben, sonst werden HUSB/WIFE/FAMS-Zeilen faelschlich als neu
    erkannt.
    """
    zziel = ziel_raw.split("\n")
    vorhanden = {tuple(b) for b in in_bloecke(ziel_raw)}
    einzeln = set(zziel)

    neu = []
    for b in in_bloecke(quell_raw):
        if b[0].startswith(IDENTITAET):
            continue
        if tuple(b) in vorhanden:
            continue
        if len(b) == 1 and b[0] in einzeln:
            continue
        # Gleiche Kopfzeile (z.B. identischer NAME): Unterzeilen in den
        # bestehenden Block einhaengen, statt ihn ein zweites Mal anzulegen.
        if b[0].startswith("1 NAME "):
            pos = next((i for i, z in enumerate(zziel) if z == b[0]), None)
            if pos is not None:
                ende = pos + 1
                while ende < len(zziel) and not zziel[ende].startswith("1 "):
                    ende += 1
                fehlend = [z for z in b[1:] if z not in zziel[pos:ende]]
                zziel[ende:ende] = fehlend
                einzeln.update(fehlend)
                continue
        neu.extend(b)
        vorhanden.add(tuple(b))
        einzeln.update(b)
    return zziel + neu


def baue(con, vorgaenge):
    records = [[r["id"], r["type"], r["raw"]]
               for r in con.execute("SELECT id, type, raw FROM rec ORDER BY seq")]
    idx = {r[0]: i for i, r in enumerate(records)}

    ersetzen = {}        # alte ID -> neue ID
    entfernen = set()
    neue = []
    feldvorgaenge = {}
    kindvorgaenge = {}

    # 1. Durchgang: alle Ersetzungen sammeln, BEVOR gemergt wird
    for v in vorgaenge:
        if v["art"] == "merge" and v["ziel2"] in idx and v["ziel"] in idx:
            ersetzen[v["ziel2"]] = v["ziel"]

    def ids_ersetzen(text):
        if not ersetzen:
            return text
        return re.sub(r"@([A-Za-z0-9_]+)@",
                      lambda m: "@" + ersetzen.get(m.group(1), m.group(1)) + "@",
                      text)

    for v in vorgaenge:
        art = v["art"]
        if art in ("neu_person", "neu_familie"):
            neue.append(v)
        elif art == "merge":
            ziel, quelle = v["ziel"], v["ziel2"]
            if quelle in idx and ziel in idx:
                # Quellrecord zuerst auf die Ziel-IDs umschreiben, sonst
                # werden HUSB/WIFE/FAMS-Zeilen faelschlich als neu erkannt
                records[idx[ziel]][2] = "\n".join(merge_bloecke(
                    ids_ersetzen(records[idx[ziel]][2]),
                    ids_ersetzen(records[idx[quelle]][2])))
                entfernen.add(quelle)
        elif art == "feld":
            feldvorgaenge.setdefault(v["ziel"], []).append(v)
        elif art == "kind":
            kindvorgaenge.setdefault(v["ziel"], []).append(v)

    # Feld- und Kindvorgaenge anwenden
    for rid, vs in feldvorgaenge.items():
        if rid not in idx:
            continue
        zeilen = records[idx[rid]][2].split("\n")
        for v in vs:
            d = json.loads(v["daten"])
            for i, z in enumerate(zeilen):
                if z == d["alt"]:
                    zeilen[i] = d["neu"]
                    break
        records[idx[rid]][2] = "\n".join(zeilen)

    for rid, vs in kindvorgaenge.items():
        if rid not in idx:
            continue
        zeilen = records[idx[rid]][2].split("\n")
        for v in vs:
            d = json.loads(v["daten"])
            neu_z = f"1 CHIL @{d['kind']}@"
            if neu_z in zeilen:
                continue
            pos = max((i for i, z in enumerate(zeilen)
                       if z.startswith("1 CHIL ")), default=None)
            if pos is None:
                pos = max((i for i, z in enumerate(zeilen)
                           if z.startswith(("1 HUSB ", "1 WIFE "))), default=0)
            zeilen.insert(pos + 1, neu_z)
        records[idx[rid]][2] = "\n".join(zeilen)

    # globales Ersetzen der Verweise
    raus = []
    for rid, typ, raw in records:
        if rid in entfernen:
            continue
        if ersetzen:
            def sub(m):
                return "@" + ersetzen.get(m.group(1), m.group(1)) + "@"
            raw = re.sub(r"@([A-Za-z0-9_]+)@", sub, raw)
            raw = "\n".join(entdoppeln(raw.split("\n")))
        if typ == "TRLR":
            for v in neue:
                raus.append(json.loads(v["daten"])["raw"])
        raus.append(raw)
    return "\n".join(raus)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--pruefe", action="store_true")
    ap.add_argument("--diff", action="store_true")
    a = ap.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    vorgaenge = lade_vorgaenge()
    text = baue(con, vorgaenge)
    quelle = Path([r[0] for r in con.execute(
        "SELECT v FROM meta WHERE k='source'")][0])
    orig = quelle.read_text(encoding="utf-8-sig")

    if a.pruefe:
        gleich = orig == text
        print(f"Journal  : {len(vorgaenge)} Vorgänge")
        print(f"Quelle   : {len(orig)} Zeichen  sha {hashlib.sha256(orig.encode()).hexdigest()[:16]}")
        print(f"Erzeugt  : {len(text)} Zeichen  sha {hashlib.sha256(text.encode()).hexdigest()[:16]}")
        print("BYTE-IDENTISCH" if gleich else "abweichend (erwartet, wenn Journal gefüllt)")
        if not gleich and not vorgaenge:
            for i, (x, y) in enumerate(zip(orig, text)):
                if x != y:
                    print("erste Abweichung bei", i)
                    print("  Quelle :", repr(orig[max(0, i-60):i+60]))
                    print("  Erzeugt:", repr(text[max(0, i-60):i+60]))
                    break
            sys.exit(1)
        return

    if a.diff:
        d = list(difflib.unified_diff(orig.split("\n"), text.split("\n"),
                                      "OFB original", "OFB erweitert", n=2, lineterm=""))
        print("\n".join(d) if d else "keine Unterschiede")
        plus = sum(1 for z in d if z.startswith("+") and not z.startswith("+++"))
        minus = sum(1 for z in d if z.startswith("-") and not z.startswith("---"))
        print(f"\n>> {plus} Zeilen hinzu, {minus} Zeilen entfernt")
        return

    if not a.out:
        print(__doc__)
        return
    ziel = Path(a.out)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(text, encoding="utf-8")
    print(f"{ziel}: {len(text)} Zeichen, {len(vorgaenge)} Vorgänge angewendet")


if __name__ == "__main__":
    main()
