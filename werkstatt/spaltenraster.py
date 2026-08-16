#!/usr/bin/env python3
"""Das Spaltenraster einer Formularperiode – vorgeschlagen, vom Menschen bestätigt.

    python3 -m werkstatt.spaltenraster taufe          Vorschlag anzeigen
    python3 -m werkstatt.spaltenraster taufe --merken  und übernehmen

**Warum das anders läuft als bei den Zeilen.** Zeilen wechseln mit jeder
Seite: mal sechs Einträge, mal acht, und die Höhen schwanken um ein
Drittel. Deshalb wird das Zeilenraster je Seite neu eingepasst
(`zeilenraster.py`).

Spalten wechseln nicht. Das Formular ist **gedruckt**; innerhalb einer
Formularperiode stehen die Trennstriche auf jeder Seite an derselben
Stelle. Gemessen an den fünf Taufseiten der Demo, relativ zur Breite der
Buchhälfte:

    0.000  0.013  0.066  0.265  0.830
    0.002  0.013  0.067  0.264  0.828
    0.002         0.066  0.264  0.817
    0.002  0.013  0.066  0.264  0.819
    0.000         0.064  0.265  0.829

Das ist auf drei Nachkommastellen dasselbe. Deshalb genügt es, das Raster
**einmal je Periode** festzulegen.

**Warum es trotzdem nicht vollautomatisch geht.** Die Abstimmung über
mehrere Seiten liefert bei der Taufe 9 von 10 Linien, beim Sterberegister
eine zu viel und beim Eheregister drei zu wenig. Automatische
Spaltenerkennung ist in diesem Projekt zweimal gescheitert; ein Vorschlag,
den ein Mensch in zwei Minuten je Buch geraderückt, ist der ehrlichere
Weg. Genau das meinte Hermann mit der Vorbereitungsphase je Quelle.

## Was gespeichert wird

Je Periode und Buchhälfte die **relativen** x-Werte (0 = linker Rand der
Hälfte, 1 = rechter). Relativ, weil Scans unterschiedlich beschnitten
sind und die Papiererkennung um ein paar Pixel schwankt; die Verhältnisse
bleiben.
"""
import argparse
import json

from . import db, perioden, seiten as _seiten, einstellungen

NAH = 0.012              # relativer Abstand, ab dem zwei Linien dieselbe sind


def _relative_linien(pfad):
    """Spaltenlinien einer Seite, je Buchhälfte und relativ zur Breite."""
    from . import raster
    v = raster.vorschlag(str(pfad))
    raus = []
    for s in v["seiten"]:
        br = s["x1"] - s["x0"]
        if br <= 0:
            raus.append([])
            continue
        roh = sorted(round((x - s["x0"]) / br, 4) for x in s["spalten"])
        # Doppelt erkannte Striche derselben Seite erst zusammenfassen,
        # sonst stimmen sie in der Abstimmung zweimal ab - dann steht da
        # "11 von 8 Seiten".
        eins = []
        for x in roh:
            if eins and x - eins[-1] <= NAH:
                eins[-1] = round((eins[-1] + x) / 2, 4)
            else:
                eins.append(x)
        raus.append(eins)
    return raus


def stimme(proben, mindestanteil=0.6):
    """Aus vielen Seiten die Linien, die immer wiederkehren.

    Eine Linie, die auf drei von fünf Seiten an derselben Stelle steht,
    ist gedruckt. Eine, die nur einmal auftaucht, ist ein Tintenstrich,
    ein Falz oder ein Fleck.
    """
    haelften = max((len(p) for p in proben), default=0)
    raus = []
    for h in range(haelften):
        punkte = sorted(x for p in proben if len(p) > h for x in p[h])
        dabei = sum(1 for p in proben if len(p) > h)
        noetig = max(2, int(dabei * mindestanteil))
        gruppen, akt = [], []
        for x in punkte:
            if akt and x - akt[-1] > NAH:
                gruppen.append(akt)
                akt = []
            akt.append(x)
        if akt:
            gruppen.append(akt)
        raus.append([dict(x=round(sum(g) / len(g), 4), stimmen=len(g),
                          von=dabei)
                     for g in gruppen if len(g) >= noetig])
    return raus


def vorschlag(con, register, seiten_max=8):
    """Rastervorschlag aus den vorhandenen Seiten dieses Registers."""
    ordner = einstellungen.ordner(con, register)
    bilder = _seiten.bilder(ordner)[:seiten_max]
    if not bilder:
        return dict(fehler="keine Bilder im Ordner", haelften=[])
    proben = [_relative_linien(b) for b in bilder]
    h = stimme(proben)
    return dict(register=register, seiten=[b.name for b in bilder],
                haelften=h,
                spalten=perioden.zur_seite(con, register, bilder[0].stem))


def hole(con, register, bild=None):
    """Das bestätigte Raster – oder None, wenn keines festgelegt wurde."""
    perioden.lege_an(con)
    _spalte_nachruesten(con)
    q = "SELECT spalten_x FROM periode WHERE register=?"
    par = [register]
    if bild:
        q += " AND von_bild<=? AND (bis_bild IS NULL OR bis_bild>=?)"
        par += [bild, bild]
    r = con.execute(q + " ORDER BY von_bild DESC LIMIT 1", par).fetchone()
    if not r or not r["spalten_x"]:
        return None
    return json.loads(r["spalten_x"])


def merke(con, register, haelften, bild=None):
    """Das bestätigte Raster festhalten. `haelften` = Liste von Listen x."""
    perioden.lege_an(con)
    _spalte_nachruesten(con)
    wert = json.dumps([[round(float(x), 4) for x in sorted(h)]
                       for h in haelften], ensure_ascii=False)
    q = "UPDATE periode SET spalten_x=? WHERE register=?"
    par = [wert, register]
    if bild:
        q += " AND von_bild<=? AND (bis_bild IS NULL OR bis_bild>=?)"
        par += [bild, bild]
    cur = con.execute(q, par)
    if not cur.rowcount:
        # Noch keine Periode gelesen: eine anlegen, die alles abdeckt.
        con.execute(
            "INSERT INTO periode (register, von_bild, bis_bild, seiten, "
            "spalten, spalten_x) VALUES (?,?,?,?,?,?)",
            (register, "", None, 0, "[]", wert))
    con.commit()
    return sum(len(h) for h in haelften)


def _spalte_nachruesten(con):
    da = {r[1] for r in con.execute("PRAGMA table_info(periode)")}
    if "spalten_x" not in da:
        con.execute("ALTER TABLE periode ADD COLUMN spalten_x TEXT")
        con.commit()


def zellen(grenzen_y, haelften, block, falz=None):
    """Alle Zellen einer Seite: (zeile, spalte, x0, y0, x1, y1).

    Erst mit einem bestätigten Spaltenraster wird eine einzelne Zelle
    adressierbar - die Voraussetzung für die Lupe je Feld und für jede
    Handschrifterkennung, die Text einer Spalte zuordnen soll.
    """
    raus = []
    breite = block["x1"] - block["x0"]
    for zi, (y0, y1) in enumerate(zip(grenzen_y, grenzen_y[1:])):
        for hi, hs in enumerate(haelften or []):
            if not hs:
                continue
            # Die Hälfte im Seitenbild: links vom Falz, rechts davon.
            hx0 = block["x0"] if hi == 0 else (falz or block["x0"] + breite / 2)
            hx1 = (falz or block["x0"] + breite / 2) if hi == 0 else block["x1"]
            hb = hx1 - hx0
            kanten = [hx0 + x * hb for x in hs]
            for si, (a, b) in enumerate(zip(kanten, kanten[1:])):
                raus.append(dict(zeile=zi, haelfte=hi, spalte=si,
                                 x0=int(a), y0=int(y0),
                                 x1=int(b), y1=int(y1)))
    return raus


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("register")
    ap.add_argument("--merken", action="store_true")
    a = ap.parse_args()
    con = db.verbinde()
    v = vorschlag(con, a.register)
    if v.get("fehler"):
        raise SystemExit(v["fehler"])
    print(f"{a.register}: {len(v['seiten'])} Seiten befragt")
    for i, h in enumerate(v["haelften"]):
        print(f"  Hälfte {i}: {len(h)} Linien")
        for e in h:
            print(f"     {e['x']:.3f}   {e['stimmen']} von {e['von']} Seiten")
    if v.get("spalten"):
        print(f"  gelesene Überschriften: {len(v['spalten'])} Spalten")
    if a.merken:
        n = merke(con, a.register,
                  [[e["x"] for e in h] for h in v["haelften"]])
        print(f"-> {n} Linien übernommen")


if __name__ == "__main__":
    main()
