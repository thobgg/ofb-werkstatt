#!/usr/bin/env python3
"""GEDCOM 7 ausgeben und prüfen, der zweite Ausgang.

    python3 -m werkstatt.ausgabe7 --neu -o datei.ged
    python3 -m werkstatt.ausgabe7 --pruefe datei.ged
    python3 -m werkstatt.ausgabe7 --tags

**Warum ein zweiter Ausgang und nicht ein neuer erster.** Der Kern von
`ausgabe.py` ist die Fortschreibung: Die Vorlage läuft Record für Record
durch, unberührte Records gehen zeichengleich hindurch. Das geht nur, weil
Vorlage und Ausgabe dasselbe Format haben, und die Bestände sind 5.5.1. Wer
in GEDCOM 7 fortschreiben wollte, müsste die ganze Vorlage übersetzen, und
damit wäre das Versprechen weg, das die Werkstatt überhaupt tragbar macht.

GEDCOM 7 steht deshalb genau dort, wo es sinnvoll ist: bei der
**Neuausgabe**, also für den, der ohne Vorlage anfängt, und als
Zweitausfertigung neben der Fortschreibung, für Programme, die 7 lesen.

**Was hier fremd zugekauft ist.** Geschrieben wird nicht von Hand, sondern
über `gedcom7` von David Straub (MIT). Das Paket setzt die Zeilen aus einem
Strukturbaum, kürzt Erweiterungstags über das Schema ab, bricht lange Werte
in `CONT`, verdoppelt ein führendes `@` und lehnt verbotene Zeichen ab. Von
Hand nachgebaut wäre das eine zweite Fehlerquelle ohne Gewinn:

    python3 -m pip install gedcom7

Ohne das Paket bleibt alles beim Alten, nur dieser Ausgang fehlt.

**Die Prüfung ist der eigentliche Ertrag.** Dasselbe Paket bringt die
Tabellen der Spezifikation mit, also welche Substruktur unter welcher
Struktur stehen darf und welchen Payload sie trägt. Damit prüft `--pruefe`
nicht nur die Grammatik, sondern das Schema, und zwar durch fremden Code an
fremden Tabellen. Ein selbstgeschriebener Prüfer würde dieselben Annahmen
bestätigen, die beim Schreiben schon drinstecken.

**Kein Zeitstempel.** Weder `HEAD.DATE` noch `CHAN` werden geschrieben,
obwohl beide erlaubt wären. Zweimal ausgeben muss zweimal dasselbe ergeben,
sonst ist keine Ausgabe mehr mit der vorigen vergleichbar, und der Beleg
über Verlustfreiheit hinge an einer Uhr.

## Was GEDCOM 7 an der Ausgabe ändert

    5.5.1                        7.0
    2 VERS 5.5.1                 2 VERS 7.0
    1 CHAR UTF-8                 entfällt, UTF-8 ist vorgeschrieben
    1 _KB_NAME …                 dasselbe, aber im HEAD.SCHMA erklärt
    2 DATE (um Ostern)           2 DATE / 3 PHRASE um Ostern
    1 DEAT totgeboren            1 DEAT / 2 NOTE totgeboren
    2 CONC …                     entfällt, es gibt nur CONT

Die eigenen Tags der OFB-Konvention (`_KB_NAME`, `_BERUF_KB`, `_GODP` …)
bleiben, wie sie sind. In 5.5.1 stehen sie unerklärt in der Datei und jedes
lesende Programm muss raten; in 7 nennt das Schema im Kopf für jeden eine
URI, die auf `doku/gedcom7-tags.md` zeigt. Das ist der zweite Grund für
diesen Ausgang: Die Hauskonvention wird dokumentiert statt geduldet.
"""
import argparse
from pathlib import Path

from . import db, katalog, konfig
from .ausgabe import gedcom_datum, kennungen_vergeben

# Wohin die Erweiterungstags zeigen. Die Spezifikation verlangt eine URI je
# eigenem Tag und empfiehlt, dass sie auf eine Beschreibung führt. Sie führt
# hier auf die Datei, die diese Tags erklärt, mit dem Tag als Sprungmarke.
BASIS = ("https://github.com/thobgg/ofb-werkstatt/blob/main/"
         "doku/gedcom7-tags.md#")

# Ereignisse tragen in GEDCOM 7 keinen Text: ihr Payload ist `Y` oder leer.
# Was in 5.5.1 hinter dem Tag stehen durfte, wird hier zur Notiz darunter.
# Irrt diese Liste, meldet es die Prüfung; sie ist keine Annahme, die
# unbemerkt bleiben kann.
OHNE_TEXT = {"ADOP", "BAPM", "BARM", "BASM", "BIRT", "BLES", "BURI", "CHR",
             "CHRA", "CONF", "CREM", "DEAT", "DIV", "DIVF", "EMIG", "ENGA",
             "FCOM", "GRAD", "IMMI", "MARB", "MARC", "MARL", "MARR", "MARS",
             "NATU", "ORDN", "PROB", "RETI", "WILL"}

# Tags, deren Wert ein Ort ist und die deshalb ein PLAC darunter tragen.
ALS_ORT = {"RESI"}

# Diese Tags schreibt der Personenrecord schon unter NAME.
SCHON_AM_NAMEN = {"_KB_NAME", "_RUFNAME"}


# ----------------------------------------------------------------- Paket
def paket():
    """Das Fremdpaket holen, mit einer Meldung statt eines Stapels."""
    try:
        import gedcom7
    except ModuleNotFoundError:
        raise SystemExit(
            "Für GEDCOM 7 fehlt das Paket `gedcom7` von David Straub:\n"
            "    python3 -m pip install gedcom7\n"
            "Die Ausgabe in 5.5.1 braucht es nicht.")
    return gedcom7


def da():
    """Ist der zweite Ausgang benutzbar? Für die Maske, ohne Abbruch."""
    try:
        import gedcom7                                          # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def s(tag, text="", *, zeiger=None, xref=None, kinder=None):
    """Eine Struktur bauen.

    Kinder werden dem Konstruktor übergeben und nicht nachträglich an die
    Liste gehängt: Nur so setzt das Paket den Rückverweis, und ohne den
    kennt eine Struktur ihren Typ nicht, weil er vom Ort abhängt. `RESI`
    unter INDI ist ein anderer Typ als `RESI` unter FAM.
    """
    from gedcom7.types import GedcomStructure
    return GedcomStructure(tag=tag, pointer=zeiger, text=text or "",
                           xref=xref, children=list(kinder or ()))


# ------------------------------------------------------------------ Datum
def datum7(wert):
    """Datumszeilen: eine Angabe, oder eine Phrase darunter.

    `gedcom_datum` klammert ein, was sich nicht eindeutig lesen lässt. In
    5.5.1 ist die Klammer die einzige Möglichkeit, Text als Text zu
    kennzeichnen. GEDCOM 7 hat dafür `PHRASE`: Das Datum bleibt leer, der
    Wortlaut steht darunter, und ein lesendes Programm weiß, dass es keine
    verlorene Angabe vor sich hat, sondern eine unauflösbare.
    """
    g = gedcom_datum(wert)
    if not g:
        return None
    if g.startswith("(") and g.endswith(")"):
        return s("DATE", "", kinder=[s("PHRASE", g[1:-1])])
    return s("DATE", g)


# --------------------------------------------------------------- Merkmale
def _merkmal_struktur(tag, wert):
    if tag in ALS_ORT:
        return s(tag, "", kinder=[s("PLAC", wert)] if wert else [])
    if tag in OHNE_TEXT:
        return s(tag, "", kinder=[s("NOTE", wert)] if wert else [])
    return s(tag, wert)


def merkmale(con, *, person=None, familie=None):
    z = []
    for m in con.execute(
            "SELECT tag, wert FROM merkmal WHERE person IS ? AND familie IS ? "
            "ORDER BY kb, tag, id", (person, familie)):
        tag = m["tag"]
        if "." in tag or tag in SCHON_AM_NAMEN:
            continue
        z.append(_merkmal_struktur(tag, m["wert"]))
    return z


def merkmale_zu(con, tag, *, person=None, familie=None):
    """Unterzeilen eines Ereignisses: Ziele der Form `MARR.NOTE`."""
    return [s(m["tag"].split(".")[-1], m["wert"]) for m in con.execute(
        "SELECT tag, wert FROM merkmal WHERE person IS ? AND familie IS ? "
        "AND tag LIKE ? ORDER BY id", (person, familie, f"{tag}.%"))]


def ereignis(art, *, wert=None, datum=None, ort=None, quelle=None, zusatz=()):
    """Eine Ereignisstruktur mit allem, was darunter gehört."""
    k = []
    text = ""
    if wert:
        if art in OHNE_TEXT:
            # `1 DEAT totgeboren` ist in 7 kein gültiger Payload. Der Text
            # geht nicht verloren, er rückt eine Ebene tiefer.
            k.append(s("NOTE", wert))
        else:
            text = wert
    if datum:
        d = datum7(datum)
        if d is not None:
            k.append(d)
    if ort:
        k.append(s("PLAC", ort))
    if quelle:
        k.append(s("NOTE", quelle))
    k.extend(zusatz)
    return s(art, text, kinder=k)


# ---------------------------------------------------------------- Records
def person7(con, p, xref, fam_als_kind, fam_als_gatte):
    k = []
    voll = " ".join(x for x in (p["givn"], f"/{p['surn']}/" if p["surn"] else "")
                    if x) or (p["name"] or "")
    unter = []
    if p["givn"]:
        unter.append(s("GIVN", p["givn"]))
    if p["surn"]:
        unter.append(s("SURN", p["surn"]))
    for n in con.execute("SELECT wert FROM namensform WHERE person=? "
                         "AND art='kb'", (p["id"],)):
        unter.append(s("_KB_NAME", n["wert"]))
    for n in con.execute("SELECT wert FROM namensform WHERE person=? "
                         "AND art='rufname'", (p["id"],)):
        unter.append(s("_RUFNAME", n["wert"]))
    k.append(s("NAME", voll, kinder=unter))
    if p["sex"] in ("M", "F", "X", "U"):
        k.append(s("SEX", p["sex"]))

    for e in con.execute("SELECT art, datum, ort, wert, quelle FROM ereignis "
                         "WHERE person=? ORDER BY id", (p["id"],)):
        if e["art"] == "OCCU":
            # Ohne Wert gäbe es ein leeres OCCU, und das ist ein Beruf, den
            # niemand genannt hat. Die Kirchenbuchform steht im eigenen Tag.
            if e["wert"]:
                k.append(s("_BERUF_KB", e["wert"]))
            continue
        k.append(ereignis(e["art"], wert=e["wert"], datum=e["datum"],
                          ort=e["ort"], quelle=e["quelle"],
                          zusatz=merkmale_zu(con, e["art"], person=p["id"])))
    k.extend(merkmale(con, person=p["id"]))
    for f in sorted(fam_als_kind):
        k.append(s("FAMC", zeiger=f"@{f}@"))
    for f in sorted(fam_als_gatte):
        k.append(s("FAMS", zeiger=f"@{f}@"))
    return s("INDI", xref=f"@{xref}@", kinder=k)


def familie7(con, f, xref, xr):
    k = []
    if f["mann"] and xr.get(f["mann"]):
        k.append(s("HUSB", zeiger=f"@{xr[f['mann']]}@"))
    if f["frau"] and xr.get(f["frau"]):
        k.append(s("WIFE", zeiger=f"@{xr[f['frau']]}@"))
    for c in con.execute("SELECT person FROM kind WHERE familie=? "
                         "ORDER BY person", (f["id"],)):
        if xr.get(c["person"]):
            k.append(s("CHIL", zeiger=f"@{xr[c['person']]}@"))
    for e in con.execute("SELECT art, datum, ort, quelle FROM ereignis "
                         "WHERE familie=? ORDER BY id", (f["id"],)):
        k.append(ereignis(e["art"], datum=e["datum"], ort=e["ort"],
                          quelle=e["quelle"],
                          zusatz=merkmale_zu(con, e["art"], familie=f["id"])))
    k.extend(merkmale(con, familie=f["id"]))
    return s("FAM", xref=f"@{xref}@", kinder=k)


# -------------------------------------------------------------------- Kopf
def eigene_tags(records):
    """Jedes Erweiterungstag, das in diesen Records wirklich vorkommt.

    Nicht aus einer gepflegten Liste: Wer ein Feld im Zahnrad einschaltet,
    dessen Ziel ein eigener Tag ist, bekäme sonst eine Datei, in der ein
    undeklarierter Tag steht. Gezählt wird, was geschrieben wird.
    """
    raus = set()

    def geh(x):
        if x.tag.startswith("_"):
            raus.add(x.tag)
        for c in x.children:
            geh(c)

    for r in records:
        geh(r)
    return sorted(raus)


# Was jeder eigene Tag bedeutet. Von Hand, nicht aus dem Katalog: Dort
# steht der Titel des ersten Feldes, das zufällig auf ihn zeigt, und
# `_ALTER_KB` hieße dann „Bräutigam: Altersangabe“, obwohl der Tag für
# jede Person gilt. Welche Felder darauf zielen, kommt darunter aus dem
# Katalog und bleibt damit von selbst aktuell.
BESCHREIBUNG = {
    "_KB_NAME": "Der Name in der Schreibweise des Kirchenbuchs, neben der "
                "normalisierten Form unter NAME. Beide werden geführt: "
                "`Fallerin` im Buch, `Faller` als Name.",
    "_RUFNAME": "Der Name, mit dem die Person gerufen wurde, wenn das "
                "Kirchenbuch ihn eigens nennt.",
    "_BERUF_KB": "Die Berufsbezeichnung im Wortlaut des Kirchenbuchs, etwa "
                 "„Bürger und Weingärtner“.",
    "_ALTER_KB": "Die Altersangabe, wie sie im Eintrag steht, oft auf Jahre, "
                 "Monate und Tage genau. Ein daraus errechnetes Geburtsdatum "
                 "gehört nicht hierher, sondern unter BIRT.DATE mit CAL.",
    "_TODURSACHE": "Die Todesursache im Wortlaut des Kirchenbuchs.",
    "_KB_DATUM": "Die Datumsangabe im Wortlaut, wenn sie sich nicht "
                 "verlustfrei in ein GEDCOM-Datum bringen lässt.",
    "_KB_RELI": "Die Konfessionsangabe im Wortlaut des Eintrags.",
    "_KB_ELTERN": "Eltern, wie der Eintrag sie nennt, samt Beruf, Ort und "
                  "Vermerken. Solange die Werkstatt daraus keine eigenen "
                  "Datensätze bildet, bleibt es Text.",
    "_NOTE_TAUFE": "Bemerkung zum Taufeintrag, für die es kein eigenes Feld "
                   "gibt.",
    "_NOTE_HEIRAT": "Bemerkung zum Traueintrag, meist die Fundstelle: "
                    "„Ehereg. Bd. 6, Bild 2, Nr. 1“.",
    "_NOTE_BEGR": "Bemerkung zum Begräbniseintrag.",
    "_NOTE_ORT": "Die Ortsangabe im Wortlaut, etwa „von Hausen bei "
                 "Brackenheim“, wo PLAC nur den Ort führt.",
    "_NOTE_STAND": "Der Personenstand im Wortlaut, etwa „Wittwer“, "
                   "„lediger Sohn“.",
    "_GODP": "Die Paten im Wortlaut des Eintrags. Als eigene Datensätze "
             "werden sie erst geführt, wenn die Werkstatt Verweise anlegt.",
    "_ASSO": "Platzhalter für einen Verweis auf eine beteiligte Person. "
             "Solange es den Datensatz nicht gibt, bleibt das Feld leer und "
             "der Wortlaut steht in `_GODP`.",
    "_STAT": "Ein Vermerk zum Stand des Eintrags, etwa „unehelich“.",
    "_FAMREG": "Die Seitenzahl des Familienregisters, auf die der Eintrag "
               "verweist.",
}


def tag_felder():
    """Welche Felder des Katalogs auf welchen eigenen Tag zielen."""
    t = {}
    for art, felder in katalog.KATALOG.items():
        for x in felder:
            for ziel in (x.ziel, x.ziel_kb):
                tag = (ziel or "").split(".")[-1]
                if tag.startswith("_"):
                    t.setdefault(tag, []).append(f"{art}: {x.titel}")
    return t


def kopf(records):
    g = konfig.konfig().get("gemeinde", {}).get("name", "")
    k = [s("GEDC", kinder=[s("VERS", "7.0")])]
    tags = eigene_tags(records)
    if tags:
        k.append(s("SCHMA", kinder=[
            s("TAG", f"{t} {BASIS}{t.lower()}") for t in tags]))
    k.append(s("SOUR", "OFB-Werkstatt", kinder=[s("NAME", "OFB-Werkstatt")]))
    if g:
        k.append(s("NOTE", f"Ortsfamilienbuch {g}"))
    return s("HEAD", kinder=k)


# -------------------------------------------------------------- Neuausgabe
def neuausgabe(con, schreib=False):
    """Alles aus den eigenen Tabellen, in GEDCOM 7."""
    g7 = paket()
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

    leib, z = [], dict(personen=0, familien=0)
    for p in con.execute("SELECT * FROM person ORDER BY id"):
        leib.append(person7(con, p, xr[p["id"]],
                            {f for f in als_kind.get(p["id"], ()) if f},
                            {f for f in als_gatte.get(p["id"], ()) if f}))
        z["personen"] += 1
    for f in con.execute("SELECT * FROM familie ORDER BY id"):
        leib.append(familie7(con, f, xf[f["id"]], xr))
        z["familien"] += 1

    # Der Kopf kann erst stehen, wenn der Leib steht: Im Schema darf nur,
    # was auch vorkommt.
    records = [kopf(leib)] + leib + [s("TRLR")]
    z["eigene_tags"] = len(eigene_tags(leib))
    return g7.dumps(records, byte_order_mark=False).encode("utf-8"), z


# ---------------------------------------------------------------- Prüfung
def _pfad(x):
    teile = []
    while x is not None:
        n = x.tag.rsplit("/", 1)[-1] if "://" in x.tag else x.tag
        teile.append(f"{n} {x.xref}" if x.xref else n)
        x = x.parent
    return " > ".join(reversed(teile))


def pruefe(daten):
    """Eine GEDCOM-7-Datei gegen Grammatik und Schema halten.

    Rückgabe `(ok, meldungen)`, wobei jede Meldung
    `{grund, anzahl, beispiel}` ist. Gebündelt, nicht aufgezählt: Ein
    einziger fehlender Schemaeintrag erzeugt sonst eine Zeile je Vorkommen,
    und der Bericht über die alte 5.5.1-Ausgabe war 4630 Zeilen lang für
    drei Ursachen. Was man beheben muss, ist die Ursache.

    Geprüft wird in drei Lagen, und keine davon glaubt der vorigen:

    1. **Grammatik und Zeiger.** Der Parser des Pakets. Er lehnt ab, was
       nicht der ABNF entspricht, und findet Verweise, die ins Leere gehen.
       Genau die hat der Probelauf bisher mit einem eigenen Ausdruck gesucht.
    2. **Schema.** Für jede Struktur sagt das Paket, welcher Typ sie an
       ihrem Ort ist. Kommt nichts zurück, obwohl der Tag ein Standardtag
       ist, steht sie an einer Stelle, an der die Spezifikation sie nicht
       vorsieht. Dazu der Payload: leer, `Y`, Zeiger oder Text.
    3. **Serialisierung.** Einlesen und zurückschreiben muss dieselben
       Zeichen ergeben. Derselbe Gedanke wie beim Leerlauftest der
       Fortschreibung, nur eine Ebene tiefer.
    """
    g7 = paket()
    from gedcom7 import const

    text = daten.decode("utf-8") if isinstance(daten, bytes) else daten
    try:
        records = g7.loads(text)
    except g7.GedcomParseError as e:
        return False, [dict(grund=f"Grammatik: {e}", anzahl=1, beispiel="")]

    funde = {}

    def merke(grund, ort):
        e = funde.setdefault(grund, dict(grund=grund, anzahl=0, beispiel=ort))
        e["anzahl"] += 1

    def geh(x):
        typ = x.type_id
        if x.tag.startswith("_"):
            # Ein deklarierter Tag wäre zur URI aufgelöst worden.
            merke(f"eigener Tag {x.tag} ohne Eintrag im HEAD.SCHMA", _pfad(x))
        elif typ is None and "://" not in x.tag:
            # Steht der Tag unter einem Elternteil, dessen Typ selbst
            # unbekannt ist, sagt das nichts: Unter einer Erweiterung darf
            # stehen, was die Erweiterung festlegt.
            if x.parent is None or x.parent.type_id is not None:
                merke(f"an dieser Stelle sieht die Spezifikation "
                      f"kein {x.tag} vor", _pfad(x))
        if typ is not None:
            soll = const.payloads.get(typ)
            hat = x.text or ""
            if soll == "" and (hat or x.pointer):
                merke(f"{x.tag} trägt einen Wert, darf aber keinen haben",
                      _pfad(x))
            elif soll == "Y|<NULL>" and hat not in ("", "Y"):
                merke(f"{x.tag} trägt Text; erlaubt ist nur „Y“ oder nichts",
                      f"{_pfad(x)}: „{hat[:40]}“")
            elif soll and soll.startswith("@<") and not x.pointer:
                merke(f"{x.tag} braucht einen Verweis, hat aber Text",
                      _pfad(x))
        for c in x.children:
            geh(c)

    for r in records:
        geh(r)

    zurueck = g7.dumps(records, byte_order_mark=text.startswith("﻿"))
    if zurueck != text:
        merke("Zurückgeschrieben ergibt die Datei nicht dieselben Zeichen", "")

    meldungen = sorted(funde.values(), key=lambda m: -m["anzahl"])
    return not meldungen, meldungen


def pruefe_datei(pfad):
    return pruefe(Path(pfad).read_bytes())


# ------------------------------------------------------------------- Tags
def tagliste():
    """Der Inhalt von `doku/gedcom7-tags.md`.

    Die URIs im Schema einer GEDCOM-7-Datei sollen auf eine Beschreibung
    führen. Diese Datei ist das Ziel; sie wird erzeugt, damit sie nicht
    hinter dem Katalog herhinkt.
    """
    felder = tag_felder()
    z = ["# Die eigenen Tags der OFB-Werkstatt", "",
         "*Erzeugt von `python3 -m werkstatt.ausgabe7 --tags`. Die URIs im",
         "`HEAD.SCHMA` einer GEDCOM-7-Ausgabe zeigen auf die Abschnitte",
         "dieser Datei.*", "",
         "Ein Ortsfamilienbuch führt die Form des Kirchenbuchs neben der",
         "normalisierten: `Fallerin` steht im Buch, `Faller` ist der Name.",
         "GEDCOM kennt dafür keine Tags, also gibt es eigene. In GEDCOM",
         "5.5.1 stehen sie unerklärt in der Datei und jedes lesende",
         "Programm muss raten; in GEDCOM 7 nennt das Schema im Kopf für",
         "jeden eine URI, und die zeigt hierher.", "",
         "Die Konvention stammt aus dem gedruckten Ortsfamilienbuch",
         "Haberschlacht und wird nicht geändert, damit Neues zum",
         "Bestehenden passt. Wer sie liest, verliert nichts, wenn er sie",
         "übergeht: Alles Wesentliche steht auch in den Standardtags.", ""]
    for tag in sorted(set(BESCHREIBUNG) | set(felder)):
        z += [f"## {tag}", "",
              BESCHREIBUNG.get(tag, "Noch nicht beschrieben."), "",
              f"    {BASIS}{tag.lower()}", ""]
        if felder.get(tag):
            z.append("Felder der Aktkarte, die hierher schreiben:")
            z.append("")
            z += [f"- {x}" for x in sorted(set(felder[tag]))]
            z.append("")
    return "\n".join(z)


# -------------------------------------------------------------------- CLI
def _zeige(meldungen, grenze=20):
    for m in meldungen[:grenze]:
        mal = f" ({m['anzahl']}×)" if m["anzahl"] > 1 else ""
        print(f"    {m['grund']}{mal}")
        if m["beispiel"]:
            print(f"      z. B. {m['beispiel']}")
    if len(meldungen) > grenze:
        print(f"    … und {len(meldungen) - grenze} weitere Arten")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--neu", action="store_true",
                    help="Neuausgabe in GEDCOM 7")
    ap.add_argument("--pruefe", metavar="DATEI",
                    help="eine GEDCOM-7-Datei gegen Grammatik und Schema halten")
    ap.add_argument("--tags", action="store_true",
                    help="doku/gedcom7-tags.md auf die Ausgabe schreiben")
    ap.add_argument("-o", "--ziel", help="Zieldatei; ohne sie nur Probelauf")
    a = ap.parse_args()

    if a.tags:
        print(tagliste())
        return

    if a.pruefe:
        ok, meldungen = pruefe_datei(a.pruefe)
        if ok:
            print(f"  ✓ {a.pruefe}: gültiges GEDCOM 7")
            raise SystemExit(0)
        print(f"  ✗ {a.pruefe}: {len(meldungen)} Beanstandung(en)")
        _zeige(meldungen)
        raise SystemExit(1)

    if not a.neu:
        raise SystemExit(__doc__)

    con = db.verbinde()
    daten, z = neuausgabe(con, schreib=bool(a.ziel))
    print("  Neuausgabe 7.0: " + " · ".join(f"{k} {v}" for k, v in z.items()))
    print(f"  {len(daten)} Byte")
    ok, meldungen = pruefe(daten)
    print(f"  {'✓' if ok else '✗'} Prüfung: "
          + ("gültiges GEDCOM 7" if ok
             else f"{len(meldungen)} Beanstandung(en)"))
    _zeige(meldungen)
    if a.ziel:
        p = Path(a.ziel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(daten)
        print(f"  geschrieben: {p}")
    else:
        print("  (nichts geschrieben, mit -o DATEI ausgeben)")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
