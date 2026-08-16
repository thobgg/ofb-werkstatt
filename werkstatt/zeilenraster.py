#!/usr/bin/env python3
"""Aus gefundenen Linien ein Zeilenraster einpassen.

    python3 -m werkstatt.zeilenraster --soll        gegen die geprüften Seiten
    python3 -m werkstatt.zeilenraster demo/bilder/taufe/1184798-00359.jpg 6

**Warum das nötig war.** Der Streifen unter jedem Eintrag ist das, was der
Bearbeiter beim Entscheiden ansieht. Gemessen über die dreizehn
Beispielseiten wurden aber nur drei an gemessenen Linien geschnitten;
sieben wurden gleichmäßig geteilt, weil die Zahl der gefundenen Linien
nicht zur Zahl der Einträge passte.

Der Blick auf die Zahlen zeigte, dass das Problem nicht Blindheit ist,
sondern Überfluss. Auf Bild 1184799-00022 stehen 13 Linien für 8 nötige
Grenzen, und die Abstände lauten

    196, 396, 284, 64, 316, 240, 72, 284, 328, 68, 264, 64
                     ^^                ^^            ^^  ^^

Diese 64–72 px sind **Doppellinien**: der gedruckte Trennstrich besteht
aus zwei feinen Strichen, oder derselbe Strich wird an Ober- und
Unterkante erkannt. Sie wegzuwerfen und dafür gleichmäßig zu teilen,
verschenkt genau die Information, die da ist.

## Was hier passiert

1. **Verschmelzen.** Linien, die näher beieinander liegen als ein Drittel
   der erwarteten Zeilenhöhe, sind dieselbe Linie. Aus dem Paar wird die
   Mitte.
2. **Einpassen.** Ein Eintragsraster ist fast gleichmäßig: `y = a + b·i`.
   Aus je zwei Kandidaten wird ein solches Modell gebildet und gezählt,
   wie viele der übrigen dazu passen (RANSAC). Das Modell mit den meisten
   Treffern gewinnt.
3. **Einrasten.** Wo eine gemessene Linie in der Nähe liegt, gilt sie –
   nicht der gerechnete Wert. Nur wo keine ist, wird interpoliert. So
   bleibt die Genauigkeit der Messung erhalten, und geraten wird nur, was
   fehlt.

Die Güte sagt hinterher, wie viele der Grenzen gemessen und wie viele
gerechnet sind. Das steht auch in der Maske, denn ein gerechneter Schnitt
sieht aus wie ein gemessener.
"""
import argparse
import json
from pathlib import Path

TOLERANZ = 0.22          # Anteil der Zeilenhöhe, in dem eine Linie einrastet
DOPPELT = 0.34           # darunter sind zwei Linien dieselbe


def verschmelze(linien, hoehe):
    """Doppelt erkannte Linien zu einer machen."""
    if not linien:
        return []
    grenze = max(8.0, hoehe * DOPPELT)
    raus, gruppe = [], [linien[0]]
    for y in linien[1:]:
        if y - gruppe[-1] < grenze:
            gruppe.append(y)
        else:
            raus.append(sum(gruppe) / len(gruppe))
            gruppe = [y]
    raus.append(sum(gruppe) / len(gruppe))
    return [int(round(y)) for y in raus]


def _modelle(kand, anzahl):
    """Kandidatenpaare als (Anfang, Schrittweite) – jedes Paar eine Hypothese.

    Zwei Linien legen ein gleichmäßiges Raster fest, wenn man weiß, wie
    viele Zeilen dazwischenliegen. Da das unbekannt ist, wird jeder
    plausible Abstand durchprobiert.
    """
    for i in range(len(kand)):
        for j in range(i + 1, len(kand)):
            spanne = kand[j] - kand[i]
            for schritte in range(1, anzahl + 1):
                b = spanne / schritte
                if b <= 0:
                    continue
                yield kand[i] - b * i * 0, b, kand[i], i, schritte


def passe_ein(linien, anzahl, papier, hoehe_vorgabe=None):
    """Genau `anzahl`+1 Grenzen. Rückgabe (grenzen, gemessen, hoehe).

    `gemessen` ist die Zahl der Grenzen, die auf einer wirklich gefundenen
    Linie sitzen; der Rest ist gerechnet.
    """
    y0, y1 = papier
    if not linien:
        h = (y1 - y0) / anzahl
        return [int(y0 + i * h) for i in range(anzahl + 1)], 0, h

    grob = (max(linien) - min(linien)) / max(1, len(linien) - 1)
    kand = verschmelze(sorted(linien), hoehe_vorgabe or grob)

    # Erwartete Zeilenhöhe: die Spanne der Kandidaten, verteilt auf die
    # Zahl der Einträge. Deckt auch den Fall ab, dass oben oder unten eine
    # Linie fehlt – dann ist die Schätzung etwas zu klein, und das Modell
    # gleicht es aus.
    spanne = kand[-1] - kand[0]
    h0 = hoehe_vorgabe or (spanne / max(1, anzahl))

    bestes, beste_zahl = None, -1
    for _, b, anker, _, _ in _modelle(kand, anzahl + 1):
        if not (0.55 * h0 <= b <= 1.9 * h0):
            continue
        for start in range(0, anzahl + 1):
            a = anker - b * start
            if a < y0 - b or a > y1:
                continue
            soll = [a + b * i for i in range(anzahl + 1)]
            tol = b * TOLERANZ
            treffer = sum(1 for s in soll
                          if any(abs(s - k) <= tol for k in kand))
            # Ein Raster, das über das Papier hinausragt, ist keins.
            strafe = sum(1 for s in soll if s < y0 - tol or s > y1 + tol)
            # Wie viel der beschriebenen Fläche das Raster überhaupt
            # abdeckt. Ohne diesen Term gewann auf Bild 00919 ein Raster
            # mit halber Zeilenhöhe: Es traf ebenso viele Linien, füllte
            # aber nur ein Drittel der Seite, und der Streifen zeigte die
            # obere Hälfte eines Eintrags.
            deckung = min(1.0, (b * anzahl) / max(1.0, y1 - y0))
            wert = treffer - 2 * strafe + 1.5 * deckung
            if wert > beste_zahl:
                beste_zahl, bestes = wert, (a, b)
    if bestes is None:
        h = (y1 - y0) / anzahl
        return [int(y0 + i * h) for i in range(anzahl + 1)], 0, h

    a, b = bestes
    grenzen, gemessen = [], 0
    tol = b * TOLERANZ
    for i in range(anzahl + 1):
        s = a + b * i
        nah = [k for k in kand if abs(k - s) <= tol]
        if nah:
            grenzen.append(int(round(min(nah, key=lambda k: abs(k - s)))))
            gemessen += 1
        else:
            grenzen.append(int(round(s)))
    # Monoton und im Papier halten.
    grenzen = sorted(grenzen)
    grenzen[0] = max(grenzen[0], int(y0))
    grenzen[-1] = min(grenzen[-1], int(y1))
    return grenzen, gemessen, b


def fuer_bild(pfad, anzahl):
    """Zeilenraster einer Seite. Rückgabe (grenzen, gemessen, block)."""
    from . import raster
    v = raster.vorschlag(str(pfad))
    if not v["seiten"]:
        return [], 0, None
    block = dict(v["seiten"][0])
    block["x1"] = max(s["x1"] for s in v["seiten"])
    block["y0"] = min(s["y0"] for s in v["seiten"])
    block["y1"] = max(s["y1"] for s in v["seiten"])
    grenzen, gemessen, _ = passe_ein(
        sorted(v["zeilen"]), anzahl, (block["y0"], block["y1"]))
    return grenzen, gemessen, block


def _soll():
    """Gegen die von Hand geprüften Seiten messen."""
    from . import konfig
    p = konfig.WURZEL / "daten" / "soll_zeilen.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    orte = [konfig.WURZEL / "demo" / "bilder" / "taufe",
            konfig.WURZEL / "bilder" / "taufe"]
    gesamt = treffer40 = treffer80 = 0
    for name, s in d["seiten"].items():
        datei = next((o / s["bild"] for o in orte if (o / s["bild"]).exists()),
                     None)
        if not datei:
            print(f"  {name}: Bild fehlt")
            continue
        soll = s["linien"]
        grenzen, gemessen, _ = fuer_bild(datei, len(s["eintraege"]))
        # Die Wahrheit nennt die Oberkanten der Einträge; unsere Grenzen
        # sind eine mehr (die Unterkante der letzten Zeile).
        ist = grenzen[:len(soll)]
        ab = [abs(a - b) for a, b in zip(ist, soll)]
        gesamt += len(ab)
        treffer40 += sum(1 for x in ab if x <= 40)
        treffer80 += sum(1 for x in ab if x <= 80)
        print(f"  {name}  {len(soll)} Linien, {gemessen} von {len(grenzen)} "
              f"Grenzen gemessen")
        print(f"     soll {soll}")
        print(f"     ist  {ist}")
        print(f"     ab   {ab}  (max {max(ab)} px)")
    if gesamt:
        print(f"\n  {treffer40} von {gesamt} Linien auf ±40 px "
              f"({100*treffer40//gesamt} %), {treffer80} auf ±80 px "
              f"({100*treffer80//gesamt} %)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bild", nargs="?")
    ap.add_argument("anzahl", nargs="?", type=int)
    ap.add_argument("--soll", action="store_true")
    a = ap.parse_args()
    if a.soll or not a.bild:
        _soll()
        return
    grenzen, gemessen, block = fuer_bild(a.bild, a.anzahl)
    print(f"{len(grenzen)} Grenzen, davon {gemessen} gemessen:")
    print(f"  {grenzen}")
    print(f"  Höhen: {[b - a for a, b in zip(grenzen, grenzen[1:])]}")


if __name__ == "__main__":
    main()
