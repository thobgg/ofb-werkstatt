#!/usr/bin/env python3
"""Wortschatz aus fremden Dateien einlesen — Tabellen, Texte, Listen.

Der Bestandsimport (`import_gedcom.py`) verlangt Personen: Namen mit Daten,
aus denen ein Treffer sich prüfen lässt. Die meisten Vorarbeiten anderer
Forscher haben diese Form nicht. Da liegt eine Namensliste als Tabelle, ein
Ortsverzeichnis, ein abgetipptes Register als Textdokument. Solche Quellen
können nie bestätigen — aber sie können die Vorschlagsliste ordnen, und
genau daran scheitert das Lesen fremder Familien.

**Offen für beliebige Dateien.** Es gibt kein vorgeschriebenes Format. Der
Einleser nimmt, was er findet:

    .csv .tsv .txt          eingebaute Bordmittel
    .xlsx .ods              Tabellen sind gezippte XML-Dateien
    .docx                   ebenso
    ein Ordner              alles darin, rekursiv

**Was in welche Klasse gehört**, sagt entweder die Kopfzeile oder die
Konfiguration. Ohne beides landet alles in `offen` und rankt schwächer,
aber es wirkt. Niemand muss seine Tabelle umbauen.

    [[kontext]]
    name   = "Namensliste Nachbarpfarrei"
    art    = "wortschatz"
    datei  = "~/listen/nachbarn.xlsx"
    gilt   = "vokabular"
    # optional, wenn die Kopfzeile nicht erkannt wird:
    spalten = { "Fam.-Name" = "nachname", "Wohnort" = "ort" }

Aufruf:

    python3 -m werkstatt.import_wortschatz --aus-konfig
    python3 -m werkstatt.import_wortschatz datei.xlsx --klasse nachname
"""
import argparse
import csv
import io
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from . import db, konfig

KLASSEN = ("nachname", "vorname", "ort", "beruf", "offen")

# Kopfzeilen, die sich ohne Rückfrage zuordnen lassen. Deutsch und Englisch,
# weil Vorarbeiten aus beiden Welten kommen. Kleingeschrieben verglichen,
# Satzzeichen und Punkte fliegen vorher raus.
KOPF = {
    "nachname": "nachname", "familienname": "nachname", "famname": "nachname",
    "name": "nachname", "surname": "nachname", "lastname": "nachname",
    "geburtsname": "nachname", "mädchenname": "nachname",
    "maedchenname": "nachname",
    "vorname": "vorname", "vornamen": "vorname", "rufname": "vorname",
    "givenname": "vorname", "firstname": "vorname", "taufname": "vorname",
    "ort": "ort", "wohnort": "ort", "geburtsort": "ort", "heimatort": "ort",
    "gemeinde": "ort", "place": "ort", "birthplace": "ort", "residence": "ort",
    "beruf": "beruf", "stand": "beruf", "gewerbe": "beruf",
    "occupation": "beruf", "profession": "beruf",
}

# Was kein Wort ist: Zahlen, Daten, Kürzel, Satzzeichenhaufen.
UNWORT = re.compile(r"^[\W\d_]*$")
WORT = re.compile(r"[^\W\d_][\w'’\-\.]*", re.UNICODE)


def falte(s):
    """Vergleichsform — dieselbe Regel wie in suche.falte()."""
    s = unicodedata.normalize("NFKD", (s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def kopf_klasse(text):
    """Was sagt eine Spaltenüberschrift? None heißt: nicht erkannt."""
    k = re.sub(r"[^\wäöüß]+", "", (text or "").lower())
    return KOPF.get(k)


# ------------------------------------------------------------- Leser
# Jeder Leser liefert Zeilen als Liste von Zellen. Was daraus wird,
# entscheidet erst `sammle()` — so bleibt das Format austauschbar.

def lies_csv(pfad):
    roh = pfad.read_bytes()
    text = roh.decode("utf-8-sig", errors="replace")
    probe = text[:4096]
    try:
        dialekt = csv.Sniffer().sniff(probe, delimiters=",;\t|")
    except csv.Error:
        dialekt = csv.excel
        dialekt.delimiter = "\t" if "\t" in probe else ";" if ";" in probe else ","
    return [z for z in csv.reader(io.StringIO(text), dialekt)]


def lies_txt(pfad):
    text = pfad.read_bytes().decode("utf-8-sig", errors="replace")
    return [[z] for z in text.splitlines()]


def _xml(zf, name):
    try:
        return ET.fromstring(zf.read(name))
    except KeyError:
        return None


def lies_xlsx(pfad):
    """xlsx ohne Fremdbibliothek: ein ZIP mit XML darin.

    Zeichenketten stehen zentral in sharedStrings.xml, die Zellen verweisen
    mit t="s" nur auf deren Nummer. Wer das übersieht, liest lauter Zahlen.
    """
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(pfad) as zf:
        geteilt = []
        s = _xml(zf, "xl/sharedStrings.xml")
        if s is not None:
            for si in s.findall(f"{ns}si"):
                geteilt.append("".join(t.text or "" for t in si.iter(f"{ns}t")))
        zeilen = []
        blaetter = [n for n in zf.namelist()
                    if n.startswith("xl/worksheets/") and n.endswith(".xml")]
        for blatt in sorted(blaetter):
            b = _xml(zf, blatt)
            if b is None:
                continue
            for row in b.iter(f"{ns}row"):
                zelle = []
                for c in row.findall(f"{ns}c"):
                    v = c.find(f"{ns}v")
                    if c.get("t") == "s" and v is not None:
                        try:
                            zelle.append(geteilt[int(v.text)])
                            continue
                        except (ValueError, IndexError):
                            pass
                    if c.get("t") == "inlineStr":
                        zelle.append("".join(t.text or ""
                                             for t in c.iter(f"{ns}t")))
                    else:
                        zelle.append(v.text if v is not None else "")
                if any(zelle):
                    zeilen.append(zelle)
    return zeilen


def lies_ods(pfad):
    ns = {"table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
          "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}
    with zipfile.ZipFile(pfad) as zf:
        w = _xml(zf, "content.xml")
    if w is None:
        return []
    zeilen = []
    for row in w.iter(f"{{{ns['table']}}}table-row"):
        zelle = []
        for c in row.findall(f"{{{ns['table']}}}table-cell"):
            zelle.append(" ".join(
                p.text or "" for p in c.iter(f"{{{ns['text']}}}p")))
        if any(zelle):
            zeilen.append(zelle)
    return zeilen


def lies_docx(pfad):
    """docx: Absätze und Tabellenzellen, beides als Zeilen."""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(pfad) as zf:
        d = _xml(zf, "word/document.xml")
    if d is None:
        return []
    zeilen = []
    for tbl in d.iter(f"{ns}tbl"):
        for tr in tbl.iter(f"{ns}tr"):
            zelle = [" ".join(t.text or "" for t in tc.iter(f"{ns}t"))
                     for tc in tr.findall(f"{ns}tc")]
            if any(zelle):
                zeilen.append(zelle)
    in_tabelle = {id(p) for tbl in d.iter(f"{ns}tbl") for p in tbl.iter(f"{ns}p")}
    for p in d.iter(f"{ns}p"):
        if id(p) in in_tabelle:
            continue
        text = "".join(t.text or "" for t in p.iter(f"{ns}t")).strip()
        if text:
            zeilen.append([text])
    return zeilen


LESER = {".csv": lies_csv, ".tsv": lies_csv, ".txt": lies_txt, ".md": lies_txt,
         ".xlsx": lies_xlsx, ".xlsm": lies_xlsx, ".ods": lies_ods,
         ".docx": lies_docx}


def dateien(pfad):
    """Eine Datei oder alles Lesbare in einem Ordner."""
    p = Path(pfad).expanduser()
    if p.is_dir():
        return sorted(f for f in p.rglob("*")
                      if f.is_file() and f.suffix.lower() in LESER)
    return [p] if p.suffix.lower() in LESER else []


# ------------------------------------------------------------- Sammeln

def zerlege(zelle, klasse):
    """Eine Zelle in Wörter. Was Wort ist, hängt von der Klasse ab.

    Bei Orten und Berufen zählt die ganze Zelle — „Bönnigheim, Amt
    Besigheim" ist eine Ortsangabe, nicht zwei. Bei Namen zählt jedes Wort
    einzeln, weil Vornamensketten die Regel sind.
    """
    zelle = (zelle or "").strip(" \t\r\n\"'")
    if not zelle or UNWORT.match(zelle) or len(zelle) > 120:
        return []
    if klasse in ("ort", "beruf"):
        return [zelle]
    return [w for w in WORT.findall(zelle) if len(w) > 1]


def sammle(pfad, vorgabe=None, spalten=None, still=False):
    """Wörter aus einer Datei ziehen — mit Klasse, wo sie erkennbar ist.

    Reihenfolge der Zuordnung: was in der Konfiguration steht, schlägt die
    Kopfzeile; die Kopfzeile schlägt die Vorgabe; ohne alles `offen`.
    """
    p = Path(pfad).expanduser()
    zeilen = LESER[p.suffix.lower()](p)
    if not zeilen:
        return {}
    spalten = {falte(k): v for k, v in (spalten or {}).items()}

    # Kopfzeile nur annehmen, wenn sie mindestens eine Spalte erklärt —
    # sonst ist die erste Zeile schon Inhalt und darf nicht verlorengehen.
    kopf = [None] * max(len(z) for z in zeilen)
    erste = zeilen[0]
    erkannt = 0
    for i, z in enumerate(erste):
        k = spalten.get(falte(z)) or kopf_klasse(z)
        if k in KLASSEN:
            kopf[i] = k
            erkannt += 1
    rest = zeilen[1:] if erkannt else zeilen
    if not erkannt:
        kopf = [None] * len(kopf)

    raus = {}
    for z in rest:
        # Eine Zeile mit anderer Spaltenzahl gehört nicht zu dieser
        # Kopfzeile. In einem .docx stehen Absätze und Tabellen
        # nebeneinander — ohne diese Prüfung erbte ein freier Absatz die
        # Spaltenbedeutung der Tabelle darüber.
        passt = len(z) == len(erste)
        for i, zelle in enumerate(z):
            klasse = ((kopf[i] if passt and i < len(kopf) else None)
                      or vorgabe or "offen")
            for w in zerlege(zelle, klasse):
                s = (klasse, w)
                raus[s] = raus.get(s, 0) + 1
    if not still:
        n = sum(raus.values())
        print(f"  {p.name}: {len(raus)} Wörter, {n} Vorkommen"
              + (f", Spalten erkannt: {erkannt}" if erkannt else ""))
    return raus


def schreibe(con, hid, worte, woher):
    for (klasse, wort), anzahl in worte.items():
        con.execute(
            "INSERT INTO wortschatz (herkunft, klasse, wort, gefaltet, "
            "anzahl, woher) VALUES (?,?,?,?,?,?) "
            "ON CONFLICT(herkunft, klasse, wort) DO UPDATE SET "
            "anzahl = anzahl + excluded.anzahl",
            (hid, klasse, wort, falte(wort), anzahl, woher))
    con.commit()


def importiere(pfad, con=None, klasse=None, spalten=None, name=None,
               parochien=None, still=False):
    """Eine Datei oder einen Ordner einlesen. Gibt die Herkunfts-ID zurück.

    Der Rang steht fest: **immer `vokabular`**. Eine Wortliste hat keine
    Daten, an denen ein Treffer sich prüfen ließe — sie darf ranken, nie
    bestätigen. Wer in konfig.toml `gilt = "beleg"` schreibt, bekommt hier
    trotzdem Vokabular; das ist keine Bevormundung, sondern der Unterschied
    zwischen „der Name kommt vor" und „diese Person ist es".
    """
    con = con or db.verbinde()
    quelle = Path(pfad).expanduser()
    fs = dateien(quelle)
    if not fs:
        raise SystemExit(f"{quelle}: nichts Lesbares gefunden — bekannt sind "
                         + ", ".join(sorted(LESER)))
    hid = db.herkunft_id(con, "wortschatz", quelle.name,
                         notiz=f"Wortschatz aus {quelle}",
                         gilt="vokabular", parochien=parochien)
    if name:
        con.execute("UPDATE herkunft SET name=? WHERE id=?", (name, hid))
    con.execute("DELETE FROM wortschatz WHERE herkunft=?", (hid,))
    for f in fs:
        try:
            schreibe(con, hid, sammle(f, klasse, spalten, still), f.name)
        except Exception as e:
            print(f"  {f.name}: übersprungen ({e})", file=sys.stderr)
    z = con.execute("SELECT klasse, count(*) n FROM wortschatz "
                    "WHERE herkunft=? GROUP BY klasse ORDER BY n DESC",
                    (hid,)).fetchall()
    if not still:
        print(f"{quelle.name}: " + ", ".join(f"{r['n']} {r['klasse']}"
                                             for r in z))
    return hid


def aus_konfig(con=None, still=False):
    """Alle Quellen mit art = wortschatz aus konfig.toml einlesen."""
    con = con or db.verbinde()
    getan = []
    for q in konfig.kontext():
        if q["art"] not in ("wortschatz", "csv", "xlsx", "docx", "ods", "txt"):
            continue
        if not q["datei"]:
            continue
        getan.append(importiere(
            q["datei"], con, spalten=q.get("spalten"), name=q["name"],
            parochien=q["parochien"], still=still))
    if not getan and not still:
        print("Keine Wortschatzquelle in konfig.toml — "
              'art = "wortschatz" eintragen.')
    return getan


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("datei", nargs="*")
    ap.add_argument("--aus-konfig", action="store_true")
    ap.add_argument("--klasse", choices=KLASSEN,
                    help="Vorgabe, wenn die Kopfzeile nichts hergibt")
    a = ap.parse_args()
    con = db.verbinde()
    if a.aus_konfig:
        aus_konfig(con)
    for d in a.datei:
        importiere(d, con, klasse=a.klasse)
    if not a.datei and not a.aus_konfig:
        ap.error("Datei angeben oder --aus-konfig")


if __name__ == "__main__":
    main()
