#!/usr/bin/env python3
"""Die Seite in lesbare Blöcke schneiden, bevor gelesen wird.

    python3 -m werkstatt.bloecke bilder/taufe/1184798-00359.jpg

**Warum überhaupt.** Eine Kirchenbuchseite dieses Bandes ist 5679 px breit
und trägt neun Spalten. Wer sie als ein Bild anschaut, bekommt sie
heruntergerechnet – bei 1500 px Anzeigebreite bleiben je Spalte gut
hundert Pixel, und Kurrent auf hundert Pixel ist kein Text mehr.

Gemessen an Seite 00359: Die Lesung füllte die vier linken Spalten und
notierte zu allen fünf rechten „steht auf der rechten Buchseite; im
vorliegenden Bildausschnitt nicht enthalten". Das war falsch – sie stehen
im selben Bild. Sie waren nur nicht lesbar angekommen, und das Modell hat
sich die Lücke plausibel erklärt, statt sie zu melden. Verloren gingen
dabei Geburtsdatum, Taufdatum, Taufender, Paten und der Verweis ins
Familienregister, also die wertvollsten Anker der Seite.

**Was hier geschnitten wird.** Je Eintragszeile zwei Blöcke, links und
rechts vom Bund. Jeder ist rund 2800 px breit und behält damit fast die
volle Auflösung, wenn er mit 2576 px Kante angeschaut wird.

Die Zeile bleibt zusammen – das ist die Regel „Kontext ist Teil der
Information". Getrennt wird nur am Bund, und beide Hälften gehören im
Auftrag zusammen, weil sie derselbe Eintrag sind. Dazu kommt der
gedruckte Spaltenkopf als eigener Block: Ohne ihn weiß niemand, dass die
dritte Spalte rechts „Wer die Tauf-Handlung verrichtete" heißt.
"""
import argparse
import json
from pathlib import Path

from . import konfig, raster

ORDNER = "bloecke"
# Die Buchkruemmung laesst den Text am Bund auslaufen. Ein Rand von 30 px
# an den Schnittkanten faengt das ab, ohne die Nachbarzeile hereinzuholen.
RAND = 30
# Der gedruckte Kopf steht ueber der ersten Zeilenlinie. Wie hoch er ist,
# schwankt; 1,4 Zeilenhoehen sind grosszuegig und schneiden nie hinein.
KOPF_FAKTOR = 1.4


def _bild(pfad):
    from PIL import Image
    return Image.open(pfad)


def _speichern(im, kasten, ziel, guete=88):
    x0, y0, x1, y1 = [int(v) for v in kasten]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(im.width, x1), min(im.height, y1)
    if x1 - x0 < 40 or y1 - y0 < 20:
        return None
    ziel.parent.mkdir(parents=True, exist_ok=True)
    im.crop((x0, y0, x1, y1)).save(ziel, quality=guete)
    return dict(datei=str(ziel), x=x0, y=y0, w=x1 - x0, h=y1 - y0)


def schneide(pfad, ziel_ordner=None, still=False, nur_kopf=False):
    """Eine Seite in Blöcke schneiden. Gibt die Beschreibung zurück.

    Ohne erkannte Zeilenlinien wird nichts geschnitten – dann ist der
    ehrliche Zustand „kein Raster", nicht ein willkürlich geteiltes Bild.
    """
    pfad = Path(pfad)
    r = raster.vorschlag(pfad)
    zeilen = sorted(r["zeilen"])
    seiten = r["seiten"]
    if len(zeilen) < 2 or not seiten:
        return dict(datei=pfad.name, bloecke=[], grund=(
            f"kein brauchbares Raster: {len(zeilen)} Zeilenlinien, "
            f"{len(seiten)} Buchseiten"))

    # Die unterste Zeile hat oft keine Schlusslinie – das Formular endet
    # am Papier, nicht an einem Strich. Ohne Ergaenzung faellt der letzte
    # Eintrag jeder Seite weg, und zwar lautlos.
    unten = max(s["y1"] for s in seiten)
    hoehen = [zeilen[i + 1] - zeilen[i] for i in range(len(zeilen) - 1)]
    mittel = sum(hoehen) / len(hoehen) if hoehen else 0
    if mittel and unten - zeilen[-1] > mittel * 0.6:
        zeilen = zeilen + [unten]

    ziel = Path(ziel_ordner or (pfad.parent / ORDNER / pfad.stem))
    im = _bild(pfad)
    # Die Haelften: was die Papiererkennung als Buchseiten gefunden hat.
    # Bei nur einer Seite bleibt es bei einer Haelfte – ein Register muss
    # nicht ueber den Bund laufen.
    haelften = [(s["x0"], s["x1"]) for s in seiten]
    namen = ["links", "rechts"][:len(haelften)] or ["ganz"]

    z = dict(datei=pfad.name, groesse=r["groesse"], falz=r["falz"],
             zeilen=zeilen, haelften=haelften, bloecke=[], kopf=[],
             spalten=[s["spalten"] for s in seiten])

    # Der gedruckte Spaltenkopf, einmal je Haelfte.
    hoehe = (zeilen[1] - zeilen[0]) if len(zeilen) > 1 else 400
    kopf_y0 = max(0, zeilen[0] - int(hoehe * KOPF_FAKTOR))
    for (x0, x1), name in zip(haelften, namen):
        b = _speichern(im, (x0 - RAND, kopf_y0, x1 + RAND, zeilen[0] + RAND),
                       ziel / f"kopf_{name}.jpg")
        if b:
            z["kopf"].append(dict(b, seite=name))

    # Beim Suchen der Formularperioden zaehlt nur der gedruckte Kopf. Die
    # Eintragszeilen dann nicht zu schneiden spart bei 16 Stichproben je
    # Register rund hundert ueberfluessige Bilddateien.
    if nur_kopf:
        (ziel / "raster.json").write_text(
            json.dumps(z, ensure_ascii=False, indent=1), encoding="utf-8")
        return z

    # Je Zeile eine Reihe von Blöcken.
    for i in range(len(zeilen) - 1):
        y0, y1 = zeilen[i], zeilen[i + 1]
        reihe = []
        for (x0, x1), name in zip(haelften, namen):
            b = _speichern(im, (x0 - RAND, y0 - RAND, x1 + RAND, y1 + RAND),
                           ziel / f"zeile{i + 1:02d}_{name}.jpg")
            if b:
                reihe.append(dict(b, seite=name))
        if reihe:
            z["bloecke"].append(dict(zeile=i + 1, teile=reihe))

    (ziel / "raster.json").write_text(
        json.dumps(z, ensure_ascii=False, indent=1), encoding="utf-8")
    if not still:
        print(f"  {pfad.name}: {len(z['bloecke'])} Zeilen à "
              f"{len(haelften)} Blöcke, Kopf {len(z['kopf'])}×")
        for b in z["bloecke"][:1]:
            for t in b["teile"]:
                print(f"    {t['seite']:7} {t['w']}×{t['h']} px  "
                      f"{konfig.kurz(t['datei'])}")
    return z


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bild", nargs="+")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    for b in a.bild:
        z = schneide(b, still=a.json)
        if a.json:
            print(json.dumps(z, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
