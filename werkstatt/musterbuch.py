#!/usr/bin/env python3
"""Nachgestellte Kirchenbuchseiten für die Demo – ohne fremde Rechte.

    python3 -m werkstatt.musterbuch            nach bilder/taufe/
    python3 -m werkstatt.musterbuch --ziel /tmp/probe

Die Werkstatt liest Bilder, und ohne Bilder kann sie niemand ausprobieren:
keine Streifen, kein Spaltenkopf, keine Seitenschau. Echte Scans dürfen
aber nicht mit. Urheberrechtlich wären Aufnahmen einer Seite von 1808
zwar frei – § 68 UrhG stellt originalgetreue Reproduktionen gemeinfreier
Werke selbst frei –, aber die Nutzungsbedingungen der Anbieter (hier
Ancestry) untersagen die Weitergabe unabhängig davon, und daran hängt der
Zugang des Bearbeiters. Das ist die bindende Schranke, nicht das
Urheberrecht.

Wo dasselbe Buch bei einem Anbieter mit freier Rechteangabe liegt – die
Deutsche Digitale Bibliothek führt die Haberschlachter Kirchenbücher bis
1807 –, wäre eine echte Seite erlaubt und besser als jede Nachstellung.
Diese Datei ist der Weg, der ohne solche Prüfung auskommt.

Also werden Seiten **nachgestellt**: dieselbe Spaltenaufteilung wie das
württembergische Normalformular ab 1808, gefüllt mit den Pilotlesungen,
die ohnehin mitfahren. Das ist kein Faksimile und will keins sein – die
Schrift ist gesetzt, nicht Kurrent. Was es zeigt, ist die **Mechanik**:
Zeilenerkennung, Spaltenblöcke, Kopfband, Streifen, Seitenschau.

Ein angenehmer Nebeneffekt: Weil Seite und Lesung aus derselben Quelle
kommen, steht im Streifen wirklich das, was im Feld daneben steht. Bei
einem fremden Scan wäre die Demo ein Nebeneinander zweier Dinge, die
nichts miteinander zu tun haben.
"""
import argparse
import json
from pathlib import Path

from . import konfig

# Das Normalformular: neun Spalten, vier links vom Bund, fünf rechts –
# abgelesen am gedruckten Kopf, nicht erfunden. Die Breiten sind Anteile.
SPALTEN_LINKS = [
    ("Zahl\nder\nGebor-\nnen.", 0.07, ["lfd_nr"]),
    ("Taufnamen\ndes\nKindes.", 0.20, ["kind_vorname", "randvermerk"]),
    ("Eltern.", 0.53, ["_eltern"]),
    ("Ort\nder\nGeburt.", 0.20, ["geburt_ort"]),
]
SPALTEN_RECHTS = [
    ("Zeit\nder\nGeburt.", 0.15, ["geburt_datum", "geburt_zeit"]),
    ("Ort\nund Tag\nder\nTaufe.", 0.17, ["tauf_ort", "tauf_datum"]),
    ("Wer\ndie\nTauf-Handlung\nverrichtete.", 0.17, ["taufender"]),
    ("Tauf - Zeugen.", 0.42, ["paten"]),
    ("Seitenzahl\ndes\nFamilien-\nRegisters.", 0.09, ["fam_reg"]),
]

BREITE, HOEHE = 4000, 3100
RAND = 140
BUND = 90                      # Lücke in der Mitte, wie am Buchrücken
KOPF_H = 300


def _schrift(groesse, fett=False, hand=False):
    from PIL import ImageFont
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSerif"
         + ("-Bold" if fett else "") + ".ttf")
    if hand:
        p = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"
    try:
        return ImageFont.truetype(p, groesse)
    except Exception:
        return ImageFont.load_default()


def _umbrechen(zeichner, text, schrift, breite):
    """Text auf die Spaltenbreite umbrechen."""
    worte, zeilen, jetzt = str(text or "").split(), [], ""
    for w in worte:
        probe = (jetzt + " " + w).strip()
        if zeichner.textlength(probe, font=schrift) > breite and jetzt:
            zeilen.append(jetzt)
            jetzt = w
        else:
            jetzt = probe
    if jetzt:
        zeilen.append(jetzt)
    return zeilen


def _eltern(f):
    """Die Elternspalte, wie sie im Buch steht – ein Fließtext."""
    v = f.get("vater_name", {}).get("wert") or ""
    beruf = f.get("vater_beruf", {}).get("wert") or ""
    m = f.get("mutter_name", {}).get("wert") or ""
    geb = (f.get("mutter_geborene", {}).get("kb")
           or f.get("mutter_geborene", {}).get("wert") or "")
    # Die Kirchenbuchform enthaelt das "geb." oft schon.
    geb = geb.strip()
    for vor in ("geb.", "geb", "geborene", "geborne"):
        if geb.lower().startswith(vor):
            geb = geb[len(vor):].strip(" .")
            break
    her = f.get("mutter_herkunft", {}).get("wert") or ""
    z = ", ".join(x for x in (v, beruf) if x)
    if m:
        z += f", und {m}"
        if geb:
            z += f" geb. {geb}"
    if her:
        z += f", {her}"
    return z


def _wert(f, namen, e=None):
    if namen == ["_eltern"]:
        return _eltern(f)
    if namen == ["lfd_nr"]:
        # Die laufende Nummer steht am Eintrag, nicht in den Feldern.
        return str((e or {}).get("lfd_nr") or "")
    return "  ".join(str(f.get(n, {}).get("wert") or "") for n in namen).strip()


def seite(eintraege, ziel, titel="1808"):
    """Eine Doppelseite zeichnen."""
    from PIL import Image, ImageDraw
    im = Image.new("L", (BREITE, HOEHE), 246)
    d = ImageDraw.Draw(im)

    x0, x1 = RAND, BREITE - RAND
    mitte = BREITE // 2
    haelften = [(x0, mitte - BUND // 2, SPALTEN_LINKS),
                (mitte + BUND // 2, x1, SPALTEN_RECHTS)]

    y_kopf = RAND
    y_erste = RAND + KOPF_H
    hoehe = (HOEHE - RAND - y_erste) // max(1, len(eintraege))

    kopfschrift = _schrift(30, fett=True)
    handschrift = _schrift(34, hand=True)

    for hx0, hx1, spalten in haelften:
        gesamt = sum(s[1] for s in spalten)
        x = hx0
        grenzen = [x]
        for _, anteil, _ in spalten:
            x += int((hx1 - hx0) * anteil / gesamt)
            grenzen.append(x)
        grenzen[-1] = hx1

        # Rahmen und Spaltenlinien – die kraeftigen Striche, an denen
        # raster.py sein Gitter findet.
        d.rectangle([hx0, y_kopf, hx1, HOEHE - RAND], outline=0, width=5)
        for g in grenzen[1:-1]:
            d.line([(g, y_kopf), (g, HOEHE - RAND)], fill=0, width=4)
        d.line([(hx0, y_erste), (hx1, y_erste)], fill=0, width=6)

        for i, (ueber, _, _) in enumerate(spalten):
            mx = (grenzen[i] + grenzen[i + 1]) // 2
            zeilen = ueber.split("\n")
            ty = y_kopf + (KOPF_H - len(zeilen) * 38) // 2
            for z in zeilen:
                d.text((mx - d.textlength(z, font=kopfschrift) / 2, ty), z,
                       fill=0, font=kopfschrift)
                ty += 38

        for n, e in enumerate(eintraege):
            oben = y_erste + n * hoehe
            d.line([(hx0, oben), (hx1, oben)], fill=0, width=4)
            f = e.get("felder", {})
            for i, (_, _, namen) in enumerate(spalten):
                text = _wert(f, namen, e)
                if not text:
                    continue
                bx = grenzen[i] + 14
                bw = grenzen[i + 1] - grenzen[i] - 28
                ty = oben + 20
                for z in _umbrechen(d, text, handschrift, bw):
                    if ty > oben + hoehe - 40:
                        break
                    d.text((bx, ty), z, fill=25, font=handschrift)
                    ty += 44

    # "a. 1808" steht im Original im Kopf der Elternspalte, nicht mitten
    # auf der Seite – dort ueberdeckte es die Nachbarueberschrift.
    hx0, _, spalten = haelften[0]
    anteil = sum(s[1] for s in spalten[:2]) / sum(s[1] for s in spalten)
    breite = haelften[0][1] - hx0
    d.text((hx0 + breite * anteil + 60, y_kopf + KOPF_H // 2 + 10),
           f"a. {titel}", fill=0, font=_schrift(40, fett=True))
    ziel.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(ziel, quality=90)
    return ziel


def erzeuge(ziel_ordner=None, still=False):
    """Aus den mitgelieferten Pilotlesungen ein Musterbuch zeichnen."""
    quelle = konfig.WURZEL / "daten" / "pilot.json"
    if not quelle.exists():
        raise SystemExit(f"{quelle} fehlt – ohne Lesungen keine Musterseiten")
    d = json.loads(quelle.read_text(encoding="utf-8"))
    ziel = Path(ziel_ordner or (konfig.WURZEL / "bilder" / d.get("register",
                                                                "taufe")))
    raus = []
    for bild, inhalt in sorted(d.get("seiten", {}).items()):
        es = inhalt.get("eintraege", [])
        p = seite(es, ziel / f"muster-{bild}.jpg",
                  titel=str(es[0].get("jahr") or 1808) if es else "1808")
        raus.append(p)
        if not still:
            print(f"  {konfig.kurz(p)} – {len(es)} Einträge")
    return raus


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ziel")
    a = ap.parse_args()
    fs = erzeuge(a.ziel)
    print(f"{len(fs)} Musterseiten. Sie sind **nachgestellt**, kein Faksimile "
          "– gesetzte Schrift statt Kurrent.")


if __name__ == "__main__":
    main()
