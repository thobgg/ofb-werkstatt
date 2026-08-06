#!/usr/bin/env python3
"""Namens- und Personensuche für die Erfassungsmaske.

Zwei Ebenen, beide beim Tippen:
  1. Nachname   -> Vokabular des OFB samt kanonischer Form der
                   Aequivalenzklasse (Bührlin -> Bierle, 122 Personen)
  2. Person     -> konkrete OFB-Records samt Lebensdaten und Ehe.
                   Auswahl davon ist 'find and use'.

Getrennt von der Maske, damit es auch auf der Kommandozeile nutzbar ist:
  python3 -m werkstatt.suche Kröneck
"""
import json
import re
import sqlite3
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

from . import db as _db
from . import konfig as _k

ROOT = _k.WURZEL
KLASSEN = ROOT / "daten" / "namensklassen.json"


def falte(s):
    s = (s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("ß", "ss")


@lru_cache(maxsize=1)
def klassen():
    return json.loads(KLASSEN.read_text()) if KLASSEN.exists() else {}


@lru_cache(maxsize=1)
def inventar():
    """Nachname -> (Anzahl, kanonische Form der Klasse, Klassengroesse)."""
    con = _db.verbinde()
    # nach gefalteter Form gruppieren; angezeigt wird die gebraeuchlichste
    # Schreibung, nicht die Kleinschreib-Normalform aus surn_norm
    gruppen = {}
    quellen = list(con.execute(
        "SELECT surn AS a, surn_kanon AS b FROM person WHERE surn IS NOT NULL"))
    quellen += list(con.execute(
        "SELECT wert AS a, NULL AS b FROM namensform WHERE art='surn'"))
    # Wörter ohne Person — eingelesene Namenslisten, Ortsverzeichnisse,
    # abgetippte Register. Sie ranken mit, bestätigen aber nie: ihre
    # Herkunft ist immer `vokabular`, und die Ampel liest den Rang, nicht
    # diese Liste. `offen` zählt dazu, weil eine Spalte ohne erkennbare
    # Überschrift meist doch Namen enthält.
    quellen += list(con.execute(
        "SELECT wort AS a, NULL AS b FROM wortschatz "
        "WHERE klasse IN ('nachname','offen')"))
    for surn, norm in ((r["a"], r["b"]) for r in quellen):
        for v in (surn, norm):
            v = (v or "").strip()
            if not v:
                continue
            gruppen.setdefault(falte(v), {})
            gruppen[falte(v)][v] = gruppen[falte(v)].get(v, 0) + 1
    con.close()
    zahl = {}
    for schreibungen in gruppen.values():
        # Variante mit Grossbuchstaben bevorzugen, dann die haeufigste
        beste = max(schreibungen, key=lambda s: (s[:1].isupper(), schreibungen[s]))
        # reine Kleinschreibformen stammen aus surn_norm und sind keine
        # echten Schreibvarianten ('von Westen' u.ae. bleiben erhalten)
        if beste.islower() and not beste.startswith(("von ", "van ", "zu ")):
            continue
        zahl[beste] = max(schreibungen.values())
    k = klassen()
    gruppe = {}
    for name, haupt in k.items():
        gruppe.setdefault(haupt, 0)
    for name, haupt in k.items():
        gruppe[haupt] = gruppe.get(haupt, 0) + zahl.get(name, 0)
    raus = {}
    for n, c in zahl.items():
        haupt = k.get(n)
        raus[n] = (c, haupt, gruppe.get(haupt, 0) if haupt else 0)
    return raus


@lru_cache(maxsize=1)
def personen():
    """Liste aller Personen mit Kurzinfo für die Trefferanzeige."""
    con = _db.verbinde()
    ev, ehe = {}, {}
    for r in con.execute(
            "SELECT person, familie, art, datum FROM ereignis"):
        schl = r["person"] if r["person"] is not None else ("F", r["familie"])
        ev.setdefault(schl, {}).setdefault(r["art"], r["datum"])
    for r in con.execute("SELECT id, mann, frau FROM familie"):
        m = ev.get(("F", r["id"]), {}).get("MARR")
        for p, andere in ((r["mann"], r["frau"]), (r["frau"], r["mann"])):
            if p:
                ehe.setdefault(p, []).append((r["id"], m, andere))
    namen = {r["id"]: r["name"] for r in con.execute("SELECT id, name FROM person")}
    raus = []
    for r in con.execute("SELECT id, name, givn, surn, sex FROM person"):
        e = ev.get(r["id"], {})
        lebt = []
        for t, kurz in (("CHR", "~"), ("BIRT", "*"), ("DEAT", "†")):
            if e.get(t):
                lebt.append(f"{kurz}{e[t]}")
                if len(lebt) == 2:
                    break
        ehen = []
        for fid, datum, andere in ehe.get(r["id"], [])[:2]:
            ehen.append(f"⚭{(datum or '?')} {namen.get(andere, '?')}")
        raus.append(dict(id=r["id"], name=r["name"] or "",
                         givn=r["givn"] or "", surn=(r["surn"] or "").strip(),
                         sex=r["sex"] or "", leben=" ".join(lebt),
                         ehe="; ".join(ehen)))
    con.close()
    return raus


def namen_treffer(q, limit=8):
    qf = falte(q)
    if not qf:
        return []
    inv = inventar()
    tref = []
    for n, (c, haupt, gross) in inv.items():
        nf = falte(n)
        if nf.startswith(qf):
            rang = 0
        elif qf in nf:
            rang = 1
        else:
            continue
        tref.append((rang, -c, n, c, haupt, gross))
    tref.sort()
    return [dict(name=t[2], anzahl=t[3], kanonisch=t[4], klasse=t[5])
            for t in tref[:limit]]


def personen_treffer(q, limit=8, sex=None):
    qf = falte(q)
    if len(qf) < 2:
        return []
    tref = []
    for p in personen():
        nf = falte(p["name"])
        sf = falte(p["surn"])
        if sf.startswith(qf):
            rang = 0
        elif qf in nf:
            rang = 1
        else:
            continue
        if sex and p["sex"] and p["sex"] != sex:
            rang += 2
        tref.append((rang, 0 if p["ehe"] else 1, p["name"], p))
    tref.sort(key=lambda t: (t[0], t[1], t[2]))
    return [t[3] for t in tref[:limit]]


def main():
    q = " ".join(sys.argv[1:])
    if not q:
        print(__doc__)
        return
    print(f"=== Nachnamen zu {q!r} ===")
    for t in namen_treffer(q):
        k = (f"  -> Klasse {t['kanonisch']} ({t['klasse']})"
             if t["kanonisch"] and t["kanonisch"] != t["name"] else "")
        print(f"  {t['name']:20} {t['anzahl']:4}{k}")
    print(f"\n=== Personen zu {q!r} ===")
    for p in personen_treffer(q):
        print(f"  {p['id']:8} {p['name']:36} {p['leben']:34} {p['ehe'][:50]}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------- Anbindung
@lru_cache(maxsize=1)
def familien():
    """Familie -> Daten; plus Zuordnung Person -> Ehen und Herkunftsfamilie."""
    con = _db.verbinde()
    namen = {r["id"]: r["name"] for r in con.execute("SELECT id, name FROM person")}
    marr = {r["familie"]: r["datum"] for r in con.execute(
        "SELECT familie, datum FROM ereignis WHERE art='MARR' AND familie IS NOT NULL")}
    fam, fams, famc = {}, {}, {}
    for r in con.execute("SELECT id, mann, frau FROM familie"):
        fam[r["id"]] = dict(id=r["id"], husb=r["mann"], wife=r["frau"],
                            husb_name=namen.get(r["mann"], ""),
                            wife_name=namen.get(r["frau"], ""),
                            marr=marr.get(r["id"]), kinder=[])
        for p in (r["mann"], r["frau"]):
            if p:
                fams.setdefault(p, []).append(r["id"])
    for r in con.execute("SELECT familie, person FROM kind"):
        if r["familie"] in fam:
            fam[r["familie"]]["kinder"].append(r["person"])
        famc.setdefault(r["person"], []).append(r["familie"])
    con.close()
    return fam, fams, famc


def anbindung(vater=None, mutter=None):
    """Entscheidungsvorschlag: an welche Familie haengt das Kind?

    beide bekannt + gemeinsame Familie  -> anbinden
    beide bekannt, keine gemeinsame     -> neue Familie, aber nachfragen
    nur einer bekannt                   -> neue Familie mit dem bekannten Teil
    """
    fam, fams, famc = familien()
    vf = set(fams.get(vater or "", []))
    mf = set(fams.get(mutter or "", []))
    gemeinsam = sorted(vf & mf)
    def kurz(fid):
        f = fam[fid]
        return dict(id=fid, marr=f["marr"], kinder=len(f["kinder"]),
                    husb=f["husb"], wife=f["wife"],
                    text=f"{f['husb_name']} ⚭ {f['wife_name']}"
                         + (f" · {f['marr']}" if f["marr"] else "")
                         + f" · {len(f['kinder'])} Kinder")
    if gemeinsam:
        return dict(art="anbinden", familie=kurz(gemeinsam[0]),
                    weitere=[kurz(f) for f in gemeinsam[1:]],
                    hinweis="gemeinsame Familie im OFB")
    if vater and mutter:
        return dict(art="neu_pruefen", familie=None,
                    weitere=[kurz(f) for f in sorted(vf | mf)],
                    hinweis="beide Eltern gefunden, aber KEINE gemeinsame "
                            "Familie — neue Ehe oder falsche Zuordnung?")
    if vater or mutter:
        return dict(art="neu", familie=None,
                    weitere=[kurz(f) for f in sorted(vf | mf)],
                    hinweis="nur ein Elternteil zugeordnet")
    return dict(art="neu", familie=None, weitere=[],
                hinweis="beide Eltern neu")


def herkunft(person):
    """Eltern einer Person — zur Kontrolle gegen die Vaterangabe im Register."""
    fam, fams, famc = familien()
    raus = []
    for fid in famc.get(person or "", []):
        f = fam.get(fid)
        if f:
            raus.append(dict(id=fid, vater=f["husb_name"], mutter=f["wife_name"],
                             vater_id=f["husb"], mutter_id=f["wife"]))
    return raus
