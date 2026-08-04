#!/usr/bin/env python3
"""Testquelle: liest wie die API, kostet nichts.

    python3 -m werkstatt.testdaten            was die Quelle hergibt
    python3 -m werkstatt.testdaten --wahrheit die geprüften Verknüpfungen

Warum das kein Luxus ist: Die Maske war messbar kaputt (`ofb_id` gegen
`person`), seit dem Schemawechsel. Aufgefallen ist es nie, weil sie nur zwei
Zustände kannte — leer, oder ein API-Schlüssel und echtes Geld. Ein Werkzeug,
dessen Hauptbildschirm nur gegen Bezahlung sichtbar wird, wird nicht geprüft.

Quelle sind die 22 Taufeinträge des Pilotlaufs (Haberschlacht 1808/09,
Bilder 00361–00365) aus dem Nachbarprojekt, das dabei unangetastet bleibt.

**Ausgeliefert wird nur die Rohlesung.** Die 39 von Hand geprüften
Personenverweise bleiben zurück — sie sind die *Wahrheit*, nicht die Eingabe.
Der Abgleich muss sie selbst wiederfinden; genau das macht den Durchlauf
prüfbar statt selbstbestätigend. Wer die Verweise mitliefert, misst
hinterher nur, dass er sie mitgeliefert hat.
"""
import argparse
import shutil
import sqlite3
from pathlib import Path

from . import konfig

PILOT = (konfig.WURZEL.parent / "OFB" / "OFB-Haberschlacht"
         / "Transkription-1808" / "daten" / "erfassung.sqlite")
STREIFEN = PILOT.parent.parent / "scans" / "zeilen"
ZIEL_STREIFEN = Path("bilder") / "taufe" / "zeilen"

NAME = "Pilotlauf Haberschlacht 1808/09"


def vorhanden():
    return PILOT.exists()


def _con():
    p = sqlite3.connect(f"file:{PILOT}?mode=ro", uri=True)
    p.row_factory = sqlite3.Row
    return p


def seiten(register=None):
    """Welche Bilder diese Quelle abdeckt."""
    if not vorhanden():
        return []
    p = _con()
    q = "SELECT DISTINCT register, bild FROM eintrag"
    r = [(x["register"], x["bild"]) for x in p.execute(q)]
    p.close()
    return sorted(b for reg, b in r if register in (None, reg))


def lies_seite(bild):
    """Eine Seite 'lesen' — dieselbe Form, die auch die API liefert.

    Rückgabe wie in lesen.lies_seite(): {"eintraege": [{"lfd_nr", "felder"}]}
    """
    if not vorhanden():
        return {"eintraege": []}
    p = _con()
    raus = []
    for e in p.execute("SELECT * FROM eintrag WHERE bild=? "
                       "ORDER BY CAST(nr AS INTEGER)", (bild,)):
        felder = {}
        for f in p.execute("SELECT * FROM feld WHERE eintrag_id=? ORDER BY reihe, id",
                           (e["id"],)):
            if f["gelesen"] is None:
                continue
            felder[f["name"]] = {"wert": f["gelesen"], "kb": f["kb_form"],
                                 # Der Pilotlauf hat keine Selbsteinschätzung
                                 # festgehalten. Nichts zu erfinden ist
                                 # richtiger, als eine Zahl zu behaupten.
                                 "zuversicht": None, "notiz": None}
        raus.append({"lfd_nr": e["nr"], "jahr": e["jahr"], "band": e["band"],
                     "ausschnitt": _streifen(e["ausschnitt"]),
                     "felder": felder})
    p.close()
    return {"eintraege": raus}


def _streifen(pfad):
    if not pfad:
        return None
    name = Path(pfad).name
    if (konfig.WURZEL / ZIEL_STREIFEN / name).exists():
        return str(ZIEL_STREIFEN / name)
    return None


def streifen_kopieren():
    """Zeilenstreifen in die Werkstatt holen.

    Der Bildpfad der Maske ist bewusst auf die Projektwurzel eingesperrt —
    ein Verweis ins Nachbarverzeichnis wäre ein Loch im Dateizugriff.
    """
    if not STREIFEN.exists():
        return 0
    ziel = konfig.WURZEL / ZIEL_STREIFEN
    ziel.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(STREIFEN.iterdir()):
        if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            shutil.copy2(f, ziel / f.name)
            n += 1
    return n


def wahrheit():
    """Die geprüften Verweise: (bild, nr, feld) -> OFB-Kennung.

    Nicht Eingabe, sondern Maßstab. Damit lässt sich messen, wie viel der
    Abgleich von dem wiederfindet, was ein Mensch bestätigt hat.
    """
    if not vorhanden():
        return {}
    p = _con()
    raus = {}
    for r in p.execute(
            "SELECT e.bild, e.nr, f.name, f.ofb_id, f.gelesen, f.beleg "
            "FROM feld f JOIN eintrag e ON e.id=f.eintrag_id "
            "WHERE f.ofb_id IS NOT NULL"):
        raus[(r["bild"], str(r["nr"]), r["name"])] = dict(
            xref=r["ofb_id"], gelesen=r["gelesen"], beleg=r["beleg"])
    p.close()
    return raus


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wahrheit", action="store_true")
    a = ap.parse_args()
    if not vorhanden():
        raise SystemExit(f"Pilotdaten nicht gefunden: {PILOT}")
    if a.wahrheit:
        w = wahrheit()
        print(f"{len(w)} geprüfte Verweise")
        for (bild, nr, feld), d in sorted(w.items())[:10]:
            print(f"  {bild} Nr.{nr:>3}  {feld:16} {d['gelesen']:18} "
                  f"-> {d['xref']:7} {d['beleg'] or ''}")
        return
    ss = seiten()
    print(f"{NAME}: {len(ss)} Seiten")
    for b in ss:
        d = lies_seite(b)
        n_f = sum(len(e["felder"]) for e in d["eintraege"])
        print(f"  {b}  {len(d['eintraege'])} Einträge, {n_f} gefüllte Felder")


if __name__ == "__main__":
    main()
