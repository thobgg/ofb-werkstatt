#!/usr/bin/env python3
"""Konten für den Mehrbenutzerbetrieb: eine Datei, zwei Rollen.

    python3 -m werkstatt.nutzer --anlegen NAME --rolle redakteur
    python3 -m werkstatt.nutzer --anlegen NAME                    (bearbeiter)
    python3 -m werkstatt.nutzer --liste
    python3 -m werkstatt.nutzer --weg NAME

**Ohne die Datei ändert sich nichts.** Existiert `daten/nutzer.txt`
nicht, bleibt die Werkstatt der Einzelplatz ohne Anmeldung, den das
README beschreibt. Erst die Datei schaltet den Kontenbetrieb ein - für
die eine Instanz je Parochie, an der mehrere Bearbeiter arbeiten und
einer Redakteur ist.

**Die Rollen** folgen dem Muster der Crowdsourcing-Projekte (viele
schlagen vor, einer übernimmt gegen die Quelle):

    redakteur   alles - Runden planen und lesen lassen, übergeben,
                ausgeben, Einstellungen, Quellen
    bearbeiter  korrigieren und bestätigen; übergeben, ausgeben und
                alles Kostende oder Strukturelle bleibt beim Redakteur
    gast        nur lesen - plus der Hinweis-Stift: ein Knopf am
                Eintrag, der dem Redakteur eine Anmerkung hinterlässt
                (das bewährte Muster aus Kies und Schorndorf)

**Das Format** ist eine Zeile je Konto, von Hand lesbar:

    name:pbkdf2$<runden>$<salz-hex>$<hash-hex>:rolle

Passwörter stehen nie im Klartext in der Datei; gehasht wird mit
PBKDF2-SHA256. Die Datei liegt in `daten/` und damit außerhalb von Git.
"""
import argparse
import hashlib
import hmac
import secrets

from . import konfig

DATEI = konfig.WURZEL / "daten" / "nutzer.txt"
ROLLEN = ("redakteur", "bearbeiter", "gast")
RUNDEN = 200_000


def _hash(passwort, salz, runden=RUNDEN):
    return hashlib.pbkdf2_hmac("sha256", passwort.encode("utf-8"),
                               bytes.fromhex(salz), runden).hex()


def lade(datei=None):
    """{name: (pbkdf2-feld, rolle)} - leer, wenn es die Datei nicht gibt.

    `datei` ist für das Portal da: Es verwaltet die Kontendateien fremder
    Instanzen über deren Pfad, ohne die Vorgabe der eigenen zu berühren.
    """
    datei = datei or DATEI
    if not datei.exists():
        return {}
    raus = {}
    for zeile in datei.read_text(encoding="utf-8").split("\n"):
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#"):
            continue
        teile = zeile.split(":")
        if len(teile) != 3:
            continue
        name, feld, rolle = (t.strip() for t in teile)
        if rolle in ROLLEN:
            raus[name] = (feld, rolle)
    return raus


def aktiv():
    """Gibt es Konten? Dann gilt der Kontenbetrieb."""
    return bool(lade())


def pruefe(name, passwort):
    """Rolle des Kontos, wenn Name und Passwort stimmen - sonst None."""
    eintrag = lade().get(name)
    if not eintrag:
        return None
    feld, rolle = eintrag
    try:
        art, runden, salz, soll = feld.split("$")
        if art != "pbkdf2":
            return None
        ist = _hash(passwort, salz, int(runden))
    except (ValueError, TypeError):
        return None
    return rolle if hmac.compare_digest(ist, soll) else None


def anlegen(name, passwort, rolle="bearbeiter", datei=None):
    if rolle not in ROLLEN:
        raise SystemExit(f"Rolle {rolle!r} - erlaubt: {', '.join(ROLLEN)}")
    if ":" in name or not name.strip():
        raise SystemExit("Der Name darf keinen Doppelpunkt enthalten.")
    salz = secrets.token_hex(16)
    feld = f"pbkdf2${RUNDEN}${salz}${_hash(passwort, salz)}"
    konten = lade(datei)
    konten[name.strip()] = (feld, rolle)
    _schreibe(konten, datei)


def setze_rolle(name, rolle, datei=None):
    if rolle not in ROLLEN:
        raise SystemExit(f"Rolle {rolle!r} - erlaubt: {', '.join(ROLLEN)}")
    konten = lade(datei)
    if name not in konten:
        raise SystemExit(f"Kein Konto {name!r}.")
    konten[name] = (konten[name][0], rolle)
    _schreibe(konten, datei)


def entfernen(name, datei=None):
    konten = lade(datei)
    if name not in konten:
        raise SystemExit(f"Kein Konto {name!r}.")
    del konten[name]
    _schreibe(konten, datei)


def _schreibe(konten, datei=None):
    datei = datei or DATEI
    datei.parent.mkdir(parents=True, exist_ok=True)
    zeilen = ["# Konten der Werkstatt - eine Zeile je Konto:",
              "# name:pbkdf2$runden$salz$hash:rolle",
              "# Anlegen mit: python3 -m werkstatt.nutzer --anlegen NAME"]
    zeilen += [f"{n}:{f}:{r}" for n, (f, r) in sorted(konten.items())]
    datei.write_text("\n".join(zeilen) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--anlegen", metavar="NAME")
    ap.add_argument("--rolle", choices=ROLLEN, default="bearbeiter")
    ap.add_argument("--passwort", help="sonst wird verdeckt gefragt")
    ap.add_argument("--weg", metavar="NAME")
    ap.add_argument("--liste", action="store_true")
    a = ap.parse_args()
    if a.anlegen:
        pw = a.passwort
        if not pw:
            import getpass
            pw = getpass.getpass(f"Passwort für {a.anlegen}: ")
            if pw != getpass.getpass("Noch einmal: "):
                raise SystemExit("Die Eingaben stimmen nicht überein.")
        if len(pw) < 8:
            raise SystemExit("Mindestens 8 Zeichen.")
        anlegen(a.anlegen, pw, a.rolle)
        print(f"Konto {a.anlegen} ({a.rolle}) in {konfig.kurz(DATEI)}")
        return
    if a.weg:
        entfernen(a.weg)
        print(f"Konto {a.weg} entfernt.")
        return
    konten = lade()
    if not konten:
        print("Keine Konten - die Werkstatt läuft als Einzelplatz "
              "ohne Anmeldung.")
        return
    for n, (_, r) in sorted(konten.items()):
        print(f"  {n:20} {r}")


if __name__ == "__main__":
    main()
