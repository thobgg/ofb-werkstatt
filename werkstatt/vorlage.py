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
abweicht. `notiz` nur bei Unsicherheit oder Besonderheit.

## Die eine Regel, auf die es ankommt

**Was lesbar ist, gehört ins Feld — auch wenn der Rest es nicht ist.**

Bei den Eltern steht im Register regelmäßig „Rosina Margaretha, geb.
⟨Gekritzel⟩". Die Vornamen sind klar, der Mädchenname nicht. Dann:

    richtig   "wert": "Rosina Margaretha",
              "notiz": "Nachname nach 'geb.' nicht lesbar"

    falsch    "wert": null,
              "notiz": "Vornamen Rosina Margaretha klar, Nachname nicht"

Der Grund: Der Abgleich sucht die **Elternehe** im Bestand und leitet den
Nachnamen daraus ab. Er trägt über die Vornamen von Vater *und* Mutter —
gerade weil die Nachnamen das unzuverlässigste Feld sind. Ein `null`
verschenkt genau die Angabe, die den Treffer bringt.

`null` ist richtig, wenn **gar nichts** zu lesen ist. Geraten wird nie:
Unsicheres kommt mit niedriger `zuversicht` und einer Notiz ins Feld,
nicht als Erfindung.

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


# ------------------------------------------------- Claude Code anstoßen
AUFTRAG = """Lies die Kirchenbuchseiten nach ANLEITUNG.md in diesem Ordner.

Die Regeln stehen in prompt.txt, die Seiten in seiten.json. Schreibe für
jede Seite eine Datei antwort/<bild>.json in der dort beschriebenen Form.

Arbeite die Seiten der Reihe nach ab und schreibe jede Antwort sofort, bevor
du die nächste Seite ansiehst — dann geht bei einem Abbruch nichts verloren.
Seiten, für die schon eine Antwort liegt, überspringst du."""


def werkzeug():
    """Pfad zur Claude-Code-Kommandozeile, falls vorhanden."""
    import shutil
    return shutil.which("claude")


_BEREIT = {}


def bereitschaft(neu=False):
    """Was die Sitzungsquelle auf diesem Rechner vorfindet.

    Es gibt **keinen laufenden Chat**, an den sich die Werkstatt hängt.
    `claude -p` startet jedes Mal eine eigene, kurze Sitzung ohne Verlauf.
    Die Zuordnung zum richtigen Konto macht das Programm selbst: Wer sich
    einmal mit `claude auth login` angemeldet hat, dessen Anmeldung liegt
    im Benutzerprofil. Die Werkstatt fragt sie hier nur ab und speichert
    nichts davon.
    """
    if _BEREIT and not neu:
        return _BEREIT
    import subprocess
    w = werkzeug()
    d = dict(pfad=w, da=bool(w), version=None, angemeldet=False,
             konto=None, weg=None, abo=None, meldung=None)
    if not w:
        d["meldung"] = ("Claude Code ist auf diesem Rechner nicht installiert "
                        "(oder nicht im Suchpfad).")
        _BEREIT.clear(), _BEREIT.update(d)
        return d
    try:
        d["version"] = subprocess.run(
            [w, "--version"], capture_output=True, text=True,
            timeout=30).stdout.strip() or None
        p = subprocess.run([w, "auth", "status"], capture_output=True,
                           text=True, timeout=30)
        s = json.loads(p.stdout)
        d.update(angemeldet=bool(s.get("loggedIn")), konto=s.get("email"),
                 weg=s.get("authMethod"), abo=s.get("subscriptionType"))
        if not d["angemeldet"]:
            d["meldung"] = "Claude Code ist installiert, aber nicht angemeldet."
    except Exception as e:
        d["meldung"] = f"Status nicht lesbar: {e}"
    _BEREIT.clear(), _BEREIT.update(d)
    return d


def lesen_lassen(con, runde_id, still=False, zeitlimit=3600):
    """Die abgelegten Seiten von Claude Code lesen lassen.

    Die Werkstatt hält dabei **keine Anmeldedaten**. Sie ruft nur das
    Programm auf, das der Bearbeiter ohnehin auf seinem Rechner hat und das
    unter seinem eigenen Zugang läuft — mit Pro- oder Max-Abonnement also
    ohne API-Schlüssel und ohne zweite Rechnung.

    Ein Benutzername-und-Passwort-Feld in der Werkstatt gäbe es dafür nicht:
    Kontodaten gehören nicht in eine fremde Anwendung, und einen solchen
    Zugang für Programme gibt es auch gar nicht.
    """
    import subprocess
    w = werkzeug()
    if not w:
        return dict(ok=False, meldung=(
            "claude nicht gefunden — entweder Claude Code installieren "
            "oder die Seiten von Hand in einer Sitzung lesen lassen"))
    ziel, _ = lege_vor(con, runde_id, still=True)
    if not still:
        print(f"  {w} im Ordner {ziel.relative_to(konfig.WURZEL)}")
        print("  Das läuft über das Abonnement des Bearbeiters, nicht über "
              "einen API-Schlüssel.")
    # Die Sitzung laeuft im Rundenordner, die Scans liegen aber im
    # Bilderverzeichnis. Ohne --add-dir sieht sie die Seiten nicht und
    # meldet trotzdem Erfolg — sie hat ja nichts falsch gemacht, nur nichts
    # zu tun gehabt. Deshalb beide Verzeichnisse freigeben.
    bilder = str(einstellungen.ordner(
        con, con.execute("SELECT register FROM runde WHERE id=?",
                         (runde_id,)).fetchone()["register"]))
    try:
        p = subprocess.run(
            [w, "-p", AUFTRAG, "--permission-mode", "acceptEdits",
             "--add-dir", bilder, "--add-dir", str(konfig.WURZEL)],
            cwd=ziel, capture_output=True, text=True, timeout=zeitlimit)
    except subprocess.TimeoutExpired:
        return dict(ok=False, meldung=f"Zeitlimit von {zeitlimit}s erreicht")
    s = stand(con, runde_id)
    # `ok` misst das Ergebnis, nicht den Rueckgabewert: Eine Sitzung, die
    # sauber erklaert, warum sie nichts lesen konnte, beendet sich mit 0.
    return dict(ok=p.returncode == 0 and s["fertig"] > 0, rc=p.returncode,
                ausgabe=(p.stdout or "")[-2000:],
                fehler=(p.stderr or "")[-1000:],
                fertig=s["fertig"], gesamt=s["gesamt"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lege-vor", type=int, metavar="RUNDE")
    ap.add_argument("--stand", type=int, metavar="RUNDE")
    ap.add_argument("--lesen-lassen", type=int, metavar="RUNDE",
                    help="Claude Code die abgelegten Seiten lesen lassen")
    a = ap.parse_args()
    con = db.verbinde()
    if a.lesen_lassen:
        d = lesen_lassen(con, a.lesen_lassen)
        print(f"  {'fertig' if d['ok'] else 'abgebrochen'} — "
              f"{d.get('fertig', 0)}/{d.get('gesamt', 0)} Seiten beantwortet")
        if not d["ok"]:
            print("  " + str(d.get("meldung") or d.get("fehler", ""))[:300])
    elif a.lege_vor:
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
