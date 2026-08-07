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
import os
import sys
from pathlib import Path

from . import bloecke, db, einstellungen, katalog, konfig, lesen, seiten

ORDNER = Path("ausgabe") / "lesen"

ANLEITUNG = """# Lesen für Runde {nr} — {titel}

{anzahl} Seiten aus `{bilder}`.

## Was zu tun ist

Für **jede** Seite in `seiten.json` eine Datei `antwort/<bild>.json` schreiben.
`<bild>` ist der Name ohne Endung, genau wie in `seiten.json`.

## Die Blöcke, nicht die ganze Seite

Zu jeder Seite steht in `seiten.json`:

    kopf    die gedruckten Spaltenüberschriften, je Buchseite ein Bild
    zeilen  je Eintragszeile die Blöcke, links und rechts vom Bund

**Sieh zuerst den Kopf an.** Er sagt, welche Spalte was bedeutet — bei
diesem Formular neun Stück, vier links und fünf rechts. Danach je Zeile
beide Blöcke, und zwar **beide zusammen**: Sie sind derselbe Eintrag, nur
diesseits und jenseits des Bundes. Der rechte Block trägt Geburtszeit,
Tauftag, den taufenden Geistlichen, die Paten und den Verweis ins
Familienregister — Angaben, die in der linken Hälfte schlicht nicht
vorkommen.

Die ganze Seite (`datei`) ist zusätzlich da, für den Überblick und für
Zweifelsfälle. **Zum Lesen taugt sie nicht**: 5679 px breit, auf
Anzeigegröße heruntergerechnet bleiben je Spalte gut hundert Pixel.

Steht bei einer Seite `hinweis` statt `zeilen`, hat die Zeilenerkennung
versagt — dann die ganze Seite lesen und das im Feld `unleserlich`
vermerken.

Eine Zeile ohne Eintrag (leeres Formular am Seitenende) wird
übersprungen, nicht als leerer Eintrag geliefert.

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

    # Blöcke statt der ganzen Seite. Eine Doppelseite dieses Bandes ist
    # 5679 px breit; wer sie als ein Bild anschaut, bekommt sie
    # heruntergerechnet und liest die schmalen rechten Spalten nicht mehr.
    # Siehe bloecke.py — dort steht die Messung dazu.
    liste = []
    for b in bilder:
        d = dateien.get(b, "")
        e = {"bild": b, "datei": d, "antwort": f"antwort/{b}.json"}
        if d:
            try:
                bl = bloecke.schneide(d, still=True)
                if bl.get("bloecke"):
                    e["kopf"] = [k["datei"] for k in bl["kopf"]]
                    e["zeilen"] = [
                        {"zeile": z["zeile"],
                         "teile": [x["datei"] for x in z["teile"]]}
                        for z in bl["bloecke"]]
                else:
                    e["hinweis"] = bl.get("grund", "keine Blöcke")
            except Exception as ex:
                e["hinweis"] = f"Blöcke nicht geschnitten: {ex}"
        liste.append(e)
    (ziel / "seiten.json").write_text(
        json.dumps(liste, ensure_ascii=False, indent=2), encoding="utf-8")
    (ziel / "prompt.txt").write_text(lesen.prompt(art, con), encoding="utf-8")

    felder = konfig.felder(art, con)
    (ziel / "ANLEITUNG.md").write_text(ANLEITUNG.format(
        nr=r["nr"], runde=runde_id,
        titel=konfig.register(art).get("titel", art),
        anzahl=len(bilder), bilder=quelle,
        jahr=r["jahr"] if "jahr" in r.keys() and r["jahr"] else 1808,
        beispielfeld=felder[1] if len(felder) > 1 else felder[0],
        felder=katalog.als_prompt(art, con)), encoding="utf-8")

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
_BEREIT_ZEIT = [0.0]
# Kurz genug, dass eine Anmeldung oder Abmeldung nebenan auffaellt, lang
# genug, dass ein Seitenaufbau nicht zweimal `claude` startet (~0,35 s je
# Aufruf). Ohne Verfall log man sich ab und die Werkstatt zeigt weiter gruen.
_BEREIT_GILT = 15.0


def bereitschaft(neu=False):
    """Was die Sitzungsquelle auf diesem Rechner vorfindet.

    Es gibt **keinen laufenden Chat**, an den sich die Werkstatt hängt.
    `claude -p` startet jedes Mal eine eigene, kurze Sitzung ohne Verlauf.
    Die Zuordnung zum richtigen Konto macht das Programm selbst: Wer sich
    einmal mit `claude auth login` angemeldet hat, dessen Anmeldung liegt
    im Benutzerprofil. Die Werkstatt fragt sie hier nur ab und speichert
    nichts davon.
    """
    import subprocess
    import time
    if _BEREIT and not neu and time.monotonic() - _BEREIT_ZEIT[0] < _BEREIT_GILT:
        return _BEREIT
    _BEREIT_ZEIT[0] = time.monotonic()
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
        # Die Werkstatt haengt hier an einer fremden Ausgabe. Aendert eine
        # kuenftige Version von Claude Code deren Form, darf das die Quelle
        # nicht verschwinden lassen — dann waere ein funktionierender Weg aus
        # der Oberflaeche heraus nicht mehr erreichbar. Also im Zweifel
        # anbieten und den Zweifel danebenschreiben.
        d["angemeldet"] = None
        d["meldung"] = (f"Anmeldestand nicht lesbar ({e}). Lesen wird trotzdem "
                        "angeboten — ob es klappt, zeigt der erste Versuch.")
    _BEREIT.clear(), _BEREIT.update(d)
    return d


# Für jedes Fenster: wie es einen Befehl mitbekommt. Getestet wird der
# Reihe nach, das erste vorhandene gewinnt.
_FENSTER = [
    ("gnome-terminal", lambda b: ["--title=Claude-Anmeldung", "--"] + b),
    ("konsole", lambda b: ["-e"] + b),
    ("xfce4-terminal", lambda b: ["--title=Claude-Anmeldung", "-x"] + b),
    ("alacritty", lambda b: ["-e"] + b),
    ("kitty", lambda b: b),
    ("xterm", lambda b: ["-title", "Claude-Anmeldung", "-e"] + b),
    ("x-terminal-emulator", lambda b: ["-e"] + b),
]


def anmelden():
    """Ein Fenster mit `claude auth login` öffnen.

    Die Anmeldung ist ein Gespräch: sie schickt in den Browser und wartet
    auf die Rückmeldung. Das braucht ein richtiges Fenster — deshalb wird
    eines geöffnet, statt den Befehl blind im Hintergrund zu starten.
    Die Werkstatt sieht dabei nichts von dem, was dort eingegeben wird;
    sie fragt hinterher nur `claude auth status` ab.
    """
    import shutil
    import subprocess
    w = werkzeug()
    if not w:
        return dict(ok=False, meldung="Claude Code ist nicht installiert.",
                    befehl="claude auth login")
    if os.name == "nt":
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "Claude-Anmeldung", "cmd", "/k",
                 w, "auth", "login", "--claudeai"],
                close_fds=True)
            return dict(ok=True, meldung="Ein Fenster ist aufgegangen.")
        except Exception as e:
            return dict(ok=False, meldung=str(e), befehl="claude auth login")
    if sys.platform == "darwin":
        skript = konfig.WURZEL / "daten" / "anmelden.command"
        skript.parent.mkdir(parents=True, exist_ok=True)
        skript.write_text(f'#!/bin/sh\n"{w}" auth login --claudeai\n')
        skript.chmod(0o755)
        subprocess.Popen(["open", "-a", "Terminal", str(skript)])
        return dict(ok=True, meldung="Ein Fenster ist aufgegangen.")
    # Nach der Anmeldung stehen bleiben, sonst ist die Meldung schneller
    # weg als lesbar.
    innen = ["sh", "-c", f'"{w}" auth login --claudeai; echo; '
             'echo "Fertig — dieses Fenster kann zu."; read x']
    for name, bau in _FENSTER:
        p = shutil.which(name)
        if not p:
            continue
        try:
            subprocess.Popen([p] + bau(innen), close_fds=True,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return dict(ok=True, meldung="Ein Fenster ist aufgegangen.")
        except Exception:
            continue
    return dict(ok=False, befehl="claude auth login", meldung=(
        "Kein Terminalfenster gefunden. Bitte eines von Hand öffnen und "
        "den Befehl eingeben."))


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
    art = con.execute("SELECT register FROM runde WHERE id=?",
                      (runde_id,)).fetchone()["register"]
    bilder = einstellungen.ordner(con, art)
    # Die Bilder liegen oft als Symlink im Projekt und in Wirklichkeit
    # woanders — auf einer zweiten Platte, im Archivordner. Die Sitzung
    # sieht dann einen Verweis, den sie nicht verfolgen darf, und meldet
    # ehrlich, dass sie nichts lesen konnte. Also auch die Ziele freigeben.
    ordner = {str(bilder), str(konfig.WURZEL)}
    for f in seiten.bilder(bilder)[:200]:
        if f.is_symlink() or f.resolve() != f:
            ordner.add(str(f.resolve().parent))
    frei = []
    for o in sorted(ordner):
        frei += ["--add-dir", o]
    try:
        p = subprocess.run(
            [w, "-p", AUFTRAG, "--permission-mode", "acceptEdits", *frei],
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
