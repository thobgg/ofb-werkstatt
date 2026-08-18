#!/usr/bin/env python3
"""Sicherung einer Instanz: eine ZIP-Datei mit allem, was Arbeit war.

    python3 -m werkstatt.sicherung                     eigene Instanz
    python3 -m werkstatt.sicherung --ziel /pfad/ab.zip
    python3 -m werkstatt.sicherung --wiederherstellen sicherung.zip

**Was hinein kommt:** die Datenbank als konsistenter Schnappschuss
(`Connection.backup()`, nicht Dateikopie - eine offene SQLite-Datei
einfach zu kopieren geht meistens gut und irgendwann nicht), die
Kontenliste, beide Konfigurationsdateien, die Kontextquellen und die
GEDCOM-Ausgaben. **Nicht** hinein kommen die Scans - sie sind groß und
liegen beim Bearbeiter bzw. kommen per Upload wieder; wer sie mitsichern
will, nimmt `--mit-bildern`.

**Wiederherstellen** ist bewusst Kommandozeile, kein Knopf: Es
überschreibt den aktuellen Stand. Vorher wird die laufende Datenbank
als `.vorher` daneben gelegt - ein Fehlgriff ist damit umkehrbar.

Im Portal gibt es je Projekt den Knopf „Sicherung erstellen" und die
Liste zum Herunterladen; behalten werden die letzten zehn.
"""
import argparse
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

DB = Path("daten") / "erfassung.sqlite"

# Was neben der Datenbank gesichert wird, relativ zur Instanzwurzel.
DATEIEN = ("daten/nutzer.txt", "konfig.toml", "konfig.local.toml")
ORDNER = ("quellen", "ausgabe")
BILDORDNER = ("bilder", "scans")


def _schnappschuss(db, ziel):
    """Die Datenbank konsistent kopieren, auch wenn gerade einer schreibt."""
    quelle = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    kopie = sqlite3.connect(ziel)
    try:
        quelle.backup(kopie)
    finally:
        kopie.close()
        quelle.close()


def erstellen(wurzel, ziel=None, mit_bildern=False):
    """Sicherung einer Instanz. Rückgabe: Pfad der ZIP-Datei."""
    wurzel = Path(wurzel)
    db = wurzel / DB
    if not db.is_file():
        raise SystemExit(f"keine Datenbank unter {wurzel}")
    stempel = datetime.now().strftime("%Y-%m-%d-%H%M")
    ziel = Path(ziel) if ziel else wurzel / "sicherungen" / (
        f"{wurzel.name}-{stempel}.zip")
    ziel.parent.mkdir(parents=True, exist_ok=True)

    schnapp = ziel.with_suffix(".db-schnappschuss")
    _schnappschuss(db, schnapp)
    try:
        with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(schnapp, "daten/erfassung.sqlite")
            for rel in DATEIEN:
                p = wurzel / rel
                if p.is_file():
                    z.write(p, rel)
            ordner = ORDNER + (BILDORDNER if mit_bildern else ())
            for o in ordner:
                basis = wurzel / o
                if not basis.is_dir():
                    continue
                for p in sorted(basis.rglob("*")):
                    if p.is_file():
                        z.write(p, str(p.relative_to(wurzel)))
    finally:
        schnapp.unlink(missing_ok=True)
    return ziel


def aufraeumen(wurzel, behalten=10):
    """Alte Sicherungen entfernen - die jüngsten `behalten` bleiben."""
    o = Path(wurzel) / "sicherungen"
    if not o.is_dir():
        return 0
    alle = sorted(o.glob("*.zip"))
    weg = alle[:-behalten] if behalten else alle
    for p in weg:
        p.unlink()
    return len(weg)


def liste(wurzel):
    o = Path(wurzel) / "sicherungen"
    if not o.is_dir():
        return []
    return [dict(datei=p.name, bytes=p.stat().st_size,
                 zeit=datetime.fromtimestamp(p.stat().st_mtime)
                 .isoformat(timespec="minutes"))
            for p in sorted(o.glob("*.zip"), reverse=True)]


def wiederherstellen(wurzel, zip_pfad):
    """Eine Sicherung zurückspielen. Die laufende DB bleibt als .vorher.

    Kein Löschen: Was in der Sicherung fehlt, aber im Verzeichnis liegt,
    bleibt stehen. Die Datenbank wird ersetzt (nach Sicherungskopie),
    alles Übrige überschrieben.
    """
    wurzel, zip_pfad = Path(wurzel), Path(zip_pfad)
    if not zipfile.is_zipfile(zip_pfad):
        raise SystemExit(f"{zip_pfad} ist keine ZIP-Datei")
    db = wurzel / DB
    if db.is_file():
        vorher = db.with_suffix(".sqlite.vorher")
        vorher.write_bytes(db.read_bytes())
    n = 0
    with zipfile.ZipFile(zip_pfad) as z:
        for name in z.namelist():
            # Kein Pfadausbruch: nur relative Namen ohne '..'.
            p = Path(name)
            if p.is_absolute() or ".." in p.parts:
                continue
            ziel = wurzel / p
            ziel.parent.mkdir(parents=True, exist_ok=True)
            ziel.write_bytes(z.read(name))
            n += 1
    return n


def main():
    from . import konfig
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ziel", help="Pfad der ZIP-Datei (sonst "
                    "sicherungen/<name>-<datum>.zip)")
    ap.add_argument("--mit-bildern", action="store_true")
    ap.add_argument("--wiederherstellen", metavar="ZIP")
    a = ap.parse_args()
    if a.wiederherstellen:
        antwort = input(
            "Die Sicherung überschreibt den aktuellen Stand.\n"
            "Die laufende Datenbank bleibt als .vorher liegen. "
            "Fortfahren? [ja/nein] ")
        if antwort.strip().lower() != "ja":
            raise SystemExit("abgebrochen")
        n = wiederherstellen(konfig.WURZEL, a.wiederherstellen)
        print(f"{n} Datei(en) zurückgespielt - den Server neu starten.")
        return
    ziel = erstellen(konfig.WURZEL, a.ziel, a.mit_bildern)
    print(f"Sicherung: {ziel}  ({ziel.stat().st_size // 1024} kB)")


if __name__ == "__main__":
    main()
