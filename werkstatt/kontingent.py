#!/usr/bin/env python3
"""KI-Kontingent je Instanz: ein Deckel, keine Abrechnung.

    python3 -m werkstatt.kontingent            Stand zeigen
    python3 -m werkstatt.einstellungen --setze ki.budget_dollar 5

Die Einstellung `ki.budget_dollar` deckelt, was das Modell in dieser
Instanz lesen darf. Geprüft wird gegen die Summe der verbuchten
Auftragskosten (`auftrag.dollar`) – gemessen, nicht geschätzt, dieselbe
Quelle wie die Verbrauchsanzeige im Zahnrad.

Geprüft wird an zwei Stellen: **vor** dem Planen und Lesen, und noch
einmal **vor jeder einzelnen Seite** im Läufer. Nur die erste Prüfung
wäre wirkungslos, sobald eine Runde mehrere Seiten umfasst – geprüft
würde einmal, gelesen zwanzigmal. Reißt der Deckel mitten in einer
Runde, bleiben die restlichen Seiten `wartet`; ein späterer Lauf holt
sie nach, sobald der Deckel angehoben ist. Überschritten wird um
höchstens eine Seite, weil der verbuchte Verbrauch zählt und nicht der
erwartete.

Der Weg über das Abonnement (`quelle='datei'`) zählt mit: `claude -p`
meldet den Gegenwert selbst, und in einer gehosteten Instanz läuft er
über das Konto des Betreibers. Die Testdaten zählen nicht – sie kosten
nichts und sollen nie an einem Deckel scheitern.

**Der Deckel ist Opt-out, nicht Opt-in.** Eine frische Datenbank läuft
mit `VORGABE` los; wer mehr will, hebt ihn an, und wer gar keinen will,
leert das Feld. Vorher galt das Umgekehrte: keine Einstellung, kein
Deckel. Das ist der falsche Auslieferungszustand für etwas, das mit dem
Schlüssel eines anderen Geld ausgibt, denn der Schutz fehlt genau dem,
der ihn am nötigsten hat, nämlich dem, der die Werkstatt zum ersten Mal
startet.

Die Vorgabe deckt rund eine Tranche ab (20 Seiten zu etwa 0,24 $). Die
erste Runde läuft also durch, die zweite verlangt eine bewusste
Entscheidung.

Datenbanken, die schon gelesen haben, sind ausgenommen: `db.wandere()`
trägt ihnen einmalig den leeren Wert ein. Sonst würde eine Vorgabe
greifen, die nie jemand gesetzt hat, und einen laufenden Bestand
aussperren.
"""
from . import einstellungen, lesen

SCHLUESSEL = "ki.budget_dollar"
VORGABE = 5.0
# Abschalten braucht ein Wort, keine leere Eingabe: Die Einstellungsmaske
# löscht leere Werte aus der Tabelle, und eine fehlende Zeile heißt hier
# „nie entschieden", also Vorgabe. Wer keinen Deckel will, schreibt es hin.
AUS = ("aus", "kein", "keiner", "unbegrenzt", "")


def budget(con):
    """Der Deckel in Dollar – None, wenn ausdrücklich keiner gilt.

    Direkt in die Tabelle statt über `einstellungen.wert()`: Dort gilt ein
    leerer Wert als „nicht gesetzt". Hier ist er die ausdrückliche
    Abschaltung, und der Unterschied trägt die ganze Entscheidung – „noch
    nie entschieden" heißt Vorgabe, „bewusst geleert" heißt kein Deckel.
    """
    r = con.execute("SELECT wert FROM einstellung WHERE schluessel=?",
                    (SCHLUESSEL,)).fetchone()
    if r is None or r[0] is None:     # nie gesetzt: die Vorgabe gilt
        return VORGABE
    w = str(r[0]).strip().lower()
    if w in AUS:                      # ausdrücklich abgeschaltet
        return None
    try:
        return float(w.replace(",", "."))
    except ValueError:
        # Ein Tippfehler darf den Schutz nicht abschalten.
        return VORGABE


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
