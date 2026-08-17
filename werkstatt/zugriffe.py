#!/usr/bin/env python3
"""Das Zugriffslog der Vorführinstanz auswerten.

    python3 -m werkstatt.zugriffe                    daten/zugriffe.log
    python3 -m werkstatt.zugriffe --log pfad/datei
    ssh nas cat /volume1/.../zugriffe.log | python3 -m werkstatt.zugriffe -

Das Log schreibt der Demo-Modus (eine Zeile je Zugriff: Zeit, Absender,
Anfrage, Antwortcode; Bilder und Standabfragen sind schon beim Schreiben
ausgesiebt). Hier wird daraus, was der Betreiber wissen will: Kam jemand,
wer ungefähr, was hat er angesehen - und rüttelt jemand am Passwort.

Besucher heißt: eine Absenderadresse an einem Tag. Das ist bewusst grob;
wer morgens vom Handy und abends vom Rechner kommt, zählt doppelt. Eine
feinere Zählung bräuchte Sitzungen oder Konten, und beides hat die
Werkstatt absichtlich nicht.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

from . import konfig


def lies(zeilen):
    """Logzeilen -> Liste (tag, wer, methode, pfad, code)."""
    raus = []
    for z in zeilen:
        t = z.split()
        if len(t) < 5:
            continue
        zeit, wer, methode, pfad = t[0], t[1], t[2], t[3]
        code = t[-1]
        raus.append((zeit[:10], wer, methode, pfad.split("?")[0], code))
    return raus


def bericht(saetze, aus=sys.stdout):
    if not saetze:
        print("Das Log ist leer - noch kein Zugriff.", file=aus)
        return
    gut = [s for s in saetze if s[4] != "401"]
    schlecht = [s for s in saetze if s[4] == "401"]

    tage = Counter(s[0] for s in gut)
    besucher_je_tag = {t: len({s[1] for s in gut if s[0] == t})
                       for t in tage}
    print(f"Zeitraum : {min(s[0] for s in saetze)} bis "
          f"{max(s[0] for s in saetze)}", file=aus)
    print(f"Zugriffe : {len(gut)} angemeldet, {len(schlecht)} abgewiesen "
          f"(401)", file=aus)
    print(f"Besucher : {len({s[1] for s in gut})} Adressen insgesamt",
          file=aus)
    print("\nJe Tag:", file=aus)
    for t in sorted(tage):
        print(f"  {t}  {besucher_je_tag[t]:2} Besucher, "
              f"{tage[t]:4} Zugriffe", file=aus)

    print("\nMeistaufgerufen:", file=aus)
    for pfad, n in Counter(s[3] for s in gut).most_common(10):
        print(f"  {n:5}  {pfad}", file=aus)

    if schlecht:
        print("\nAbgewiesene Absender (Passwort falsch oder fehlend):",
              file=aus)
        for wer, n in Counter(s[1] for s in schlecht).most_common(10):
            print(f"  {n:5}  {wer}", file=aus)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--log", default=None,
                    help="Logdatei; '-' liest von der Standardeingabe")
    a = ap.parse_args()
    quelle = a.log or str(konfig.WURZEL / "daten" / "zugriffe.log")
    if quelle == "-":
        zeilen = sys.stdin.read().split("\n")
    else:
        p = Path(quelle)
        if not p.exists():
            raise SystemExit(f"Kein Log unter {p} - die Vorführinstanz "
                             f"schreibt es erst im Demo-Modus.")
        zeilen = p.read_text(encoding="utf-8").split("\n")
    bericht(lies(zeilen))


if __name__ == "__main__":
    main()
