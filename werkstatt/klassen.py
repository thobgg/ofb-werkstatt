#!/usr/bin/env python3
"""Äquivalenzklassen von Familiennamen aus dem OFB.

Jede _KB_NAME -> NAME-Zuordnung ist eine Kante zwischen zwei Schreibungen.
Der transitive Abschluss (Union-Find) liefert Klassen zusammengehoeriger Namen.

Die Relation ist NICHT wirklich transitiv: eine einzelne Fehlzuordnung
(z.B. 'Bührle -> Müller', 1 Beleg) verschmilzt zwei fremde Familien.
Genau deshalb ist der Abschluss ein Fehlerdetektor — verdaechtig sind
Klassen, die nur an einer schwachen Kante (wenige Belege) haengen.

Aufruf:
  python3 -m werkstatt.klassen                 # alle Klassen ab Groesse 2
  python3 -m werkstatt.klassen --min-kante 2   # Kanten mit 1 Beleg ignorieren
  python3 -m werkstatt.klassen --name Bierle   # nur die Klasse von Bierle
  python3 -m werkstatt.klassen --brueckenn     # nur die verdaechtigen Bruecken
"""
import argparse
import collections
import difflib
import json
import sqlite3
import unicodedata
from pathlib import Path

from . import konfig as _k

ROOT = _k.WURZEL
DB = _k.bestand()
EXPORT = ROOT / "daten" / "namensklassen.json"

# Aufnahmeregel fuer eine Kante, datengetrieben aus dem Graubereich bestimmt:
#   sicher   ab Naehe 0.65 (Neck->Beck, Keßer->Käser, Rohr->Rorer ...)
#   knapp    0.60-0.65 nur mit >=2 Belegen — dort kollidieren
#            Bierle->Buehrlen (richtig, 5 Belege) und
#            Schneider->Fischer (falsch, 1 Beleg) bei identischer Naehe 0.62
#   darunter immer Fehlzuordnung (Buehrle->Mueller 0.50, Hermann->Maier 0.33)
NAEHE_SICHER = 0.65
NAEHE_KNAPP = 0.60


def kante_gilt(naehe, belege):
    return naehe >= NAEHE_SICHER or (naehe >= NAEHE_KNAPP and belege >= 2)


def falte(s):
    s = (s or "").lower().strip()
    s = s.replace("ß", "ss").replace("ck", "k").replace("th", "t")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def aehnlich(a, b):
    return difflib.SequenceMatcher(None, falte(a), falte(b)).ratio()


def kb_nachname(value):
    t = value.split("/")
    return (t[1] if len(t) > 2 else value).strip()


def lade_kanten(con):
    """(a,b) -> Anzahl Belege. a = Kirchenbuchform, b = kanonischer Name."""
    kanten = collections.Counter()
    for r in con.execute(
        "SELECT k.value AS kb, i.surn AS nm FROM kb k "
        "JOIN indi i ON i.id=k.owner WHERE k.tag='_KB_NAME'"
    ):
        a, b = kb_nachname(r["kb"]), (r["nm"] or "").strip()
        if a and b and a != b:
            kanten[(a, b)] += 1
    return kanten


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-kante", type=int, default=1,
                    help="Kanten mit weniger Belegen ignorieren (Default 1 = alle)")
    ap.add_argument("--name", default=None, help="nur die Klasse dieses Namens")
    ap.add_argument("--export", action="store_true",
                    help="Klassen als JSON nach wissen/namensklassen.json schreiben")
    ap.add_argument("--bruecken", action="store_true",
                    help="nur Kanten zeigen, deren Wegfall die Klasse zerlegt")
    a = ap.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    haeufig = collections.Counter()
    for r in con.execute("SELECT surn, surn_norm FROM indi"):
        for v in (r["surn"], r["surn_norm"]):
            if v:
                haeufig[v.strip()] += 1

    kanten = lade_kanten(con)
    benutzt = {}
    verworfen = []
    for (x, y), n in kanten.items():
        s = aehnlich(x, y)
        if n < a.min_kante:
            continue
        if not kante_gilt(s, n):
            verworfen.append((x, y, n, s))
            continue
        benutzt[(x, y)] = n

    if verworfen and not a.name and not a.bruecken:
        print("Verworfene Kanten (Fehlzuordnung, Wiederheirat oder "
              "Namenswechsel — keine Schreibvariante):")
        for x, y, n, s in sorted(verworfen, key=lambda t: -t[2]):
            print(f"   {x} -> {y}   {n} Beleg(e), Naehe {s:.2f}")
        print()

    uf = UF()
    for (x, y) in benutzt:
        uf.union(x, y)

    klassen = collections.defaultdict(set)
    for x in list(uf.p):
        klassen[uf.find(x)].add(x)

    if a.bruecken:
        # Kante ist Bruecke, wenn ihr Entfernen die Klasse zerlegt
        print("Verdaechtige Bruecken (Wegfall zerlegt die Klasse):\n")
        for (x, y), n in sorted(benutzt.items(), key=lambda t: t[1]):
            uf2 = UF()
            for (p, q) in benutzt:
                if (p, q) != (x, y):
                    uf2.union(p, q)
            if uf2.find(x) != uf2.find(y):
                la = sorted({z for z in uf2.p if uf2.find(z) == uf2.find(x)})
                lb = sorted({z for z in uf2.p if uf2.find(z) == uf2.find(y)})
                warn = "  <== SCHWACH" if n <= 1 else ""
                print(f"  {x} -> {y}  ({n} Beleg{'e' if n != 1 else ''}){warn}")
                print(f"      trennt {la}")
                print(f"         von {lb}\n")
        return

    if a.export:
        raus = {}
        for wurzel, gruppe in klassen.items():
            if len(gruppe) < 2:
                continue
            haupt = max(gruppe, key=lambda n: haeufig.get(n, 0))
            for n in gruppe:
                raus[n] = haupt
        EXPORT.write_text(json.dumps(raus, ensure_ascii=False, indent=1, sort_keys=True))
        print(f"{len(raus)} Schreibungen in {len({v for v in raus.values()})} Klassen "
              f"-> {EXPORT.relative_to(ROOT)}")
        return

    ziel = None
    if a.name:
        ziel = uf.find(a.name) if a.name in uf.p else None
        if ziel is None:
            print(f"'{a.name}' hat keine Variantenkante im OFB.")
            return

    for wurzel, gruppe in sorted(klassen.items(),
                                 key=lambda t: -sum(haeufig.get(n, 0) for n in t[1])):
        if len(gruppe) < 2:
            continue
        if ziel and wurzel != ziel:
            continue
        gesamt = sum(haeufig.get(n, 0) for n in gruppe)
        haupt = max(gruppe, key=lambda n: haeufig.get(n, 0))
        print(f"\n=== {haupt}  ({len(gruppe)} Schreibungen, {gesamt} Personen) ===")
        for n in sorted(gruppe, key=lambda n: -haeufig.get(n, 0)):
            mark = "  <- kanonisch" if n == haupt else ""
            print(f"   {n:16} {haeufig.get(n, 0):4}{mark}")
        ki = [(x, y, c) for (x, y), c in benutzt.items() if x in gruppe or y in gruppe]
        print("   Kanten: " + ", ".join(f"{x}->{y}({c})" for x, y, c in sorted(ki, key=lambda t: -t[2])))


if __name__ == "__main__":
    main()
