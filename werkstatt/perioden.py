#!/usr/bin/env python3
"""Formularperioden eines Bandes finden — einmal je Ordner, am Kopf.

    python3 -m werkstatt.perioden taufe
    python3 -m werkstatt.perioden --alle

Ein Kirchenbuch wechselt im Lauf der Jahrzehnte das gedruckte Formular:
andere Spalten, andere Reihenfolge, andere Bezeichnungen. Wer eine
Aktkarte für den ganzen Band festschreibt, liest die späteren Jahrgänge
mit den falschen Feldern.

**Geometrisch geht es nicht.** Gemessen an 14 Stichproben desselben
Taufregisters findet die senkrechte Linienerkennung zwischen 2 und 11
Spaltenlinien — Belichtung, Buchkrümmung und die Lage im Bild schwanken
stärker als jeder echte Formularwechsel. Deshalb liest hier das Modell.

**Aber sparsam.** Nicht die Seiten, nur den **gedruckten Kopf**: ein
schmaler Streifen über den Spaltenüberschriften, der bereits geschnitten
wird. Jede fünfte Seite genügt; bei 80 Seiten sind das 16 kleine Bilder
und ein Aufruf je Register. Wo sich der Spaltentext ändert, liegt eine
Grenze; die genaue Seite dazwischen wird durch Halbieren nachgefasst.

**Die Hand kostet nichts.** Wer die Taufe verrichtet hat, steht als eigene
Spalte im Formular und wird ohnehin gelesen. Der Pfarrerwechsel — laut
`CLAUDE.md` die Variable mit dem größten Einfluss — fällt also aus den
erfassten Daten heraus, sobald eine Tranche durch ist. Dafür braucht es
keinen zweiten Blick.
"""
import argparse
import json
import subprocess
from pathlib import Path

from . import bloecke, db, einstellungen, konfig, seiten, vorlage

JEDE = 5

AUFTRAG = """Du siehst die gedruckten Spaltenköpfe von Kirchenbuchseiten —
je Seite ein oder zwei Bilder, links und rechts vom Bund. Es geht **nicht**
um die handschriftlichen Einträge, sondern allein um den **gedruckten
Formularkopf**.

Für jede **Seite** genau ein Eintrag — nicht je Bild. Wo zwei Bilder zu
einer Seite gehören (links und rechts vom Bund), gehören ihre Spalten in
**eine** Liste, links zuerst. Als `bild` den Seitennamen einsetzen, der
unten vor dem Doppelpunkt steht, nicht den Dateipfad.

Lies die Spaltenüberschriften von links nach rechts ab, im Wortlaut des
Drucks, mit originaler Rechtschreibung.

Antworte NUR mit JSON:

{"seiten": [{"bild": "<Name wie unten>", "spalten": ["…", "…"],
             "lesbar": true, "notiz": null}]}

`lesbar: false`, wenn der Kopf abgeschnitten, verdeckt oder unleserlich
ist — dann `spalten: []`. Rate nichts: Ein erfundener Spaltenname erzeugt
eine Formulargrenze, die es nicht gibt.

Die Bilder:
"""


def lege_an(con):
    con.execute("""CREATE TABLE IF NOT EXISTS periode (
      id       INTEGER PRIMARY KEY,
      register TEXT NOT NULL,
      von_bild TEXT NOT NULL,
      bis_bild TEXT NOT NULL,
      seiten   INTEGER NOT NULL DEFAULT 0,
      spalten  TEXT,                  -- JSON: die gedruckten Ueberschriften
      notiz    TEXT,
      erkannt  TEXT,
      UNIQUE(register, von_bild))""")
    con.commit()


def stichproben(bilder, jede=JEDE):
    """Jede n-te Seite, erste und letzte immer dabei."""
    if not bilder:
        return []
    z = list(bilder[::jede])
    if bilder[-1] not in z:
        z.append(bilder[-1])
    return z


def koepfe(con, register, jede=JEDE, still=True):
    """Kopfblöcke der Stichproben schneiden. Gibt {bild: [pfade]} zurück."""
    ordner = einstellungen.ordner(con, register)
    raus = {}
    for f in stichproben(seiten.bilder(ordner), jede):
        try:
            z = bloecke.schneide(f, still=True, nur_kopf=True)
        except Exception as e:
            if not still:
                print(f"  {f.stem}: kein Kopf ({e})")
            continue
        if z.get("kopf"):
            raus[f.stem] = [k["datei"] for k in z["kopf"]]
    return raus


def frage_modell(kopfbilder, zeitlimit=1800):
    """Ein Aufruf für alle Stichproben eines Registers."""
    w = vorlage.werkzeug()
    if not w:
        raise SystemExit("Claude Code ist nicht eingerichtet — ohne das "
                         "lassen sich die Formularköpfe nicht lesen.")
    zeilen = []
    ordner = set()
    for bild, pfade in kopfbilder.items():
        zeilen.append(f"  {bild}: " + " , ".join(pfade))
        for p in pfade:
            ordner.add(str(Path(p).parent))
    frei = []
    for o in sorted(ordner | {str(konfig.WURZEL)}):
        frei += ["--add-dir", o]
    p = subprocess.run([w, "-p", AUFTRAG + "\n".join(zeilen),
                        "--output-format", "json", *frei],
                       capture_output=True, text=True, timeout=zeitlimit,
                       cwd=str(konfig.WURZEL))
    try:
        antwort = json.loads(p.stdout)
    except Exception:
        raise SystemExit(f"keine lesbare Antwort: {(p.stdout or '')[:300]}")
    text = antwort.get("result") or ""
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j < 0:
        raise SystemExit(f"kein JSON in der Antwort: {text[:300]}")
    return json.loads(text[i:j + 1]), antwort.get("total_cost_usd")


def _schluessel(spalten):
    """Vergleichsform eines Formularkopfs — Reihenfolge zählt, Zierrat nicht."""
    return tuple(" ".join(str(s).lower().split()).strip(" .:-")
                 for s in (spalten or []))


def _enthalten(klein, gross):
    """Steht `klein` als zusammenhängende Folge in `gross`?"""
    if not klein or len(klein) > len(gross):
        return False
    n = len(klein)
    return any(gross[i:i + n] == klein for i in range(len(gross) - n + 1))


def _seitenname(x):
    """Aus dem, was das Modell als „bild" zurückgibt, den Seitennamen.

    Der Auftrag nennt Seitenname und Bildpfade; welchen von beiden die
    Antwort einsetzt, ist nicht erzwingbar. Ein Lauf lieferte
    `1184798-00389/kopf_links.jpg` — daraus wurden 32 „Seiten" statt 17,
    und die Segmentierung zerfiel. Also hier zurechtrücken statt sich auf
    die Form der Antwort zu verlassen.
    """
    s = str(x or "").replace("\\", "/")
    teile = [t for t in s.split("/") if t]
    for t in teile:
        if t.lower().startswith("kopf"):
            continue
        return Path(t).stem
    return Path(s).stem


def _zusammenlegen(proben):
    """Linke und rechte Hälfte derselben Seite zu einem Kopf vereinen."""
    nach_seite = {}
    for s in proben:
        name = _seitenname(s.get("bild"))
        e = nach_seite.setdefault(name, dict(bild=name, spalten=[],
                                             lesbar=False))
        if s.get("lesbar") and s.get("spalten"):
            e["spalten"] += list(s["spalten"])
            e["lesbar"] = True
    return sorted(nach_seite.values(), key=lambda s: s["bild"])


def segmentiere(gelesen, alle_bilder):
    """Aus den Stichproben zusammenhängende Abschnitte machen.

    Unlesbare Köpfe unterbrechen nicht: Sie erben den Abschnitt der
    vorigen Stichprobe. Ein verdeckter Kopf ist kein Formularwechsel.
    """
    proben = _zusammenlegen(gelesen.get("seiten", []))
    abschnitte = []
    for s in proben:
        if not s.get("lesbar") or not s.get("spalten"):
            continue
        k = _schluessel(s["spalten"])
        # **Weniger Spalten sind kein Formularwechsel.** Auf manchen
        # Aufnahmen ist nur eine Buchhaelfte im Bild oder ihr Kopf nicht
        # lesbar; dann kommen fuenf statt neun Spalten zurueck. Der erste
        # Lauf machte daraus vier Perioden, die abwechselnd 9 und 5 Spalten
        # hatten — sichtbar Unsinn, denn ein Formular wechselt nicht hin
        # und her. Wo eine Spaltenfolge in der anderen enthalten ist,
        # gehoert beides zusammen, und die reichere gilt.
        vor = abschnitte[-1] if abschnitte else None
        if vor and (_enthalten(k, vor["schluessel"])
                    or _enthalten(vor["schluessel"], k)):
            vor["bis"] = s["bild"]
            if len(k) > len(vor["schluessel"]):
                vor["schluessel"], vor["spalten"] = k, s["spalten"]
        else:
            abschnitte.append(dict(schluessel=k, spalten=s["spalten"],
                                   von=s["bild"], bis=s["bild"]))
    # Bis zur naechsten Grenze durchziehen: Zwischen zwei Stichproben liegt
    # die echte Grenze irgendwo; ohne Nachfassen gilt die spaetere Probe.
    for i, a in enumerate(abschnitte):
        if i + 1 < len(abschnitte):
            spaeter = [b for b in alle_bilder if b < abschnitte[i + 1]["von"]]
            if spaeter:
                a["bis"] = spaeter[-1]
        else:
            a["bis"] = alle_bilder[-1] if alle_bilder else a["bis"]
        a["seiten"] = sum(1 for b in alle_bilder if a["von"] <= b <= a["bis"])
    return abschnitte


def merke(con, register, abschnitte):
    from datetime import datetime, timezone
    lege_an(con)
    jetzt = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con.execute("DELETE FROM periode WHERE register=?", (register,))
    for a in abschnitte:
        con.execute(
            "INSERT INTO periode (register, von_bild, bis_bild, seiten, "
            "spalten, erkannt) VALUES (?,?,?,?,?,?)",
            (register, a["von"], a["bis"], a["seiten"],
             json.dumps(a["spalten"], ensure_ascii=False), jetzt))
    con.commit()


def gemeldet(con, register=None):
    lege_an(con)
    q = "SELECT * FROM periode"
    par = ()
    if register:
        q += " WHERE register=?"
        par = (register,)
    raus = []
    for r in con.execute(q + " ORDER BY register, von_bild", par):
        d = dict(r)
        d["spalten"] = json.loads(d["spalten"] or "[]")
        raus.append(d)
    return raus


def haende(con, register):
    """Die Schreiber, gratis aus den schon gelesenen Einträgen.

    Der taufende, trauende oder beerdigende Geistliche steht als eigene
    Spalte im Formular. Wo er wechselt, wechselt die Hand — und das ist
    die Variable mit dem groessten Einfluss auf die Lesequalitaet.
    """
    feld = {"taufe": "taufender", "ehe": "trauender",
            "tod": "beerdigender"}.get(register)
    if not feld:
        return []
    return [dict(r) for r in con.execute(
        "SELECT COALESCE(f.korrigiert, f.gelesen) wer, count(*) n, "
        "min(e.bild) von, max(e.bild) bis FROM feld f "
        "JOIN eintrag e ON e.id=f.eintrag_id "
        "WHERE e.register=? AND f.name=? AND COALESCE(f.korrigiert, f.gelesen) "
        "IS NOT NULL GROUP BY wer ORDER BY von", (register, feld))]


def neu_schneiden(con, register, still=False):
    """Aus der aufgehobenen Rohantwort noch einmal segmentieren — gratis."""
    roh = konfig.WURZEL / "daten" / f"koepfe_{register}.json"
    if not roh.exists():
        raise SystemExit(f"keine gespeicherte Lesung für {register}")
    gelesen = json.loads(roh.read_text(encoding="utf-8"))
    alle = [f.stem for f in seiten.bilder(einstellungen.ordner(con, register))]
    a = segmentiere(gelesen, alle)
    merke(con, register, a)
    if not still:
        _zeige(a)
    return a


def _zeige(abschnitte):
    for x in abschnitte:
        print(f"  {x['von']} – {x['bis']}  ({x['seiten']} Seiten)")
        print(f"    {len(x['spalten'])} Spalten: "
              + " | ".join(x["spalten"][:6])
              + (" …" if len(x["spalten"]) > 6 else ""))


def pruefe(con, register, jede=JEDE, still=False):
    """Ein Register durchmustern und die Abschnitte festhalten."""
    kb = koepfe(con, register, jede, still)
    if not kb:
        return dict(register=register, abschnitte=[], grund="keine Kopfblöcke")
    if not still:
        print(f"{register}: {len(kb)} Stichproben, "
              f"{sum(len(v) for v in kb.values())} Kopfbilder")
    gelesen, kosten = frage_modell(kb)
    # Die Rohantwort aufheben: Am Schnitt laesst sich nachbessern, ohne die
    # Koepfe noch einmal lesen zu lassen. Der erste Lauf am Taufregister
    # kostete 1,09 $ und war wegen einer Segmentierungsregel unbrauchbar.
    roh = konfig.WURZEL / "daten" / f"koepfe_{register}.json"
    roh.parent.mkdir(parents=True, exist_ok=True)
    roh.write_text(json.dumps(gelesen, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    alle = [f.stem for f in seiten.bilder(einstellungen.ordner(con, register))]
    a = segmentiere(gelesen, alle)
    merke(con, register, a)
    if not still:
        _zeige(a)
        if kosten:
            print(f"  über die API hätte das {kosten:.3f} $ gekostet")
    return dict(register=register, abschnitte=a, kosten=kosten)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("register", nargs="?")
    ap.add_argument("--alle", action="store_true")
    ap.add_argument("--jede", type=int, default=JEDE)
    ap.add_argument("--haende", action="store_true")
    ap.add_argument("--neu-schneiden", action="store_true",
                    help="ohne Modell aus der gespeicherten Lesung")
    a = ap.parse_args()
    con = db.verbinde()
    regs = list(konfig.register()) if a.alle else [a.register]
    for r in regs:
        if not r:
            ap.error("Register angeben oder --alle")
        if a.haende:
            print(f"{r}: Schreiber")
            for h in haende(con, r):
                print(f"  {h['wer']:24} {h['n']:4} Einträge  "
                      f"{h['von']} – {h['bis']}")
            continue
        if getattr(a, "neu_schneiden", False):
            neu_schneiden(con, r)
        else:
            pruefe(con, r, a.jede)


if __name__ == "__main__":
    main()
