#!/usr/bin/env python3
"""Modellanbindung: Registerseite hinein, strukturierte Einträge heraus.

Der Kern der Werkstatt. Alles andere — Sichtung, Suche, Kaskade, Maske —
arbeitet um diesen Schritt herum.

    export ANTHROPIC_API_KEY=...
    python3 -m werkstatt.lesen ehe bilder/ehe/seite.jpg
    python3 -m werkstatt.lesen ehe --alle --grenze 5
    python3 -m werkstatt.lesen ehe --trocken       nur Prompt zeigen, nichts senden

Bewusst **ganze Seite** statt Zeilenstreifen: Das Modell findet die Einträge
auf einer gedruckten Registerseite selbst, und die Rastererkennung steckt bei
42 %. Der Kern haengt damit nicht an einem ungelösten Vorschritt. Streifen
werden erst für die Lupe beim Korrigieren gebraucht.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import db, einstellungen, konfig, seiten

API = "https://api.anthropic.com/v1/messages"

# Vorgaben; änderbar unter /einstellungen. Preise je Million Token
# (Stand August 2026), Batch-API halbiert sie.
MODELLE = {
    "claude-opus-5":   dict(name="Opus 5",   ein=5.0,  aus=25.0, kante=2576),
    "claude-sonnet-5": dict(name="Sonnet 5", ein=3.0,  aus=15.0, kante=2576),
    "claude-haiku-4-5": dict(name="Haiku 4.5", ein=1.0, aus=5.0,  kante=1568),
    "claude-fable-5":  dict(name="Fable 5",  ein=10.0, aus=50.0, kante=2576),
}
MODELL = "claude-opus-5"

# Die Vorgängerfassung stand auf 1568 px mit dem Kommentar "groesser bringt
# nichts, kostet nur Tokens". Das galt für die damaligen Modelle; Opus 5 und
# Sonnet 5 nehmen 2576 px auf der langen Kante.
#
# Für Kurrentschrift ist das kein Detail. `CLAUDE.md` hält selbst fest:
# "Auflösung zählt. Ancestry-JPG (24 MP) gegen Archion-PDF (14 MP) löste
# Eheeintrag Nr. 4 auf, der vorher unlesbar war."
#
# Der Preis dafür ist klein: 1600 -> 4784 Bildtoken, bei Opus 5 also
# 0,008 -> 0,024 $ je Seite, mit Batch die Hälfte. Gegen die gemessenen
# 0,13 $/Seite fällt das kaum ins Gewicht.
MAX_KANTE = 2576


# --------------------------------------------------------------- Prompt
BASIS = """Du transkribierst eine Seite aus einem deutschen Kirchenbuch.
Die Seite ist tabellarisch gedruckt; jede Zeile ist ein Eintrag.

GRUNDREGELN

1. Lies WÖRTLICH, was dasteht — nicht, was plausibel wäre. Abkürzungen,
   alte Schreibungen und Kürzel bleiben unverändert.
2. Gib zu jedem Feld an, wie sicher du bist (0.0 bis 1.0). Sei ehrlich:
   Familiennamen sind erfahrungsgemäß die unsicherste Angabe, Daten und
   Vornamen die sicherste.
3. Rate nicht. Ist etwas unlesbar, schreibe null und begründe kurz.
3a. **Teillesungen gehören ins Feld, nicht in die Notiz.** Ist bei einer
   Person der Vorname klar und der Nachname nicht, schreibe die Vornamen in
   "wert" und erkläre in "notiz", dass der Nachname fehlt — nicht umgekehrt.
   Der Abgleich trägt über die Vornamen: Er sucht die Elternehe im Bestand
   und leitet den Nachnamen daraus ab. Ein Feld mit null verschenkt genau
   die Angabe, die den Treffer bringen würde.
   Beispiel: Steht da "Rosina Margaretha, geb. ⟨unleserlich⟩", dann
   wert = "Rosina Margaretha", notiz = "Nachname nach 'geb.' nicht lesbar".
4. Nutze die Nachbarzeilen: Dieselbe Hand schreibt wiederkehrende Formeln
   ("B. u. Weingärtner in ...") — daran eichst du die Buchstabenformen.
   Register sind chronologisch: Das Datum eines Eintrags liegt zwischen dem
   des vorigen und des nächsten.
5. Die letzte Spalte nennt meist die Seitenzahl des Familienregisters.
   Sie ist wertvoll — gib sie immer an, wenn lesbar."""

WARNUNG = """
BELEGTE FEHLLESUNGEN DIESER HAND — prüfe diese Stellen besonders:
{katalog}
Diese Liste stammt aus bestätigten Korrekturen an derselben Handschrift."""

AUSGABE = """
Antworte NUR mit JSON, ohne Vorspann:

{{"eintraege": [
  {{"lfd_nr": "11",
    "felder": {{
      "{beispiel}": {{"wert": "...", "kb": "wörtlich wie im Buch",
                    "zuversicht": 0.9, "notiz": null}}
    }}
  }}
]}}

{felder}

"kb" nur setzen, wenn die Schreibung im Buch von der normalisierten Form
abweicht. "notiz" nur bei Unsicherheit oder Besonderheit."""


def fehlerkatalog(con, schreiber=None, grenze=12):
    """Belegte Fehllesungen aus den bisherigen Korrekturen — je Hand."""
    q = ("SELECT gelesen, korrigiert, sum(anzahl) n FROM fehlerkatalog "
         "GROUP BY gelesen, korrigiert ORDER BY n DESC LIMIT ?")
    try:
        rows = list(con.execute(q, (grenze,)))
    except Exception:
        return ""
    if not rows:
        return ""
    return "\n".join(f"  gelesen «{r['gelesen']}» → tatsächlich «{r['korrigiert']}» "
                     f"({r['n']}×)" for r in rows)


def prompt(art, con=None, schreiber=None):
    felder = konfig.felder(art, con)
    text = BASIS
    if con is not None:
        kat = fehlerkatalog(con, schreiber)
        if kat:
            text += WARNUNG.format(katalog=kat)
    # Der Katalog statt einer Aufzählung: Er nennt zu jedem Feld, was
    # gemeint ist, und bei den heiklen auch, woran man es erkennt —
    # „geborene“, „weiland“, Zwillinge, Nottaufe, Zählmonate. Eine bloße
    # Namensliste lässt das Modell raten, was `mutter_herkunft` sein soll.
    from . import katalog
    text += AUSGABE.format(felder=katalog.als_prompt(art, con),
                           beispiel=felder[1] if len(felder) > 1 else felder[0])
    return text


# --------------------------------------------------------------- Bild
def bild_teil(pfad, kante=None):
    """Bild verkleinern und als base64 einbetten."""
    from PIL import Image
    import io
    kante = kante or MAX_KANTE
    im = Image.open(pfad)
    if max(im.size) > kante:
        im.thumbnail((kante, kante))
    if im.mode != "RGB":
        im = im.convert("RGB")
    puffer = io.BytesIO()
    im.save(puffer, format="JPEG", quality=88)
    return {"type": "image", "source": {
        "type": "base64", "media_type": "image/jpeg",
        "data": base64.standard_b64encode(puffer.getvalue()).decode()}}


# --------------------------------------------------------------- API
def frage(inhalt, system, schluessel, modell=MODELL, max_tokens=8000):
    daten = json.dumps({
        "model": modell, "max_tokens": max_tokens, "system": system,
        "messages": [{"role": "user", "content": inhalt}],
    }).encode()
    req = urllib.request.Request(API, data=daten, headers={
        "content-type": "application/json",
        "x-api-key": schluessel,
        "anthropic-version": "2023-06-01",
    })
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            antwort = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"API-Fehler {e.code}: {e.read().decode()[:400]}")
    text = "".join(t["text"] for t in antwort["content"] if t["type"] == "text")
    return text, antwort.get("usage", {})


def json_aus(text):
    """JSON aus der Antwort schälen, auch wenn Zäune drumherum stehen."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        t = t[4:] if t.startswith("json") else t
    a, b = t.find("{"), t.rfind("}")
    return json.loads(t[a:b + 1]) if a >= 0 else {}


# --------------------------------------------------------------- Ablauf
def einstellung(con, name, vorgabe):
    """Wert aus den Einstellungen, sonst die Vorgabe hier."""
    if con is None:
        return vorgabe
    try:
        return einstellungen.wert(con, f"ki.{name}", vorgabe)
    except Exception:
        return vorgabe


def lies_seite(pfad, art, schluessel, con=None, kontext=None, trocken=False):
    sys_prompt = prompt(art, con)
    if trocken:
        print(sys_prompt)
        return None, {}
    modell = einstellung(con, "modell", MODELL)
    kante = int(einstellung(con, "max_kante", MAX_KANTE))
    marken = int(einstellung(con, "max_tokens", 8000))
    inhalt = []
    if kontext:
        inhalt.append({"type": "text", "text":
                       "Vorige Seite endet mit: " + kontext})
    inhalt += _seitenteile(pfad, art, kante)
    text, nutzung = frage(inhalt, sys_prompt, schluessel, modell, marken)
    return json_aus(text), nutzung


def _seitenteile(pfad, art, kante):
    """Was von einer Seite an das Modell geht: Blöcke, nicht die Seite.

    Die ganze Aufnahme ist rund 5700 px breit und trägt neun Spalten. Auf
    2576 px verkleinert bleiben je Spalte gut zweihundert Pixel, und die
    schmalen rechten Spalten kommen unlesbar an. Gemessen an Seite 00359:
    Die Lesung füllte die vier linken Spalten und notierte zu allen fünf
    rechten „im vorliegenden Bildausschnitt nicht enthalten" — falsch, sie
    standen im selben Bild.

    Der Weg über die Sitzung war deshalb schon umgestellt; dieser hier
    nicht, und er hätte billig, aber falsch gelesen: 0,12 $ je Seite für
    vier von neun Spalten.

    Teurer ist es trotzdem nicht sehr. Gerechnet für eine Eheseite:
    ganze Seite 6.900 Bildtoken, achtzehn Blöcke 20.500 — 0,12 gegen
    0,24 $ je Seite, und mit der Batch-API die Hälfte davon. Zum
    Vergleich: der Weg über die Sitzung kostet gemessen 2,25 $.
    """
    from . import bloecke
    try:
        z = bloecke.schneide(pfad, still=True)
    except Exception:
        z = {}
    if not z.get("bloecke"):
        # Ohne Raster bleibt nur die ganze Seite — mit dem Vermerk, dass
        # die schmalen Spalten dann unsicher sind.
        return [bild_teil(pfad, kante),
                {"type": "text", "text":
                 f"Transkribiere alle Einträge dieser Seite ({art}). "
                 "Achtung: Das Zeilenraster ließ sich nicht erkennen, du "
                 "siehst die ganze Seite verkleinert. Was du in schmalen "
                 "Spalten nicht sicher liest, gehört ins Feld "
                 "`unleserlich`, nicht ins Feld."}]

    teile = []
    if z.get("kopf"):
        teile.append({"type": "text", "text":
                      "Zuerst der gedruckte Spaltenkopf dieser Seite — er "
                      "sagt, welche Spalte was bedeutet:"})
        teile += [bild_teil(k["datei"], kante) for k in z["kopf"]]
    teile.append({"type": "text", "text":
                  f"Nun die Einträge, je Zeile ein oder zwei Bilder (links "
                  f"und rechts vom Bund derselben Zeile — sie gehören "
                  f"zusammen). Transkribiere jede Zeile als einen Eintrag "
                  f"({art})."})
    for b in z["bloecke"]:
        teile.append({"type": "text", "text": f"— Zeile {b['zeile']} —"})
        teile += [bild_teil(t["datei"], kante) for t in b["teile"]]
    return teile


def kosten(modell, ein, aus, batch=False):
    """Was ein Lauf gekostet hat — in Dollar."""
    m = MODELLE.get(modell)
    if not m:
        return None
    d = ein / 1e6 * m["ein"] + aus / 1e6 * m["aus"]
    return d / 2 if batch else d


def speichere(con, art, pfad, ergebnis):
    """Einträge und Felder in die Erfassungsdatenbank schreiben."""
    reihen = {n: i for i, n in enumerate(konfig.felder(art, con))}
    hid = db.herkunft_id(con, "modell", MODELL, f"gelesen aus {Path(pfad).name}")
    n_e = n_f = 0
    for e in ergebnis.get("eintraege", []):
        nr = str(e.get("lfd_nr") or "")
        con.execute("INSERT OR IGNORE INTO eintrag (register,bild,nr,herkunft) "
                    "VALUES (?,?,?,?)", (art, Path(pfad).stem, nr, hid))
        row = con.execute("SELECT id FROM eintrag WHERE register=? AND bild=? AND nr=?",
                          (art, Path(pfad).stem, nr)).fetchone()
        if not row:
            continue
        eid = row["id"]
        n_e += 1
        for name, f in (e.get("felder") or {}).items():
            if not isinstance(f, dict):
                f = {"wert": f}
            # Wie in runde.speichere(): eine zweite Lesung ersetzt die
            # erste, aber nie eine menschliche Korrektur.
            con.execute(
                "INSERT INTO feld "
                "(eintrag_id,name,gelesen,kb_form,zuversicht,beleg,reihe) "
                "VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(eintrag_id, name) DO UPDATE SET "
                " gelesen=excluded.gelesen, kb_form=excluded.kb_form, "
                " zuversicht=excluded.zuversicht, beleg=excluded.beleg, "
                " reihe=excluded.reihe "
                # Nicht `entscheidung IS NULL` pruefen: Die Spalte steht per
                # Vorgabe auf 'offen' und wird vom Abgleich gesetzt, ist
                # also nie leer — die Bedingung blockierte jede
                # Aktualisierung. Der ehrliche Marker fuer Menschenarbeit
                # ist `korrigiert` und der bestaetigte Eintrag.
                "WHERE feld.korrigiert IS NULL AND EXISTS ("
                "  SELECT 1 FROM eintrag e WHERE e.id=feld.eintrag_id "
                "  AND e.status <> 'bestaetigt')",
                (eid, name, f.get("wert"), f.get("kb"), f.get("zuversicht"),
                 f.get("notiz"), reihen.get(name, 99)))
            n_f += 1
    con.commit()
    return n_e, n_f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("register")
    ap.add_argument("bild", nargs="*")
    ap.add_argument("--alle", action="store_true", help="alle Bilder des Registers")
    ap.add_argument("--grenze", type=int, default=0, help="höchstens so viele Seiten")
    ap.add_argument("--trocken", action="store_true", help="nur Prompt zeigen")
    a = ap.parse_args()

    if a.register not in konfig.register():
        raise SystemExit(f"unbekanntes Register: {a.register}")
    con = db.verbinde()

    if a.trocken:
        print(prompt(a.register, con))
        return

    schluessel = os.environ.get("ANTHROPIC_API_KEY")
    if not schluessel:
        raise SystemExit("ANTHROPIC_API_KEY nicht gesetzt")

    fs = [Path(b) for b in a.bild]
    if a.alle:
        fs = seiten.bilder(einstellungen.ordner(con, a.register))
    if a.grenze:
        fs = fs[:a.grenze]
    if not fs:
        raise SystemExit("keine Bilder angegeben")

    ein = tok_e = tok_a = 0
    for i, f in enumerate(fs, 1):
        print(f"[{i}/{len(fs)}] {f.name} … ", end="", flush=True)
        erg, nutzung = lies_seite(f, a.register, schluessel, con)
        n_e, n_f = speichere(con, a.register, f, erg)
        ein += n_e
        tok_e += nutzung.get("input_tokens", 0)
        tok_a += nutzung.get("output_tokens", 0)
        print(f"{n_e} Einträge, {n_f} Felder")
    print(f"\n{ein} Einträge aus {len(fs)} Seiten")
    print(f"Token: {tok_e} hinein, {tok_a} heraus")


if __name__ == "__main__":
    main()
