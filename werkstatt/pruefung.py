#!/usr/bin/env python3
"""Bestandsprüfung: logische Widersprüche im Bestand finden.

    python3 -m werkstatt.pruefung
    python3 -m werkstatt.pruefung --regel mutter_zu_alt
    python3 -m werkstatt.pruefung --nur fehler

Nachgebaut nach zwei etablierten Vorbildern, damit hier nichts neu erfunden
wird, was seit Jahren funktioniert:

  **Gramps**, `Verify the Data` — 43 Regeln, 15 Grenzwerte, getrennt nach
  Fehler (logisch unmöglich) und Warnung (auffällig, aber denkbar).
  Vorgaben: Höchstalter 90, Altersabstand Ehepartner 30, Jahre zwischen
  Kindern 8, Spanne aller Kinder 25, Heirat ab 17 bis 50, Mutter 17–48,
  Vater 18–65, höchstens 3 Ehen, 12 bzw. 15 Kinder.

  **Ahnenblatt**, Plausibilitätsprüfung — sieben Altersgrenzen
  (Mindestalter bei Geburt eines Kindes, Höchstalter Mutter, Höchstalter
  Vater, Mindestalter bei Eheschließung, Altersdifferenz Ehepartner,
  Altersdifferenz Geschwister, maximales Alter) sowie Prüfungen auf
  doppelte Personen, unbekanntes Geschlecht, Personen ohne Verweise,
  fehlende Rückverweise und Datumsangaben in der Zukunft.

## Was hier anders ist

Beide Programme prüfen einen **fertigen Bestand auf innere Widersprüche**.
Die Werkstatt braucht das auch — aber sie braucht zusätzlich etwas anderes:
zu entscheiden, ob ein **Zuordnungsvorschlag** überhaupt möglich ist. Das
tut `abgleich._plausibel()` und ist nicht dasselbe.

    Bestandsprüfung   „diese Angaben widersprechen einander"   -> hier
    Match-Filter      „dieses Paar kann nicht die Eltern sein" -> abgleich

Die Grenzwerte sind dieselben, der Zeitpunkt ist ein anderer.

## Angepasst an Kirchenbücher des 19. Jahrhunderts

Nicht alles aus den Vorlagen taugt hier unverändert:

  * **Mehrfachehen** sind kein Verdacht, sondern Normalfall. Bei hoher
    Sterblichkeit ist die dritte Ehe häufig; die Grenze steht auf 4 statt 3.
  * **Gleicher Nachname der Eheleute** ist im Dorf verbreitet, nicht
    verdächtig — bleibt Warnung, aber ohne Nachdruck.
  * **Unbekanntes Geschlecht** ist dagegen sehr wohl ein Befund: Die
    Übergabe setzt es nur, wenn das Register ein Feld dafür führt.
  * **Geburtsabstand unter neun Monaten** meldet Ahnenblatt. Zwillinge
    dürfen dabei nicht auffallen — gleiches Datum wird ausgenommen.
"""
import argparse
import re
from collections import defaultdict

from . import db, einstellungen

MONAT = {m: i for i, m in enumerate(
    "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}

# Grenzwerte, mit Herkunft und Einheit. Die Zahlen stammen aus Gramps bzw.
# Ahnenblatt; wo sie abweichen, steht die Begründung dabei.
#
#   Gramps `Verify the Data` führt 15 Grenzwerte:
#     oldage 90 · hwdif 30 · cspace 8 · cbspan 25 · yngmar 17 · oldmar 50
#     oldmom 48 · yngmom 17 · yngdad 18 · olddad 65 · wedder 3
#     mxchildmom 12 · mxchilddad 15 · lngwdw 30 · oldunm 99
#
#   Ahnenblatt führt sieben Altersgrenzen: Mindestalter bei Geburt eines
#   Kindes, Höchstalter der Mutter, Höchstalter des Vaters, Mindestalter bei
#   Eheschließung, Altersdifferenz Ehepartner, Altersdifferenz Geschwister,
#   maximales Alter einer Person.
GRENZWERTE = [
    # (schlüssel, vorgabe, einheit, quelle, beschriftung, erläuterung)
    ("hoechstalter", 90, "Jahre", "Gramps oldage",
     "Höchstalter einer Person", ""),
    ("ehe_altersabstand", 30, "Jahre", "Gramps hwdif · Ahnenblatt",
     "Altersabstand der Eheleute", ""),
    ("heirat_min", 17, "Jahre", "Gramps yngmar · Ahnenblatt",
     "Mindestalter bei der Heirat", ""),
    ("heirat_max", 50, "Jahre", "Gramps oldmar",
     "Höchstalter bei der Heirat", ""),
    ("mutter_alter_min", 17, "Jahre", "Gramps yngmom · Ahnenblatt",
     "Mutter mindestens", ""),
    ("mutter_alter_max", 48, "Jahre", "Gramps oldmom · Ahnenblatt",
     "Mutter höchstens", ""),
    ("vater_alter_min", 18, "Jahre", "Gramps yngdad · Ahnenblatt",
     "Vater mindestens", ""),
    ("vater_alter_max", 65, "Jahre", "Gramps olddad · Ahnenblatt",
     "Vater höchstens", ""),
    ("kinder_abstand", 8, "Jahre", "Gramps cspace",
     "Lücke zwischen zwei Kindern", ""),
    ("geschwister_abstand_min_monate", 9, "Monate", "Ahnenblatt",
     "Kinder dichter als", "Zwillinge sind ausgenommen — gleiches Datum "
     "gilt nicht als Befund."),
    ("kinder_spanne", 25, "Jahre", "Gramps cbspan · Ahnenblatt",
     "Spanne aller Kinder einer Familie", ""),
    ("kinder_mutter_max", 12, "Kinder", "Gramps mxchildmom",
     "Kinder je Mutter", ""),
    ("kinder_vater_max", 15, "Kinder", "Gramps mxchilddad",
     "Kinder je Vater", ""),
    ("ehen_max", 4, "Ehen", "Gramps wedder (3), hier 4",
     "Ehen je Person",
     "Gramps sagt 3. Bei der Sterblichkeit des 19. Jahrhunderts ist die "
     "dritte Ehe häufig und die vierte kein Fehler, nur bemerkenswert."),
]
GRENZEN = {k: v for k, v, *_ in GRENZWERTE}


# ------------------------------------------------------------------ Datum
def datum(s):
    """GEDCOM-Datum zu (Jahr, Monat, Tag). Fehlendes bleibt None.

    Bewusst nachsichtig: `ABT 1750`, `BET 1740 AND 1745`, `um 1780` sollen
    ihr Jahr hergeben, statt die ganze Prüfung fallen zu lassen.
    """
    s = str(s or "").upper()
    if not s.strip():
        return None
    j = re.search(r"\b(1[0-9]\d\d|20\d\d)\b", s)
    if not j:
        return None
    jahr = int(j.group(1))
    m = re.search(r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b", s)
    t = re.match(r"^\D*(\d{1,2})\s+[A-Z]{3}", s)
    return (jahr, MONAT.get(m.group(1)) if m else None,
            int(t.group(1)) if t else None)


def unscharf(s):
    return bool(re.search(r"\b(ABT|BEF|AFT|EST|CAL|BET|FROM|UM|CA)\b",
                          str(s or "").upper()))


def monate(a, b):
    """Abstand in Monaten, so genau wie die Daten hergeben."""
    if not a or not b:
        return None
    return (b[0] - a[0]) * 12 + ((b[1] or 1) - (a[1] or 1))


def frueher(a, b):
    """a liegt sicher vor b — bei gleicher Genauigkeit verglichen."""
    if not a or not b:
        return False
    tiefe = min(len([x for x in a if x is not None]),
                len([x for x in b if x is not None]))
    return tuple(a[:tiefe]) < tuple(b[:tiefe])


def jahre(a, b):
    if not a or not b:
        return None
    n = b[0] - a[0]
    if a[1] and b[1] and (b[1], b[2] or 1) < (a[1], a[2] or 1):
        n -= 1
    return n


# ---------------------------------------------------------------- Bestand
def lade(con):
    p = {}
    for r in con.execute("SELECT id, name, givn, surn, sex, herkunft FROM person"):
        p[r["id"]] = dict(r, ereignis={})
    for r in con.execute("SELECT person, art, datum FROM ereignis "
                         "WHERE person IS NOT NULL"):
        x = p.get(r["person"])
        if x is not None and r["art"] not in x["ereignis"]:
            x["ereignis"][r["art"]] = r["datum"]
    f = {}
    for r in con.execute("SELECT id, mann, frau FROM familie"):
        f[r["id"]] = dict(r, kinder=[], ereignis={})
    for r in con.execute("SELECT familie, art, datum FROM ereignis "
                         "WHERE familie IS NOT NULL"):
        x = f.get(r["familie"])
        if x is not None and r["art"] not in x["ereignis"]:
            x["ereignis"][r["art"]] = r["datum"]
    for r in con.execute("SELECT familie, person FROM kind"):
        if r["familie"] in f:
            f[r["familie"]]["kinder"].append(r["person"])
    ehen = defaultdict(list)
    for fid, x in f.items():
        for s in (x["mann"], x["frau"]):
            if s:
                ehen[s].append(fid)
    return p, f, ehen


def _d(x, art):
    return datum(x["ereignis"].get(art))


def geburt(x):
    return _d(x, "BIRT") or _d(x, "CHR")


# ---------------------------------------------------------------- Regeln
# (schluessel, schwere, titel) — die Reihenfolge bestimmt die Ausgabe.
REGELN = [
    ("geburt_nach_tod", "fehler", "Geburt nach dem Tod"),
    ("taufe_vor_geburt", "fehler", "Taufe vor der Geburt"),
    ("begraebnis_vor_tod", "fehler", "Begräbnis vor dem Tod"),
    ("taufe_nach_begraebnis", "fehler", "Taufe nach dem Begräbnis"),
    ("heirat_vor_geburt", "fehler", "Heirat vor der eigenen Geburt"),
    ("heirat_nach_tod", "fehler", "Heirat nach dem eigenen Tod"),
    ("kind_vor_geburt_des_elternteils", "fehler", "Kind vor der Geburt des Elternteils"),
    ("kind_nach_tod_der_mutter", "fehler", "Kind nach dem Tod der Mutter"),
    ("kind_lange_nach_tod_des_vaters", "fehler", "Kind lange nach dem Tod des Vaters"),
    ("jahr_unmoeglich", "fehler", "Jahreszahl außerhalb des Möglichen"),

    ("hohes_alter", "warnung", "sehr hohes Alter"),
    ("mutter_zu_jung", "warnung", "Mutter sehr jung"),
    ("mutter_zu_alt", "warnung", "Mutter sehr alt"),
    ("vater_zu_jung", "warnung", "Vater sehr jung"),
    ("vater_zu_alt", "warnung", "Vater sehr alt"),
    ("heirat_zu_jung", "warnung", "sehr jung bei der Heirat"),
    ("heirat_zu_alt", "warnung", "sehr alt bei der Heirat"),
    ("ehe_altersabstand", "warnung", "großer Altersabstand der Eheleute"),
    ("kinder_abstand_gross", "warnung", "große Lücke zwischen Geschwistern"),
    ("kinder_abstand_klein", "warnung", "Geschwister zu dicht beieinander"),
    ("kinder_spanne", "warnung", "sehr lange Geburtenfolge"),
    ("zu_viele_kinder", "warnung", "sehr viele Kinder"),
    ("zu_viele_ehen", "warnung", "sehr viele Ehen"),
    ("geschlecht_unbekannt", "warnung", "Geschlecht nicht gesetzt"),
    ("ohne_verweis", "warnung", "Person ohne jede Verknüpfung"),
    ("mehrere_elternfamilien", "warnung", "mehrere Elternfamilien"),
    ("ehepaar_gleicher_name", "warnung", "Eheleute mit gleichem Nachnamen"),
]
TITEL = {k: t for k, _, t in REGELN}
SCHWERE = {k: s for k, s, _ in REGELN}


def pruefe(con, grenzen=None):
    """Alle Regeln über den ganzen Bestand. Rückgabe: Liste von Befunden."""
    g = dict(GRENZEN)
    g.update(grenzen or {})
    for k in g:
        g[k] = einstellungen.zahl(con, f"pruef.{k}", g[k])
    p, fam, ehen = lade(con)
    kindschaft = defaultdict(list)
    for fid, x in fam.items():
        for k in x["kinder"]:
            kindschaft[k].append(fid)

    raus = []

    def melde(regel, pid=None, fid=None, text=""):
        raus.append(dict(regel=regel, schwere=SCHWERE[regel],
                         titel=TITEL[regel], person=pid, familie=fid,
                         name=(p[pid]["name"] if pid in p else None), text=text))

    # ---- je Person
    for pid, x in p.items():
        geb, chr_, tod, bur = (_d(x, "BIRT"), _d(x, "CHR"),
                               _d(x, "DEAT"), _d(x, "BURI"))
        if geb and tod and frueher(tod, geb):
            melde("geburt_nach_tod", pid, text=f"* {geb[0]} nach † {tod[0]}")
        if geb and chr_ and frueher(chr_, geb):
            melde("taufe_vor_geburt", pid, text=f"~ {chr_[0]} vor * {geb[0]}")
        if tod and bur and frueher(bur, tod):
            melde("begraebnis_vor_tod", pid, text=f"⚰ {bur[0]} vor † {tod[0]}")
        if chr_ and bur and frueher(bur, chr_):
            melde("taufe_nach_begraebnis", pid, text=f"~ {chr_[0]} nach ⚰ {bur[0]}")
        for art, d in x["ereignis"].items():
            dd = datum(d)
            if dd and not (1000 <= dd[0] <= 2100):
                melde("jahr_unmoeglich", pid, text=f"{art} {d}")
        a = jahre(geburt(x), tod)
        if a is not None and a > g["hoechstalter"]:
            melde("hohes_alter", pid, text=f"{a} Jahre")
        if not x["sex"]:
            melde("geschlecht_unbekannt", pid)
        if not ehen.get(pid) and not kindschaft.get(pid):
            melde("ohne_verweis", pid)
        if len(kindschaft.get(pid, [])) > 1:
            melde("mehrere_elternfamilien", pid,
                  text=f"{len(kindschaft[pid])} Familien")
        if len(ehen.get(pid, [])) > g["ehen_max"]:
            melde("zu_viele_ehen", pid, text=f"{len(ehen[pid])} Ehen")

    # ---- je Familie
    for fid, x in fam.items():
        mann, frau = p.get(x["mann"]), p.get(x["frau"])
        marr = _d(x, "MARR")
        for s, wer in ((mann, "Mann"), (frau, "Frau")):
            if not s:
                continue
            gb, td = geburt(s), _d(s, "DEAT")
            if marr and gb and frueher(marr, gb):
                melde("heirat_vor_geburt", s["id"], fid,
                      f"{wer}: ⚭ {marr[0]} vor * {gb[0]}")
            if marr and td and frueher(td, marr):
                melde("heirat_nach_tod", s["id"], fid,
                      f"{wer}: ⚭ {marr[0]} nach † {td[0]}")
            a = jahre(gb, marr)
            if a is not None and a < g["heirat_min"]:
                melde("heirat_zu_jung", s["id"], fid, f"{wer}: {a} Jahre")
            if a is not None and a > g["heirat_max"]:
                melde("heirat_zu_alt", s["id"], fid, f"{wer}: {a} Jahre")
        if mann and frau:
            gm, gf = geburt(mann), geburt(frau)
            if gm and gf and abs(gm[0] - gf[0]) > g["ehe_altersabstand"]:
                melde("ehe_altersabstand", None, fid,
                      f"{abs(gm[0] - gf[0])} Jahre")
            # Im Dorf verbreitet, nicht verdächtig — aber gelegentlich ein
            # Zeichen für eine Fehlzuordnung.
            if (mann["surn"] and frau["surn"]
                    and mann["surn"].lower() == frau["surn"].lower()):
                melde("ehepaar_gleicher_name", None, fid, mann["surn"])

        # ---- Kinder
        kinder = [(geburt(p[k]), k) for k in x["kinder"] if k in p]
        # Nach Datum sortieren, aber None ist nicht vergleichbar: Ein Kind
        # mit bloßer Jahresangabe ergibt (1750, None, None).
        kinder = sorted(((d, k) for d, k in kinder if d),
                        key=lambda x: (x[0][0], x[0][1] or 0, x[0][2] or 0))
        for elt, jung, alt, wer in ((mann, "vater_alter_min", "vater_alter_max", "Vater"),
                                    (frau, "mutter_alter_min", "mutter_alter_max", "Mutter")):
            if not elt:
                continue
            ge = geburt(elt)
            td = _d(elt, "DEAT")
            for d, k in kinder:
                a = jahre(ge, d)
                if a is None:
                    pass
                elif a < 0:
                    melde("kind_vor_geburt_des_elternteils", elt["id"], fid,
                          f"{wer} * {ge[0]}, Kind * {d[0]}")
                elif a < g[jung]:
                    melde(f"{wer.lower()}_zu_jung", elt["id"], fid,
                          f"{a} Jahre bei {p[k]['name']}")
                elif a > g[alt]:
                    melde(f"{wer.lower()}_zu_alt", elt["id"], fid,
                          f"{a} Jahre bei {p[k]['name']}")
                if td and frueher(td, d):
                    # Nachgeborene Kinder gibt es; beim Vater sind bis zu
                    # neun Monate nach seinem Tod unauffällig.
                    if wer == "Mutter":
                        melde("kind_nach_tod_der_mutter", elt["id"], fid,
                              f"† {td[0]}, Kind * {d[0]}")
                    elif (monate(td, d) or 0) > 9:
                        melde("kind_lange_nach_tod_des_vaters", elt["id"], fid,
                              f"† {td[0]}, Kind * {d[0]}")
        for (d1, k1), (d2, k2) in zip(kinder, kinder[1:]):
            n = monate(d1, d2)
            if n is None:
                continue
            if n > g["kinder_abstand"] * 12:
                melde("kinder_abstand_gross", None, fid,
                      f"{n // 12} Jahre zwischen {p[k1]['name']} und {p[k2]['name']}")
            # Zwillinge dürfen nicht auffallen: gleicher Tag ist kein Befund.
            elif 0 < n < g["geschwister_abstand_min_monate"] and d1 != d2:
                melde("kinder_abstand_klein", None, fid,
                      f"{n} Monate zwischen {p[k1]['name']} und {p[k2]['name']}")
        if len(kinder) > 1:
            spanne = kinder[-1][0][0] - kinder[0][0][0]
            if spanne > g["kinder_spanne"]:
                melde("kinder_spanne", None, fid, f"{spanne} Jahre")
        if frau and len(x["kinder"]) > g["kinder_mutter_max"]:
            melde("zu_viele_kinder", frau["id"], fid,
                  f"{len(x['kinder'])} Kinder")
        elif mann and len(x["kinder"]) > g["kinder_vater_max"]:
            melde("zu_viele_kinder", mann["id"], fid,
                  f"{len(x['kinder'])} Kinder")
    return raus


def zusammenfassung(befunde):
    z = defaultdict(int)
    for b in befunde:
        z[b["regel"]] += 1
    return dict(z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regel", help="nur diese Regel, mit Einzelfällen")
    ap.add_argument("--nur", choices=("fehler", "warnung"))
    ap.add_argument("--grenze", type=int, default=8, help="Beispiele je Regel")
    a = ap.parse_args()
    con = db.verbinde()
    befunde = pruefe(con)

    if a.regel:
        treffer = [b for b in befunde if b["regel"] == a.regel]
        print(f"=== {TITEL.get(a.regel, a.regel)} — {len(treffer)} Fälle ===")
        for b in treffer:
            print(f"  {(b['name'] or ''):38} {b['text']}")
        return

    z = zusammenfassung(befunde)
    n_p = con.execute("SELECT count(*) FROM person").fetchone()[0]
    n_f = con.execute("SELECT count(*) FROM familie").fetchone()[0]
    print(f"Bestand: {n_p} Personen, {n_f} Familien\n")
    for schwere in ("fehler", "warnung"):
        if a.nur and a.nur != schwere:
            continue
        teil = [(k, s, t) for k, s, t in REGELN if s == schwere and z.get(k)]
        n = sum(z[k] for k, _, _ in teil)
        print(f"=== {schwere.upper()} — {n} Befunde ===")
        if not teil:
            print("  keine\n")
            continue
        for k, _, t in teil:
            print(f"  {z[k]:6}  {t:42} --regel {k}")
        print()
    print(f"insgesamt {len(befunde)} Befunde")


if __name__ == "__main__":
    main()
