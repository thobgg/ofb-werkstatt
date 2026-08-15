#!/usr/bin/env python3
"""Einen Eintrag ein zweites Mal lesen und die Unterschiede zeigen.

    python3 -m werkstatt.nachlesen 12

Zwei unabhängige Lesungen derselben Zeile sind das beste Werkzeug gegen
stille Lesefehler. Wo sie übereinstimmen, ist die Sache wahrscheinlich
klar; wo sie auseinandergehen, liegt der Zweifel – und zwar sichtbar,
statt in einer Zuversichtszahl versteckt, die nichts wert ist.

Gemessen am eigenen Bestand: Dieselbe Zeile wurde einmal als `Wöß`,
`B. u. Weingärtner`, `† 11. Februar` gelesen und ein zweites Mal als
`Möß`, `B. u. Wagner`, `† 4.te Februar`. Drei Felder, drei Unterschiede,
alle drei vorher unauffällig. Ohne die zweite Lesung wäre keiner davon
aufgefallen.

Das ist auch die Antwort auf „was kann ein Besucher hier eigentlich
prüfen": Die mitgelieferten Rohlesungen zeigen den Durchlauf, aber nicht
das Lesen. Wer Claude Code hat, liest dieselbe Seite selbst und hält sein
Ergebnis gegen das mitgelieferte.

**Geändert wird nichts.** Die zweite Lesung wird gezeigt, nicht
übernommen. Was gilt, entscheidet der Bearbeiter am Bild.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from . import bloecke, db, einstellungen, katalog, konfig, seiten, vorlage

AUFTRAG = """Lies diesen einen Eintrag aus einem württembergischen
Kirchenbuch. Du siehst ihn als ein oder zwei Bilder – links und rechts vom
Bund derselben Zeile – und dazu den gedruckten Spaltenkopf.

Antworte NUR mit JSON:

{"felder": {"feldname": {"wert": "…", "kb": "wörtlich wie im Buch"}}}

`kb` nur, wenn die Schreibung im Buch von der normalisierten Form
abweicht. Was du nicht lesen kannst, lässt du weg – geraten wird nicht.

%s

Die Bilder:
"""


def _zeilenindex(con, e):
    """Der wievielte Eintrag der Seite ist das? Zählung wie beim Schneiden."""
    nrs = [r["nr"] for r in con.execute(
        "SELECT nr FROM eintrag WHERE register=? AND bild=? "
        "ORDER BY CAST(nr AS INTEGER), nr", (e["register"], e["bild"]))]
    return nrs.index(e["nr"]) if e["nr"] in nrs else None


def bilder_zum_eintrag(con, e):
    """Kopf- und Zeilenblöcke dieses Eintrags. Schneidet, falls nötig."""
    ordner = einstellungen.ordner(con, e["register"])
    datei = next((f for f in seiten.bilder(ordner) if f.stem == e["bild"]), None)
    if not datei:
        return [], "Bilddatei nicht gefunden"
    z = bloecke.schneide(datei, still=True)
    if not z.get("bloecke"):
        return [], z.get("grund", "keine Blöcke")
    i = _zeilenindex(con, e)
    if i is None or i >= len(z["bloecke"]):
        return [], (f"Zeile {i} nicht im Raster – die Seite hat "
                    f"{len(z['bloecke'])} Zeilenbänder")
    return ([k["datei"] for k in z.get("kopf", [])]
            + [t["datei"] for t in z["bloecke"][i]["teile"]], None)


def frage_modell(bilder, art, con, zeitlimit=900):
    w = vorlage.werkzeug()
    if not w:
        return None, ("Claude Code ist nicht eingerichtet – ohne das kann "
                      "hier niemand ein zweites Mal lesen.")
    auftrag = (AUFTRAG % katalog.als_prompt(art, con)
               + "\n".join(f"  {b}" for b in bilder))
    frei = []
    for o in sorted({str(Path(b).parent) for b in bilder}
                    | {str(konfig.WURZEL)}):
        frei += ["--add-dir", o]
    with tempfile.TemporaryDirectory() as tmp:
        try:
            p = subprocess.run([w, "-p", auftrag, "--output-format", "json",
                                *frei], capture_output=True, text=True,
                               timeout=zeitlimit, cwd=tmp)
        except subprocess.TimeoutExpired:
            return None, f"keine Antwort in {zeitlimit} Sekunden"
    try:
        a = json.loads(p.stdout)
        text = a.get("result") or ""
        i, j = text.find("{"), text.rfind("}")
        return (json.loads(text[i:j + 1]), None) if i >= 0 else (
            None, f"kein JSON in der Antwort: {text[:200]}")
    except Exception as e:
        return None, f"Antwort nicht lesbar: {e}"


def vergleiche(con, eintrag_id, zeitlimit=900):
    """Zweite Lesung holen und gegen das Gespeicherte halten."""
    e = con.execute("SELECT * FROM eintrag WHERE id=?",
                    (eintrag_id,)).fetchone()
    if not e:
        return dict(ok=False, meldung=f"kein Eintrag {eintrag_id}")
    bilder, grund = bilder_zum_eintrag(con, e)
    if not bilder:
        return dict(ok=False, meldung=grund)
    neu, fehler = frage_modell(bilder, e["register"], con, zeitlimit)
    if fehler:
        return dict(ok=False, meldung=fehler)

    alt = {r["name"]: dict(wert=(r["korrigiert"] if r["korrigiert"] is not None
                                else r["gelesen"]), kb=r["kb_form"],
                           eigen=r["korrigiert"] is not None)
           for r in con.execute("SELECT name, gelesen, korrigiert, kb_form "
                                "FROM feld WHERE eintrag_id=?", (eintrag_id,))}
    nf = neu.get("felder") or {}
    raus = []
    for name in sorted(set(alt) | set(nf)):
        a = (alt.get(name) or {}).get("wert") or ""
        b = ((nf.get(name) or {}).get("wert") or "")
        akb = (alt.get(name) or {}).get("kb") or ""
        bkb = ((nf.get(name) or {}).get("kb") or "")
        if not a and not b:
            continue
        gleich = a.strip() == b.strip()
        raus.append(dict(name=name, alt=a, neu=b, alt_kb=akb, neu_kb=bkb,
                         gleich=gleich,
                         eigen=(alt.get(name) or {}).get("eigen", False)))
    z = dict(ok=True, bilder=[konfig.kurz(b) for b in bilder],
             felder=raus,
             gleich=sum(1 for x in raus if x["gleich"]),
             anders=sum(1 for x in raus if not x["gleich"]))
    return z


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("eintrag", type=int)
    a = ap.parse_args()
    z = vergleiche(db.verbinde(), a.eintrag)
    if not z["ok"]:
        raise SystemExit(z["meldung"])
    print(f"{z['gleich']} gleich, {z['anders']} anders")
    for f in z["felder"]:
        if not f["gleich"]:
            print(f"  {f['name']:24} gespeichert: {f['alt'][:40]!r}")
            print(f"  {'':24} zweite Lesung: {f['neu'][:40]!r}")


if __name__ == "__main__":
    main()
