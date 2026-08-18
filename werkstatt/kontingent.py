#!/usr/bin/env python3
"""KI-Kontingent je Instanz: ein Deckel, keine Abrechnung.

    python3 -m werkstatt.kontingent            Stand zeigen
    python3 -m werkstatt.einstellungen --setze ki.budget_dollar 5

Die Einstellung `ki.budget_dollar` deckelt, was das Modell in dieser
Instanz lesen darf. Geprüft wird **vor** dem Planen und Lesen gegen die
Summe der verbuchten Auftragskosten (`auftrag.dollar`) – gemessen, nicht
geschätzt, dieselbe Quelle wie die Verbrauchsanzeige im Zahnrad.

Der Weg über das Abonnement (`quelle='datei'`) zählt mit: `claude -p`
meldet den Gegenwert selbst, und in einer gehosteten Instanz läuft er
über das Konto des Betreibers. Die Testdaten zählen nicht – sie kosten
nichts und sollen nie an einem Deckel scheitern.

Keine Einstellung = kein Deckel. Der Einzelplatz des README merkt von
alledem nichts; gesetzt wird der Wert vom Betreiber über das Portal oder
von Hand über `ki.budget_dollar`.
"""
from . import einstellungen, lesen

SCHLUESSEL = "ki.budget_dollar"


def budget(con):
    """Der Deckel in Dollar – None, wenn keiner gesetzt ist."""
    w = einstellungen.wert(con, SCHLUESSEL)
    try:
        return float(str(w).replace(",", ".")) if w not in (None, "") else None
    except ValueError:
        return None


def verbraucht(con):
    """Summe der verbuchten Auftragskosten in Dollar.

    Über die API steht der Betrag nicht in `dollar`, sondern wird wie in
    der Verbrauchsanzeige aus Token und Preisliste gerechnet; über das
    Abonnement meldet `claude -p` ihn selbst.
    """
    gesamt = 0.0
    modell = einstellungen.wert(con, "ki.modell", lesen.MODELL)
    for r in con.execute(
            "SELECT COALESCE(quelle,'api') q, COALESCE(SUM(dollar),0) d, "
            "COALESCE(SUM(tokens_ein),0) e, COALESCE(SUM(tokens_aus),0) a "
            "FROM auftrag WHERE tokens_ein>0 OR dollar>0 "
            "GROUP BY COALESCE(quelle,'api')"):
        if r["q"] == "testdaten":
            continue
        gesamt += r["d"] or (lesen.kosten(modell, r["e"], r["a"]) or 0.0)
    return round(gesamt, 4)


def frei(con, quelle="api"):
    """(True, None) wenn gelesen werden darf, sonst (False, Meldung)."""
    if quelle == "testdaten":
        return True, None
    deckel = budget(con)
    if deckel is None:
        return True, None
    ist = verbraucht(con)
    if ist < deckel:
        return True, None
    return False, (f"KI-Kontingent erschöpft: {ist:.2f} $ von "
                   f"{deckel:.2f} $ verbraucht. Den Deckel setzt der "
                   f"Betreiber (Einstellung {SCHLUESSEL}).")


def main():
    from . import db
    con = db.verbinde()
    d, ist = budget(con), verbraucht(con)
    print(f"  verbraucht  {ist:.2f} $")
    print(f"  Kontingent  " + (f"{d:.2f} $" if d is not None else "keines"))
    if d is not None:
        ok, meldung = frei(con)
        print(f"  Stand       " + ("frei" if ok else meldung))


if __name__ == "__main__":
    main()
