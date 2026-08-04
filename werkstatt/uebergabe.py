#!/usr/bin/env python3
"""Übergabepunkt: bestätigte Erfassung wird zum Bestand.

Ohne diesen Schritt bringt der Registerwechsel nichts. Die Ehe von 1812 kann
die Taufe von 1819 nur ankern, wenn sie zwischen beiden Arbeitsschritten aus
`eintrag`/`feld` in `person`/`familie`/`ereignis` überführt wurde — dort sucht
`suche.py`.

Das ist der Mechanismus "die ersten hundert tragen die nächsten tausend".

    python3 -m werkstatt.uebergabe --stand
    python3 -m werkstatt.uebergabe ehe            Probelauf
    python3 -m werkstatt.uebergabe ehe --schreib

Nur **bestätigte** Einträge werden übernommen. Was das Modell gelesen, aber
niemand geprüft hat, wird nicht zum Anker für die nächste Tranche — sonst
verfestigen sich Lesefehler stillschweigend.
"""
import argparse
import re

from . import db, konfig

# Welche Rolle wird zu welcher Person, und was verbindet sie
BAUPLAN = {
    "ehe": {
        "personen": ["braeutigam", "braut"],
        "familie": ("braeutigam", "braut"),
        "ereignis": [("MARR", "trauung_datum", "trauung_ort", "familie")],
    },
    "taufe": {
        "personen": ["kind", "vater", "mutter"],
        "familie": ("vater", "mutter"),
        "kind": "kind",
        "ereignis": [("BIRT", "geburt_datum", "geburt_ort", "kind"),
                     ("CHR", "tauf_datum", "tauf_ort", "kind")],
    },
    "tod": {
        "personen": ["verstorbener"],
        "ereignis": [("DEAT", "sterbe_datum", None, "verstorbener"),
                     ("BURI", "begraebnis_datum", None, "verstorbener")],
    },
}


def jahr(s):
    m = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", str(s or ""))
    return int(m.group(1)) if m else None


def werte(con, eintrag_id):
    """Felder eines Eintrags: name -> (wert, kb, person_id, rolle)."""
    raus = {}
    for f in con.execute(
            "SELECT name, rolle, gelesen, korrigiert, kb_form, person, status "
            "FROM feld WHERE eintrag_id=?", (eintrag_id,)):
        wert = f["korrigiert"] if f["korrigiert"] is not None else f["gelesen"]
        raus[f["name"]] = dict(wert=(wert or "").strip() or None,
                               kb=f["kb_form"], person=f["person"],
                               rolle=f["rolle"], status=f["status"])
    return raus


def rollenfeld(felder, rolle):
    """Das Namensfeld einer Rolle finden (vater -> vater_name)."""
    for name, f in felder.items():
        if f["rolle"] == rolle:
            return name, f
    for kandidat in (f"{rolle}_name", f"{rolle}_vorname", rolle):
        if kandidat in felder:
            return kandidat, felder[kandidat]
    return None, None


def person_anlegen(con, hid, vorname, nachname, kb=None):
    name = " ".join(x for x in (vorname, nachname) if x)
    cur = con.execute(
        "INSERT INTO person (name, givn, surn, herkunft) VALUES (?,?,?,?)",
        (name, vorname, nachname, hid))
    pid = cur.lastrowid
    if kb:
        con.execute("INSERT OR IGNORE INTO namensform (person,art,wert) "
                    "VALUES (?,?,?)", (pid, "kb", kb))
    return pid


def teile_namen(wert):
    """'Johann Georg Kröneck' -> ('Johann Georg', 'Kröneck')."""
    t = (wert or "").split()
    if not t:
        return None, None
    return (" ".join(t[:-1]) or None, t[-1]) if len(t) > 1 else (None, t[0])


def uebernimm(con, art, schreib=False):
    plan = BAUPLAN.get(art)
    if not plan:
        return {"uebersprungen": f"kein Bauplan für {art}"}
    hid = db.herkunft_id(con, "erfassung", art, "aus bestätigter Erfassung")
    z = dict(eintraege=0, personen_neu=0, personen_verknuepft=0,
             familien=0, ereignisse=0, kinder=0)

    for e in con.execute(
            "SELECT id, bild, nr, jahr FROM eintrag "
            "WHERE register=? AND status='bestaetigt' ORDER BY bild, nr", (art,)):
        felder = werte(con, e["id"])
        z["eintraege"] += 1
        pid = {}

        for rolle in plan["personen"]:
            name, f = rollenfeld(felder, rolle)
            if not f or not f["wert"]:
                continue
            if f["person"]:                       # find-and-use: schon zugeordnet
                pid[rolle] = f["person"]
                z["personen_verknuepft"] += 1
                continue
            vn = felder.get(f"{rolle}_vorname", {}).get("wert")
            if vn is None:
                vn, nn = teile_namen(f["wert"])
            else:
                nn = f["wert"]
            pid[rolle] = (person_anlegen(con, hid, vn, nn, f["kb"])
                          if schreib else -1)   # -1 = Platzhalter im Probelauf
            z["personen_neu"] += 1

        fam = None
        if plan.get("familie"):
            a, b = plan["familie"]
            if pid.get(a) or pid.get(b):
                if schreib:
                    cur = con.execute(
                        "INSERT INTO familie (mann, frau, herkunft) VALUES (?,?,?)",
                        (pid.get(a), pid.get(b), hid))
                    fam = cur.lastrowid
                else:
                    fam = -1
                z["familien"] += 1

        if plan.get("kind") and fam and pid.get(plan["kind"]):
            if schreib and fam > 0:
                con.execute("INSERT OR IGNORE INTO kind (familie, person) VALUES (?,?)",
                            (fam, pid[plan["kind"]]))
            z["kinder"] += 1

        for art_e, feld_dat, feld_ort, traeger in plan["ereignis"]:
            d = felder.get(feld_dat, {}).get("wert")
            if not d:
                continue
            ort = felder.get(feld_ort, {}).get("wert") if feld_ort else None
            ziel_p = pid.get(traeger) if traeger != "familie" else None
            ziel_f = fam if traeger == "familie" else None
            if not (ziel_p or ziel_f):
                continue
            if schreib:
                con.execute(
                    "INSERT INTO ereignis (person,familie,art,datum,jahr,ort,quelle) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (ziel_p, ziel_f, art_e, d, jahr(d), ort,
                     f"{art} {e['bild']} Nr. {e['nr']}"))
            z["ereignisse"] += 1

    if schreib:
        con.commit()
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("register", nargs="*")
    ap.add_argument("--schreib", action="store_true")
    ap.add_argument("--stand", action="store_true")
    a = ap.parse_args()
    con = db.verbinde()

    if a.stand:
        for r in con.execute(
                "SELECT register, status, count(*) n FROM eintrag "
                "GROUP BY register, status ORDER BY register"):
            print(f"  {r['register']:8} {r['status']:12} {r['n']:5}")
        for t, n in db.stand(con).items():
            print(f"  {t:12} {n:6}")
        return

    for art in (a.register or list(konfig.register())):
        z = uebernimm(con, art, a.schreib)
        modus = "geschrieben" if a.schreib else "Probelauf"
        print(f"{art} ({modus}): " +
              " · ".join(f"{k} {v}" for k, v in z.items()))
    if not a.schreib:
        print("\n(nichts geschrieben — mit --schreib übernehmen)")


if __name__ == "__main__":
    main()
