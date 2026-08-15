#!/usr/bin/env python3
"""Der Durchlauf: Tranche planen, lesen lassen, übergeben, weiterschalten.

    python3 -m werkstatt.runde --stand
    python3 -m werkstatt.runde --plane taufe --seiten 4 --quelle testdaten
    python3 -m werkstatt.runde --lies 1
    python3 -m werkstatt.runde --uebergib 1

Eine Runde ist eine Tranche: so und so viele Seiten EINES Registers, die
zusammen gelesen, zusammen korrigiert und zusammen übergeben werden.

    geplant  ──lesen──►  korrigieren  ──übergeben──►  fertig
                              │
                              └── die Maske zeigt genau diese Runde

**Die Reihenfolge Ehen → Taufen → Tode ist Bedingung, nicht Empfehlung.**
Der Elternehe-Anker trägt im Taufjahr 1808 noch 94 %, 1813 noch 53 %, 1820
nur 18 % – es sei denn, die Ehen ab 1808 sind vorher übergeben, dann wächst
er mit. Wer die Taufen vorzieht, prüft sie später ein zweites Mal. Deshalb
schlägt `vorschlag()` das nächste Register selbst vor, und eine neue Runde
beginnt erst, wenn die vorige übergeben ist.
"""
import argparse
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path

from . import db, einstellungen, konfig, seiten, streifen, testdaten, vorlage

STAENDE = ("geplant", "liest", "korrigieren", "uebergeben", "fertig")


def jetzt():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ----------------------------------------------------------------- Planung
def register_reihe(con=None):
    """Registerreihenfolge – aus den Einstellungen, sonst wie in konfig.toml."""
    if con is None:
        return list(konfig.register())
    return einstellungen.reihenfolge(con)


def gelesene_bilder(con, register):
    return {r["bild"] for r in con.execute(
        "SELECT DISTINCT bild FROM eintrag WHERE register=?", (register,))}


def offene_bilder(con, register, quelle="api"):
    """Bilder dieses Registers, die noch nicht gelesen sind.

    Bei `quelle=testdaten` zählt nur, was die Testquelle abdeckt – sonst
    plante die Werkstatt zwanzig Seiten und läse vier.
    """
    schon = gelesene_bilder(con, register)
    if quelle == "testdaten":
        alle = testdaten.seiten(register)
        # Nur Seiten, zu denen auch ein Bild daliegt. Die Testquelle deckt
        # mehr Seiten ab, als die Demo an Bildern mitbringt; ohne diesen
        # Schnitt bekommt der Betrachter Eintraege ohne Streifen und ohne
        # ganze Seite – also genau das, was die Werkstatt zeigen soll,
        # nicht. Liegt gar kein Bild da, bleibt es bei der vollen Liste:
        # lesen laesst sich die Quelle auch ohne Bilder.
        da = {f.stem for f in seiten.bilder(einstellungen.ordner(con, register))}
        if da:
            alle = [b for b in alle if b in da]
    else:
        # 'api' und 'datei' lesen beide aus dem Bilderordner – der Unterschied
        # ist nur, wer die Seite anschaut.
        alle = [f.stem for f in seiten.bilder(einstellungen.ordner(con, register))]
    # Bestaetigte Dubletten gar nicht erst einplanen. Zwei Aufnahmen
    # derselben Buchoeffnung kosten sonst zweimal und liefern jeden
    # Eintrag doppelt in den Bestand – gemessen an 00359/00360.
    from . import dubletten
    weg = dubletten.uebersprungene(con)
    return [b for b in alle if b not in schon and b not in weg]


def offene_runde(con):
    """Die eine Runde, die noch läuft. Es gibt immer höchstens eine."""
    r = con.execute("SELECT * FROM runde WHERE stand<>'fertig' "
                    "ORDER BY id DESC LIMIT 1").fetchone()
    return dict(r) if r else None


def vorschlag(con, quelle="api"):
    """Welches Register als Nächstes – und warum.

    Der Vorschlag zählt immer den **Bilderbestand**, nicht die gewählte
    Quelle. Sonst meldet die Werkstatt „alle Seiten gelesen", während 148
    Bilder ungelesen im Ordner liegen und bloß die Testquelle erschöpft ist.
    """
    offen = offene_runde(con)
    if offen:
        return dict(register=offen["register"], runde=offen,
                    grund="läuft bereits")
    reihe = register_reihe(con)
    letzte = con.execute("SELECT register FROM runde WHERE stand='fertig' "
                         "ORDER BY id DESC LIMIT 1").fetchone()
    start = (reihe.index(letzte["register"]) + 1) % len(reihe) if letzte else 0
    for i in range(len(reihe)):
        reg = reihe[(start + i) % len(reihe)]
        rest = offene_bilder(con, reg, "api")
        if rest:
            grund = ("erste Runde – Ehen zuerst, sie bauen den Anker"
                     if not letzte and reg == reihe[0]
                     else f"{len(rest)} Seiten offen")
            if quelle == "testdaten" and not offene_bilder(con, reg, "testdaten"):
                grund += " – die Testquelle ist erschöpft, dafür braucht es die API"
            return dict(register=reg, runde=None, grund=grund, offen=len(rest))
    return dict(register=None, runde=None, grund="alle Seiten gelesen")


def plane(con, register, anzahl=None, quelle="api"):
    anzahl = anzahl or einstellungen.seitenzahl(con, register)
    offen = offene_runde(con)
    if offen:
        raise SystemExit(
            f"Runde {offen['nr']} ({offen['register']}) steht noch auf "
            f"'{offen['stand']}' – erst abschließen.")
    bilder = offene_bilder(con, register, quelle)[:anzahl]
    if not bilder:
        raise SystemExit(f"keine ungelesenen Seiten in {register} "
                         f"(Quelle {quelle})")
    nr = (con.execute("SELECT COALESCE(MAX(nr),0)+1 FROM runde").fetchone()[0])
    cur = con.execute(
        "INSERT INTO runde (nr, register, von_bild, bis_bild, seiten, quelle, "
        "stand, begonnen) VALUES (?,?,?,?,?,?,'geplant',?)",
        (nr, register, bilder[0], bilder[-1], len(bilder), quelle, jetzt()))
    rid = cur.lastrowid
    a = con.execute(
        "INSERT INTO auftrag (runde, art, stand, seiten_gesamt) "
        "VALUES (?,'lesen','wartet',?)", (rid, len(bilder)))
    for b in bilder:
        con.execute("INSERT OR IGNORE INTO auftrag_seite (auftrag, bild) "
                    "VALUES (?,?)", (a.lastrowid, b))
    con.commit()
    return rid


# ------------------------------------------------------------------ Lesen
def _rolle(art, feldname):
    """Welches Feld trägt den Namen welcher Person.

    Rolle heißt hier: *dieses Feld ist die Person*, nicht bloß eine
    Angabe über sie. `vater_name` trägt den Vater, `vater_beruf` nicht –
    sonst stünde jedes Berufsfeld in der Maske als Personenentscheidung.
    """
    from . import katalog
    x = katalog.feld(art, feldname)
    if x and x.rolle and feldname in (f"{x.rolle}_name",
                                      f"{x.rolle}_vorname", x.rolle):
        return x.rolle
    for r in konfig.personen_rollen(art):
        if feldname in (f"{r}_name", f"{r}_vorname", r):
            return r
    return None


def speichere(con, art, bild, ergebnis, runde_id=None, hid=None):
    """Gelesene Einträge festhalten – für beide Quellen derselbe Weg."""
    reihen = {n: i for i, n in enumerate(konfig.felder(art, con))}
    n_e = n_f = 0
    for e in ergebnis.get("eintraege", []):
        nr = str(e.get("lfd_nr") or "")
        con.execute(
            "INSERT OR IGNORE INTO eintrag "
            "(register, band, bild, nr, jahr, ausschnitt, herkunft, runde) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (art, e.get("band"), bild, nr, e.get("jahr"),
             e.get("ausschnitt"), hid, runde_id))
        row = con.execute(
            "SELECT id FROM eintrag WHERE register=? AND bild=? AND nr=?",
            (art, bild, nr)).fetchone()
        if not row:
            continue
        eid = row["id"]
        n_e += 1
        for name, f in (e.get("felder") or {}).items():
            if not isinstance(f, dict):
                f = {"wert": f}
            # Eine zweite Lesung derselben Seite muss die erste ersetzen.
            # `INSERT OR IGNORE` liess sie stillschweigend fallen: Die Seite
            # wurde neu gelesen, in der Maske stand weiter die alte Fassung,
            # und die neu hinzugekommenen Felder – Taufdatum, Paten,
            # Volltext – fehlten schlicht. Aufgefallen ist es erst, weil ein
            # Mensch das Taufdatum vermisste.
            #
            # Was ein Mensch angefasst hat, bleibt: `korrigiert` und die
            # Entscheidung ueberschreibt keine Lesung.
            con.execute(
                "INSERT INTO feld "
                "(eintrag_id, name, rolle, gelesen, kb_form, zuversicht, "
                " beleg, reihe) VALUES (?,?,?,?,?,?,?,?) "
                "ON CONFLICT(eintrag_id, name) DO UPDATE SET "
                " gelesen=excluded.gelesen, kb_form=excluded.kb_form, "
                " zuversicht=excluded.zuversicht, beleg=excluded.beleg, "
                " reihe=excluded.reihe "
                # Nicht `entscheidung IS NULL` pruefen: Die Spalte steht per
                # Vorgabe auf 'offen' und wird vom Abgleich gesetzt, ist
                # also nie leer – die Bedingung blockierte jede
                # Aktualisierung. Der ehrliche Marker fuer Menschenarbeit
                # ist `korrigiert` und der bestaetigte Eintrag.
                "WHERE feld.korrigiert IS NULL AND EXISTS ("
                "  SELECT 1 FROM eintrag e WHERE e.id=feld.eintrag_id "
                "  AND e.status <> 'bestaetigt')",
                (eid, name, _rolle(art, name), f.get("wert"), f.get("kb"),
                 f.get("zuversicht"), f.get("notiz"), reihen.get(name, 99)))
            n_f += 1
    con.commit()
    return n_e, n_f


def _bildpfad(con, art, bild):
    """Die Datei zu einem Bildnamen – Endung offen, entpackte PDFs eingeschlossen."""
    for f in seiten.bilder(einstellungen.ordner(con, art)):
        if f.stem == bild:
            return f
    return einstellungen.ordner(con, art) / f"{bild}.jpg"


def lauf(runde_id):
    """Der Läufer. Eigene Verbindung – er arbeitet in einem eigenen Thread."""
    con = db.verbinde()
    r = con.execute("SELECT * FROM runde WHERE id=?", (runde_id,)).fetchone()
    a = con.execute("SELECT * FROM auftrag WHERE runde=? AND art='lesen' "
                    "ORDER BY id DESC LIMIT 1", (runde_id,)).fetchone()
    if not r or not a:
        return
    art, quelle, aid = r["register"], r["quelle"], a["id"]
    con.execute("UPDATE runde SET stand='liest' WHERE id=?", (runde_id,))
    con.execute("UPDATE auftrag SET stand='laeuft', begonnen=? WHERE id=?",
                (jetzt(), aid))
    con.commit()

    if quelle == "datei":
        # Seiten und Prompt ablegen, falls das noch nicht geschehen ist.
        vorlage.lege_vor(con, runde_id, still=True)

    schluessel = None
    if quelle == "api":
        import os
        schluessel = os.environ.get("ANTHROPIC_API_KEY")
        if not schluessel:
            con.execute("UPDATE auftrag SET stand='fehler', meldung=?, "
                        "beendet=? WHERE id=?",
                        ("ANTHROPIC_API_KEY nicht gesetzt", jetzt(), aid))
            con.execute("UPDATE runde SET stand='geplant' WHERE id=?", (runde_id,))
            con.commit()
            return

    hid = db.herkunft_id(
        con, "erfassung" if quelle == "api" else "testdaten",
        f"{art} Runde {r['nr']}",
        notiz=f"gelesen aus {quelle}")

    fertig = 0
    con.execute("UPDATE auftrag_seite SET meldung=NULL "
                "WHERE auftrag=? AND stand='fertig'", (aid,))
    for s in list(con.execute(
            "SELECT * FROM auftrag_seite WHERE auftrag=? AND stand<>'fertig' "
            "ORDER BY bild", (aid,))):
        bild = s["bild"]
        con.execute("UPDATE auftrag_seite SET stand='laeuft' WHERE id=?", (s["id"],))
        con.execute("UPDATE auftrag SET aktuell=? WHERE id=?", (bild, aid))
        con.commit()
        try:
            if quelle == "testdaten":
                erg = testdaten.lies_seite(bild)
                nutzung = {}
            elif quelle == "datei":
                erg = vorlage.lies_seite(r["nr"], bild)
                nutzung = {}
            else:
                from . import lesen
                pfad = _bildpfad(con, art, bild)
                erg, nutzung = lesen.lies_seite(pfad, art, schluessel, con)
            n_e, n_f = speichere(con, art, bild, erg, runde_id, hid)
            # Streifen gleich mitschneiden – der Bearbeiter braucht sie beim
            # Korrigieren, und sie kosten nichts als eine halbe Sekunde CPU.
            # Das Modell hat die Zuordnung schon geliefert: wie viele Einträge
            # und in welcher Reihenfolge. Mehr braucht das Abzählen nicht.
            guete = ""
            try:
                _, guete = streifen.fuer_bild(con, art, bild)
            except Exception as x:
                guete = f"Streifen nicht geschnitten: {type(x).__name__}"
            con.execute(
                "UPDATE auftrag_seite SET stand='fertig', eintraege=?, felder=?, "
                "meldung=? WHERE id=?",
                (n_e, n_f,
                 None if guete in ("passt", "letzte Linie ergänzt") else guete,
                 s["id"]))
            con.execute(
                "UPDATE auftrag SET tokens_ein=tokens_ein+?, "
                "tokens_aus=tokens_aus+? WHERE id=?",
                (nutzung.get("input_tokens", 0),
                 nutzung.get("output_tokens", 0), aid))
        except FileNotFoundError as e:
            # Bei der Quelle 'datei' heisst eine fehlende Antwort nur: noch
            # nicht gelesen. Das ist kein Fehler, sondern der Normalzustand,
            # bis die Sitzung durch ist – die Seite bleibt wartend und der
            # Lauf laesst sich beliebig oft wiederholen.
            con.execute("UPDATE auftrag_seite SET stand='wartet', meldung=? "
                        "WHERE id=?", (str(e)[:400], s["id"]))
        except Exception as e:
            # Sonstige Fehler gelten je Seite, nicht je Lauf. Ein SystemExit
            # mitten in zwanzig Seiten waere in einem Hintergrund-Thread ein
            # stiller Tod: Die ersten Seiten waeren gespeichert, und niemand
            # wuesste, warum es aufgehoert hat.
            con.execute("UPDATE auftrag_seite SET stand='fehler', meldung=? "
                        "WHERE id=?", (f"{type(e).__name__}: {e}"[:400], s["id"]))
            traceback.print_exc()
        fertig += 1
        con.execute("UPDATE auftrag SET seiten_fertig=? WHERE id=?", (fertig, aid))
        con.commit()

    schlecht = con.execute(
        "SELECT count(*) FROM auftrag_seite WHERE auftrag=? AND stand='fehler'",
        (aid,)).fetchone()[0]
    con.execute("UPDATE auftrag SET stand=?, aktuell=NULL, beendet=?, "
                "meldung=? WHERE id=?",
                ("fehler" if schlecht == a["seiten_gesamt"] else "fertig",
                 jetzt(), f"{schlecht} Seite(n) mit Fehler" if schlecht else None,
                 aid))
    offen = con.execute(
        "SELECT count(*) FROM auftrag_seite WHERE auftrag=? AND stand='wartet'",
        (aid,)).fetchone()[0]
    # Abgleichen, was da ist – auch wenn noch Seiten fehlen. Bei der Quelle
    # 'datei' kann das Lesen über mehrere Sitzungen gehen; solange dürfen die
    # schon gelesenen Einträge nicht grau liegen bleiben.
    from . import abgleich
    abgleich.runde_pruefen(con, runde_id)

    if offen:
        # Die Runde bleibt beim Lesen stehen, damit ein zweiter Lauf die
        # fehlenden Seiten nachholt.
        con.execute("UPDATE runde SET stand='geplant' WHERE id=?", (runde_id,))
        con.execute("UPDATE auftrag SET stand='wartet', meldung=? WHERE id=?",
                    (f"{offen} Seite(n) noch ohne Antwort", aid))
        con.commit()
        return

    con.execute("UPDATE runde SET stand='korrigieren' WHERE id=?", (runde_id,))
    con.commit()
    con.close()


LAEUFER = {}


def starte(runde_id):
    """Läufer im Hintergrund – der Browser darf zugemacht werden."""
    t = LAEUFER.get(runde_id)
    if t and t.is_alive():
        return False
    t = threading.Thread(target=lauf, args=(runde_id,), daemon=True,
                         name=f"runde-{runde_id}")
    LAEUFER[runde_id] = t
    t.start()
    return True


# --------------------------------------------------------------- Übergabe
def uebergib(con, runde_id, schreib=False):
    """Bestätigte Einträge dieser Runde werden zum Bestand.

    Erst danach kann die nächste Tranche gegen sie ankern – das ist der
    ganze Sinn der Reihenfolge Ehen → Taufen → Tode. Ohne diesen Schritt
    ist der Registerwechsel wirkungslos.
    """
    from . import uebergabe
    r = con.execute("SELECT * FROM runde WHERE id=?", (runde_id,)).fetchone()
    if not r:
        raise SystemExit(f"keine Runde {runde_id}")
    z = uebergabe.uebernimm(con, r["register"], schreib, runde_id,
                            marke=f"{r['register']} Runde {r['nr']}")
    if schreib:
        con.execute("UPDATE runde SET stand='fertig', beendet=? WHERE id=?",
                    (jetzt(), runde_id))
        con.commit()
        # Sofort, nicht am Ende. Wer ein Ortsfamilienbuch für eine andere
        # Zeit hat, arbeitet in einer Kopie davon – zwei getrennt
        # gewachsene Bestände hinterher zu verschmelzen ist die Arbeit, die
        # niemand mehr sauber hinbekommt. Siehe ausgabe.arbeitskopie().
        from . import ausgabe
        try:
            z["arbeitskopie"] = ausgabe.arbeitskopie(con)["datei"]
        except Exception as e:
            # Eine gescheiterte Kopie darf die Übergabe nicht zurücknehmen –
            # die Daten liegen in der Datenbank, die Datei ist ihr Abbild.
            z["arbeitskopie_fehler"] = f"{type(e).__name__}: {e}"
    return z


def verwerfen(con, runde_id):
    """Eine Runde rückstandslos zurücknehmen.

    Nötig, damit sich derselbe Durchlauf wiederholen lässt – zum Prüfen, zum
    Vorführen, und wenn eine Runde mit falschen Einstellungen lief. Gelöscht
    wird nur, was diese Runde erzeugt hat: ihre Einträge und die Personen und
    Familien ihrer Übergabe. Der eingelesene Bestand bleibt unberührt.
    """
    r = con.execute("SELECT * FROM runde WHERE id=?", (runde_id,)).fetchone()
    if not r:
        return {}
    marke = f"{r['register']} Runde {r['nr']}"
    h = con.execute("SELECT id FROM herkunft WHERE art='erfassung' AND datei=?",
                    (marke,)).fetchone()
    z = dict(eintraege=0, personen=0, familien=0)
    z["eintraege"] = con.execute(
        "SELECT count(*) FROM eintrag WHERE runde=?", (runde_id,)).fetchone()[0]
    # Reihenfolge ist hier nicht Geschmack, sondern Bedingung: `feld.person`
    # zeigt auf Personen. Wer die Personen zuerst löscht, läuft in einen
    # Fremdschlüsselfehler – und zwar erst dann, wenn der Abgleich nach der
    # Übergabe noch einmal lief und auf die eigenen Neuanlagen zeigte.
    con.execute("DELETE FROM eintrag WHERE runde=?", (runde_id,))
    con.execute("DELETE FROM auftrag WHERE runde=?", (runde_id,))
    if h:
        z["personen"] = con.execute(
            "SELECT count(*) FROM person WHERE herkunft=?", (h["id"],)).fetchone()[0]
        z["familien"] = con.execute(
            "SELECT count(*) FROM familie WHERE herkunft=?", (h["id"],)).fetchone()[0]
        # Verweise aus anderen Runden lösen, sonst hält der Fremdschlüssel
        con.execute("UPDATE feld SET person=NULL, entscheidung='offen' "
                    "WHERE person IN (SELECT id FROM person WHERE herkunft=?)",
                    (h["id"],))
        con.execute("DELETE FROM vorgang WHERE ziel IN "
                    "(SELECT CAST(id AS TEXT) FROM person WHERE herkunft=?) "
                    "AND art='neu_person'", (h["id"],))
        con.execute("DELETE FROM ereignis WHERE person IN "
                    "(SELECT id FROM person WHERE herkunft=?)", (h["id"],))
        con.execute("DELETE FROM ereignis WHERE familie IN "
                    "(SELECT id FROM familie WHERE herkunft=?)", (h["id"],))
        con.execute("DELETE FROM kind WHERE person IN "
                    "(SELECT id FROM person WHERE herkunft=?)", (h["id"],))
        con.execute("DELETE FROM familie WHERE herkunft=?", (h["id"],))
        con.execute("DELETE FROM person WHERE herkunft=?", (h["id"],))
        con.execute("DELETE FROM herkunft WHERE id=?", (h["id"],))
    con.execute("DELETE FROM runde WHERE id=?", (runde_id,))
    con.commit()
    return z


def offen_in_runde(con, runde_id):
    """Was in dieser Runde noch auf Bestätigung wartet."""
    r = con.execute(
        "SELECT count(*) n, SUM(status='bestaetigt') fix FROM eintrag "
        "WHERE runde=?", (runde_id,)).fetchone()
    a = dict(gruen=0, gelb=0, rot=0, grau=0)
    for x in con.execute(
            "SELECT f.ampel, count(*) n FROM feld f "
            "JOIN eintrag e ON e.id=f.eintrag_id WHERE e.runde=? "
            "GROUP BY f.ampel", (runde_id,)):
        a[x["ampel"]] = x["n"]
    return dict(eintraege=r["n"] or 0, bestaetigt=r["fix"] or 0, ampel=a)


# -------------------------------------------------------------- Fortschritt
def fortschritt(con, runde_id):
    a = con.execute("SELECT * FROM auftrag WHERE runde=? ORDER BY id DESC "
                    "LIMIT 1", (runde_id,)).fetchone()
    if not a:
        return None
    d = dict(a)
    d["seiten"] = [dict(x) for x in con.execute(
        "SELECT bild, stand, eintraege, felder, meldung FROM auftrag_seite "
        "WHERE auftrag=? ORDER BY bild", (a["id"],))]
    return d


def stand(con):
    """Was der Startbildschirm zeigt – echte Zahlen, keine Vermutungen."""
    raus = []
    for art in register_reihe(con):
        ordner = einstellungen.ordner(con, art)
        bilder = seiten.bilder(ordner)
        gelesen = gelesene_bilder(con, art)
        e = con.execute(
            "SELECT count(*) n, "
            "SUM(status='bestaetigt') fix FROM eintrag WHERE register=?",
            (art,)).fetchone()
        raus.append(dict(
            register=art, titel=konfig.register(art).get("titel", art),
            ordner=konfig.kurz(ordner),
            bilder=len(bilder), gelesen=len(gelesen),
            eintraege=e["n"] or 0, bestaetigt=e["fix"] or 0,
            seiten_je_runde=einstellungen.seitenzahl(con, art),
            pdfs=len(seiten.pdfs(ordner)),
            offen_api=len(offene_bilder(con, art, "api")),
            offen_test=len(offene_bilder(con, art, "testdaten"))))
    return raus


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stand", action="store_true")
    ap.add_argument("--plane")
    ap.add_argument("--seiten", type=int, default=0)
    ap.add_argument("--quelle", default="api",
                    choices=("api", "testdaten", "datei"))
    ap.add_argument("--lies", type=int)
    ap.add_argument("--uebergib", type=int)
    ap.add_argument("--verwirf", type=int)
    ap.add_argument("--schreib", action="store_true")
    a = ap.parse_args()
    con = db.verbinde()

    if a.verwirf:
        z = verwerfen(con, a.verwirf)
        print("verworfen: " + " · ".join(f"{k} {v}" for k, v in z.items()))
        return

    if a.uebergib:
        z = uebergib(con, a.uebergib, a.schreib)
        print(("geschrieben: " if a.schreib else "Probelauf: ")
              + " · ".join(f"{k} {v}" for k, v in z.items()))
        if not a.schreib:
            print("(nichts geschrieben – mit --schreib übernehmen)")
        return

    if a.plane:
        rid = plane(con, a.plane, a.seiten or None, a.quelle)
        r = con.execute("SELECT * FROM runde WHERE id=?", (rid,)).fetchone()
        print(f"Runde {r['nr']}: {r['register']}, {r['seiten']} Seiten "
              f"({r['von_bild']} – {r['bis_bild']}), Quelle {r['quelle']}")
        return
    if a.lies:
        lauf(a.lies)
        f = fortschritt(con, a.lies)
        print(f"gelesen: {f['seiten_fertig']}/{f['seiten_gesamt']} Seiten")
        for s in f["seiten"]:
            print(f"  {s['bild']}  {s['stand']:7} {s['eintraege']:3} Einträge"
                  + (f"  ⚠ {s['meldung']}" if s["meldung"] else ""))
        return

    for z in stand(con):
        print(f"  {z['titel']:16} {z['bilder']:4} Bilder · "
              f"{z['gelesen']:3} gelesen · {z['eintraege']:4} Einträge · "
              f"{z['bestaetigt']:4} bestätigt")
    v = vorschlag(con)
    print(f"\n  nächster Schritt: {v['register'] or '–'}  ({v['grund']})")
    r = offene_runde(con)
    if r:
        print(f"  offene Runde {r['nr']}: {r['register']}, Stand {r['stand']}")


if __name__ == "__main__":
    main()
