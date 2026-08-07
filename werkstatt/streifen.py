#!/usr/bin/env python3
"""Zeilenstreifen schneiden — für den Menschen, nicht für das Modell.

    python3 -m werkstatt.streifen taufe 1184798-00359
    python3 -m werkstatt.streifen --runde 1

Der Streifen ist das, was der Bearbeiter beim Entscheiden ansieht. Er
entsteht deshalb **nach** dem Lesen und **vor** dem Korrigieren — und kostet
dort nichts: gedruckte Linien finden, Pixel zählen, Pillow. Ein Modell dafür
zu bezahlen wäre Geld fürs Kopfrechnen.

## Wer was beisteuert

    Modell     wie viele Einträge, in welcher Reihenfolge
               — fällt beim Transkribieren ohnehin an, kostet nichts extra
    Geometrie  wo die Zeilenlinien liegen
    Abzählen   Eintrag N ist Band N

Das Modell muss **keine Koordinaten** nennen. Einträge und Zeilenbänder
stehen in derselben Reihenfolge; damit genügt Abzählen. Koordinaten schätzen
zu lassen ist in diesem Projekt zweimal gescheitert (`ansatz.md`).

## Warum nicht dem Modell Streifen schicken

Weil es teurer und schlechter wäre. Heute geht **eine** Seite als **ein**
Bild hinein. Sechs Streifen wären sechs Bilder — mehr Token für weniger
Zusammenhang. Dieselbe Hand schreibt in jedem Eintrag `B. u. Weingärtner in
Haberschlacht`; daran eicht man die Buchstabenformen.

## Wenn die Erkennung nicht aufgeht

Gemessen wurden 22 von 22 Zeilenlinien bei ±40 px — aber auf anderen Seiten
als jeder beliebigen. Auf Bild 00359 fand die linke Buchseite nur eine
Linie, die rechte sechs; gerettet hat es die Vereinigung. Deshalb drei
Stufen, und die schwächste sagt es:

    passt genau       Bänder = Einträge                 -> zuschneiden
    letzte Linie      Bänder = Einträge - 1             -> Papierkante als
    fehlt                                                  Abschluss
    passt nicht       alles andere                      -> gleichmäßig
                                                           teilen, vermerken
"""
import argparse
from pathlib import Path

from . import db, einstellungen, konfig, raster, seiten

ZIEL = "zeilen"       # Unterordner im Bilderordner des Registers
RAND = 25             # Pixel Zugabe oben und unten, damit nichts abschneidet


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
    # linke Hälfte — in der Maske stand ein Taufdatum, das im Bild nicht
    # zu sehen war, und niemand konnte es prüfen.
    #
    # Ob ein Formular wirklich durchläuft, wollte ich messen; die
    # Linienpaarung trägt das Urteil nicht (siehe raster.paarung). Also
    # immer verbinden: Fälschlich getrennt kostet die halben Felder,
    # fälschlich verbunden einen doppelt so breiten Streifen.
    block = dict(v["seiten"][0])
    block["x1"] = max(s["x1"] for s in v["seiten"])
    z = sorted(v["zeilen"])

    if len(z) - 1 == anzahl:
        return list(zip(z, z[1:])), block, "passt"
    if len(z) == anzahl:
        # Die letzte gefundene Linie ist der obere Rand des letzten Eintrags;
        # nach unten schließt die Papierkante ab.
        g = z + [block["y1"]]
        return list(zip(g, g[1:])), block, "letzte Linie ergänzt"

    # Gleichmäßig teilen. Grob, aber besser als kein Streifen — und der
    # Vermerk sorgt dafür, dass niemand es für gemessen hält.
    y0, y1 = (z[0], z[-1]) if len(z) >= 2 else (block["y0"], block["y1"])
    h = (y1 - y0) / anzahl
    return ([(int(y0 + i * h), int(y0 + (i + 1) * h)) for i in range(anzahl)],
            block, f"gleichmäßig geteilt ({len(z)} Linien für {anzahl} Einträge)")


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
        for nr, (a, e) in zip(nummern, b):
            p = ziel / f"{bild}_{nr}.jpg"
            k = (block["x0"], max(0, a - RAND),
                 block["x1"] - block["x0"],
                 min(im.size[1], e + RAND) - max(0, a - RAND))
            im.crop((k[0], k[1], k[0] + k[2], k[1] + k[3])).save(p, quality=88)
            # Die Seitengroesse gehoert dazu: Die Maske zeigt die Seite
            # verkleinert und muss die Marke umrechnen. Ohne sie rechnete
            # sie gegen die Breite des verkleinerten Bildes und legte den
            # Rahmen ueber die halbe Seite.
            raus[nr] = (konfig.kurz(p),
                        ",".join(str(int(v)) for v in
                                 (*k, im.size[0], im.size[1])),
                        konfig.kurz(datei))
    if not still:
        print(f"  {bild}: {len(raus)} Streifen — {guete}")
    return raus, guete


def fuer_bild(con, art, bild, still=True):
    """Streifen für alle Einträge eines Bildes und in die Datenbank eintragen."""
    nummern = [r["nr"] for r in con.execute(
        "SELECT nr FROM eintrag WHERE register=? AND bild=? "
        "ORDER BY CAST(nr AS INTEGER), nr", (art, bild))]
    if not nummern:
        return 0, "keine Einträge"
    pfade, guete = schneide(con, art, bild, nummern, still)
    for nr, (p, kasten, seite) in pfade.items():
        con.execute("UPDATE eintrag SET ausschnitt=?, kasten=?, seite=? "
                    "WHERE register=? AND bild=? AND nr=?",
                    (p, kasten, seite, art, bild, nr))
    if guete.startswith("gleichmäßig"):
        con.execute("UPDATE eintrag SET bemerkung=? WHERE register=? AND bild=?",
                    (f"Zeilenraster unsicher: {guete}", art, bild))
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
