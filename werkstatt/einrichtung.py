#!/usr/bin/env python3
"""Das erste Mal: aus einem leeren Ordner ein Projekt machen.

Bisher war der Einstieg eine Datei. Wer die Werkstatt frisch auspackte,
sah „Musterhausen" und leere Register und musste erst `konfig.local.toml`
von Hand schreiben — genau dort bricht ab, wer kein Programmierer ist.

Hier wird dieselbe Datei geschrieben, nur aus drei Angaben: wie die
Gemeinde heißt, welche Register geführt werden, wo die Scans liegen.
Alles Weitere bleibt, wo es steht: Feldlisten, Rollen und Kaskaden stehen
in `konfig.toml` und sind nichts, was man beim ersten Start entscheidet.

**Ein Projekt ist ein Ordner.** Eine zweite Pfarrei bekommt eine zweite
Auspackung — eigene Datenbank, eigene Bilder, eigene lokale Konfiguration.
Das ist keine Notlösung, sondern hält zwei Bestände sauber getrennt; nichts
kann versehentlich vom einen in den anderen wandern.
"""
import re
from pathlib import Path

from . import konfig


def eingerichtet():
    """Steht schon ein eigener Name da, oder noch das Beispiel?"""
    return konfig.LOKAL.exists() and bool(
        (konfig.konfig().get("gemeinde") or {}).get("name")
        ) and konfig.konfig()["gemeinde"]["name"] != "Musterhausen"


def _wert(s):
    """Eine Zeichenkette so einpacken, dass TOML sie wieder herausbekommt.

    Von Hand, weil die Standardbibliothek TOML nur lesen kann. Es geht
    ausschließlich um Zeichenketten — deshalb reicht der einfache
    Grundstock: Rückstrich und Anführungszeichen schützen, Steuerzeichen
    fliegen raus.
    """
    s = re.sub(r"[\x00-\x1f]", " ", str(s)).strip()
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def schreibe(gemeinde, register, ort=None, religion=None):
    """konfig.local.toml erzeugen. Gibt den geschriebenen Text zurück.

    `register` ist eine Liste aus `{art, ordner}`. Nur bekannte Arten
    werden übernommen — eine erfundene hätte keine Feldliste und würde
    beim ersten Lesen scheitern, dann aber unverständlich.
    """
    bekannt = list(konfig.register())
    zeilen = [
        "# Lokale Konfiguration — steht in .gitignore und geht in kein Repo.",
        "# Von der Einrichtung geschrieben; von Hand ändern ist erlaubt.",
        "",
        "[gemeinde]",
        f"name        = {_wert(gemeinde)}",
        f"ort_default = {_wert(ort or gemeinde)}",
    ]
    if religion:
        zeilen.append(f"religion_default = {_wert(religion)}")
    genommen = []
    for r in register:
        art = (r.get("art") or "").strip()
        if art not in bekannt:
            continue
        ordner = (r.get("ordner") or "").strip()
        if not ordner:
            continue
        zeilen += ["", f"[register.{art}]", f"ordner = {_wert(ordner)}"]
        genommen.append(art)
    if not genommen:
        raise SystemExit("Kein Register mit Bildordner angegeben.")
    text = "\n".join(zeilen) + "\n"
    konfig.LOKAL.write_text(text, encoding="utf-8")
    # Die Konfiguration wird einmal gelesen und gemerkt. Ohne das Leeren
    # arbeitet der laufende Server bis zum Neustart mit „Musterhausen"
    # weiter — und niemand versteht, warum die Einrichtung nichts bewirkt.
    konfig.konfig.cache_clear()
    return text


def vorschlag():
    """Was die Einrichtung anbietet, wenn sie nichts weiß."""
    return [dict(art=art,
                 titel=(konfig.register(art) or {}).get("titel", art),
                 ordner=(konfig.register(art) or {}).get(
                     "ordner", f"bilder/{art}"))
            for art in konfig.register()]
