#!/usr/bin/env python3
"""GEDCOM ausgeben — der Weg nach draußen.

    python3 -m werkstatt.ausgabe --leerlauf         Verlustfreiheit belegen
    python3 -m werkstatt.ausgabe --fort             Fortschreibung, Probelauf
    python3 -m werkstatt.ausgabe --fort -o datei.ged
    python3 -m werkstatt.ausgabe --neu  -o datei.ged

Zwei Arten, und beide werden gebraucht:

**Fortschreibung** — für den, der ein Ortsfamilienbuch hat. Die Quelldatei
läuft Record für Record durch; unberührte Records gehen **zeichengleich**
hindurch, nur was ein Vorgang anfasst, wird neu geschrieben. Der Beleg dafür
ist der Leerlauftest: ohne Änderungen muss die Ausgabe Byte für Byte der
Vorlage entsprechen. Schlägt er fehl, ist irgendwo etwas verloren gegangen —
und man sieht sofort wo.

**Neuausgabe** — für den, der bei Null angefangen hat. Alles aus
`person`/`familie`/`ereignis`, ohne Vorlage.

Der Unterschied ist nicht Bequemlichkeit. Ein Ortsfamilienbuch enthält
Jahrzehnte Handarbeit in Feldern, die diese Werkstatt gar nicht kennt —
Quellenangaben, Notizen, Bilder, Ortsdefinitionen. Wer es aus den eigenen
Tabellen neu schreibt, wirft all das weg. Deshalb ist Durchreichen die
Voreinstellung und Neuschreiben die Ausnahme.
"""
import argparse
import re
from pathlib import Path

from . import db, konfig

MONAT = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()


# ------------------------------------------------------------------ Datei
def eigenschaften(con, hid):
    r = con.execute("SELECT bom, zeilenende, schluss FROM herkunft WHERE id=?",
                    (hid,)).fetchone()
    return dict(r) if r else dict(bom=0, zeilenende="lf", schluss=1)


def als_bytes(records, eig):
    """Recordliste zu Dateibytes — mit BOM, Zeilenende und Schlussumbruch."""
    text = "\n".join(records)
    if eig["schluss"]:
        text += "\n"
    if eig["zeilenende"] == "crlf":
        text = text.replace("\n", "\r\n")
    roh = text.encode("utf-8")
    return (b"\xef\xbb\xbf" + roh) if eig["bom"] else roh


def quelle_id(con):
    """Die Herkunft, die als Vorlage dient — die eingelesene GEDCOM-Datei."""
    r = con.execute("SELECT id, datei FROM herkunft WHERE art='gedcom' "
                    "AND id IN (SELECT herkunft FROM rec) "
                    "ORDER BY id LIMIT 1").fetchone()
    return (r["id"], r["datei"]) if r else (None, None)


# ------------------------------------------------------- Records schreiben
def gedcom_datum(datum):
    """Datum durchreichen. GEDCOM-Formen bleiben, wie sie sind.

    Bewusst keine Normalisierung: Was aus dem Bestand kommt, ist bereits
    GEDCOM; was aus der Erfassung kommt, steht so im Kirchenbuch. Beides
    umzurechnen hieße, eine Angabe zu erfinden, die niemand geprüft hat.
    """
    return (datum or "").strip()


# Diese Tags schreibt person_record schon unter 1 NAME — als Merkmal
# noch einmal, und die Angabe stünde zweimal im Record.
SCHON_AM_NAMEN = {"_KB_NAME", "_RUFNAME"}

# Tags, deren Wert ein Ort ist und deshalb als PLAC darunter gehört.
ALS_ORT = {"RESI"}


def merkmale(con, *, person=None, familie=None):
    """Merkmalszeilen einer Person oder Familie.

    Der Tag kommt aus dem Feldkatalog und wird unverändert geschrieben —
    ob er in GEDCOM 5.5.1 steht oder eine eigene Erweiterung ist,
    entscheidet die Aktkarte, nicht die Ausgabe. Die Einstufung steht im
    Zahnrad; hier wird sie nicht noch einmal beurteilt.

    Ebene 1, weil die meisten dieser Angaben Eigenschaften der Person sind
    und nicht Unterangaben eines Ereignisses. Punkt-Ziele wie `BURI.NOTE`
    werden auf ihre letzte Stufe verkürzt und an das Ereignis gehängt, das
    ohnehin geschrieben wird.
    """
    z = []
    for m in con.execute(
            "SELECT tag, wert FROM merkmal WHERE person IS ? AND familie IS ? "
            "ORDER BY kb, tag, id", (person, familie)):
        tag = m["tag"]
        if "." in tag:
            continue                     # gehört zu einem Ereignis, s.u.
        if tag in SCHON_AM_NAMEN:
            continue                     # steht bereits unter 1 NAME
        if tag in ALS_ORT:
            # RESI ist in GEDCOM eine Ereignisstruktur, kein Textfeld. Der
            # Ort gehört als PLAC darunter, sonst lesen ihn manche
            # Programme gar nicht.
            z.append(f"1 {tag}")
            z.append(f"2 PLAC {m['wert']}")
            continue
        z.append(f"1 {tag} {m['wert']}")
    return z


def merkmale_zu(con, tag, *, person=None, familie=None):
    """Unterzeilen eines Ereignisses: Ziele der Form `MARR.NOTE`."""
    z = []
    for m in con.execute(
            "SELECT tag, wert FROM merkmal WHERE person IS ? AND familie IS ? "
            "AND tag LIKE ? ORDER BY id", (person, familie, f"{tag}.%")):
        z.append(f"2 {m['tag'].split('.')[-1]} {m['wert']}")
    return z


def person_record(con, p, xref, fam_als_kind, fam_als_gatte):
    """Einen neuen INDI-Record schreiben — für Personen ohne Vorlage."""
    z = [f"0 @{xref}@ INDI"]
    voll = " ".join(x for x in (p["givn"], f"/{p['surn']}/" if p["surn"] else "")
                    if x) or (p["name"] or "")
    z.append(f"1 NAME {voll}")
    if p["givn"]:
        z.append(f"2 GIVN {p['givn']}")
    if p["surn"]:
        z.append(f"2 SURN {p['surn']}")
    # Kirchenbuchform neben der Normalform — Konvention des bestehenden OFB.
    # Sie darf die Normalform nie ersetzen: dort steht `Krönich`, nicht `Kröneck`.
    for n in con.execute("SELECT wert FROM namensform WHERE person=? AND art='kb'",
                         (p["id"],)):
        z.append(f"2 _KB_NAME {n['wert']}")
    for n in con.execute("SELECT wert FROM namensform WHERE person=? "
                         "AND art='rufname'", (p["id"],)):
        z.append(f"2 _RUFNAME {n['wert']}")
    if p["sex"]:
        z.append(f"1 SEX {p['sex']}")
    for e in con.execute("SELECT art, datum, ort, wert, quelle FROM ereignis "
                         "WHERE person=? ORDER BY id", (p["id"],)):
        if e["art"] == "OCCU":
            z.append(f"1 _BERUF_KB {e['wert']}" if e["wert"] else "1 OCCU")
            continue
        z.append(f"1 {e['art']}" + (f" {e['wert']}" if e["wert"] else ""))
        if e["datum"]:
            z.append(f"2 DATE {gedcom_datum(e['datum'])}")
        if e["ort"]:
            z.append(f"2 PLAC {e['ort']}")
        if e["quelle"]:
            z.append(f"2 NOTE {e['quelle']}")
        z += merkmale_zu(con, e["art"], person=p["id"])
    z += merkmale(con, person=p["id"])
    for f in sorted(fam_als_kind):
        z.append(f"1 FAMC @{f}@")
    for f in sorted(fam_als_gatte):
        z.append(f"1 FAMS @{f}@")
    return "\n".join(z)


def familie_record(con, f, xref, xr):
    z = [f"0 @{xref}@ FAM"]
    if f["mann"] and xr.get(f["mann"]):
        z.append(f"1 HUSB @{xr[f['mann']]}@")
    if f["frau"] and xr.get(f["frau"]):
        z.append(f"1 WIFE @{xr[f['frau']]}@")
    for k in con.execute("SELECT person FROM kind WHERE familie=? ORDER BY person",
                         (f["id"],)):
        if xr.get(k["person"]):
            z.append(f"1 CHIL @{xr[k['person']]}@")
    for e in con.execute("SELECT art, datum, ort, quelle FROM ereignis "
                         "WHERE familie=? ORDER BY id", (f["id"],)):
        z.append(f"1 {e['art']}")
        if e["datum"]:
            z.append(f"2 DATE {gedcom_datum(e['datum'])}")
        if e["ort"]:
            z.append(f"2 PLAC {e['ort']}")
        if e["quelle"]:
            z.append(f"2 NOTE {e['quelle']}")
        z += merkmale_zu(con, e["art"], familie=f["id"])
    z += merkmale(con, familie=f["id"])
    return "\n".join(z)


# -------------------------------------------------------------- Kennungen
def freie_kennung(vorhanden, praefix):
    """Nächste freie Kennung im Stil der Vorlage: I4112, F1347 …"""
    n = 0
    for x in vorhanden:
        m = re.fullmatch(rf"{praefix}(\d+)", x or "")
        if m:
            n = max(n, int(m.group(1)))
    while True:
        n += 1
        k = f"{praefix}{n}"
        if k not in vorhanden:
            yield k


def kennungen_vergeben(con, schreib=False):
    """Neuen Personen und Familien eine Kennung geben — dauerhaft.

    Die Kennung muss in die Datenbank zurück. Sonst bekommt jede Ausgabe
    andere Nummern, und jedes Programm, das die Datei liest, hält dieselben
    Menschen für neue.
    """
    da_p = {r["xref"] for r in con.execute(
        "SELECT xref FROM person WHERE xref IS NOT NULL")}
    da_f = {r["xref"] for r in con.execute(
        "SELECT xref FROM familie WHERE xref IS NOT NULL")}
    gp, gf = freie_kennung(da_p, "I"), freie_kennung(da_f, "F")
    neu_p, neu_f = {}, {}
    for r in con.execute("SELECT id FROM person WHERE xref IS NULL ORDER BY id"):
        k = next(gp)
        da_p.add(k)
        neu_p[r["id"]] = k
    for r in con.execute("SELECT id FROM familie WHERE xref IS NULL ORDER BY id"):
        k = next(gf)
        da_f.add(k)
        neu_f[r["id"]] = k
    if schreib:
        con.executemany("UPDATE person SET xref=? WHERE id=?",
                        [(k, i) for i, k in neu_p.items()])
        con.executemany("UPDATE familie SET xref=? WHERE id=?",
                        [(k, i) for i, k in neu_f.items()])
        con.commit()
    return neu_p, neu_f


# ---------------------------------------------------------- Fortschreibung
def fortschreiben(con, schreib=False):
    """Vorlage durchreichen, Neues anhängen, berührte Records ergänzen.

    Rückgabe: (bytes, Zählung).
    """
    hid, datei = quelle_id(con)
    if hid is None:
        raise SystemExit(
            "keine Vorlage vorhanden — es wurde kein GEDCOM mit Recordtabelle "
            "eingelesen.\nFür einen Bestand ohne Vorlage: --neu")
    eig = eigenschaften(con, hid)
    kennungen_vergeben(con, schreib)

    # „Neu" heißt: steht noch nicht in der Vorlage — nicht „hat gerade
    # eine Kennung bekommen". Der Unterschied fällt erst beim zweiten Mal
    # auf: Nach der ersten Ausgabe haben die Personen ihre Kennung, und
    # eine Fortschreibung, die nur frisch Vergebenes anhängt, ließe sie
    # sämtlich weg. Die Arbeitskopie der zweiten Runde hätte damit die
    # erste Runde stillschweigend wieder verloren.
    in_vorlage = {r["xref"] for r in con.execute(
        "SELECT xref FROM rec WHERE herkunft=? AND xref IS NOT NULL", (hid,))}
    neu_p = {r["id"]: r["xref"] for r in con.execute(
        "SELECT id, xref FROM person WHERE xref IS NOT NULL ORDER BY id")
        if r["xref"] not in in_vorlage}
    neu_f = {r["id"]: r["xref"] for r in con.execute(
        "SELECT id, xref FROM familie WHERE xref IS NOT NULL ORDER BY id")
        if r["xref"] not in in_vorlage}

    # Kennung je Personen- und Familienzeile, alte wie neue
    xr = {r["id"]: r["xref"] for r in con.execute(
        "SELECT id, xref FROM person WHERE xref IS NOT NULL")}
    xr.update(neu_p)
    xf = {r["id"]: r["xref"] for r in con.execute(
        "SELECT id, xref FROM familie WHERE xref IS NOT NULL")}
    xf.update(neu_f)

    # Wer gehört zu welcher Familie — für FAMC/FAMS der neuen Personen und
    # für die CHIL-Zeilen, die in bestehende Familien nachgetragen werden.
    als_kind, als_gatte = {}, {}
    for r in con.execute("SELECT familie, person FROM kind"):
        als_kind.setdefault(r["person"], set()).add(xf.get(r["familie"]))
    for r in con.execute("SELECT id, mann, frau FROM familie"):
        for p in (r["mann"], r["frau"]):
            if p:
                als_gatte.setdefault(p, set()).add(xf.get(r["id"]))

    # Ergänzungen an bestehenden Records: neue Kinder in alte Familien,
    # neue Familien bei alten Personen.
    nachtrag = {}
    for pid, fams in als_kind.items():
        if pid in neu_p:
            continue
        for fx in fams:
            if fx:
                nachtrag.setdefault(xr.get(pid), []).append(f"1 FAMC @{fx}@")
    for pid, fams in als_gatte.items():
        if pid in neu_p:
            continue
        for fx in fams:
            if fx:
                nachtrag.setdefault(xr.get(pid), []).append(f"1 FAMS @{fx}@")
    for fid, fx in xf.items():
        if fid in neu_f:
            continue
        for k in con.execute("SELECT person FROM kind WHERE familie=?", (fid,)):
            if k["person"] in neu_p:
                nachtrag.setdefault(fx, []).append(
                    f"1 CHIL @{neu_p[k['person']]}@")

    z = dict(durchgereicht=0, ergaenzt=0, neu_personen=0, neu_familien=0)
    raus, schluss = [], []
    for r in con.execute("SELECT xref, typ, raw FROM rec WHERE herkunft=? "
                         "ORDER BY seq", (hid,)):
        if r["typ"] == "TRLR":
            schluss.append(r["raw"])
            continue
        zusatz = [x for x in nachtrag.get(r["xref"], [])
                  if x not in r["raw"].split("\n")]
        if zusatz:
            raus.append(r["raw"] + "\n" + "\n".join(sorted(set(zusatz))))
            z["ergaenzt"] += 1
        else:
            raus.append(r["raw"])
            z["durchgereicht"] += 1

    for pid, xref in neu_p.items():
        p = con.execute("SELECT * FROM person WHERE id=?", (pid,)).fetchone()
        raus.append(person_record(con, p, xref,
                                  {f for f in als_kind.get(pid, ()) if f},
                                  {f for f in als_gatte.get(pid, ()) if f}))
        z["neu_personen"] += 1
    for fid, xref in neu_f.items():
        f = con.execute("SELECT * FROM familie WHERE id=?", (fid,)).fetchone()
        raus.append(familie_record(con, f, xref, xr))
        z["neu_familien"] += 1

    raus.extend(schluss or ["0 TRLR"])
    return als_bytes(raus, eig), z


def leerlauf(con):
    """Der Beleg für die Verlustfreiheit.

    Ohne Änderungen muss die Ausgabe Byte für Byte der Vorlage entsprechen.
    Der Test ist streng, billig und ehrlich: Er misst nicht, ob der Export
    plausibel aussieht, sondern ob überhaupt etwas verloren ging.
    """
    hid, datei = quelle_id(con)
    if hid is None:
        return False, "keine Vorlage mit Recordtabelle vorhanden", None
    eig = eigenschaften(con, hid)
    records = [r["raw"] for r in con.execute(
        "SELECT raw FROM rec WHERE herkunft=? ORDER BY seq", (hid,))]
    aus = als_bytes(records, eig)

    quelle = _vorlagenpfad(con, hid)
    if not quelle or not quelle.exists():
        return None, f"Vorlage {datei} liegt nicht mehr am Ort — nicht prüfbar", aus
    soll = quelle.read_bytes()
    if aus == soll:
        return True, f"{len(soll)} Byte, zeichengleich", aus
    return False, _erster_unterschied(soll, aus), aus


def _vorlagenpfad(con, hid):
    r = con.execute("SELECT notiz, datei FROM herkunft WHERE id=?",
                    (hid,)).fetchone()
    if r and r["notiz"]:
        p = Path(str(r["notiz"]).split(",")[0])
        if p.exists():
            return p
    for q in konfig.kontext():
        if q["datei"] and Path(q["datei"]).name == r["datei"]:
            p = Path(q["datei"])
            if not p.is_absolute():
                p = konfig.WURZEL / p
            return p.resolve()
    return None


def _erster_unterschied(soll, ist):
    n = min(len(soll), len(ist))
    for i in range(n):
        if soll[i] != ist[i]:
            a = soll[max(0, i - 40):i + 40]
            b = ist[max(0, i - 40):i + 40]
            return (f"Unterschied ab Byte {i} von {len(soll)}\n"
                    f"    Vorlage: {a!r}\n"
                    f"    Ausgabe: {b!r}")
    return f"Länge verschieden: Vorlage {len(soll)}, Ausgabe {len(ist)} Byte"


# ------------------------------------------------------------- Neuausgabe
KOPF = """0 HEAD
1 SOUR OFB-Werkstatt
2 NAME OFB-Werkstatt
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8"""


def neuausgabe(con, schreib=False):
    """Alles aus den eigenen Tabellen — für den Bestand ohne Vorlage."""
    neu_p, neu_f = kennungen_vergeben(con, schreib)
    xr = {r["id"]: r["xref"] for r in con.execute(
        "SELECT id, xref FROM person WHERE xref IS NOT NULL")}
    xr.update(neu_p)
    xf = {r["id"]: r["xref"] for r in con.execute(
        "SELECT id, xref FROM familie WHERE xref IS NOT NULL")}
    xf.update(neu_f)

    als_kind, als_gatte = {}, {}
    for r in con.execute("SELECT familie, person FROM kind"):
        als_kind.setdefault(r["person"], set()).add(xf.get(r["familie"]))
    for r in con.execute("SELECT id, mann, frau FROM familie"):
        for p in (r["mann"], r["frau"]):
            if p:
                als_gatte.setdefault(p, set()).add(xf.get(r["id"]))

    g = konfig.konfig().get("gemeinde", {}).get("name", "")
    raus = [KOPF + (f"\n1 NOTE Ortsfamilienbuch {g}" if g else "")]
    z = dict(personen=0, familien=0)
    for p in con.execute("SELECT * FROM person ORDER BY id"):
        raus.append(person_record(
            con, p, xr[p["id"]],
            {f for f in als_kind.get(p["id"], ()) if f},
            {f for f in als_gatte.get(p["id"], ()) if f}))
        z["personen"] += 1
    for f in con.execute("SELECT * FROM familie ORDER BY id"):
        raus.append(familie_record(con, f, xf[f["id"]], xr))
        z["familien"] += 1
    raus.append("0 TRLR")
    return als_bytes(raus, dict(bom=0, zeilenende="lf", schluss=1)), z


# ------------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leerlauf", action="store_true",
                    help="Verlustfreiheit gegen die Vorlage belegen")
    ap.add_argument("--fort", action="store_true", help="Fortschreibung")
    ap.add_argument("--neu", action="store_true", help="Neuausgabe")
    ap.add_argument("-o", "--ziel", help="Zieldatei; ohne sie nur Probelauf")
    a = ap.parse_args()
    con = db.verbinde()

    if a.leerlauf:
        ok, meldung, _ = leerlauf(con)
        zeichen = {True: "✓", False: "✗", None: "·"}[ok]
        print(f"  {zeichen} Leerlauftest: {meldung}")
        raise SystemExit(0 if ok is not False else 1)

    if not (a.fort or a.neu):
        raise SystemExit(__doc__)

    daten, z = (neuausgabe if a.neu else fortschreiben)(con, schreib=bool(a.ziel))
    art = "Neuausgabe" if a.neu else "Fortschreibung"
    print(f"  {art}: " + " · ".join(f"{k} {v}" for k, v in z.items()))
    print(f"  {len(daten)} Byte")
    if a.ziel:
        p = Path(a.ziel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(daten)
        print(f"  geschrieben: {p}")
    else:
        print("  (nichts geschrieben — mit -o DATEI ausgeben)")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------ Arbeitskopie
def arbeitskopie(con, ordner=None):
    """Den vollständigen Bestand nach jeder Übergabe neu schreiben.

    **Warum sofort und nicht am Ende.** Wer ein Ortsfamilienbuch für eine
    frühere oder spätere Zeit hat, arbeitet nicht neben ihm her, sondern in
    einer Kopie davon. Zwei getrennt gewachsene Bestände am Schluss
    zusammenzuführen ist die Arbeit, die niemand mehr sauber hinbekommt:
    Dieselbe Person steht dann zweimal da, mit anderer Kennung, anderer
    Schreibweise, anderen Kindern — und keine Maschine kann entscheiden,
    welche der beiden die richtige ist.

    Deshalb entsteht die Kopie schrittweise: Jede übergebene Runde schreibt
    sie neu, mit allem, was bis dahin da ist. Wer nach der dritten Runde
    aufhört, hat einen vollständigen Bestand, keinen halben.

    **Die Vorlage wird nie angefasst.** Geschrieben wird ausschließlich nach
    `ausgabe/`; die Quelldatei bleibt Byte für Byte, wie sie war. Die
    vorige Kopie bleibt als `.vorher.ged` liegen — ein Schritt zurück ist
    damit immer möglich.
    """
    hid, _ = quelle_id(con)
    daten, z = (fortschreiben(con, schreib=True) if hid is not None
                else neuausgabe(con, schreib=True))
    name = (konfig.konfig().get("gemeinde", {}).get("name") or "OFB").replace(
        "/", "-")
    ziel = Path(ordner or (konfig.WURZEL / "ausgabe")) / f"{name}_arbeitskopie.ged"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    if ziel.exists():
        ziel.replace(ziel.with_suffix(".vorher.ged"))
    ziel.write_bytes(daten)
    return dict(datei=konfig.kurz(ziel), bytes=len(daten),
                art="fort" if hid is not None else "neu", zahlen=z)
