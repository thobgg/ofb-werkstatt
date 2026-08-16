#!/usr/bin/env python3
"""Zeilenstreifen schneiden – für den Menschen, nicht für das Modell.

    python3 -m werkstatt.streifen taufe 1184798-00359
    python3 -m werkstatt.streifen --runde 1

Der Streifen ist das, was der Bearbeiter beim Entscheiden ansieht. Er
entsteht deshalb **nach** dem Lesen und **vor** dem Korrigieren – und kostet
dort nichts: gedruckte Linien finden, Pixel zählen, Pillow. Ein Modell dafür
zu bezahlen wäre Geld fürs Kopfrechnen.

## Wer was beisteuert

    Modell     wie viele Einträge, in welcher Reihenfolge
               – fällt beim Transkribieren ohnehin an, kostet nichts extra
    Geometrie  wo die Zeilenlinien liegen
    Abzählen   Eintrag N ist Band N

Das Modell muss **keine Koordinaten** nennen. Einträge und Zeilenbänder
stehen in derselben Reihenfolge; damit genügt Abzählen. Koordinaten schätzen
zu lassen ist in diesem Projekt zweimal gescheitert (`ansatz.md`).

## Warum nicht dem Modell Streifen schicken

Weil es teurer und schlechter wäre. Heute geht **eine** Seite als **ein**
Bild hinein. Sechs Streifen wären sechs Bilder – mehr Token für weniger
Zusammenhang. Dieselbe Hand schreibt in jedem Eintrag `B. u. Weingärtner in
Haberschlacht`; daran eicht man die Buchstabenformen.

## Wenn die Erkennung nicht aufgeht

Das Raster wird eingepasst, nicht abgezählt – siehe `zeilenraster.py`. Aus
den gefundenen Linien entsteht ein fast gleichmäßiges Modell, gemessene
Linien rasten ein, fehlende werden gerechnet. Die Güte nennt hinterher,
wie viele Grenzen gemessen sind; nur die gerechneten stehen als Warnung
in der Maske.

Gemessen gegen vier von Hand geprüfte Seiten: 22 von 22 Linien auf ±40 px.
Über die dreizehn Beispielseiten: 10 vollständig gemessen, insgesamt 4
gerechnete Grenzen. Die Vorgängerfassung teilte 7 von 13 Seiten
gleichmäßig, obwohl die Linien da waren.
"""
import argparse
from pathlib import Path

from . import db, einstellungen, konfig, raster, seiten

ZIEL = "zeilen"       # Unterordner im Bilderordner des Registers
# Zugabe oben und unten, als Anteil der Hoehe **dieses** Bandes.
#
# Fester Pixelwert ging nicht: Die Zeilenhoehen reichen von 260 px im
# Sterberegister bis 640 px im Eheregister, und die Handschrift haengt
# unterschiedlich weit unter die gedruckte Linie - gemessen zwischen 0
# und 86 px auf drei Seiten.
#
# Genau messen ging auch nicht, jedenfalls nicht mit vertretbarem
# Aufwand: Drei Anlaeufe, die Kante an der Schrift auszurichten, haben
# entweder den Nachsatz abgeschnitten oder die Oberlaengen der naechsten
# Zeile. Der Versuch steht als zeilenraster.nach_schrift noch da, wird
# aber nicht benutzt.
#
# Fuer den Zweck des Streifens braucht es die Genauigkeit auch nicht: Er
# ist das, was der Bearbeiter beim Entscheiden ansieht. Fehlender Text
# kostet eine Information, ein Stueck vom Nachbarn kostet nichts und
# hilft beim Einordnen. Also grosszuegig.
RAND_ANTEIL = 1 / 6


def baender(bild, anzahl):
    """Zeilenbänder für so viele Einträge. Rückgabe: (bänder, block, güte)."""
    v = raster.vorschlag(str(bild))
    if not v["seiten"]:
        return [], None, "kein Papier erkannt"
    # Über **beide** Buchseiten, nicht nur über die linke, und zwar in
    # jeder Aktart. Ein Eintrag dieser Formulare läuft über den Bund:
    # Taufe links Name und Eltern, rechts Tauftag, Taufender und Paten;
    # Ehe links Namen, Stand und Eltern, rechts Geburtsdaten,
    # Proklamation, Dispensationen. Der Streifen zeigte bisher nur die
    # linke Hälfte – in der Maske stand ein Taufdatum, das im Bild nicht
    # zu sehen war, und niemand konnte es prüfen.
    #
    # Ob ein Formular wirklich durchläuft, wollte ich messen; die
    # Linienpaarung trägt das Urteil nicht (siehe raster.paarung). Also
    # immer verbinden: Fälschlich getrennt kostet die halben Felder,
    # fälschlich verbunden einen doppelt so breiten Streifen.
    block = dict(v["seiten"][0])
    block["x1"] = max(s["x1"] for s in v["seiten"])
    block["y0"] = min(s["y0"] for s in v["seiten"])
    block["y1"] = max(s["y1"] for s in v["seiten"])

    # Das Raster wird eingepasst, nicht abgezählt. Die alte Fassung
    # verlangte, dass die Zahl der gefundenen Linien zur Zahl der
    # Eintraege passt - sonst teilte sie gleichmaessig. Gemessen ueber die
    # dreizehn Beispielseiten traf das auf sieben zu, obwohl die Linien
    # da waren: Doppelt erkannte Striche machten aus 9 noetigen Grenzen
    # 13 Kandidaten. Siehe zeilenraster.py.
    from . import zeilenraster
    grenzen, gemessen, _ = zeilenraster.passe_ein(
        sorted(v["zeilen"]), anzahl, (block["y0"], block["y1"]))
    baender_ = list(zip(grenzen, grenzen[1:]))
    # Ab wann heisst es "unsicher"? Nicht schon bei einer gerechneten
    # Grenze von sieben - dann steht die Warnung bei der Haelfte aller
    # Eintraege, und eine Warnung, die immer da ist, liest niemand.
    # Gemessen an Runde 1: 17 von 34 Eintraegen trugen sie wegen einer
    # einzigen gerechneten Grenze.
    if gemessen >= len(grenzen) - 1:
        guete = "passt"
    elif gemessen >= 2:
        guete = (f"{len(grenzen) - gemessen} von {len(grenzen)} Grenzen "
                 f"gerechnet, der Rest gemessen")
    else:
        guete = f"gleichmäßig geteilt ({len(v['zeilen'])} Linien gefunden)"
    return baender_, block, guete


def schneide(con, art, bild, nummern, still=True):
    """Je Eintrag einen Streifen. Rückgabe: {nr: Pfad relativ zur Wurzel}."""
    from PIL import Image
    quelle = einstellungen.ordner(con, art)
    datei = next((f for f in seiten.bilder(quelle) if f.stem == bild), None)
    if not datei:
        return {}, "Bilddatei nicht gefunden"

    b, block, guete = baender(datei, len(nummern))
    if not b:
        return {}, guete

    ziel = quelle / ZIEL
    ziel.mkdir(parents=True, exist_ok=True)
    raus = {}
    with Image.open(datei) as im:
        # Der gedruckte Kopf, einmal je Seite und exakt so breit wie die
        # Streifen – dann stehen Ueberschrift und Zelle uebereinander.
        kopf = None
        if b:
            oben = b[0][0]
            hoehe = b[0][1] - b[0][0]
            # 0,75 statt 1,4 Zeilenhoehen: Darueber liegt nur noch der
            # Papierrand mit dem Schatten der Buchkante, und der nimmt in
            # der Maske Platz weg, den der Eintrag braucht.
            #
            # Und nicht ueber die Papierkante hinaus: Gemessen an Bild
            # 00359 liegt die erste Linie bei y=1156, das Papier beginnt
            # bei 972, 0,75 Zeilenhoehen waeren 847. Der Kopf bekam so
            # 125 px schwarze Buchkante mit und wurde in der Maske
            # entsprechend gestaucht.
            k0 = max(0, block["y0"], int(oben - hoehe * 0.75))
            # Ein paar Pixel unter die Linie: Die Ueberschriften stehen
            # zweizeilig und mit Unterlaengen dicht darueber; genau auf
            # der Linie geschnitten fehlt die zweite Zeile halb. Weniger
            # als RAND, weil der erste Streifen dieselbe Linie noch
            # einmal von oben mitnimmt - sonst steht die Ueberschrift in
            # der Maske doppelt da.
            k1 = min(im.size[1], oben + 8)
            if oben - k0 > 20:
                kp = ziel / f"{bild}_kopf.jpg"
                im.crop((block["x0"], k0, block["x1"], k1)).save(
                    kp, quality=88)
                kopf = konfig.kurz(kp)
        for nr, (a, e) in zip(nummern, b):
            p = ziel / f"{bild}_{nr}.jpg"
            rand = int((e - a) * RAND_ANTEIL)
            k = (block["x0"], max(0, a - rand),
                 block["x1"] - block["x0"],
                 min(im.size[1], e + rand) - max(0, a - rand))
            im.crop((k[0], k[1], k[0] + k[2], k[1] + k[3])).save(p, quality=88)
            # Die Seitengroesse gehoert dazu: Die Maske zeigt die Seite
            # verkleinert und muss die Marke umrechnen. Ohne sie rechnete
            # sie gegen die Breite des verkleinerten Bildes und legte den
            # Rahmen ueber die halbe Seite.
            raus[nr] = (konfig.kurz(p),
                        ",".join(str(int(v)) for v in
                                 (*k, im.size[0], im.size[1])),
                        konfig.kurz(datei), kopf)
    if not still:
        print(f"  {bild}: {len(raus)} Streifen – {guete}")
    return raus, guete


def fuer_bild(con, art, bild, still=True):
    """Streifen für alle Einträge eines Bildes und in die Datenbank eintragen."""
    nummern = [r["nr"] for r in con.execute(
        "SELECT nr FROM eintrag WHERE register=? AND bild=? "
        "ORDER BY CAST(nr AS INTEGER), nr", (art, bild))]
    if not nummern:
        return 0, "keine Einträge"
    pfade, guete = schneide(con, art, bild, nummern, still)
    for nr, (p, kasten, seite, kopf) in pfade.items():
        con.execute("UPDATE eintrag SET ausschnitt=?, kasten=?, seite=?, "
                    "kopf=? WHERE register=? AND bild=? AND nr=?",
                    (p, kasten, seite, kopf, art, bild, nr))
    if guete != "passt":
        con.execute("UPDATE eintrag SET bemerkung=? WHERE register=? AND bild=?",
                    (f"Zeilenraster unsicher: {guete}", art, bild))
    else:
        con.execute("UPDATE eintrag SET bemerkung=NULL WHERE register=? "
                    "AND bild=? AND bemerkung LIKE 'Zeilenraster%'",
                    (art, bild))
    con.commit()
    return len(pfade), guete


def fuer_runde(con, runde_id, still=True):
    r = con.execute("SELECT register FROM runde WHERE id=?", (runde_id,)).fetchone()
    if not r:
        return {}
    z = {}
    for x in con.execute("SELECT DISTINCT bild FROM eintrag WHERE runde=?",
                         (runde_id,)):
        n, guete = fuer_bild(con, r["register"], x["bild"], still)
        z[x["bild"]] = (n, guete)
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("register", nargs="?")
    ap.add_argument("bild", nargs="?")
    ap.add_argument("--runde", type=int)
    a = ap.parse_args()
    con = db.verbinde()
    if a.runde:
        for bild, (n, guete) in fuer_runde(con, a.runde, still=False).items():
            pass
    elif a.register and a.bild:
        fuer_bild(con, a.register, a.bild, still=False)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
