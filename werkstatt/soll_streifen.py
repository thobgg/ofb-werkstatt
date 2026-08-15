#!/usr/bin/env python3
"""Sollwerte aus von Hand geschnittenen Eintragsstreifen zurueckgewinnen.

Wer eine Seite von Hand in Eintragsstreifen zerlegt hat, besitzt damit bereits
abgelesene Zeilengrenzen – sie stecken in den Streifen. Dieses Skript sucht
jeden Streifen per Kreuzkorrelation im vollen Seitenscan wieder und leitet
aus den Fundstellen die Grenzen ab.

    Streifen n endet bei y1, Streifen n+1 beginnt bei y0  ->  Grenze = Mitte

**Genauigkeit.** Nur so gut wie der Schnitt. Wurden die Streifen grosszuegig
um den *Text* geschnitten statt an den Linien, betraegt der Versatz zur
tatsaechlichen gedruckten Linie bis zu 45 px – gemessen an den vier
Taufregisterseiten. Fuer eine strengere Messung muessen die Grenzen von Hand
abgelesen und in `daten/soll_zeilen.json` nachgetragen werden.

Die erste und letzte Grenze je Seite sind Schnittkanten, keine Linien: die
letzte ist das **Ende der Erfassung**, nicht die Papierkante – unter dem
letzten beschriebenen Eintrag laeuft die Tabelle oft leer weiter.

    python3 -m werkstatt.soll_streifen bilder/taufe scans/zeilen \
        --muster '(\\d+)_(\\d+)\\.jpg' --seite '1184798-{}.jpg'
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.signal import fftconvolve

SKALA = 4


def _grau(pfad, skala):
    b = Image.open(pfad).convert("L")
    k = b.resize((b.width // skala, b.height // skala), Image.BILINEAR)
    return np.asarray(k, dtype=np.float64), b.size


def kreuzkorrelation(gross, klein):
    """Beste Fundstelle von `klein` in `gross`. Gibt (y, x, guete)."""
    k = klein - klein.mean()
    zaehler = fftconvolve(gross, k[::-1, ::-1], mode="valid")
    eins = np.ones_like(klein)
    s1 = fftconvolve(gross, eins[::-1, ::-1], mode="valid")
    s2 = fftconvolve(gross ** 2, eins[::-1, ::-1], mode="valid")
    n = klein.size
    var = np.maximum(s2 - s1 ** 2 / n, 1e-9)
    r = zaehler / np.sqrt(var * (k ** 2).sum() + 1e-9)
    y, x = np.unravel_index(np.argmax(r), r.shape)
    return int(y), int(x), float(r[y, x])


def finde(seiten_ordner, streifen_ordner, muster, seitenname, mindestguete=0.85):
    fund = {}
    for s in sorted(Path(streifen_ordner).glob("*.jpg")):
        m = re.match(muster, s.name)
        if not m:
            continue
        nr, eintrag = m.group(1), int(m.group(2))
        seite = Path(seiten_ordner) / seitenname.format(nr)
        if not seite.exists():
            print(f"  {s.name}: Seite {seite.name} fehlt")
            continue
        g, _ = _grau(seite, SKALA)
        k, (kb, kh) = _grau(s, SKALA)
        y, x, guete = kreuzkorrelation(g, k)
        if guete < mindestguete:
            print(f"  {s.name}: Guete {guete:.2f} zu niedrig – uebersprungen")
            continue
        fund.setdefault(nr, []).append(
            dict(eintrag=eintrag, y0=y * SKALA, y1=y * SKALA + kh,
                 x0=x * SKALA, breite=kb, guete=round(guete, 4)))
        print(f"  {s.name:16} y {y*SKALA:5}–{y*SKALA+kh:5}  x0 {x*SKALA:5}  r={guete:.3f}")
    return fund


def grenzen(fund):
    seiten = {}
    for nr, e in fund.items():
        e = sorted(e, key=lambda t: t["y0"])
        g = [e[0]["y0"]]
        for a, b in zip(e, e[1:]):
            g.append(round((a["y1"] + b["y0"]) / 2))
        seiten[nr] = dict(
            eintraege=[t["eintrag"] for t in e],
            formular_x=[e[0]["x0"], e[0]["x0"] + e[0]["breite"]],
            linien=g,
            ende_erfassung=e[-1]["y1"])
    return seiten


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("seiten")
    ap.add_argument("streifen")
    ap.add_argument("--muster", default=r"(\d+)_(\d+)\.jpg",
                    help="Regex mit Gruppe 1 = Seitennummer, 2 = Eintragsnummer")
    ap.add_argument("--seite", default="{}.jpg",
                    help="Dateiname der Seite, {} = Seitennummer")
    ap.add_argument("--ziel", default="daten/soll_zeilen.json")
    a = ap.parse_args()

    fund = finde(a.seiten, a.streifen, a.muster, a.seite)
    if not fund:
        print("nichts gefunden")
        return
    s = grenzen(fund)
    n = sum(len(v["linien"]) for v in s.values())
    print(f"\n{len(s)} Seiten, {n} Linien, {len(s)} Enden der Erfassung")
    Path(a.ziel).write_text(json.dumps(dict(seiten=s), indent=2,
                                       ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"-> {a.ziel}  (Herkunfts- und Genauigkeitshinweise von Hand ergaenzen)")


if __name__ == "__main__":
    main()
