#!/usr/bin/env python3
"""Konfiguration laden. Alles Ortsspezifische steht in konfig.toml,
nicht im Code — Registerarten, Felder, Vorbelegungen, Bestandsdatei."""
import tomllib
from functools import lru_cache
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
DATEI = WURZEL / "konfig.toml"


@lru_cache(maxsize=1)
def konfig():
    if not DATEI.exists():
        raise SystemExit(f"konfig.toml fehlt: {DATEI}")
    with DATEI.open("rb") as f:
        return tomllib.load(f)


def register(art=None):
    """Alle Registerarten, oder eine bestimmte."""
    r = konfig().get("register", {})
    return r.get(art) if art else r


def felder(art):
    return register(art).get("felder", [])


def personen_rollen(art):
    return register(art).get("personen", [])


def datumsfelder(art):
    return register(art).get("datum", [])


def bilderordner(art):
    return WURZEL / register(art).get("ordner", f"bilder/{art}")


def vorbelegung():
    g = konfig().get("gemeinde", {})
    return {"ort": g.get("ort_default", ""),
            "religion": g.get("religion_default", "")}


def bestand():
    p = (konfig().get("bestand", {}) or {}).get("gedcom", "")
    return (WURZEL / p) if p else None
