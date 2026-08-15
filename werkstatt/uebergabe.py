#!/usr/bin/env python3
"""Übergabepunkt: bestätigte Erfassung wird zum Bestand.

Ohne diesen Schritt bringt der Registerwechsel nichts. Die Ehe von 1812 kann
die Taufe von 1819 nur ankern, wenn sie zwischen beiden Arbeitsschritten aus
`eintrag`/`feld` in `person`/`familie`/`ereignis` überführt wurde – dort sucht
`suche.py`.

Das ist der Mechanismus "die ersten hundert tragen die nächsten tausend".

    python3 -m werkstatt.uebergabe --stand
    python3 -m werkstatt.uebergabe ehe            Probelauf
    python3 -m werkstatt.uebergabe ehe --schreib

Nur **bestätigte** Einträge werden übernommen. Was das Modell gelesen, aber
niemand geprüft hat, wird nicht zum Anker für die nächste Tranche – sonst
verfestigen sich Lesefehler stillschweigend.
"""
import argparse
import re

from . import db, journal, katalog, konfig

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
        # DEAT beim Taufeintrag: der Randvermerk am Seitenrand nennt oft
        # den Tod des Täuflings. Diese Angabe steht im Buch – sie hier
        # liegen zu lassen hieße, sie später im Sterberegister erneut
        # suchen zu müssen. Gefüllt wird das Feld von randvermerk.py.
        "ereignis": [("BIRT", "geburt_datum", "geburt_ort", "kind"),
                     ("CHR", "tauf_datum", "tauf_ort", "kind"),
                     ("DEAT", "sterbe_datum", None, "kind")],
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
            "SELECT name, rolle, gelesen, korrigiert, kb_form, person, beleg, status "
            "FROM feld WHERE eintrag_id=?", (eintrag_id,)):
        wert = f["korrigiert"] if f["korrigiert"] is not None else f["gelesen"]
        raus[f["name"]] = dict(wert=(wert or "").strip() or None,
                               kb=f["kb_form"], person=f["person"],
                               beleg=f["beleg"],
                               rolle=f["rolle"], status=f["status"])
    return raus


def rollenfeld(felder, rolle):
    """Das Namensfeld einer Rolle finden (vater -> vater_name).

    Erst die gebauten Namen, dann erst die Suche über die Rolle. Anders
    herum gewinnt, was zufällig zuerst in der Tabelle steht – bei
    `braut_vater` war das `braut_vater_beruf`, und der Beruf wurde zum
    Namen der Person.
    """
    for kandidat in (f"{rolle}_name", f"{rolle}_vorname", rolle):
        if kandidat in felder:
            return kandidat, felder[kandidat]
    for name, f in felder.items():
        if f["rolle"] == rolle:
            return name, f
    return None, None


GESCHLECHT = {"m": "M", "männlich": "M", "maennlich": "M", "knabe": "M",
              "sohn": "M", "w": "F", "weiblich": "F", "f": "F",
              "mädchen": "F", "maedchen": "F", "tochter": "F"}


def person_anlegen(con, hid, vorname, nachname, kb=None, sex=None):
    name = " ".join(x for x in (vorname, nachname) if x)
    sex = GESCHLECHT.get((sex or "").strip().lower())
    cur = con.execute(
        "INSERT INTO person (name, givn, surn, sex, herkunft) VALUES (?,?,?,?,?)",
        (name, vorname, nachname, sex, hid))
    pid = cur.lastrowid
    if kb:
        con.execute("INSERT OR IGNORE INTO namensform (person,art,wert) "
                    "VALUES (?,?,?)", (pid, "kb", kb))
    return pid


def teile_namen(wert):
    """'Johann Georg Kröneck' -> ('Johann Georg', 'Kröneck').

    Das letzte Wort als Nachnamen zu nehmen geht bei dieser Bevölkerung
    meistens gut und bei `Hans von der Au` oder `Anna Maria Vogt Wittwe`
    eben nicht. Wer es genau weiß, klammert den Nachnamen wie in GEDCOM:

        Johann Michael /von der Au/   -> ('Johann Michael', 'von der Au')

    Die Maske zeigt die Teilung mit, damit niemand raten muss, was in der
    Ausgabe landet.
    """
    w = (wert or "").strip()
    if "/" in w:
        vor, _, rest = w.partition("/")
        nach, _, hinten = rest.partition("/")
        vor = " ".join((vor + " " + hinten).split())
        nach = " ".join(nach.split())
        return vor or None, nach or None
    t = w.split()
    if not t:
        return None, None
    return (" ".join(t[:-1]) or None, t[-1]) if len(t) > 1 else (None, t[0])


def _voller_name(wert):
    """Vergleichsform eines Namens: gefaltet, ohne die GEDCOM-Schrägstriche."""
    from .suche import falte
    return " ".join(falte(str(wert or "").replace("/", " ")).split())


def _eigene_familie(con, name_v, name_m):
    """Ein Elternpaar, das **diese Erfassung** schon angelegt hat.

    Warum das nötig ist: Seit die Elternzeilen zerlegt werden, bekommt
    jeder Ehe- und Sterbeeintrag eigene Elternpersonen. Zwei Geschwister
    in derselben Runde legten damit dieselben Eltern zweimal an, und ein
    Vater, der in vier Einträgen vorkommt, stand viermal im Bestand.

    Warum die Regel eng ist: Verglichen werden **beide** Namen vollständig
    und nur unter dem, was die Erfassung selbst geschrieben hat. Gegen den
    gewachsenen Bestand darf hier nichts zusammengeführt werden – das ist
    Sache des Abgleichs, der Datum und Ort prüft. `Roth` kommt dort
    59-mal vor; ein Namensvergleich hätte jeden davon bestätigt.

    Verglichen wird der **ganze** Name, nicht Vor- und Nachname getrennt.
    Grund: Steht bei der Mutter nur „Regina“, macht `teile_namen` daraus
    einen Nachnamen ohne Vornamen – und eine Suche über den Vornamen fand
    dasselbe Paar viermal nicht wieder. Gemessen: vier Familien für
    Daniel Delinger und Regina, wo eine gehört.
    """
    a, b = _voller_name(name_v), _voller_name(name_m)
    if not (a and b):
        return None
    for r in con.execute(
            "SELECT f.id, f.mann, f.frau, pm.name nm, pf.name nf "
            "FROM familie f "
            "JOIN person pm ON pm.id=f.mann "
            "JOIN person pf ON pf.id=f.frau "
            "JOIN herkunft h ON h.id=f.herkunft "
            "WHERE h.art='erfassung'"):
        if _voller_name(r["nm"]) == a and _voller_name(r["nf"]) == b:
            return dict(id=r["id"], mann=r["mann"], frau=r["frau"])
    return None


def namensteile(felder, rolle):
    """Vor- und Nachname einer Rolle. Der Nachname darf fehlen.

    Im Taufregister steht beim Kind **nur der Vorname** – sein Nachname
    ergibt sich aus dem Vater. Die Vorgängerfassung nahm dasselbe Feld für
    beides und schrieb `Georg Christian /Georg Christian/` in die Ausgabe.
    """
    vn = felder.get(f"{rolle}_vorname", {}).get("wert")
    nn = felder.get(f"{rolle}_name", {}).get("wert")
    if nn and not vn:
        vn, nn = teile_namen(nn)
    return vn, nn


def uebernimm(con, art, schreib=False, runde_id=None, marke=None):
    # Der Bauplan wird aus dem Feldkatalog abgeleitet, nicht gepflegt. Die
    # Liste BAUPLAN weiter oben ist nur noch der Rückfall für Register, die
    # der Katalog nicht kennt – sonst hätte jede Änderung an der Aktkarte
    # zwei Stellen, und die zweite bliebe zurück. Genau das war beim
    # Sterbedatum aus dem Randvermerk passiert.
    plan = katalog.bauplan(art, con) if art in katalog.KATALOG else None
    if plan:
        plan = dict(plan, personen=plan["personen"],
                    familie=plan["paar"], kind=plan["kind"],
                    paare=plan.get("paare"), kinder=plan.get("kinder"),
                    ereignis=[(e["tag"], e["datum"], e["ort"], e["traeger"])
                              for e in plan["ereignis"]])
    else:
        plan = BAUPLAN.get(art)
    if not plan:
        return {"uebersprungen": f"kein Bauplan für {art}"}
    # Die Herkunft wird je Runde geführt, nicht je Register. Damit ist zu
    # jeder Person nachvollziehbar, welche Tranche sie angelegt hat – und
    # eine Runde lässt sich rückstandslos verwerfen.
    hid = db.herkunft_id(con, "erfassung", marke or art,
                         "aus bestätigter Erfassung", gilt="beleg")
    z = dict(eintraege=0, personen_neu=0, personen_verknuepft=0,
             familien=0, familien_gefunden=0, nachname_geerbt=0,
             ereignisse=0, kinder=0, merkmale=0, dubletten_vermieden=0)

    wo = "register=? AND status='bestaetigt'"
    par = [art]
    if runde_id:
        wo += " AND runde=?"
        par.append(runde_id)
    for e in con.execute(
            f"SELECT id, bild, nr, jahr FROM eintrag WHERE {wo} "
            "ORDER BY bild, nr", par):
        felder = werte(con, e["id"])
        z["eintraege"] += 1
        pid = {}

        # Der Nachname des Haushaltsvorstands vererbt sich auf die Rollen,
        # für die das Register keinen eigenen führt – beim Täufling steht
        # nur der Vorname.
        erbe = None
        if plan.get("familie"):
            erbe = namensteile(felder, plan["familie"][0])[1]

        # Elternpaare, die diese Erfassung schon angelegt hat, wieder
        # verwenden statt neu anzulegen. Muss vor der Personenschleife
        # stehen: Danach waeren die Dubletten schon geschrieben.
        schon, schon_fam = {}, {}
        for kindrolle, (vr, mr) in (plan.get("kinder") or []):
            if vr in schon:
                continue
            _, fv = rollenfeld(felder, vr)
            _, fm = rollenfeld(felder, mr)
            da = _eigene_familie(con, (fv or {}).get("wert"),
                                 (fm or {}).get("wert"))
            if da:
                schon[vr], schon[mr] = da["mann"], da["frau"]
                schon_fam[(vr, mr)] = da["id"]

        for rolle in plan["personen"]:
            if rolle in schon:
                pid[rolle] = schon[rolle]
                z["dubletten_vermieden"] += 1
                continue
            name, f = rollenfeld(felder, rolle)
            if not f or not f["wert"]:
                continue
            if f["person"]:                       # find-and-use: schon zugeordnet
                pid[rolle] = f["person"]
                z["personen_verknuepft"] += 1
                continue
            vn, nn = namensteile(felder, rolle)
            if not nn:
                nn = erbe
                if nn:
                    z["nachname_geerbt"] += 1
            sex = felder.get(f"{rolle}_geschlecht", {}).get("wert")
            if schreib:
                pid[rolle] = person_anlegen(con, hid, vn, nn, f["kb"], sex)
                journal.notiere(
                    con, "neu_person", ziel=str(pid[rolle]),
                    daten=dict(givn=vn, surn=nn, rolle=rolle),
                    quelle=f"{art} {e['bild']} Nr. {e['nr']}",
                    beleg=f["beleg"] or "kein Treffer im Bestand – neu angelegt")
            else:
                pid[rolle] = -1                 # Platzhalter im Probelauf
            z["personen_neu"] += 1

        # Mehrere Paare je Eintrag. Beim Taufeintrag ist es eines, beim
        # Eheeintrag sind es drei: das Brautpaar und die beiden
        # Elternpaare. Vorher kannte der Bauplan genau eines, und die
        # Eltern der Brautleute wurden zu Personen ohne Familie - der
        # Elternehe-Anker lief bei Eheeintraegen deshalb ins Leere.
        familien = {}
        paare = plan.get("paare") or (
            [plan["familie"]] if plan.get("familie") else [])
        for a, b in paare:
            if (a, b) in schon_fam:
                familien[(a, b)] = schon_fam[(a, b)]
                continue
            if pid.get(a) or pid.get(b):
                # Erst suchen, dann anlegen. Der Elternehe-Anker findet die
                # Familie ja gerade – sie danach ein zweites Mal anzulegen
                # macht den Treffer wieder zunichte.
                #
                # Gemessen vor dieser Prüfung: von 22 übergebenen Familien
                # gab es 10 mit denselben Eltern bereits im Bestand. Sie
                # wären so in die GEDCOM-Datei gewandert.
                da = None
                if pid.get(a) and pid.get(b):
                    da = con.execute(
                        "SELECT id FROM familie WHERE mann=? AND frau=?",
                        (pid[a], pid[b])).fetchone()
                if da:
                    familien[(a, b)] = da["id"]
                    z["familien_gefunden"] += 1
                elif schreib:
                    cur = con.execute(
                        "INSERT INTO familie (mann, frau, herkunft) VALUES (?,?,?)",
                        (pid.get(a), pid.get(b), hid))
                    familien[(a, b)] = cur.lastrowid
                    journal.notiere(
                        con, "neu_familie", ziel=str(cur.lastrowid),
                        daten=dict(mann=pid.get(a), frau=pid.get(b)),
                        quelle=f"{art} {e['bild']} Nr. {e['nr']}",
                        beleg="keine gemeinsame Familie im Bestand")
                    z["familien"] += 1
                else:
                    familien[(a, b)] = -1
                    z["familien"] += 1

        # Die Familie des Eintrags selbst - an ihr haengen die Ereignisse.
        fam = familien.get(tuple(plan["familie"])) if plan.get("familie") else None

        for kindrolle, paar in (plan.get("kinder") or (
                [(plan["kind"], plan["familie"])]
                if plan.get("kind") and plan.get("familie") else [])):
            f2 = familien.get(tuple(paar))
            if not (f2 and pid.get(kindrolle)):
                continue
            if schreib and f2 > 0 and pid[kindrolle] > 0:
                con.execute("INSERT OR IGNORE INTO kind (familie, person) VALUES (?,?)",
                            (f2, pid[kindrolle]))
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

        # Merkmale: alles, was kein Ereignis ist – Beruf, Wohnort,
        # Religion, Rufname und die Kirchenbuchformen. Ohne diesen Schritt
        # deklariert der Katalog Ziele, die nie jemand schreibt.
        for m in plan.get("merkmal", []):
            f = felder.get(m["feld"])
            if not f:
                continue
            wert = (f.get("kb") if m["kb"] else f.get("wert")) or ""
            wert = str(wert).strip()
            # Die Kirchenbuchform nur, wenn sie sich unterscheidet – sonst
            # steht dieselbe Angabe zweimal im Bestand.
            if not wert or (m["kb"] and wert == str(f.get("wert") or "").strip()):
                continue
            tr = m["traeger"]
            ziel_p = pid.get(tr) if tr and tr != "familie" else None
            ziel_f = fam if tr == "familie" else None
            if not (ziel_p or ziel_f):
                continue
            if schreib and (ziel_p or 0) > 0 or (ziel_f or 0) > 0:
                con.execute(
                    "INSERT OR IGNORE INTO merkmal "
                    "(person, familie, tag, wert, feld, kb, quelle) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (ziel_p, ziel_f, m["tag"], wert, m["feld"],
                     1 if m["kb"] else 0,
                     f"{art} {e['bild']} Nr. {e['nr']}"))
            z["merkmale"] += 1

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
        print("\n(nichts geschrieben – mit --schreib übernehmen)")


if __name__ == "__main__":
    main()
