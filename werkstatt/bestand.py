#!/usr/bin/env python3
"""Lesezugriff auf einen vorhandenen Bestand (ofb-ki/kirchenbuch.db).

**Nur lesend.** Die Werkstatt greift nie schreibend in einen fremden Bestand
ein – sie nutzt ihn als Vokabular und als Anker.

Verlässlichkeit ist nicht überall gleich: In `kirchenbuch.db` sind die
Personenstrukturen nur für einzelne Parochien belastbar, sonst taugt der
Bestand als Vokabular, darf also ranken, aber nie bestätigen.
"""
import re
import sqlite3
import unicodedata
from functools import lru_cache
from pathlib import Path

from . import konfig

# Parochien mit belastbarer Personenstruktur. Alles andere: nur Vokabular.
BELASTBAR = {"Haberschlacht", "Neipperg"}


def pfad():
    p = (konfig.konfig().get("bestand", {}) or {}).get("kirchenbuch", "")
    return Path(p).expanduser() if p else Path.home() / "ofb-ki" / "kirchenbuch.db"


@lru_cache(maxsize=1)
def con():
    d = pfad()
    if not d.exists():
        raise SystemExit(f"Bestand nicht gefunden: {d}")
    c = sqlite3.connect(f"file:{d}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


@lru_cache(maxsize=1)
def parochien():
    return {r["id"]: r["name"] for r in con().execute("SELECT id, name FROM parochie")}


def belastbar(parochie_id):
    return parochien().get(parochie_id) in BELASTBAR


# ------------------------------------------------------------------ Namen
def falte(s):
    s = (s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("ß", "ss"))


# Vornamensvarianten, die in Kirchenbüchern dieselbe Person meinen
GLEICH = [
    {"johannes", "johann", "hans", "hanns", "hanß", "joh"},
    {"johann georg", "hans georg", "jerg", "georg", "jorg"},
    {"johann jacob", "hans jacob", "jacob", "jakob"},
    {"anna maria", "maria anna"},
    {"catharina", "katharina", "cathrina"},
    {"christina", "christiana", "christine"},
    {"elisabetha", "elisabeth", "elsbeth"},
    {"magdalena", "magdalene"},
    {"barbara", "barbel"},
    {"friedrich", "fridrich", "friderich"},
]


def vorname_passt(a, b):
    """Vornamen gleich, Variante, oder einer im anderen enthalten."""
    fa, fb = falte(a), falte(b)
    if not fa or not fb:
        return False
    if fa == fb:
        return True
    for g in GLEICH:
        if fa in g and fb in g:
            return True
    # Rufname innerhalb mehrteiliger Vornamen
    ta, tb = set(fa.split()), set(fb.split())
    if ta & tb:
        return True
    return False


def nachname_passt(a, b):
    fa, fb = falte(a), falte(b)
    if not fa or not fb:
        return False
    if fa == fb:
        return True
    # gemeinsame Normalform laut mapping_familiennamen
    n = kanonisch(a)
    m = kanonisch(b)
    return bool(n and m and falte(n) == falte(m))


@lru_cache(maxsize=8192)
def kanonisch(name):
    if not name:
        return None
    r = con().execute(
        "SELECT normalized FROM mapping_familiennamen WHERE original=? LIMIT 1",
        (name,)).fetchone()
    return r["normalized"] if r else None


# ------------------------------------------------------------------ Daten
def tage(datum):
    """ISO-Datum -> Tageszahl, für Differenzen. None wenn unvollständig."""
    if not datum:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(datum))
    if not m:
        return None
    j, mo, t = (int(x) for x in m.groups())
    if not mo or not t:
        return None
    return j * 372 + mo * 31 + t


def jahr(datum):
    m = re.match(r"(\d{4})", str(datum or ""))
    return int(m.group(1)) if m else None
