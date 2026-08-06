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
    sicher und viermal falsch — der Buchstabe ist eindeutig lesbar, nur eben
    als der falsche.
  * **Häufigkeit und Wortschatz.** `Roth` kommt 59-mal im Bestand vor und
    hätte jeden Plausibilitätstest bestanden.

Dazu kommt der Rang der Quelle aus `herkunft.gilt`: Ein Treffer aus einer
Vokabularquelle rankt die Vorschlagsliste und bleibt gelb, auch wenn er
perfekt passt. Ohne eingetragene Beleg-Quelle bleibt also alles gelb — das
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
    """Personen, Familien und Trauungen einmal einlesen."""
    beleg = db.belegherkuenfte(con)
    pers = {}
    nach = {}
    for r in con.execute("SELECT id, name, givn, surn, sex, herkunft FROM person"):
        pers[r["id"]] = dict(r, geb=None, tod=None)
        s = falte(r["surn"])
        if s:
            nach.setdefault(s, []).append(r["id"])
    for r in con.execute("SELECT person, art, datum FROM ereignis "
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
    marr = {r["familie"]: r["datum"] for r in con.execute(
        "SELECT familie, datum FROM ereignis "
        "WHERE art='MARR' AND familie IS NOT NULL")}
    fam = []
    for r in con.execute("SELECT id, mann, frau, herkunft FROM familie"):
        fam.append(dict(id=r["id"], mann=r["mann"], frau=r["frau"],
                        herkunft=r["herkunft"], marr=marr.get(r["id"]),
                        jahr=jahr_aus(marr.get(r["id"]))))
    return pers, nach, fam, beleg, einstellungen.grenzen(con)


# Lebensgrenzen. Bewusst weit — sie sollen Unmögliches ausschließen, nicht
# Ungewöhnliches. Alles dazwischen entscheidet der Mensch. Änderbar in den
# Einstellungen; die Werte hier sind nur der Rückfall.
MUTTER_MIN, MUTTER_MAX = 14, 50
VATER_MIN, VATER_MAX = 16, 70


def _plausibel(pers, f, jahr, gr=None):
    """Kann dieses Paar im Jahr `jahr` ein Kind bekommen haben?

    Rückgabe (möglich, datiert). `datiert` sagt, ob überhaupt ein Datum die
    Familie in der Zeit verankert — ohne eines darf sie nie grün werden.

    Diese Prüfung fehlte zuerst, und die Messung hat es sofort gezeigt: Der
    Taufe Nr. 12 von 1809 wurde ein Paar zugeordnet, das 1699 und 1703
    geboren wurde und dessen Frau 1767 starb. Einziger gemeinsamer Nachname
    im Bestand, kein Trauungsdatum — und damit nach der alten Regel grün.
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
            # Der Vater darf im Jahr davor gestorben sein — nachgeborene
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
# Zwei sind spezifisch — `Agnes Dorothea`, `Rosina Margaretha`.
VORNAMEN_MINDESTENS = 2


def _passt(person, gelesen):
    """Wie eine Bestandsperson zu einer gelesenen Angabe passt.

    Rückgabe: (trifft, über_nachnamen). Der zweite Wert sagt, ob der
    Nachname beteiligt war — er entscheidet später über die Beweiskraft.
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

    Die Vorgängerfassung verlangte **beide Nachnamen** — also ausgerechnet
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

    Nur wenn das Feld leer ist — eine eigene Eingabe wird nie überschrieben,
    auch nicht bei einem erneuten Abgleich. Das Feld bleibt grau: Es ist
    eine Lesung, kein Treffer, und ob der Vermerk dem Täufling gilt oder
    einem anderen, sagt allein das Bild.
    """
    fid_r, text = _feld(con, e["id"], "randvermerk")
    fid_s, schon = _feld(con, e["id"], "sterbe_datum")
    if schon or not text:
        return
    d = randvermerk.sterbedatum(text, e["jahr"])
    if not d:
        return
    bel = randvermerk.beleg(
        text, geraten_jahr=not re.search(r"\b1[5-9]\d\d\b", text))
    if fid_s is None:
        # Das Feld entsteht nur, wenn das Modell es liefert — beim
        # Taufeintrag tut es das nie, dort steht der Tod am Rand. Also hier
        # anlegen, sonst hätte der Vermerk keinen Ort.
        reihen = {n: i for i, n in enumerate(konfig.felder(e["register"]))}
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

    Deshalb trägt er auch, wenn ihr Name falsch gelesen wurde — im Pilotlauf
    fand er vier Fälle, in denen der *Vater*name falsch war.
    """
    pers, nach, fam, beleg, gr = bestand
    fid_v, v = _feld(con, e["id"], "vater_name")
    fid_m, m = _feld(con, e["id"], "mutter_name")
    fid_k, _ = _feld(con, e["id"], "kind_vorname")
    _setze(con, fid_k, None, "grau", None, "neu")      # Kind ist immer neu
    _randvermerk_auswerten(con, e)

    jahr = e["jahr"]
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
            grund += " — Quelle darf nicht bestätigen"
        elif not datiert:
            # Zwei gleiche Nachnamen ohne jedes Datum sind ein Vorschlag,
            # kein Anker. Genau hier entstehen die stillen Fehltreffer.
            farbe = "gelb"
            grund += " — kein Datum, das die Familie zeitlich einordnet"
        else:
            farbe = "gruen"
        _setze(con, fid_v, f["mann"], farbe, grund,
               "verknuepft" if farbe == "gruen" else None)
        _setze(con, fid_m, f["frau"], farbe, grund,
               "verknuepft" if farbe == "gruen" else None)
        return farbe

    if len(treffer) > 1:
        grund = f"{len(treffer)} mögliche Elternehen — Entscheidung nötig"
        _setze(con, fid_v, None, "gelb", grund)
        _setze(con, fid_m, None, "gelb", grund)
        return "gelb"

    # Keine gemeinsame Familie. Einseitige Treffer sind ein Hinweis, kein
    # Beleg — genau hier stand im Pilotlauf der falsch gelesene Nachname.
    kv = [i for x in _teile(v) for i in nach.get(x, [])]
    km = [i for x in _teile(m) for i in nach.get(x, [])]
    if kv and km:
        grund = ("beide Namen im Bestand, aber KEINE gemeinsame Familie — "
                 "Zweitehe oder Fehllesung")
        _setze(con, fid_v, None, "rot", grund)
        _setze(con, fid_m, None, "rot", grund)
        return "rot"
    if kv or km:
        wer = "Vater" if kv else "Mutter"
        grund = f"nur der {wer}name kommt im Bestand vor — Elternehe fehlt"
        _setze(con, fid_v, None, "gelb" if kv else "rot", grund)
        _setze(con, fid_m, None, "gelb" if km else "rot", grund)
        return "gelb"
    _setze(con, fid_v, None, "rot", "kein Treffer im Bestand")
    _setze(con, fid_m, None, "rot", "kein Treffer im Bestand")
    return "rot"


def allgemein_pruefen(con, e, bestand, art):
    """Für Register ohne eigene Kaskade: Namen ranken, nie bestätigen.

    Ein Nachname allein genügt nie — `Johannes Bierle` hätte sonst auf
    `Carl Heinrich Bierle` gezeigt. Deshalb gibt es hier kein Grün.
    """
    pers, nach, fam, beleg, gr = bestand
    farbe = "rot"
    for rolle in konfig.personen_rollen(art):
        fid, w = _feld(con, e["id"], f"{rolle}_name")
        if fid is None:
            continue
        k = nach.get(falte(w), [])
        if len(k) == 1:
            _setze(con, fid, None, "gelb",
                   f"ein Namensträger im Bestand ({pers[k[0]]['name']}) — "
                   "ein Nachname allein bestätigt nicht")
            farbe = "gelb"
        elif k:
            _setze(con, fid, None, "gelb", f"{len(k)} Namensträger im Bestand")
            farbe = "gelb"
        else:
            _setze(con, fid, None, "rot", "kein Treffer im Bestand")
    return farbe


def runde_pruefen(con, runde_id=None, nur_offen=False):
    """Abgleich für eine Runde — oder für alles, was noch grau ist.

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
