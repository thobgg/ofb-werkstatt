#!/usr/bin/env python3
"""Doppelte Aufnahmen finden, bevor sie gelesen werden.

    python3 -m werkstatt.dubletten taufe
    python3 -m werkstatt.dubletten taufe --uebernehmen

Archion- und Ancestry-Bände enthalten regelmäßig zwei Aufnahmen derselben
Buchöffnung – mal anders belichtet, mal leicht verschoben. Wer sie beide
liest, zahlt zweimal und bekommt jeden Eintrag doppelt in den Bestand.

Gemessen an Runde 1: `1184798-00360` zeigt dieselbe Öffnung wie `00359`.
Die Sitzung hat es beim Lesen selbst bemerkt und keine Einträge geliefert
– aber erst, nachdem sie die Seite angeschaut hatte. Danach standen sechs
doppelte Einträge in der Datenbank, aus einem früheren Lauf.

**Der Vergleich ist billig und deterministisch.** Beide Bilder auf 400×400
Graustufen bringen, den mittleren quadratischen Abstand nehmen. Das
kostet Bruchteile einer Sekunde und braucht kein Modell.

## Warum kein fester Schwellwert

Der Abstand hängt an Buch, Scanner und Belichtung. Gemessen an diesem
Band: benachbarte Seiten liegen bei 73–95, die Dublette bei 39,6. Ein
fester Wert von 50 träfe hier, aber niemand weiß, ob er im nächsten Band
trifft. Deshalb wird er **aus der Strecke selbst** gewonnen: Wer deutlich
näher liegt als der Median aller Nachbarpaare, ist verdächtig.

Ein Verdacht ist keine Entscheidung. Was hier herauskommt, wird
vorgelegt; übersprungen wird erst, wenn der Bearbeiter zustimmt oder die
Einstellung es erlaubt.
"""
import argparse
import json
from pathlib import Path

from . import db, einstellungen, konfig, seiten

# Anteil des Medians, unter dem ein Paar auffaellt. 0,6 haelt bei den
# gemessenen Werten Abstand nach beiden Seiten: 39,6 liegt bei 0,51 des
# Medians, das naechstniedrigere echte Paar bei 0,94.
ANTEIL = 0.6
# Darueber ist nichts eine Dublette, auch wenn der Median hoch liegt –
# sonst erklaert eine Strecke aus lauter aehnlichen Seiten sich selbst zur
# Dublettensammlung.
DECKEL = 60.0
KANTE = 400


def lege_an(con):
    con.execute("""CREATE TABLE IF NOT EXISTS dublette (
      bild      TEXT PRIMARY KEY,
      gleich_wie TEXT NOT NULL,
      abstand   REAL NOT NULL,
      median    REAL,
      stand     TEXT NOT NULL DEFAULT 'verdacht',  -- verdacht|dublette|eigen
      geprueft  TEXT)""")
    con.commit()


def _grau(pfad):
    from PIL import Image
    import numpy as np
    im = Image.open(pfad).convert("L").resize((KANTE, KANTE))
    return np.asarray(im, dtype="float32")


def abstand(a, b):
    """Mittlerer quadratischer Abstand zweier Bilder, 0 = gleich."""
    import numpy as np
    return float(np.sqrt(((a - b) ** 2).mean()))


def messe(bilder, still=True):
    """Abstand jedes Bildes zu seinem Vorgänger."""
    raus, vor = [], None
    for p in bilder:
        try:
            a = _grau(p)
        except Exception as e:
            if not still:
                print(f"  {Path(p).name}: nicht lesbar ({e})")
            vor = None
            continue
        if vor is not None:
            raus.append(dict(bild=Path(p).stem, vorher=vor[0],
                             abstand=round(abstand(a, vor[1]), 1)))
        vor = (Path(p).stem, a)
    return raus


def verdacht(paare):
    """Welche Paare fallen aus der Reihe? Gibt (Liste, Median) zurück."""
    if len(paare) < 3:
        # Zu wenig Strecke, um einen Median zu bilden. Dann lieber nichts
        # behaupten als aus zwei Zahlen eine Regel machen.
        return [], None
    werte = sorted(p["abstand"] for p in paare)
    m = werte[len(werte) // 2]
    grenze = min(ANTEIL * m, DECKEL)
    return [dict(p, median=m, grenze=round(grenze, 1))
            for p in paare if p["abstand"] < grenze], m


def pruefe(con, register, still=False):
    """Eine Registerstrecke durchmessen und Verdachtsfälle festhalten."""
    lege_an(con)
    ordner = einstellungen.ordner(con, register)
    bilder = seiten.bilder(ordner)
    paare = messe(bilder, still)
    v, m = verdacht(paare)
    from datetime import datetime, timezone
    jetzt = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for p in v:
        con.execute(
            "INSERT INTO dublette (bild, gleich_wie, abstand, median, "
            "stand, geprueft) VALUES (?,?,?,?,'verdacht',?) "
            "ON CONFLICT(bild) DO UPDATE SET gleich_wie=excluded.gleich_wie, "
            "abstand=excluded.abstand, median=excluded.median, "
            "geprueft=excluded.geprueft WHERE dublette.stand='verdacht'",
            (p["bild"], p["vorher"], p["abstand"], m, jetzt))
    con.commit()
    if not still:
        print(f"{register}: {len(bilder)} Bilder, {len(paare)} Nachbarpaare"
              + (f", Median {m:.1f}" if m else ""))
        for p in v:
            print(f"  ⚠ {p['bild']} gleicht {p['vorher']} – Abstand "
                  f"{p['abstand']} (Grenze {p['grenze']})")
        if not v:
            print("  keine Dublette gefunden")
    return dict(bilder=len(bilder), paare=len(paare), median=m, verdacht=v)


def gemeldet(con, stand=None):
    """Was bekannt ist. Ohne `stand` alles."""
    lege_an(con)
    q = "SELECT * FROM dublette"
    par = ()
    if stand:
        q += " WHERE stand=?"
        par = (stand,)
    return [dict(r) for r in con.execute(q + " ORDER BY bild", par)]


def uebersprungene(con):
    """Bilder, die beim Planen einer Runde ausgelassen werden."""
    lege_an(con)
    return {r["bild"] for r in con.execute(
        "SELECT bild FROM dublette WHERE stand='dublette'")}


def entscheide(con, bild, ist_dublette):
    """Der Bearbeiter urteilt. Danach fasst die Messung es nicht mehr an."""
    lege_an(con)
    con.execute("UPDATE dublette SET stand=? WHERE bild=?",
                ("dublette" if ist_dublette else "eigen", bild))
    con.commit()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("register")
    ap.add_argument("--uebernehmen", action="store_true",
                    help="Verdachtsfälle gleich als Dublette buchen")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    con = db.verbinde()
    z = pruefe(con, a.register, still=a.json)
    if a.uebernehmen:
        for p in z["verdacht"]:
            entscheide(con, p["bild"], True)
        if not a.json:
            print(f"  {len(z['verdacht'])} als Dublette gebucht")
    if a.json:
        print(json.dumps(z, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
