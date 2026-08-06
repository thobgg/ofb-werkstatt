#!/usr/bin/env python3
"""Rückfragen zu einem einzelnen Eintrag — im Zweifel nachfragen können.

Die Maske kennt zwei Antworten: übernehmen oder neu anlegen. Für den
Regelfall reicht das. Der Ertrag der Arbeit steckt aber in den Fällen, die
danebenliegen, und die sehen so aus:

    „Der Mädchenname der Mutter wird verschenkt."
    „Der Tod des Täuflings steht im Randvermerk und kommt nirgends an."
    „Der Nachname ist wohl eher Möß als Wöß."

Solche Sätze passen in kein Eingabefeld. Deshalb hängt unter jedem Eintrag
ein Gespräch: der Bearbeiter fragt, das Modell antwortet mit dem Eintrag,
dem Bildausschnitt und den Bestandstreffern vor Augen.

**Es entscheidet nichts.** Die Antwort ist Text; jede Änderung macht der
Bearbeiter selbst in der Maske. Das ist dieselbe Grenze wie überall in der
Werkstatt: Ein Modell darf ranken und erklären, bestätigen darf nur ein
Anker oder ein Mensch. Ein Gespräch, das Felder überschreibt, wäre genau
die selbstverstärkende Schleife, gegen die das Stufensystem gebaut ist.

Der Verlauf wird gespeichert. Nicht als Bequemlichkeit: Was hier gefragt
wird, ist der Fehlerkatalog des nächsten Durchlaufs.
"""
import json
import subprocess
from pathlib import Path

from . import konfig, vorlage

# Der Auftrag steht hier und nicht im Prompt des Bearbeiters, damit die
# Grenze nicht verhandelbar ist.
RAHMEN = """Du hilfst bei der Transkription eines württembergischen
Kirchenbuchs. Unten stehen ein Registereintrag, wie er gelesen wurde, die
Treffer im vorhandenen Bestand und der Bildausschnitt der Zeile.

Beantworte die Frage des Bearbeiters knapp und sachlich, auf Deutsch.

Halte dich an diese Regeln:

- **Sag, worauf du dich stützt.** Bild, gelesener Text, Bestandstreffer
  oder Erfahrung mit der Schrift — das ist der Unterschied zwischen einer
  Lesung und einer Vermutung.
- **Vokabular und Häufigkeit bestätigen nichts.** Dass ein Name im Bestand
  häufig ist, macht ihn nicht richtig. Im Pilotlauf stand `Roth` 59-mal im
  Bestand und war doch `Koch`.
- **Widersprich nicht dem Bild.** Wenn die Lesung anders aussieht als der
  Bestand, ist das ein Befund, kein Fehler — benenne beide Seiten.
- **Du änderst nichts.** Wenn eine Änderung sinnvoll ist, sag welches Feld
  und was hinein sollte; eintragen wird es der Bearbeiter.
- Wenn du es nicht erkennen kannst, sag das. Eine ehrliche Unsicherheit ist
  brauchbar, eine erfundene Sicherheit nicht.
"""


def lege_an(con):
    con.execute("""CREATE TABLE IF NOT EXISTS gespraech (
      id       INTEGER PRIMARY KEY,
      eintrag  INTEGER NOT NULL REFERENCES eintrag(id) ON DELETE CASCADE,
      wer      TEXT NOT NULL,           -- mensch | modell
      text     TEXT NOT NULL,
      wann     TEXT NOT NULL)""")
    con.commit()


def verlauf(con, eintrag_id):
    lege_an(con)
    return [dict(r) for r in con.execute(
        "SELECT wer, text, wann FROM gespraech WHERE eintrag=? ORDER BY id",
        (eintrag_id,))]


def _merke(con, eintrag_id, wer, text):
    from datetime import datetime, timezone
    lege_an(con)
    con.execute(
        "INSERT INTO gespraech (eintrag, wer, text, wann) VALUES (?,?,?,?)",
        (eintrag_id, wer, text,
         datetime.now(timezone.utc).isoformat(timespec="seconds")))
    con.commit()


def lage(con, eintrag_id):
    """Alles, was zum Eintrag bekannt ist — als Text für das Modell.

    Bewusst flach und lesbar statt JSON: Das Modell soll den Eintrag lesen
    wie ein Mensch, der über die Schulter schaut.
    """
    e = con.execute("SELECT * FROM eintrag WHERE id=?", (eintrag_id,)).fetchone()
    if not e:
        raise SystemExit(f"kein Eintrag {eintrag_id}")
    z = [f"Register: {e['register']}  ·  Seite {e['bild']}  ·  "
         f"Eintrag Nr. {e['nr']}  ·  Jahr {e['jahr'] or '?'}", ""]
    z.append("Gelesene Felder (leer = im Register nicht vorhanden):")
    for f in con.execute(
            "SELECT name, gelesen, korrigiert, kb_form, ampel, beleg, person "
            "FROM feld WHERE eintrag_id=? ORDER BY id", (eintrag_id,)):
        wert = f["korrigiert"] or f["gelesen"] or ""
        teile = [f"  {f['name']:22} {wert}"]
        if f["korrigiert"] and f["gelesen"] and f["korrigiert"] != f["gelesen"]:
            teile.append(f"(gelesen war: {f['gelesen']})")
        if f["kb_form"]:
            teile.append(f"[Kirchenbuchform: {f['kb_form']}]")
        if f["ampel"] and f["ampel"] != "grau":
            teile.append(f"<{f['ampel']}>")
        if f["beleg"]:
            teile.append(f"— {f['beleg']}")
        z.append(" ".join(teile))
    return "\n".join(z)


def _bestandstreffer(con, eintrag_id):
    z = []
    for f in con.execute(
            "SELECT name, person FROM feld WHERE eintrag_id=? AND person "
            "IS NOT NULL", (eintrag_id,)):
        p = con.execute(
            "SELECT xref, name, givn, surn FROM person WHERE id=?",
            (f["person"],)).fetchone()
        if not p:
            continue
        ev = [f"{r['art']} {r['datum'] or '?'} {r['ort'] or ''}".strip()
              for r in con.execute(
                  "SELECT art, datum, ort FROM ereignis WHERE person=?",
                  (f["person"],))]
        z.append(f"  {f['name']:22} -> {p['xref']} {p['name']}"
                 + (f"   ({'; '.join(ev)})" if ev else ""))
    return z


def bild(con, eintrag_id):
    """Pfad des Streifens zu diesem Eintrag, falls einer geschnitten ist."""
    r = con.execute("SELECT ausschnitt FROM eintrag WHERE id=?",
                    (eintrag_id,)).fetchone()
    p = r and r["ausschnitt"]
    if not p:
        return None
    p = Path(p)
    return p if p.is_absolute() else konfig.WURZEL / p


def frage(con, eintrag_id, text, zeitlimit=300):
    """Eine Frage stellen und die Antwort zurückgeben.

    Läuft über `claude -p`, also über den Zugang des Bearbeiters — kein
    API-Schlüssel, keine zweite Rechnung. Ohne Claude Code gibt es eine
    ehrliche Absage statt einer erfundenen Antwort.
    """
    w = vorlage.werkzeug()
    if not w:
        return dict(ok=False, antwort=(
            "Claude Code ist auf diesem Rechner nicht eingerichtet — ohne das "
            "kann hier niemand antworten. Einrichten im Zahnrad unter "
            "KI-Anbindung."))
    _merke(con, eintrag_id, "mensch", text)
    teile = [RAHMEN, "", "=== Eintrag ===", lage(con, eintrag_id)]
    tr = _bestandstreffer(con, eintrag_id)
    if tr:
        teile += ["", "=== Treffer im vorhandenen Bestand ===", *tr]
    b = bild(con, eintrag_id)
    if b and b.exists():
        teile += ["", "=== Bildausschnitt ===",
                  f"Die Zeile liegt als Bild unter {b}. Sieh sie dir an, "
                  "bevor du über eine Lesung urteilst."]
    frueher = verlauf(con, eintrag_id)[:-1]
    if frueher:
        teile += ["", "=== Bisheriges Gespräch ==="]
        teile += [f"{'Bearbeiter' if g['wer'] == 'mensch' else 'Du'}: "
                  f"{g['text']}" for g in frueher]
    teile += ["", "=== Frage des Bearbeiters ===", text]
    auftrag = "\n".join(teile)
    zusatz = []
    if b and b.exists():
        zusatz = ["--add-dir", str(b.parent)]
    try:
        p = subprocess.run([w, "-p", auftrag, *zusatz],
                           capture_output=True, text=True, timeout=zeitlimit,
                           cwd=str(konfig.WURZEL))
    except subprocess.TimeoutExpired:
        return dict(ok=False, antwort=f"Keine Antwort in {zeitlimit} Sekunden.")
    antwort = (p.stdout or "").strip() or (p.stderr or "").strip()
    if not antwort:
        antwort = "Keine Antwort erhalten."
    _merke(con, eintrag_id, "modell", antwort)
    return dict(ok=p.returncode == 0, antwort=antwort)


def main():
    import argparse
    from . import db
    ap = argparse.ArgumentParser()
    ap.add_argument("eintrag", type=int)
    ap.add_argument("frage", nargs="+")
    a = ap.parse_args()
    con = db.verbinde()
    print(frage(con, a.eintrag, " ".join(a.frage))["antwort"])


if __name__ == "__main__":
    main()
