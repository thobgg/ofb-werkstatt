#!/usr/bin/env python3
"""Rastererkennung gegen die Sollwerte messen.

Die Sollwerte in `daten/soll_zeilen.json` sind aus den von Hand geschnittenen
Eintragsstreifen zurueckgewonnen, nicht direkt abgelesen – ihre eigene
Genauigkeit liegt bei etwa +-40 px. Deshalb werden mehrere Toleranzen
ausgewiesen statt einer einzigen Zahl.

Getrennt gezaehlt wird, was das Verfahren leisten kann:

    Linien   22 gedruckte Zeilenlinien -> Linienerkennung, exakt messbar
    Papier    4 Seitenunterkanten      -> nur als Schranke pruefbar

Die vierte Zahl je Seite ist das **Ende der Erfassung**, nicht die
Papierkante: auf 00363 und 00364 laeuft die Tabelle darunter leer bis zum
Papierende weiter. Sie taugt deshalb nur als untere Schranke – die erkannte
Papierkante muss darunter liegen, sonst waere das Formular abgeschnitten.

Ueberzaehlige Vorschlaege werden mitgezaehlt: falsche Linien kosten
Pruefzeit, richtige sparen sie. Beides gehoert nebeneinander.

    python3 -m werkstatt.messung
"""
import json
from pathlib import Path

from . import raster

WURZEL = Path(__file__).resolve().parent.parent
SOLL = WURZEL / "daten" / "soll_zeilen.json"
BILDER = WURZEL / "bilder" / "taufe"
TOLERANZEN = (25, 40, 60)


def treffer(gefunden, sollwerte, tol):
    return sum(any(abs(g - s) <= tol for g in gefunden) for s in sollwerte)


def main():
    d = json.loads(SOLL.read_text(encoding="utf-8"))
    ges = {t: [0, 0] for t in TOLERANZEN}
    schranke = [0, 0]
    ueberzaehlig = 0

    for nr, s in sorted(d["seiten"].items()):
        bild = BILDER / s["bild"]
        if not bild.exists():
            print(f"{nr}: Bild fehlt – uebersprungen")
            continue
        v = raster.vorschlag(bild)
        gef = v["zeilen"]
        unten = [b["y1"] for b in v["seiten"]]

        print(f"\n=== {nr}   Falz {v['falz']}   Buchseiten "
              f"{[(b['x0'], b['x1']) for b in v['seiten']]}")
        print(f"  Formular-x soll {s['formular_x']}")
        print(f"  Linien gefunden ({len(gef):2}): {gef}")
        print(f"  Linien soll     ({len(s['linien']):2}): {s['linien']}")
        ok = bool(unten) and min(unten) >= s["ende_erfassung"]
        schranke[0] += ok
        schranke[1] += 1
        print(f"  Papierkante unten: gefunden {unten}  "
              f">= Ende der Erfassung {s['ende_erfassung']}: {'ja' if ok else 'NEIN'}")

        for t in TOLERANZEN:
            ges[t][0] += treffer(gef, s["linien"], t)
            ges[t][1] += len(s["linien"])
        print("  Treffer: " + "  ".join(
            f"±{t}px {treffer(gef, s['linien'], t)}/{len(s['linien'])}"
            for t in TOLERANZEN))

        lo, hi = min(s["linien"]) - 60, max(s["linien"]) + 60
        drin = [g for g in gef if lo <= g <= hi]
        u = sum(not any(abs(g - x) <= 40 for x in s["linien"]) for g in drin)
        ueberzaehlig += u
        print(f"  ueberzaehlig im Eintragsbereich (±40px): {u}")

    print("\n" + "=" * 58)
    for t in TOLERANZEN:
        a, b = ges[t]
        print(f"  ±{t:2}px   Linien {a:2}/{b}  = {100*a/b:3.0f} %")
    print(f"  Papierkante unterhalb der Erfassung: {schranke[0]}/{schranke[1]}")
    print(f"  ueberzaehlige Vorschlaege gesamt: {ueberzaehlig}")
    print(f"\n  Hinweis: {d['genauigkeit']}")


if __name__ == "__main__":
    main()
