#!/usr/bin/env python3
"""Seitenraster: Spalten je Buch, Zeilen je Seite.

Daraus ergibt sich für jedes Feld der Bildausschnitt — deterministisch,
ohne dass ein Modell Koordinaten schätzen muss.

GESCHEITERT — nicht erneut versuchen.

Die Funktionen unten suchen die gedruckten Tabellenlinien über die längste
dunkle Lauflänge je Bildzeile. Gemessen an einer Seite mit sieben von Hand
abgelesenen Zeilengrenzen findet das Verfahren **eine**. 14 Prozent sind zu
wenig, um überhaupt als Vorschlag zu taugen — falsche Linien kosten mehr
Prüfzeit, als richtige einsparen.

Vorherige gescheiterte Versuche im Projekt: Zeilenerkennung per Projektion,
proportional übertragene Zeilenraster. Dies ist der vierte.

Grund: Die Linien sind unterschiedlich kräftig gezogen, teils verblasst, und
laufen jeweils nur über eine Buchseite — über die Doppelseite gemessen wird
ihre relative Länge zu klein.

**Stattdessen von Hand, aber mit Vererbung:**
  Spalten  einmal je Buch ziehen — das Formular ist über Jahrzehnte gleich
  Zeilen   auf der ersten Seite ziehen, auf Folgeseiten übernehmen und
           nur nachjustieren

Der Code bleibt als Beleg der Messung stehen.

    python3 -m kirchenbuch.raster bilder/taufe/seite.jpg
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from . import db, konfig


def papier(a, seiten=2):
    """Papierblock finden und in Buchseiten teilen (Scanränder weg)."""
    mz, ms = np.median(a, axis=1), np.median(a, axis=0)
    ys = np.where(mz > 0.6 * mz.max())[0]
    xs = np.where(ms > 0.6 * ms.max())[0]
    if not len(ys) or not len(xs):
        return []
    yb = np.split(ys, np.where(np.diff(ys) > 60)[0] + 1)
    yg = max(yb, key=len)
    xb = [b for b in np.split(xs, np.where(np.diff(xs) > 120)[0] + 1) if len(b) > 200]
    xb.sort(key=len, reverse=True)
    xb = sorted(xb[:seiten], key=lambda b: b[0])
    return [(int(b[0]), int(b[-1]), int(yg[0]), int(yg[-1])) for b in xb]


def waagerecht(aus, mindest=0.40, schwelle=180, luecke=12):
    """Waagerechte Tabellenlinien über die längste dunkle Lauflänge."""
    h, w = aus.shape
    dunkel = aus < schwelle
    lang = np.empty(h)
    for y in range(h):
        d = np.diff(np.concatenate(([0], dunkel[y].view(np.int8), [0])))
        s = np.where(d == 1)[0]
        e = np.where(d == -1)[0]
        lang[y] = (e - s).max() / w if len(s) else 0
    kand = np.where(lang > mindest)[0]
    gruppen, akt = [], []
    for y in kand:
        if akt and y - akt[-1] <= luecke:
            akt.append(y)
        else:
            if akt:
                gruppen.append(akt)
            akt = [y]
    if akt:
        gruppen.append(akt)
    return [(int(np.mean(g)), float(lang[g].max())) for g in gruppen]


def senkrecht(aus, mindest=0.30, schwelle=180, luecke=12):
    """Senkrechte Spaltenlinien — dieselbe Idee, um 90 Grad gedreht."""
    return waagerecht(aus.T, mindest, schwelle, luecke)


def vorschlag(pfad, seiten=2):
    """Rastervorschlag für eine Seite. Bewusst unvollständig."""
    a = np.asarray(Image.open(pfad).convert("L"))
    raus = []
    for x0, x1, y0, y1 in papier(a, seiten):
        aus = a[y0:y1, x0:x1]
        raus.append(dict(
            x0=x0, x1=x1, y0=y0, y1=y1,
            zeilen=[y + y0 for y, _ in waagerecht(aus)],
            spalten=[x + x0 for x, _ in senkrecht(aus)],
        ))
    return dict(datei=Path(pfad).name, groesse=list(a.shape[::-1]), seiten=raus)


def ausschnitt(raster, seite, zeile, spalte, rand=25):
    """Bildausschnitt für Zelle (Zeile, Spalte) — Basis der Lupe."""
    s = raster["seiten"][seite]
    zs, sp = sorted(s["zeilen"]), sorted(s["spalten"])
    y0 = zs[zeile] if zeile < len(zs) else s["y0"]
    y1 = zs[zeile + 1] if zeile + 1 < len(zs) else s["y1"]
    x0 = sp[spalte] if spalte < len(sp) else s["x0"]
    x1 = sp[spalte + 1] if spalte + 1 < len(sp) else s["x1"]
    return (max(0, x0 - rand), max(0, y0 - rand),
            (x1 - x0) + 2 * rand, (y1 - y0) + 2 * rand)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bild")
    ap.add_argument("--seiten", type=int, default=2)
    a = ap.parse_args()
    v = vorschlag(a.bild, a.seiten)
    print(f"{v['datei']}  {v['groesse'][0]}x{v['groesse'][1]}")
    for i, s in enumerate(v["seiten"]):
        print(f"  Buchseite {i+1}: x{s['x0']}–{s['x1']}  y{s['y0']}–{s['y1']}")
        print(f"    Zeilenlinien  ({len(s['zeilen']):2}): {s['zeilen']}")
        print(f"    Spaltenlinien ({len(s['spalten']):2}): {s['spalten']}")
    print("\nVorschlag — unvollständig. Im Editor nachziehen und bestätigen.")


if __name__ == "__main__":
    main()
