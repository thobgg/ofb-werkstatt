#!/usr/bin/env python3
"""Datenbasis: eine Struktur, viele Eingangstüren.

GEDCOM, Tabellen und die eigene Erfassung schreiben in dieselben Tabellen.
Die Suche kennt keine Herkunft, nur den Inhalt.

    python3 -m werkstatt.db --init
    python3 -m werkstatt.db --stand
"""
import argparse
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import konfig as _k

ROOT = _k.WURZEL
DB = ROOT / "daten" / "erfassung.sqlite"
SCHEMA = Path(__file__).resolve().parent / "schema.sql"


# `CREATE TABLE IF NOT EXISTS` erweitert eine bestehende Tabelle nicht. Ohne
# Nachrüstung laufen alte Datenbanken auf eine neuere schema.sql auf, und zwar
# lautlos: Die Tabelle existiert ja, nur eine Spalte fehlt.
#
# Belegt beim Einbau dieser Funktion: `eintrag` stand seit Längerem mit
# `fam_reg` und `schreiber` in schema.sql und hatte beide in der laufenden
# Datenbank nicht. `fam_reg` ist nach doku/verknuepfung.md der stärkste Anker
# überhaupt – die Spalte war da, wo man sie liest, und fehlte da, wo man sie
# schreibt. Eine von Hand gepflegte Liste hätte genau das wieder übersehen;
# deshalb wird gegen die Schemadatei verglichen statt gegen eine Aufzählung.
SPALTE = re.compile(r"^\s*([a-z_][a-z0-9_]*)\s+(.+?)\s*$", re.I)
KEIN_FELD = ("unique", "primary", "foreign", "check", "constraint")


def _spalten_aus_schema(text):
    """Tabelle -> {Spalte: Definition}, aus den CREATE-TABLE-Blöcken."""
    raus = {}
    for m in re.finditer(
            r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)\n\);",
            text, re.S | re.I):
        tabelle, rumpf = m.group(1), m.group(2)
        spalten = {}
        for zeile in rumpf.split("\n"):
            zeile = zeile.split("--")[0].strip().rstrip(",").strip()
            if not zeile or zeile.lower().startswith(KEIN_FELD):
                continue
            t = SPALTE.match(zeile)
            if t:
                spalten[t.group(1)] = t.group(2)
        raus[tabelle] = spalten
    return raus


def wandere(con, melde=None):
    """Fehlende Spalten ergänzen. Idempotent, ohne Datenverlust."""
    getan = []
    for tabelle, spalten in _spalten_aus_schema(
            SCHEMA.read_text(encoding="utf-8")).items():
        da = {r[1] for r in con.execute(f"PRAGMA table_info({tabelle})")}
        if not da:                        # Tabelle wurde gerade neu angelegt
            continue
        for spalte, defi in spalten.items():
            if spalte in da or "primary key" in defi.lower():
                continue
            # SQLite verweigert ADD COLUMN mit NOT NULL ohne Vorgabewert.
            # Lieber die Bedingung fallen lassen als die Spalte.
            if "not null" in defi.lower() and "default" not in defi.lower():
                defi = re.sub(r"\bNOT\s+NULL\b", "", defi, flags=re.I).strip()
            con.execute(f"ALTER TABLE {tabelle} ADD COLUMN {spalte} {defi}")
            getan.append(f"{tabelle}.{spalte}")
    _bestandsschutz_kontingent(con)
    con.commit()
    if getan and melde:
        melde("nachgerüstet: " + ", ".join(getan))
    return getan


def _bestandsschutz_kontingent(con):
    """Wer schon gelesen hat, behält seinen unbegrenzten Stand.

    Der KI-Deckel ist seit August 2026 Opt-out: Ohne Einstellung gilt
    `kontingent.VORGABE`. Für eine Datenbank, in der schon Aufträge
    stehen, wäre das eine Grenze, die nie jemand gesetzt hat, und der
    verbuchte Verbrauch liegt womöglich längst darüber – der nächste Lauf
    liefe gegen eine Wand. Deshalb bekommen solche Datenbanken `aus`
    eingetragen, den ausdrücklichen Verzicht auf einen Deckel. Neu
    angelegte bleiben unberührt und laufen mit der Vorgabe los.

    Läuft bei jeder Verbindung, solange kein Wert dasteht, nicht nur beim
    ersten Mal. Das ist Absicht: Wer das Feld in der Maske leert, löscht
    die Zeile, und auf einem Bestand mit Verbrauch soll daraus wieder
    „kein Deckel" werden und nicht eine Vorgabe, die den Betrieb sperrt.
    Wer eine Grenze will, trägt eine Zahl ein.
    """
    try:
        da = con.execute(
            "SELECT 1 FROM einstellung WHERE schluessel=?",
            ("ki.budget_dollar",)).fetchone()
        if da:
            return
        gelesen = con.execute(
            "SELECT 1 FROM auftrag WHERE tokens_ein>0 OR dollar>0 "
            "LIMIT 1").fetchone()
        if not gelesen:
            return
        con.execute(
            "INSERT INTO einstellung (schluessel, wert, geaendert) "
            "VALUES (?,?,?)",
            ("ki.budget_dollar", "aus",
             datetime.now(timezone.utc).isoformat(timespec="seconds")))
    except sqlite3.Error:
        # Frische Datenbank ohne die Tabellen: dann gibt es auch nichts
        # zu schützen.
        pass


def verbinde():
    DB.parent.mkdir(parents=True, exist_ok=True)
    # `timeout`: Mit mehreren Faeden kann ein Schreibvorgang auf einen
    # anderen treffen. SQLite wirft dann sofort "database is locked" – mit
    # Wartezeit versucht es stattdessen bis zu zehn Sekunden lang weiter,
    # und das genuegt fuer alles, was diese Werkstatt tut.
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    wandere(con)
    return con


def felder(art=None):
    """Feldreihenfolge je Registerart – kommt aus konfig.toml."""
    if art:
        return _k.felder(art)
    return {a: _k.felder(a) for a in _k.register()}


def herkunft_id(con, art, datei, notiz=None, gilt=None, parochien=None):
    """Herkunftseintrag anlegen oder finden."""
    jetzt = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con.execute(
        "INSERT OR IGNORE INTO herkunft (art, datei, angelegt, notiz) "
        "VALUES (?,?,?,?)", (art, datei, jetzt, notiz))
    hid = con.execute(
        "SELECT id FROM herkunft WHERE art=? AND datei IS ?",
        (art, datei)).fetchone()["id"]
    if gilt:
        con.execute("UPDATE herkunft SET gilt=?, parochien=? WHERE id=?",
                    (gilt, ",".join(parochien or []) or None, hid))
    return hid


def kontext_anwenden(con):
    """Rang aus konfig.toml auf die vorhandenen Herkünfte übertragen.

    Zugeordnet wird über den Dateinamen, nicht den Pfad – ein verschobener
    Bestand soll seinen Rang behalten.

    Die **eigene bestätigte Erfassung** ist immer `beleg`. Das ist keine
    Selbstgefälligkeit: `uebergabe.py` übernimmt ausschließlich bestätigte
    Einträge, also hat ein Mensch jeden davon gesehen. Genau darauf beruht
    „die ersten hundert tragen die nächsten tausend".
    """
    aus_konfig = {Path(q["datei"]).name: q for q in _k.kontext() if q["datei"]}
    gesetzt, offen = [], []
    for r in con.execute("SELECT id, art, datei, gilt FROM herkunft"):
        if r["art"] == "erfassung":
            con.execute("UPDATE herkunft SET gilt='beleg', name=? WHERE id=?",
                        (f"eigene Erfassung ({r['datei']})", r["id"]))
            continue
        q = aus_konfig.get(Path(r["datei"] or "").name)
        if q:
            con.execute(
                "UPDATE herkunft SET gilt=?, parochien=?, name=? WHERE id=?",
                (q["gilt"], ",".join(q["parochien"]) or None, q["name"], r["id"]))
            gesetzt.append(q["name"])
        else:
            offen.append(r["datei"])
    con.commit()
    return gesetzt, offen


def belegherkuenfte(con):
    """IDs der Herkünfte, die bestätigen dürfen. Leer = alles bleibt gelb."""
    return {r["id"] for r in con.execute(
        "SELECT id FROM herkunft WHERE gilt='beleg'")}


def stand(con):
    z = {}
    for t in ("herkunft", "person", "namensform", "familie", "kind",
              "ereignis", "eintrag", "feld"):
        z[t] = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--stand", action="store_true")
    a = ap.parse_args()
    con = verbinde()
    if a.stand:
        for t, n in stand(con).items():
            print(f"  {t:12} {n:7}")
        print()
        for r in con.execute(
                "SELECT h.art, h.datei, count(p.id) n FROM herkunft h "
                "LEFT JOIN person p ON p.herkunft=h.id GROUP BY h.id"):
            print(f"  {r['art']:10} {(r['datei'] or ''):44} {r['n']:6} Personen")
        return
    print(f"Datenbank bereit: {DB.relative_to(ROOT)}")
    for t, n in stand(con).items():
        print(f"  {t:12} {n:7}")


if __name__ == "__main__":
    main()
