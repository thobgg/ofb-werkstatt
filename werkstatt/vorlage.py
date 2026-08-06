#!/usr/bin/env python3
"""Lesen über eine Sitzung statt über die API — ohne zweite Rechnung.

    python3 -m werkstatt.vorlage --lege-vor 3
    python3 -m werkstatt.vorlage --stand 3

Wer ein Claude-Abonnement hat, zahlt für die API ein zweites Mal. Das ist
der Grund für diese Quelle: Die Werkstatt legt Seiten und Prompt in einen
Ordner, eine Sitzung liest sie, die Werkstatt nimmt die Antworten wieder auf.

    Werkstatt legt vor  ──►  ausgabe/lesen/runde-3/
                             ANLEITUNG.md · prompt.txt · seiten.json
    Sitzung liest       ──►  antwort/<bild>.json
    Werkstatt nimmt auf ──►  derselbe Weg wie API und Testdaten

Der Unterschied zur API ist Handarbeit, nicht Qualität: ein Sitzungswechsel
je Tranche statt eines Knopfdrucks, und keine Batch-Ersparnis, weil es
nichts einzureichen gibt. Das Ergebnis läuft durch dieselbe `speichere()`
wie alles andere — Abgleich, Ampel und Übergabe merken keinen Unterschied.
"""
import argparse
import json
from pathlib import Path

from . import db, einstellungen, konfig, lesen, seiten

ORDNER = Path("ausgabe") / "lesen"

ANLEITUNG = """# Lesen für Runde {nr} — {titel}

{anzahl} Seiten aus `{bilder}`.

## Was zu tun ist

Für **jede** Seite in `seiten.json` eine Datei `antwort/<bild>.json` schreiben.
`<bild>` ist der Name ohne Endung, genau wie in `seiten.json`.

Der Systemprompt steht in `prompt.txt` — er enthält die Regeln und, falls
schon Korrekturen vorliegen, die belegten Fehllesungen dieser Hand.

## Form der Antwort

```json
{{
  "eintraege": [
    {{
      "lfd_nr": "11",
      "jahr": {jahr},
      "felder": {{
        "{beispielfeld}": {{
          "wert": "...",
          "kb": "wörtlich wie im Buch, nur wenn es abweicht",
          "zuversicht": 0.9,
          "notiz": null
        }}
      }}
    }}
  ]
}}
```

Felder dieses Registers:

{felder}

`kb` nur setzen, wenn die Schreibung im Buch von der normalisierten Form
abweicht. `notiz` nur bei Unsicherheit oder Besonderheit. Unlesbares bekommt
`null` und eine Notiz — **nicht raten**.

## Zurück in die Werkstatt

Wenn die Dateien liegen:

```sh
python3 -m werkstatt.runde --lies {runde}
```

oder in der Oberfläche unter **Lesen** auf *Antworten einlesen*.

## Warum die ganze Seite und nicht einzelne Streifen

Dieselbe Hand schreibt in jedem Eintrag wiederkehrende Formeln
(`B. u. Weingärtner in ...`). Daran eicht man die Buchstabenformen. Wer nur
den zweifelhaften Namen sieht, hat diese Eichung nicht. Register sind
außerdem chronologisch: Das Datum eines Eintrags liegt zwischen dem des
vorigen und des nächsten.
"""


def ordner(runde_nr):
    return konfig.WURZEL / ORDNER / f"runde-{runde_nr}"


def lege_vor(con, runde_id, still=False):
    """Seiten, Prompt und Anleitung für eine Runde ablegen."""
    r = con.execute("SELECT * FROM runde WHERE id=?", (runde_id,)).fetchone()
    if not r:
        raise SystemExit(f"keine Runde {runde_id}")
    art = r["register"]
    ziel = ordner(r["nr"])
    (ziel / "antwort").mkdir(parents=True, exist_ok=True)

    bilder = [x["bild"] for x in con.execute(
        "SELECT s.bild FROM auftrag_seite s JOIN auftrag a ON a.id=s.auftrag "
        "WHERE a.runde=? ORDER BY s.bild", (runde_id,))]
    quelle = einstellungen.ordner(con, art)
    dateien = {f.stem: str(f) for f in seiten.bilder(quelle)}

    (ziel / "seiten.json").write_text(json.dumps(
        [{"bild": b, "datei": dateien.get(b, ""),
          "antwort": f"antwort/{b}.json"} for b in bilder],
        ensure_ascii=False, indent=2), encoding="utf-8")
    (ziel / "prompt.txt").write_text(lesen.prompt(art, con), encoding="utf-8")

    felder = konfig.felder(art)
    (ziel / "ANLEITUNG.md").write_text(ANLEITUNG.format(
        nr=r["nr"], runde=runde_id,
        titel=konfig.register(art).get("titel", art),
        anzahl=len(bilder), bilder=quelle,
        jahr=r["jahr"] if "jahr" in r.keys() and r["jahr"] else 1808,
        beispielfeld=felder[1] if len(felder) > 1 else felder[0],
        felder="\n".join(f"- `{f}`" for f in felder)), encoding="utf-8")

    if not still:
        print(f"  {ziel.relative_to(konfig.WURZEL)}")
        print(f"  {len(bilder)} Seiten · Prompt · Anleitung")
        print(f"  Antworten erwartet in {ziel.relative_to(konfig.WURZEL)}/antwort/")
    return ziel, bilder


def lies_seite(runde_nr, bild):
    """Eine abgelegte Antwort aufnehmen — Form wie bei API und Testdaten."""
    p = ordner(runde_nr) / "antwort" / f"{bild}.json"
    if not p.exists():
        raise FileNotFoundError(
            f"noch keine Antwort für {bild} — erwartet in "
            f"{p.relative_to(konfig.WURZEL)}")
    d = json.loads(p.read_text(encoding="utf-8"))
    if "eintraege" not in d:
        raise ValueError(f"{p.name}: Schlüssel 'eintraege' fehlt")
    return d


def stand(con, runde_id):
    """Was liegt schon vor, was fehlt noch."""
    r = con.execute("SELECT nr FROM runde WHERE id=?", (runde_id,)).fetchone()
    if not r:
        return None
    ziel = ordner(r["nr"])
    bilder = [x["bild"] for x in con.execute(
        "SELECT s.bild FROM auftrag_seite s JOIN auftrag a ON a.id=s.auftrag "
        "WHERE a.runde=? ORDER BY s.bild", (runde_id,))]
    da = []
    for b in bilder:
        p = ziel / "antwort" / f"{b}.json"
        n = 0
        if p.exists():
            try:
                n = len(json.loads(p.read_text(encoding="utf-8"))
                        .get("eintraege", []))
            except Exception:
                n = -1          # liegt da, ist aber nicht lesbar
        da.append(dict(bild=b, da=p.exists(), eintraege=n))
    return dict(ordner=str(ziel.relative_to(konfig.WURZEL)),
                gesamt=len(bilder), fertig=sum(1 for x in da if x["da"]),
                seiten=da)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lege-vor", type=int, metavar="RUNDE")
    ap.add_argument("--stand", type=int, metavar="RUNDE")
    a = ap.parse_args()
    con = db.verbinde()
    if a.lege_vor:
        lege_vor(con, a.lege_vor)
    elif a.stand:
        s = stand(con, a.stand)
        if not s:
            raise SystemExit("keine solche Runde")
        print(f"  {s['ordner']}  —  {s['fertig']}/{s['gesamt']} beantwortet")
        for x in s["seiten"]:
            zeichen = "✓" if x["da"] else "·"
            n = (f"{x['eintraege']} Einträge" if x["eintraege"] > 0
                 else "unlesbar" if x["eintraege"] < 0 else "")
            print(f"   {zeichen} {x['bild']}  {n}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
