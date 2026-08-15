#!/usr/bin/env python3
"""Die Normalisierung nachrechnen, die das Modell stillschweigend vornimmt.

    python3 -m werkstatt.normalform --pilot     an den Testlesungen messen
    python3 -m werkstatt.normalform --runde 3   eine Runde markieren

**Der Befund, der dieses Modul ausgeloest hat.** In den mitgelieferten
Lesungen weichen **771 von 885** Kirchenbuchformen vom kanonischen Wert
ab. Die Normalisierung ist also nicht die Ausnahme, sondern die Regel -
und sie findet vollstaendig im Modell statt, ohne Spur und ohne Pruefung:

    'geb. Sinerin'  -> 'Sinner'      plausibel
    'Moßt'          -> 'Most'        plausibel
    'g. Dobisin'    -> 'Dobisch'     Regel? Geraten?
    'Jacob David Weib' -> 'Weiß'     das ist keine Normalisierung,
                                     das ist eine geaenderte Lesung
    'geb. Kochin'   -> 'Ross'        Widerspruch; der Volltext sagt
                                     'geb. Rossin'

Der letzte Fall stand seit dem Pilotlauf in den Daten, und nichts hat ihn
bemerkt. Genau davor warnt `CLAUDE.md`: *Das Vokabular darf Kandidaten
ranken, aber niemals eine klare visuelle Lesung ueberschreiben - Konflikte
werden markiert, nicht stillschweigend angeglichen.*

## Was hier passiert

Aus der Kirchenbuchform werden **Kandidaten** gebildet, nach Regeln, die
im Buch stehen und nicht im Modell:

    Movierung      Sinerin -> Siner, Sinere, Sinerer, Sinerin
    Umlaut zurueck Kauffmännin -> Kauffmann
    Schreibvarianten  ll/l, ß/ss, th/t, i/y, doppelte Vokale

Dazu die **belegten Paare** aus dem eigenen Bestand: Jede
`_KB_NAME -> NAME`-Zuordnung des kuratierten OFB ist ein Beleg dafuer,
dass zwei Schreibungen zusammengehoeren. Steht das Paar dort, ist die
Normalisierung nicht geraten, sondern belegt.

## Was hier **nicht** passiert

Nichts wird geaendert. Das Urteil geht als Vermerk ins Feld, die Ampel
bleibt unberuehrt - sie ist das Ergebnis des Abgleichs, nicht der
Rechtschreibung. Wer eine Lesung fuer falsch haelt, entscheidet das in
der Maske.
"""
import argparse
import json
import re
import unicodedata

from . import db

# 35 echte -in-Namen stehen im OFB (Eberwein, Feuerstein, Hohenrein, ...).
# Sie duerfen nicht aufgeloest werden. Statt einer gepflegten Liste zaehlt
# der Bestand selbst: Kommt die Form dort als eigener Nachname vor, ist
# sie einer.
ENDUNGEN = ("in", "en", "e", "er")


def falte(s):
    s = (s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("ß", "ss")


def _entmovieren(f):
    """Kandidaten, die aus einer movierten Frauenform entstehen koennen."""
    raus = set()
    for e in ENDUNGEN:
        if f.endswith(e) and len(f) > len(e) + 2:
            stamm = f[: -len(e)]
            raus.add(stamm)
            raus |= {stamm + x for x in ("", "e", "er", "en")}
    return raus


def skelett(f):
    """Schreibvarianten derselben Zeit auf eine Form bringen.

    Verdoppelungen fallen weg, `th`/`dt`/`ck`/`y` werden vereinfacht. Der
    erste Anlauf bildete stattdessen Varianten in *eine* Richtung und
    meldete `Sinerin -> Sinner` als Widerspruch: Er konnte `nn` zu `n`
    kuerzen, aber nicht umgekehrt. Ein Skelett auf beiden Seiten hat diese
    Richtung nicht.
    """
    f = falte(f)
    for a, b in (("th", "t"), ("dt", "t"), ("ck", "k"), ("ph", "f"),
                 ("y", "i"), ("ey", "ei"), ("ai", "ei"), ("v", "f"),
                 ("z", "s"), ("c", "k")):
        f = f.replace(a, b)
    raus = []
    for c in f:
        if not raus or raus[-1] != c:
            raus.append(c)
    return "".join(raus)


def kandidaten(kb):
    """Alle kanonischen Formen, die sich aus der Kirchenbuchform ergeben."""
    roh = re.sub(r"^\s*g(eb(orene?[rn]?)?)?\.?\s+", "", str(kb or ""),
                 flags=re.I).strip()
    # Nur der Nachname; Vornamen normalisiert niemand nach diesen Regeln.
    teile = roh.split()
    if not teile:
        return set(), None
    letzt = teile[-1]
    f = falte(letzt)
    z = {f} | _entmovieren(f)
    z |= {skelett(x) for x in list(z)}
    return {x for x in z if len(x) > 2}, letzt


def belegte_paare(con):
    """(Kirchenbuchform, kanonisch) aus dem eigenen Bestand.

    Jede Zuordnung, die im kuratierten OFB steht, ist ein Beleg - und
    zwar einer, den ein Mensch verantwortet hat, nicht das Modell.
    """
    paare = set()
    for r in con.execute(
            "SELECT n.wert kb, p.surn s FROM namensform n "
            "JOIN person p ON p.id=n.person "
            "WHERE n.art='kb' AND p.surn IS NOT NULL"):
        kb = (r["kb"] or "").split()
        if kb:
            paare.add((falte(kb[-1]), falte(r["s"])))
    return paare


def bekannte_namen(con):
    return {falte(r[0]) for r in con.execute(
        "SELECT DISTINCT surn FROM person WHERE surn IS NOT NULL")}


def pruefe(wert, kb, volltext=None, paare=(), bekannt=()):
    """Urteil ueber eine einzelne Normalisierung.

    Rueckgabe (urteil, grund):

        belegt       das Paar steht so im Bestand
        regelhaft    aus der Kirchenbuchform ableitbar
        frei         nicht ableitbar, aber im Volltext gedeckt
        widerspruch  weder ableitbar noch im Volltext
    """
    if not (wert and kb):
        return None, None
    kand, letzt = kandidaten(kb)
    nach = falte(str(wert).split()[-1]) if str(wert).split() else ""
    if not (nach and letzt):
        return None, None
    kbf = falte(letzt)
    if kbf == nach:
        return "belegt", "Kirchenbuchform und kanonische Form sind gleich"
    if (kbf, nach) in paare:
        return "belegt", f"„{letzt} → {wert.split()[-1]}“ steht so im Bestand"
    if nach in kand or skelett(nach) in {skelett(x) for x in kand}:
        return "regelhaft", (f"aus „{letzt}“ nach den Movierungs- und "
                             f"Schreibregeln ableitbar")
    if kbf in bekannt and nach not in bekannt:
        return ("widerspruch",
                f"„{letzt}“ ist selbst ein Name des Bestands – "
                f"„{wert.split()[-1]}“ nicht")
    if volltext:
        vf = skelett(volltext)
        drin_kb = skelett(kbf) in vf
        drin_neu = skelett(nach) in vf
        # Der wichtigste Fall ueberhaupt: Die Kirchenbuchform steht gar
        # nicht im Volltext, die kanonische Form schon. Dann ist nicht die
        # Normalisierung fraglich, sondern die Kirchenbuchform selbst -
        # gemessen an `geb. Kochin` gegen einen Volltext, der
        # `geb. Rossin` sagt. Das stand seit dem Pilotlauf in den Daten.
        if drin_neu and not drin_kb:
            return ("kb_fraglich",
                    f"die Kirchenbuchform „{letzt}“ kommt im Volltext des "
                    f"Eintrags nicht vor, „{wert.split()[-1]}“ schon")
        if drin_neu:
            return "frei", ("nicht aus der Kirchenbuchform ableitbar, aber "
                            "im Volltext des Eintrags gedeckt")
    return ("widerspruch",
            f"„{wert.split()[-1]}“ folgt nicht aus „{letzt}“ und steht "
            f"nicht im Volltext")


def markiere(con, runde_id=None, still=True):
    """Die Felder einer Runde durchrechnen und Widersprueche vermerken."""
    paare, bekannt = belegte_paare(con), bekannte_namen(con)
    wo, par = "1=1", []
    if runde_id:
        wo, par = "e.runde=?", [runde_id]
    z = {}
    n = 0
    for f in con.execute(
            f"SELECT f.id, f.eintrag_id, f.name, f.kb_form, "
            f"       COALESCE(f.korrigiert, f.gelesen) w "
            f"FROM feld f JOIN eintrag e ON e.id=f.eintrag_id "
            f"WHERE {wo} AND f.kb_form IS NOT NULL", par):
        if not (f["name"].endswith("_name") or f["name"].endswith("_geborene")):
            continue
        vt = con.execute(
            "SELECT COALESCE(korrigiert, gelesen) v FROM feld "
            "WHERE eintrag_id=? AND name='volltext'",
            (f["eintrag_id"],)).fetchone()
        urteil, grund = pruefe(f["w"], f["kb_form"], vt["v"] if vt else None,
                               paare, bekannt)
        if not urteil:
            continue
        z[urteil] = z.get(urteil, 0) + 1
        con.execute("UPDATE feld SET kanonisch=? WHERE id=?",
                    (f["w"], f["id"]))
        if urteil in ("widerspruch", "kb_fraglich"):
            n += 1
            con.execute(
                "UPDATE feld SET beleg=COALESCE(beleg || ' · ', '') || ? "
                "WHERE id=?", (f"Normalform fraglich: {grund}", f["id"]))
    con.commit()
    if not still:
        for k, v in sorted(z.items()):
            print(f"  {k:12} {v}")
    return z, n


def _pilot():
    """An den mitgelieferten Lesungen messen – ohne Datenbankzustand."""
    from . import konfig
    p = konfig.WURZEL / "daten" / "pilot.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    con = db.verbinde()
    paare, bekannt = belegte_paare(con), bekannte_namen(con)
    z, faelle = {}, []
    for bild, s in d.get("seiten", {}).items():
        for e in s.get("eintraege", []):
            fs = e.get("felder") or {}
            vt = fs.get("volltext")
            vt = vt.get("wert") if isinstance(vt, dict) else None
            for k, v in fs.items():
                if not isinstance(v, dict):
                    continue
                if not (k.endswith("_name") or k.endswith("_geborene")):
                    continue
                urteil, grund = pruefe(v.get("wert"), v.get("kb"), vt,
                                       paare, bekannt)
                if not urteil:
                    continue
                z[urteil] = z.get(urteil, 0) + 1
                if urteil in ("frei", "widerspruch", "kb_fraglich"):
                    faelle.append((bild, e.get("lfd_nr"), k, v.get("wert"),
                                   v.get("kb"), urteil, grund))
    print(f"{sum(z.values())} Normalisierungen in den Testlesungen:")
    for k, v in sorted(z.items(), key=lambda x: -x[1]):
        print(f"  {k:12} {v:4}")
    if faelle:
        print("\nZum Ansehen:")
        for b, nr, k, w, kb, u, g in faelle:
            print(f"  [{u}] {b} Nr {nr}  {k}")
            print(f"        {kb!r} -> {w!r}")
            print(f"        {g}")
    return z


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pilot", action="store_true",
                    help="an den mitgelieferten Lesungen messen")
    ap.add_argument("--runde", type=int)
    a = ap.parse_args()
    if a.pilot:
        _pilot()
        return
    con = db.verbinde()
    z, n = markiere(con, a.runde, still=False)
    print(f"{n} Felder vermerkt")


if __name__ == "__main__":
    main()
