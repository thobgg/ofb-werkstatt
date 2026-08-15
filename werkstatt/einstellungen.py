#!/usr/bin/env python3
"""Betriebseinstellungen – was sich beim Arbeiten ändert.

    python3 -m werkstatt.einstellungen
    python3 -m werkstatt.einstellungen --setze seiten.ehe 10
    python3 -m werkstatt.einstellungen --setze reihenfolge ehe,taufe,tod

Die Trennlinie zu `konfig.toml`:

    konfig.toml   Registerarten, Felder, Rollen, Kontextquellen
                  -> Struktur. Einmal beim Einrichten.
    einstellung   Seitenzahl, Reihenfolge, Bildordner, Autopilot
                  -> Betrieb. Beim Arbeiten.

Betriebswerte in die TOML-Datei zurückzuschreiben hieße, sie bei jedem Klick
neu zu erzeugen und dabei ihre Kommentare zu verlieren – die machen den halben
Erklärwert der Datei aus. Was hier nicht gesetzt ist, kommt weiterhin von dort.
"""
import argparse
from pathlib import Path

from . import db, konfig

# Vorgaben mit Begründung. Die Seitenzahlen sind ungleich, weil ein
# Eheeintrag sechs Personen nennt und ein Taufeintrag drei – gleich viele
# Seiten bedeuten sehr ungleich viel Arbeit.
VORGABEN = {
    "reihenfolge": None,        # leer = Reihenfolge wie in konfig.toml
    "seiten.ehe": 10,
    "seiten.taufe": 20,
    "seiten.tod": 20,
    "seiten": 20,               # Rückfall für Register ohne eigene Angabe
    "autopilot": "normal",      # streng | normal | zuegig
    "vorauslesen": 3,           # Seiten Vorlauf vor dem Bearbeiter
    "ausgabe_je_tranche": 1,
    "mutter_alter_min": 14,
    "mutter_alter_max": 50,
    "vater_alter_min": 16,
    "vater_alter_max": 70,
}

AUTOPILOT = {
    "streng": "nichts läuft durch – jedes Feld wird vorgelegt",
    "normal": "grün läuft durch, gelb und rot werden vorgelegt",
    "zuegig": "grün und eindeutiges Gelb laufen durch",
}


def alle(con):
    return {r["schluessel"]: r["wert"] for r in
            con.execute("SELECT schluessel, wert FROM einstellung")}


def wert(con, name, vorgabe=None):
    r = con.execute("SELECT wert FROM einstellung WHERE schluessel=?",
                    (name,)).fetchone()
    if r is not None and r["wert"] not in (None, ""):
        return r["wert"]
    if vorgabe is not None:
        return vorgabe
    return VORGABEN.get(name)


def zahl(con, name, vorgabe=None):
    try:
        return int(str(wert(con, name, vorgabe)).strip())
    except (TypeError, ValueError):
        return VORGABEN.get(name)


def setze(con, name, w):
    from datetime import datetime, timezone
    con.execute(
        "INSERT INTO einstellung (schluessel, wert, geaendert) VALUES (?,?,?) "
        "ON CONFLICT(schluessel) DO UPDATE SET wert=excluded.wert, "
        "geaendert=excluded.geaendert",
        (name, None if w is None else str(w),
         datetime.now(timezone.utc).isoformat(timespec="seconds")))
    con.commit()


# ------------------------------------------------------------- Abgeleitetes
def reihenfolge(con):
    """Register in der Reihenfolge, in der sie drankommen.

    Ehen zuerst: Der Elternehe-Anker trägt im Taufjahr 1808 noch 94 %, 1820
    nur 18 % – es sei denn, die Ehen sind vorher übergeben. Tode zuletzt,
    weil sie beide vorigen Register als Anker nutzen.
    """
    aus_konfig = list(konfig.register())
    gesetzt = wert(con, "reihenfolge")
    if not gesetzt:
        return aus_konfig
    reihe = [x.strip() for x in str(gesetzt).split(",") if x.strip()]
    # Unbekanntes verwerfen, Fehlendes hinten anhängen – eine veraltete
    # Einstellung darf kein Register verschwinden lassen.
    reihe = [r for r in reihe if r in aus_konfig]
    return reihe + [r for r in aus_konfig if r not in reihe]


def seitenzahl(con, art):
    return zahl(con, f"seiten.{art}", VORGABEN.get(f"seiten.{art}",
                                                   VORGABEN["seiten"]))


def ordner(con, art):
    """Bildordner eines Registers – Einstellung schlägt konfig.toml."""
    p = wert(con, f"ordner.{art}")
    if p:
        p = Path(str(p)).expanduser()
        return p if p.is_absolute() else konfig.WURZEL / p
    return konfig.bilderordner(art)


def grenzen(con):
    return dict(
        mutter=(zahl(con, "mutter_alter_min"), zahl(con, "mutter_alter_max")),
        vater=(zahl(con, "vater_alter_min"), zahl(con, "vater_alter_max")))


def uebersicht(con):
    """Was die Einstellungsseite zeigt – Wert plus Herkunft des Werts."""
    gesetzt = alle(con)
    raus = []
    for name, vorgabe in VORGABEN.items():
        raus.append(dict(schluessel=name,
                         wert=gesetzt.get(name, vorgabe),
                         vorgabe=vorgabe,
                         eigen=name in gesetzt))
    return raus


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setze", nargs=2, metavar=("SCHLUESSEL", "WERT"))
    ap.add_argument("--loesche", metavar="SCHLUESSEL")
    a = ap.parse_args()
    con = db.verbinde()

    if a.setze:
        setze(con, a.setze[0], a.setze[1])
        print(f"  {a.setze[0]} = {a.setze[1]}")
        return
    if a.loesche:
        con.execute("DELETE FROM einstellung WHERE schluessel=?", (a.loesche,))
        con.commit()
        print(f"  {a.loesche} auf Vorgabe zurückgesetzt")
        return

    print(f"  Reihenfolge   {' → '.join(reihenfolge(con))}")
    print(f"  Autopilot     {wert(con, 'autopilot')} – "
          f"{AUTOPILOT.get(wert(con, 'autopilot'), '')}")
    print()
    for art in reihenfolge(con):
        o = ordner(con, art)
        print(f"  {art:8} {seitenzahl(con, art):3} Seiten je Runde   "
              f"{o if o.exists() else str(o) + '  ⚠ fehlt'}")
    print()
    for e in uebersicht(con):
        if e["eigen"]:
            print(f"  eigen: {e['schluessel']} = {e['wert']} "
                  f"(Vorgabe {e['vorgabe']})")


if __name__ == "__main__":
    main()
