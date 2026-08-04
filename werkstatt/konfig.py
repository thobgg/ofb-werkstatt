#!/usr/bin/env python3
"""Konfiguration laden. Alles Ortsspezifische steht in konfig.toml,
nicht im Code — Registerarten, Felder, Vorbelegungen, Bestandsdatei."""
import tomllib
from functools import lru_cache
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
DATEI = WURZEL / "konfig.toml"
LOKAL = WURZEL / "konfig.local.toml"


def _misch(grund, oben):
    """Abschnittsweise überschreiben, nicht die ganze Datei ersetzen."""
    raus = dict(grund)
    for k, v in oben.items():
        if isinstance(v, dict) and isinstance(raus.get(k), dict):
            raus[k] = _misch(raus[k], v)
        else:
            raus[k] = v
    return raus


@lru_cache(maxsize=1)
def konfig():
    """konfig.toml, darüber konfig.local.toml.

    Die lokale Datei steht in .gitignore. Dort stehen die eigenen Bestände
    mit ihren Pfaden — die gehören niemandem sonst und dürfen in kein Repo.
    Die eingecheckte konfig.toml bleibt damit das Beispiel, das jeder liest.
    """
    if not DATEI.exists():
        raise SystemExit(f"konfig.toml fehlt: {DATEI}")
    with DATEI.open("rb") as f:
        k = tomllib.load(f)
    if LOKAL.exists():
        with LOKAL.open("rb") as f:
            k = _misch(k, tomllib.load(f))
    return k


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


# ------------------------------------------------------------ Kontextquellen
RAENGE = ("beleg", "vokabular")


def kontext():
    """Die Quellen, mit denen abgeglichen wird — samt Rang.

    Der Rang ist die eine Angabe, die über die Ampel entscheidet:

        beleg      darf bestätigen  -> ein Treffer macht grün
        vokabular  rankt nur        -> ein Treffer bleibt gelb

    Ein Bestand kann beides sein. `kirchenbuch.db` belegt für Haberschlacht
    und Neipperg und ist für die übrigen 32 Parochien nur Wortschatz; dafür
    wird er zweimal eingetragen, je einmal mit `parochien` und mit `sonst`.

    Keine Quelle eingetragen heißt Nullstart: alles bleibt gelb, die Maske
    legt jedes Feld vor. Langsamer, aber nicht falsch.
    """
    raus = []
    for q in konfig().get("kontext", []) or []:
        rang = (q.get("gilt") or "vokabular").lower()
        if rang not in RAENGE:
            raise SystemExit(
                f"kontext {q.get('name')!r}: gilt={rang!r} — erlaubt: "
                + ", ".join(RAENGE))
        pfad = q.get("datei", "")
        raus.append(dict(
            name=q.get("name") or Path(pfad).name or "(ohne Namen)",
            art=(q.get("art") or "gedcom").lower(),
            datei=str(Path(pfad).expanduser()) if pfad else "",
            gilt=rang,
            parochien=[p.strip() for p in (q.get("parochien") or []) if p.strip()],
            sonst=(q.get("sonst") or "").lower() or None,
            bis_jahr=q.get("bis_jahr"),
        ))
    return raus
