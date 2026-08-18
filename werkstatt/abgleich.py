#!/usr/bin/env python3
"""Abgleich nach dem Lesen: Anker suchen, Ampel setzen.

    python3 -m werkstatt.abgleich --runde 1
    python3 -m werkstatt.abgleich --messe      gegen die geprüfte Wahrheit

Die Ampel ist **Ergebnis des Abgleichs, keine Eigenschaft der Lesung**:

    grün   ein Anker bestätigt, aus einer Quelle die bestätigen darf
    gelb   gelesen, aber nichts bestätigt es
    rot    kein Kandidat, oder die Kandidaten widersprechen sich

Zwei Dinge machen ausdrücklich NICHT grün, beide teuer gelernt:

  * **Die Selbsteinschätzung des Modells.** Bei `Koch`/`Roth` war es viermal
    sicher und viermal falsch – der Buchstabe ist eindeutig lesbar, nur eben
    als der falsche.
  * **Häufigkeit und Wortschatz.** `Roth` kommt 59-mal im Bestand vor und
    hätte jeden Plausibilitätstest bestanden.

Dazu kommt der Rang der Quelle aus `herkunft.gilt`: Ein Treffer aus einer
Vokabularquelle rankt die Vorschlagsliste und bleibt gelb, auch wenn er
perfekt passt. Ohne eingetragene Beleg-Quelle bleibt also alles gelb – das
ist der Nullstart, und er ist langsam, aber nicht falsch.
"""
import argparse
import re

from . import db, einstellungen, konfig, randvermerk
from .suche import falte


def jahr_aus(s):
    m = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", str(s or ""))
    return int(m.group(1)) if m else None


# --------------------------------------------------------------- Bestand
def _bestand(con):
    """Personen, Familien und Trauungen einmal einlesen.

    Neben den Jahren (für die Lebensgrenzen) bleiben die vollen
    Geburts-/Taufdaten samt Ort erhalten – die registereigenen Anker von
    Ehe und Tod vergleichen taggenau, und ein Jahr allein trägt dort
    nichts. Dazu die Kindschaften: Der zweite Beleg („genannter Vater =
    Vater der Taufe") braucht den Weg Person → Elternfamilie.
    """
    beleg = db.belegherkuenfte(con)
    pers = {}
    nach = {}
    for r in con.execute("SELECT id, name, givn, surn, sex, herkunft FROM person"):
        pers[r["id"]] = dict(r, geb=None, tod=None, geburten=[])
        s = falte(r["surn"])
        if s:
            nach.setdefault(s, []).append(r["id"])
    for r in con.execute("SELECT person, art, datum, ort FROM ereignis "
                         "WHERE person IS NOT NULL AND art IN "
                         "('BIRT','CHR','DEAT')"):
        p = pers.get(r["person"])
        if not p:
            continue
        j = jahr_aus(r["datum"])
        if not j:
            continue
        if r["art"] == "DEAT":
            p["tod"] = min(p["tod"], j) if p["tod"] else j
        else:
            p["geb"] = min(p["geb"], j) if p["geb"] else j
            p["geburten"].append((r["art"], r["datum"], r["ort"]))
    marr = {r["familie"]: r["datum"] for r in con.execute(
        "SELECT familie, datum FROM ereignis "
        "WHERE art='MARR' AND familie IS NOT NULL")}
    fam = []
    for r in con.execute("SELECT id, mann, frau, herkunft FROM familie"):
        fam.append(dict(id=r["id"], mann=r["mann"], frau=r["frau"],
                        herkunft=r["herkunft"], marr=marr.get(r["id"]),
                        jahr=jahr_aus(marr.get(r["id"]))))
    kind = {}
    for r in con.execute("SELECT familie, person FROM kind"):
        kind.setdefault(r["person"], []).append(r["familie"])
    return pers, nach, fam, beleg, einstellungen.grenzen(con), kind


def _nullstart(bestand):
    """Gibt es überhaupt einen Bestand, gegen den getroffen werden könnte?

    Beim ersten Start ist er leer. „Kein Treffer im Bestand" ist dann
    zwar wörtlich richtig, aber als **rot** eine Falschmeldung: Rot heißt
    „die Kandidaten widersprechen sich", und es gab gar keine. Ein neuer
    Nutzer sieht sonst 44 rote Felder und hält die Werkstatt für kaputt –
    beim ersten Durchlauf nach dem Klonen genau so passiert.
    """
    pers, nach, fam, beleg, gr, kind = bestand
    return not beleg or not pers


# Lebensgrenzen. Bewusst weit – sie sollen Unmögliches ausschließen, nicht
# Ungewöhnliches. Alles dazwischen entscheidet der Mensch. Änderbar in den
# Einstellungen; die Werte hier sind nur der Rückfall.
MUTTER_MIN, MUTTER_MAX = 14, 50
VATER_MIN, VATER_MAX = 16, 70


def _plausibel(pers, f, jahr, gr=None):
    """Kann dieses Paar im Jahr `jahr` ein Kind bekommen haben?

    Rückgabe (möglich, datiert). `datiert` sagt, ob überhaupt ein Datum die
    Familie in der Zeit verankert – ohne eines darf sie nie grün werden.

    Diese Prüfung fehlte zuerst, und die Messung hat es sofort gezeigt: Der
    Taufe Nr. 12 von 1809 wurde ein Paar zugeordnet, das 1699 und 1703
    geboren wurde und dessen Frau 1767 starb. Einziger gemeinsamer Nachname
    im Bestand, kein Trauungsdatum – und damit nach der alten Regel grün.
    Ein Falschtreffer sieht aus wie ein Erfolg und wird nie wieder geprüft.
    """
    if not jahr:
        return True, bool(f["jahr"])
    m, w = pers.get(f["mann"]), pers.get(f["frau"])
    datiert = bool(f["jahr"])
    if f["jahr"] and f["jahr"] > jahr:
        return False, datiert
    gr = gr or dict(vater=(VATER_MIN, VATER_MAX), mutter=(MUTTER_MIN, MUTTER_MAX))
    for p, (jung, alt) in ((m, gr["vater"]), (w, gr["mutter"])):
        if not p:
            continue
        if p["geb"]:
            datiert = True
            if not (jung <= jahr - p["geb"] <= alt):
                return False, datiert
        if p["tod"]:
            datiert = True
            # Der Vater darf im Jahr davor gestorben sein – nachgeborene
            # Kinder sind häufig und im Register oft vermerkt.
            grenze = jahr - 1 if p is m else jahr
            if p["tod"] < grenze:
                return False, datiert
    return True, datiert


def _teile(text):
    """Namensbestandteile einer gelesenen Angabe, gefaltet."""
    return {t for t in (falte(x) for x in str(text or "").replace(",", " ").split())
            if len(t) > 2}


# Wie viele Vornamen übereinstimmen müssen, wenn der Nachname nicht trägt.
# Einer genügt nicht: `Johann` und `Maria` sind hier fast Allgemeingut.
# Zwei sind spezifisch – `Agnes Dorothea`, `Rosina Margaretha`.
VORNAMEN_MINDESTENS = 2


def _passt(person, gelesen):
    """Wie eine Bestandsperson zu einer gelesenen Angabe passt.

    Rückgabe: (trifft, über_nachnamen). Der zweite Wert sagt, ob der
    Nachname beteiligt war – er entscheidet später über die Beweiskraft.
    """
    if not person:
        return False, False
    t = _teile(gelesen)
    if not t:
        return False, False
    nach = falte(person["surn"])
    if nach and nach in t:
        return True, True
    vor = {x for x in _teile(person["givn"])}
    return len(vor & t) >= VORNAMEN_MINDESTENS, False


def _paare(pers, fam, vater_gelesen, mutter_gelesen):
    """Familien, die zu den gelesenen Elternangaben passen.

    **Der Anker trägt über die Vornamen, nicht über die Nachnamen.**
    `doku/ansatz.md` sagt es so:

        Prüfregel: 1. Vorname(n) des Vaters passen, 2. Vornamen der Mutter
        passen **unabhängig** zum Registereintrag. … Punkt 2 trägt die
        Beweislast. In vier von 22 Fällen war der Vatername falsch gelesen
        und der Treffer kam allein über die Vornamen der Mutter.

    Die Vorgängerfassung verlangte **beide Nachnamen** – also ausgerechnet
    die zwei Felder, die im Register am schwersten zu lesen sind. Bei den
    Testdaten fiel das nie auf, weil dort schon die korrigierten Nachnamen
    standen. An einer frisch gelesenen Seite fand sie null Elternehen: kein
    einziger Mädchenname der Mütter war zu entziffern.

    Die Regel „zwei übereinstimmende Merkmale, eines nicht der Nachname"
    ist damit besser erfüllt als vorher, nicht schlechter: Vater **und**
    Mutter müssen unabhängig passen, und die Vornamen sind das verlässlich
    lesbare Feld.
    """
    if not _teile(vater_gelesen) or not _teile(mutter_gelesen):
        return []
    raus = []
    for f in fam:
        m, w = pers.get(f["mann"]), pers.get(f["frau"])
        tm, nm = _passt(m, vater_gelesen)
        tw, nw = _passt(w, mutter_gelesen)
        if tm and tw:
            raus.append(dict(f, ueber_nachnamen=nm and nw))
    return raus


# --------------------------------------------------------------- Eintrag
def _feld(con, eid, name):
    r = con.execute("SELECT id, gelesen, korrigiert FROM feld "
                    "WHERE eintrag_id=? AND name=?", (eid, name)).fetchone()
    if not r:
        return None, None
    return r["id"], (r["korrigiert"] if r["korrigiert"] is not None
                     else r["gelesen"])


def _setze(con, fid, person=None, ampel="gelb", beleg=None, entscheidung=None):
    if fid is None:
        return
    con.execute(
        "UPDATE feld SET person=?, ampel=?, beleg=COALESCE(?,beleg), "
        "entscheidung=COALESCE(?,entscheidung) WHERE id=?",
        (person, ampel, beleg, entscheidung, fid))


def _randvermerk_auswerten(con, e):
    """Steht am Rand ein Tod, wird er als Sterbedatum vorgeschlagen.

    Nur wenn das Feld leer ist – eine eigene Eingabe wird nie überschrieben,
    auch nicht bei einem erneuten Abgleich. Das Feld bleibt grau: Es ist
    eine Lesung, kein Treffer, und ob der Vermerk dem Täufling gilt oder
    einem anderen, sagt allein das Bild.
    """
    fid_r, text = _feld(con, e["id"], "randvermerk")
    if not text:
        return
    # Nur eine eigene Eingabe ist unantastbar. Ein frueher abgeleiteter
    # Wert muss der Quelle folgen: Nach einer zweiten Lesung stand im
    # Randvermerk „4. Februar" und im Sterbedatum weiter „11 FEB" – zwei
    # Angaben im selben Eintrag, die einander widersprachen.
    r = con.execute("SELECT id, korrigiert FROM feld WHERE eintrag_id=? "
                    "AND name='sterbe_datum'", (e["id"],)).fetchone()
    fid_s = r["id"] if r else None
    if r and r["korrigiert"] is not None:
        return
    d = randvermerk.sterbedatum(text, e["jahr"])
    if not d:
        return
    bel = randvermerk.beleg(
        text, geraten_jahr=not re.search(r"\b1[5-9]\d\d\b", text))
    if fid_s is None:
        # Das Feld entsteht nur, wenn das Modell es liefert – beim
        # Taufeintrag tut es das nie, dort steht der Tod am Rand. Also hier
        # anlegen, sonst hätte der Vermerk keinen Ort.
        reihen = {n: i for i, n in enumerate(konfig.felder(e["register"], con))}
        con.execute(
            "INSERT INTO feld (eintrag_id, name, rolle, gelesen, beleg, "
            "ampel, reihe) VALUES (?,?,?,?,?, 'grau', ?)",
            (e["id"], "sterbe_datum", None, d, bel,
             reihen.get("sterbe_datum", 99)))
    else:
        con.execute(
            "UPDATE feld SET gelesen=?, beleg=?, ampel='grau' WHERE id=?",
            (d, bel, fid_s))


def taufe_pruefen(con, e, bestand):
    """Elternehe-Anker: die Mutter wird abgeleitet, nicht gesucht.

    Deshalb trägt er auch, wenn ihr Name falsch gelesen wurde – im Pilotlauf
    fand er vier Fälle, in denen der *Vater*name falsch war.
    """
    fid_k, _ = _feld(con, e["id"], "kind_vorname")
    _setze(con, fid_k, None, "grau", None, "neu")      # Kind ist immer neu
    _randvermerk_auswerten(con, e)
    return paar_pruefen(con, e, bestand, "vater_name", "mutter_name",
                        e["jahr"])


def paar_pruefen(con, e, bestand, vfeld, mfeld, jahr):
    """Ein Elternpaar gegen den Bestand halten.

    Herausgelöst aus `taufe_pruefen`, weil derselbe Anker auch für Ehe-
    und Sterbeeinträge trägt: Dort steht unter *Eltern* je eine Zeile für
    Vater und Mutter, und wenn deren Ehe im Bestand steht, ist der
    Bräutigam als ihr Kind angebunden. Vorher galt das nur für Taufen –
    die Eltern der Brautleute waren gar keine Personen.

    `jahr` ist das Jahr, in dem dieses Paar ein Kind bekommen haben soll:
    bei der Taufe das Taufjahr, bei der Ehe das Geburtsjahr des
    Brautleuts. Fehlt es, prüft `_plausibel` nur noch, ob überhaupt ein
    Datum die Familie einordnet.
    """
    pers, nach, fam, beleg, gr, kind = bestand
    fid_v, v = _feld(con, e["id"], vfeld)
    fid_m, m = _feld(con, e["id"], mfeld)
    if fid_v is None and fid_m is None:
        return "grau"

    moeglich = []
    for f in _paare(pers, fam, v, m):
        ok, datiert = _plausibel(pers, f, jahr, gr)
        if ok:
            moeglich.append((f, datiert))
    treffer = [f for f, _ in moeglich]

    if len(treffer) == 1:
        f, datiert = moeglich[0]
        darf = f["herkunft"] in beleg
        weg = "Nachnamen" if f.get("ueber_nachnamen") else "Vornamen beider Eltern"
        grund = (f"Elternehe F{f['id']} über {weg}"
                 + (f", oo {f['marr']}" if f["marr"] else ""))
        if not darf:
            farbe = "gelb"
            grund += " – Quelle darf nicht bestätigen"
        elif not datiert:
            # Zwei gleiche Nachnamen ohne jedes Datum sind ein Vorschlag,
            # kein Anker. Genau hier entstehen die stillen Fehltreffer.
            farbe = "gelb"
            grund += " – kein Datum, das die Familie zeitlich einordnet"
        else:
            farbe = "gruen"
        _setze(con, fid_v, f["mann"], farbe, grund,
               "verknuepft" if farbe == "gruen" else None)
        _setze(con, fid_m, f["frau"], farbe, grund,
               "verknuepft" if farbe == "gruen" else None)
        return farbe

    if len(treffer) > 1:
        grund = f"{len(treffer)} mögliche Elternehen – Entscheidung nötig"
        _setze(con, fid_v, None, "gelb", grund)
        _setze(con, fid_m, None, "gelb", grund)
        return "gelb"

    # Keine gemeinsame Familie. Einseitige Treffer sind ein Hinweis, kein
    # Beleg – genau hier stand im Pilotlauf der falsch gelesene Nachname.
    kv = [i for x in _teile(v) for i in nach.get(x, [])]
    km = [i for x in _teile(m) for i in nach.get(x, [])]
    if kv and km:
        grund = ("beide Namen im Bestand, aber KEINE gemeinsame Familie – "
                 "Zweitehe oder Fehllesung")
        _setze(con, fid_v, None, "rot", grund)
        _setze(con, fid_m, None, "rot", grund)
        return "rot"
    if kv or km:
        wer = "Vater" if kv else "Mutter"
        grund = f"nur der {wer}name kommt im Bestand vor – Elternehe fehlt"
        _setze(con, fid_v, None, "gelb" if kv else "rot", grund)
        _setze(con, fid_m, None, "gelb" if km else "rot", grund)
        return "gelb"
    if _nullstart(bestand):
        grund = ("Nullstart – es gibt noch keinen Bestand, gegen den "
                 "geprüft werden könnte. Alles wird vorgelegt.")
        _setze(con, fid_v, None, "gelb", grund)
        _setze(con, fid_m, None, "gelb", grund)
        return "gelb"
    _setze(con, fid_v, None, "rot", "kein Treffer im Bestand")
    _setze(con, fid_m, None, "rot", "kein Treffer im Bestand")
    return "rot"


def _jahr_fuer(con, e, rolle):
    """Geburtsjahr der Person, deren Eltern gerade geprüft werden."""
    for feld in (f"{rolle}_geburt_datum", f"{rolle}_geburt_jahr"):
        _, w = _feld(con, e["id"], feld)
        if w:
            m = re.search(r"\b(1[5-9]\d\d)\b", str(w))
            if m:
                return int(m.group(1))
    return None


# ----------------------------------------------- Datum, Alter, Tageszahl
_MONAT_NR = {m: i + 1 for i, m in enumerate(randvermerk.GEDCOM_MONAT)}
_D_GEDCOM = re.compile(r"(?:(\d{1,2})\s+)?([A-Z]{3})\s+(\d{4})")
_D_PUNKTE = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})")
_D_WORT = re.compile(r"(\d{1,2})\.?\s*([A-Za-zÄÖÜäöü]{3,12})\.?\s*(\d{4})")


def datum_zerlegen(s):
    """'23 FEB 1778' · '23.02.1778' · '9. Januar 1808' · 'FEB 1778' · '1778'
    → (jahr, monat, tag), fehlende Teile None. None ganz ohne Jahr.

    Die Lesung liefert meist schon die GEDCOM-Form, aber nicht immer –
    die Ehe-Testdaten tragen Punktdaten, die Sterbedaten Monatsnamen.
    """
    s = str(s or "").strip()
    m = _D_GEDCOM.fullmatch(s.upper())
    if m and m.group(2) in _MONAT_NR:
        return (int(m.group(3)), _MONAT_NR[m.group(2)],
                int(m.group(1)) if m.group(1) else None)
    m = _D_PUNKTE.fullmatch(s)
    if m and 1 <= int(m.group(2)) <= 12:
        return int(m.group(3)), int(m.group(2)), int(m.group(1))
    m = _D_WORT.fullmatch(s)
    if m:
        w = m.group(2).lower()
        mon = randvermerk.MONATE.get(w) or randvermerk.MONATE.get(w[:3])
        if mon:
            return int(m.group(3)), mon, int(m.group(1))
    j = jahr_aus(s)
    return (j, None, None) if j else None


def _ordinal(j, m, t):
    from datetime import date
    try:
        return date(j, m, t).toordinal()
    except (ValueError, TypeError):
        return None


_ALTER_TEIL = re.compile(r"(\d+)\s*(jahr|monat|woche|tag)", re.IGNORECASE)


def geburt_aus_alter(bezug, alter):
    """'53 Jahre, 3 Monate, 10 Tage' vor dem Bezugsdatum → Geburtsdatum.

    Rückgabe ((jahr, monat, tag), taggenau). Taggenau nur, wenn Tage
    genannt sind – '53 Jahre, 3 Monate, 10 Tage' und '3 Tage' ja,
    '65 Jahre' heißt ±1 Jahr und ergibt nur ein Jahr. Dieselbe Messlatte
    wie im Machbarkeitsnachweis (kaskade_tod.py): errechnete Daten mit
    Tagesangabe trafen die Taufe auf den Tag.
    """
    teile = {einheit[:3].lower(): int(zahl)
             for zahl, einheit in _ALTER_TEIL.findall(str(alter or ""))}
    b = datum_zerlegen(bezug)
    if not teile or not b:
        return None, False
    j, m, t = b
    if not (m and t):
        return (j - teile.get("jah", 0), None, None), False
    from datetime import date, timedelta
    monate = (j * 12 + m - 1) - teile.get("jah", 0) * 12 - teile.get("mon", 0)
    jj, mm = divmod(monate, 12)
    # min(t, 28): der 31. eines kürzeren Monats wäre ungültig. Der Fehler
    # von höchstens drei Tagen liegt innerhalb der Datumstoleranz.
    d = (date(jj, mm + 1, min(t, 28))
         - timedelta(days=teile.get("tag", 0), weeks=teile.get("woc", 0)))
    return (d.year, d.month, d.day), "tag" in teile


# ------------------------------------- Registereigene Anker (Ehe und Tod)
# Bewertung wie im Machbarkeitsnachweis kaskade_tod.py (59,8 % Treffer
# gegen kirchenbuch.db). Tragfähig ist ein Kandidat mit mindestens zwei
# Merkmalen, von denen eines nicht der Nachname ist – sonst würde
# `Johannes Bierle` still mit `Carl Heinrich Bierle` verknüpft.
PUNKTE = {"datum_tag": 5, "datum_jahr": 2, "vorname": 3, "nachname": 1,
          "eltern": 4, "ehe": 4}
SCHWELLE = 6
DATUM_TOLERANZ = 5          # Tage: die Taufe folgt der Geburt um wenige Tage
MERKMAL_TEXT = {"datum_tag": "Datum taggenau", "datum_jahr": "Geburtsjahr",
                "vorname": "Vorname", "nachname": "Nachname",
                "eltern": "Eltern", "ehe": "über die Ehe"}
RANG = {"grau": 0, "rot": 1, "gelb": 2, "gruen": 3}


def _punkte(merkmale):
    return sum(PUNKTE[m] for m in merkmale)


def _tragfaehig(merkmale):
    ohne = [m for m in merkmale if m != "nachname"]
    return len(merkmale) >= 2 and ohne and _punkte(merkmale) >= SCHWELLE


def _datum_merkmal(p, geb, taggenau):
    """Wie Geburt/Taufe einer Bestandsperson zum gelesenen Datum passen.

    Rückgabe (merkmal, ort) – merkmal None, wenn kein Datum passt. Ohne
    passendes Datum ist eine Person hier kein Kandidat: Der ganze Anker
    lebt davon, dass das Register das Geburtsdatum nennt.
    """
    bester, best_ort = None, None
    for art, datum, ort in p["geburten"]:
        z = datum_zerlegen(datum)
        if not z:
            continue
        if taggenau and z[1] and z[2]:
            a, b = _ordinal(*geb), _ordinal(*z)
            if a and b and abs(a - b) <= DATUM_TOLERANZ:
                return "datum_tag", ort
        if z[0] == geb[0] and bester is None:
            bester, best_ort = "datum_jahr", ort
    return bester, best_ort


def _eltern_beleg(con, e, bestand, rolle, pid, fam_by):
    """Zweiter Beleg: genannte Eltern gegen die Eltern der Taufe."""
    pers, nach, fam, beleg, gr, kind = bestand
    _, v = _feld(con, e["id"], f"{rolle}_vater_name")
    _, m = _feld(con, e["id"], f"{rolle}_mutter_name")
    if not (v or m):
        return False
    for fid in kind.get(pid, []):
        f = fam_by.get(fid)
        if not f:
            continue
        if v and _passt(pers.get(f["mann"]), v)[0]:
            return True
        if m and _passt(pers.get(f["frau"]), m)[0]:
            return True
    return False


def _ehegatten_umweg(con, e, bestand, rolle):
    """Verheiratete Frau: die Taufe steht unter dem Mädchennamen.

    Statt ihn zu raten, wird die Ehe im Bestand gesucht – dort hängt
    dieselbe Person schon als Frau. Die Lektion aus kaskade_tod.py gilt
    weiter: NICHT aufs Geschlecht prüfen (das Feld ist meist leer), ein
    genannter Ehepartner genügt als Anlass.
    """
    pers, nach, fam, beleg, gr, kind = bestand
    _, gatte = _feld(con, e["id"], "ehegatte")
    _, name = _feld(con, e["id"], f"{rolle}_name")
    if not gatte or not _teile(name):
        return []
    raus = []
    vor = _teile(name)
    for f in fam:
        m, w = pers.get(f["mann"]), pers.get(f["frau"])
        if not m or not w:
            continue
        if not _passt(m, gatte)[0]:
            continue
        if not (_teile(w["givn"]) & vor):
            continue
        raus.append(w)
    return raus


def _rolle_pruefen(con, e, bestand, rolle, sex=None, bezugsfeld=None):
    """Der registereigene Anker für EINE Hauptrolle.

    Ehe: das Geburtsdatum steht im Register (Spalte 6), oft taggenau –
    der stärkste Anker überhaupt, weil er beide Brautleute trifft.
    Tod: das Alter ('53 Jahre, 3 Monate, 10 Tage') ergibt das
    Geburtsdatum; verheiratete Frauen laufen über die Ehe.

    Rückgabe None, wenn der Anker nichts beizutragen hat – dann bleibt
    stehen, was das Namensranking gesetzt hat.
    """
    pers, nach, fam, beleg, gr, kind = bestand
    fid, name = _feld(con, e["id"], f"{rolle}_name")
    if fid is None or not _teile(name):
        return None
    _, geborene = _feld(con, e["id"], f"{rolle}_geborene")
    _, gd = _feld(con, e["id"], f"{rolle}_geburt_datum")
    geb = datum_zerlegen(gd)
    taggenau = bool(geb and geb[1] and geb[2])
    anker = f"Geburtsdatum {gd}" if geb else None
    if not geb and bezugsfeld:
        alter = None
        for altfeld in (f"{rolle}_alter", "alter"):
            _, alter = _feld(con, e["id"], altfeld)
            if alter:
                break
        _, bez = _feld(con, e["id"], bezugsfeld)
        if alter and bez:
            geb, taggenau = geburt_aus_alter(bez, alter)
            if geb:
                anker = (f"Alter „{alter}“ → geboren "
                         + ("um " if not taggenau else "")
                         + "-".join(str(x) for x in geb if x))

    fam_by = {f["id"]: f for f in fam}
    kandidaten = []
    if geb:
        _, gort = _feld(con, e["id"], f"{rolle}_geburt_ort")
        for p in pers.values():
            if sex and p["sex"] and p["sex"] != sex:
                continue
            merkmal, ort = _datum_merkmal(p, geb, taggenau)
            if not merkmal:
                continue
            # Datum + Ort ist der Anker – widersprechen sich die Orte,
            # ist es ein anderes Kind vom selben Tag.
            if gort and ort and not (_teile(gort) & _teile(ort)):
                continue
            mk = [merkmal]
            t = _teile(name) | _teile(geborene)
            if falte(p["surn"]) and falte(p["surn"]) in t:
                mk.append("nachname")
            if _teile(p["givn"]) & _teile(name):
                mk.append("vorname")
            else:
                # „Vorname ist Pflichtbedingung, sonst stille
                # Fehlverknüpfung" (verknuepfung.md, dritter Fehlschlag):
                # Datum + Nachname allein hätte hier `Anna Barbara` auf
                # `Johann Friedrich` gelegt, weil beide am selben Tag
                # getauft sind.
                continue
            if _eltern_beleg(con, e, bestand, rolle, p["id"], fam_by):
                mk.append("eltern")
            kandidaten.append((p, mk))

    if not any(_tragfaehig(mk) for _, mk in kandidaten):
        for w in _ehegatten_umweg(con, e, bestand, rolle):
            mk = ["ehe", "vorname"]           # Vorname ist dort schon geprüft
            if geb:
                merkmal, _ = _datum_merkmal(w, geb, taggenau)
                if merkmal:
                    mk.append(merkmal)
            kandidaten.append((w, mk))
            anker = anker or "genannter Ehegatte"

    gut = sorted(((p, mk) for p, mk in kandidaten if _tragfaehig(mk)),
                 key=lambda x: -_punkte(x[1]))
    if not gut:
        return None
    if len(gut) > 1 and _punkte(gut[0][1]) <= _punkte(gut[1][1]) + 2:
        _setze(con, fid, None, "gelb",
               f"{len(gut)} Kandidaten über {anker} – Entscheidung nötig")
        return "gelb"
    p, mk = gut[0]
    grund = (f"{anker}: {p['name']} über "
             + ", ".join(MERKMAL_TEXT[m] for m in mk))
    if p["herkunft"] not in beleg:
        _setze(con, fid, None, "gelb", grund + " – Quelle darf nicht bestätigen")
        return "gelb"
    if "datum_tag" not in mk:
        # Nur das Jahr passt: ein guter Vorschlag, aber kein Anker.
        # Grün braucht den Tag – der Vorname ist ohnehin Pflicht.
        _setze(con, fid, None, "gelb", grund + " – nicht taggenau bestätigt")
        return "gelb"
    _setze(con, fid, p["id"], "gruen", grund, "verknuepft")
    return "gruen"


def register_anker(con, e, bestand, art):
    """Die registereigenen Anker über alle Hauptrollen eines Eintrags.

    Läuft NACH dem Namensranking und überschreibt nur, wo er mehr weiß.
    Das Bezugsdatum für Altersangaben kommt aus dem Bauplan (MARR bei
    der Ehe, DEAT beim Tod) – keine Registernamen im Code.
    """
    from . import katalog
    bau = katalog.bauplan(art, con)
    paar = tuple(bau.get("paar") or ())
    bezug = next((ev["datum"] for ev in bau.get("ereignis") or []
                  if ev["tag"] in ("MARR", "DEAT")), None)
    farbe = None
    for rolle in konfig.personen_rollen(art):
        sex = ("M" if paar[:1] == (rolle,)
               else "F" if rolle in paar[1:] else None)
        f = _rolle_pruefen(con, e, bestand, rolle, sex, bezug)
        if f and (farbe is None or RANG[f] > RANG[farbe]):
            farbe = f
    return farbe


def allgemein_pruefen(con, e, bestand, art):
    """Für Register ohne eigene Kaskade: Namen ranken, nie bestätigen.

    Ein Nachname allein genügt nie – `Johannes Bierle` hätte sonst auf
    `Carl Heinrich Bierle` gezeigt. Deshalb gibt es hier kein Grün.

    Für die Elternpaare gilt das nicht: Dort trägt derselbe Anker wie beim
    Taufregister, weil zwei Vornamen plus gemeinsame Familie geprüft
    werden und nicht ein Nachname allein.
    """
    from . import katalog
    pers, nach, fam, beleg, gr, kind = bestand
    farbe = "rot"
    for kindrolle, (vr, mr) in (katalog.bauplan(art, con).get("kinder") or []):
        f = paar_pruefen(con, e, bestand, f"{vr}_name", f"{mr}_name",
                         _jahr_fuer(con, e, kindrolle))
        if RANG.get(f, 0) > RANG.get(farbe, 0):
            farbe = f
    for rolle in konfig.personen_rollen(art):
        fid, w = _feld(con, e["id"], f"{rolle}_name")
        if fid is None:
            continue
        k = nach.get(falte(w), [])
        if len(k) == 1:
            _setze(con, fid, None, "gelb",
                   f"ein Namensträger im Bestand ({pers[k[0]]['name']}) – "
                   "ein Nachname allein bestätigt nicht")
            farbe = "gelb"
        elif k:
            _setze(con, fid, None, "gelb", f"{len(k)} Namensträger im Bestand")
            farbe = "gelb"
        elif _nullstart(bestand):
            _setze(con, fid, None, "gelb",
                   "Nullstart – es gibt noch keinen Bestand, gegen den "
                   "geprüft werden könnte. Alles wird vorgelegt.")
            farbe = "gelb"
        else:
            _setze(con, fid, None, "rot", "kein Treffer im Bestand")
    return farbe


def runde_pruefen(con, runde_id=None, nur_offen=False):
    """Abgleich für eine Runde – oder für alles, was noch grau ist.

    `nur_offen` lässt bestätigte Einträge in Ruhe. Das braucht es, wenn
    nachträglich eine Quelle dazukommt: Der Abgleich soll die neuen
    Möglichkeiten nutzen, aber keine Entscheidung überschreiben, die ein
    Mensch schon getroffen hat.
    """
    bestand = _bestand(con)
    if runde_id:
        rows = list(con.execute("SELECT * FROM eintrag WHERE runde=?", (runde_id,)))
    elif nur_offen:
        rows = list(con.execute(
            "SELECT * FROM eintrag WHERE status <> 'bestaetigt'"))
    else:
        rows = list(con.execute("SELECT * FROM eintrag"))
    z = dict(gruen=0, gelb=0, rot=0)
    for e in rows:
        if e["register"] == "taufe":
            f = taufe_pruefen(con, e, bestand)
        else:
            f = allgemein_pruefen(con, e, bestand, e["register"])
            # Danach die registereigenen Anker – sie überschreiben das
            # Ranking dort, wo Geburtsdatum, Alter oder Ehegatte mehr
            # wissen als der Nachname.
            f2 = register_anker(con, e, bestand, e["register"])
            if f2 and RANG[f2] > RANG.get(f, 0):
                f = f2
        z[f] = z.get(f, 0) + 1
    con.commit()
    return z


# ---------------------------------------------------------------- Messung
def messe(con):
    """Wie viel findet der Abgleich von dem, was ein Mensch bestätigt hat?

    Der Maßstab kommt aus der Testquelle und ist unabhängig: 39 Verweise,
    von Hand geprüft, in der Erfassung nicht enthalten.
    """
    from . import testdaten
    w = testdaten.wahrheit()
    if not w:
        return None
    xref = {r["id"]: r["xref"] for r in
            con.execute("SELECT id, xref FROM person")}
    treffer = falsch = fehlt = 0
    fehler = []
    for (bild, nr, feld), soll in w.items():
        r = con.execute(
            "SELECT f.person FROM feld f JOIN eintrag e ON e.id=f.eintrag_id "
            "WHERE e.bild=? AND e.nr=? AND f.name=?",
            (bild, nr, feld)).fetchone()
        ist = xref.get(r["person"]) if r and r["person"] else None
        if ist == soll["xref"]:
            treffer += 1
        elif ist is None:
            fehlt += 1
        else:
            falsch += 1
            fehler.append((bild, nr, feld, soll["xref"], ist))
    return dict(gesamt=len(w), treffer=treffer, fehlt=fehlt, falsch=falsch,
                fehler=fehler)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runde", type=int)
    ap.add_argument("--messe", action="store_true")
    a = ap.parse_args()
    con = db.verbinde()
    if a.messe:
        m = messe(con)
        if not m:
            raise SystemExit("keine Wahrheitsdaten verfügbar")
        q = 100 * m["treffer"] / m["gesamt"] if m["gesamt"] else 0
        print(f"  {m['gesamt']} geprüfte Verweise")
        print(f"  {m['treffer']:3} wiedergefunden  ({q:.0f} %)")
        print(f"  {m['fehlt']:3} nicht gefunden")
        print(f"  {m['falsch']:3} anders zugeordnet")
        for f in m["fehler"][:10]:
            print(f"    ⚠ {f[0]} Nr.{f[1]} {f[2]}: soll {f[3]}, ist {f[4]}")
        return
    z = runde_pruefen(con, a.runde)
    print("  " + " · ".join(f"{k} {v}" for k, v in z.items()))


if __name__ == "__main__":
    main()
