#!/usr/bin/env python3
"""Eine neue OFB-Instanz anlegen – Stufe 5 des Mehrbenutzer-Bauplans.

    python3 -m werkstatt.instanz --neu Neipperg
    python3 -m werkstatt.instanz --neu Neipperg --gedcom bestand.ged \\
        --redakteur maria --passwort ...
    python3 -m werkstatt.instanz --liste

**Wozu.** „Projekt anlegen" ist Provisionierung, kein Datenmodell: je
Parochie eine eigene Instanz mit eigener Datenbank und eigenem Container
hinter dem Proxy. Wer eine Parochie kompromittiert, hat nur sie – die
Sicherheitsgrenze ist die Instanzgrenze, ein Mandantenfeld gibt es nicht.

**Wie.** Derselbe Weg wie `demoinstanz.py`, nur ohne Demo-Sperre und
ohne Rücksetzer: Klon aus `git ls-files`, kurz starten, über die
Web-Schnittstelle einrichten (das ist der Weg, den auch der Browser
nimmt), Kontext-GEDCOM als Beleg einlesen, erstes Redakteurskonto in
`daten/nutzer.txt`, Betriebsdateien mit festem Port. Ab da verwaltet der
Redakteur seine Instanz selbst im Zahnrad.

**Ports.** Jede Instanz bekommt einen eigenen aus 8770 aufwärts; die
Arbeitsinstallation behält 8765, die Vorführinstanz 8766, das Portal
8767. Der Port steht in `betrieb/port`, damit Portal und Proxy ihn
nachlesen können, ohne Compose-Dateien zu deuten.
"""
import argparse
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import tomllib
from pathlib import Path

from . import nutzer as _nutzer
from .klon import Maske, ausnahmen, baue, frei, warte

WURZEL = Path("~/ofb-instanzen").expanduser()
REGISTER = ("taufe", "ehe", "tod")
ERSTER_PORT = 8770

DB = Path("daten") / "erfassung.sqlite"


def _slug(name):
    """Verzeichnis- und Dienstname aus dem Parochienamen."""
    s = name.strip().lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9_-]+", "-", s).strip("-")
    if not s:
        raise SystemExit(f"Aus {name!r} lässt sich kein Verzeichnisname "
                         f"bilden.")
    return s


def _umgebung():
    """Bauen ohne Schlüssel und ohne Demo-Sperre – wie in demoinstanz."""
    import os
    u = dict(os.environ)
    u.pop("ANTHROPIC_API_KEY", None)
    u.pop("OFB_DEMO", None)
    return u


def _naechster_port(wurzel):
    """Der kleinste freie Port ab 8770 – belegte stehen in betrieb/port."""
    belegt = set()
    if wurzel.is_dir():
        for p in wurzel.iterdir():
            f = p / "betrieb" / "port"
            if f.is_file():
                try:
                    belegt.add(int(f.read_text().strip()))
                except ValueError:
                    pass
    port = ERSTER_PORT
    while port in belegt:
        port += 1
    return port


# ---------------------------------------------------------------- Anlegen
def neu(name, wurzel=WURZEL, gedcom=None, redakteur=None, passwort=None,
        port=None, melde=print):
    """Instanz anlegen. Rückgabe: das Instanzverzeichnis."""
    slug = _slug(name)
    ziel = wurzel / slug
    if ziel.exists():
        raise SystemExit(f"{ziel} gibt es schon.")
    if gedcom:
        gedcom = Path(gedcom).expanduser()
        if not gedcom.is_file():
            raise SystemExit(f"Kontext-GEDCOM fehlt: {gedcom}")
    if redakteur and not passwort:
        raise SystemExit("Das Redakteurskonto braucht ein Passwort.")
    if passwort and len(passwort) < 8:
        raise SystemExit("Passwort: mindestens 8 Zeichen.")
    port = port or _naechster_port(wurzel)
    wurzel.mkdir(parents=True, exist_ok=True)

    try:
        n = baue(ziel)
    except subprocess.CalledProcessError:
        raise SystemExit(
            "Der Klon braucht ein Git-Arbeitsverzeichnis der Werkstatt "
            "(git ls-files ist die Quelle).\nAlles andere – etwa ein "
            "rsync ohne .git/ – könnte Arbeitsdaten des Betreibers "
            "mitkopieren.")
    melde(f"Klon: {n} Dateien in {ziel}")

    # Das Kontext-GEDCOM in die Instanz kopieren, *bevor* es eingelesen
    # wird: Die Quelle soll mit der Instanz umziehen können, nicht auf
    # einen Pfad des Wirts zeigen.
    quelle_datei = None
    if gedcom:
        (ziel / "quellen").mkdir(exist_ok=True)
        quelle_datei = ziel / "quellen" / gedcom.name
        shutil.copy2(gedcom, quelle_datei)

    bau_port = frei()
    log = ziel / "bau.log"
    server = subprocess.Popen(
        [sys.executable, "start.py", "--port", str(bau_port),
         "--kein-browser"],
        cwd=ziel, stdout=log.open("w"), stderr=subprocess.STDOUT,
        text=True, env=_umgebung())
    try:
        if not warte(bau_port):
            raise SystemExit("Der Klon startet nicht.\n"
                             + log.read_text(encoding="utf-8")[-4000:])
        m = Maske(bau_port)
        a = m("/api/einrichten", dict(
            gemeinde=name.strip(), ort=name.strip(), bestand=False,
            register=[dict(art=x, ordner=f"bilder/{x}") for x in REGISTER]))
        if not a.get("ok"):
            raise SystemExit(f"Einrichten schlug fehl: {a}")
        if quelle_datei:
            a = m("/api/quelle", dict(
                datei=str(quelle_datei), art="gedcom", gilt="beleg",
                name=f"OFB {name.strip()}", parochien=name.strip()))
            if not a.get("ok"):
                raise SystemExit(f"GEDCOM-Import schlug fehl: {a}")
            melde(f"Beleg: {gedcom.name} eingelesen")
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(10)
            except subprocess.TimeoutExpired:
                server.kill()

    meldungen = ausnahmen(log)
    if meldungen:
        melde(f"Achtung: {len(meldungen)} Ausnahme(n) beim Bau, erste:\n"
              f"  {meldungen[0][:200]}")

    # Das erste Konto. Mit ihm existiert daten/nutzer.txt, und die Instanz
    # startet im Kontenbetrieb – ohne wäre sie hinter dem Proxy offen.
    if redakteur:
        _nutzer.anlegen(redakteur, passwort, "redakteur",
                        datei=ziel / "daten" / "nutzer.txt")
        melde(f"Redakteur: {redakteur}")

    _betriebsdateien(ziel, slug, port)
    melde(f"Fertig: {ziel} auf Port {port}")
    return ziel


# ------------------------------------------------------------------ Stand
def stand(ziel):
    """Was das Portal über eine Instanz zeigt – nur lesend, aus Dateien."""
    ziel = Path(ziel)
    d = dict(verzeichnis=str(ziel), name=ziel.name, port=None,
             gemeinde=None, personen=None, familien=None, eintraege=None,
             bestaetigt=None, runden=[], budget_dollar=None,
             verbraucht_dollar=None, nutzer=[], zugriff=None, fehler=None)
    f = ziel / "betrieb" / "port"
    if f.is_file():
        try:
            d["port"] = int(f.read_text().strip())
        except ValueError:
            pass
    # konfig.local.toml zuerst: Die Einrichtung schreibt dorthin, die
    # eingecheckte konfig.toml behält ihr "Musterhausen".
    for k in (ziel / "konfig.local.toml", ziel / "konfig.toml"):
        if d["gemeinde"] or not k.is_file():
            continue
        try:
            d["gemeinde"] = (tomllib.loads(k.read_text(encoding="utf-8"))
                             .get("gemeinde", {}).get("name"))
        except (tomllib.TOMLDecodeError, OSError):
            pass
    d["nutzer"] = [dict(name=n, rolle=r) for n, (_, r) in sorted(
        _nutzer.lade(ziel / "daten" / "nutzer.txt").items())]
    db = ziel / DB
    if not db.is_file():
        d["fehler"] = "keine Datenbank"
        return d
    zeiten = [db.stat().st_mtime]
    log = ziel / "daten" / "zugriffe.log"
    if log.is_file():
        zeiten.append(log.stat().st_mtime)
    from datetime import datetime, timezone
    d["zugriff"] = datetime.fromtimestamp(
        max(zeiten), timezone.utc).isoformat(timespec="seconds")
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        try:
            for t, s in (("personen", "person"), ("familien", "familie"),
                         ("eintraege", "eintrag")):
                d[t] = con.execute(f"SELECT count(*) FROM {s}").fetchone()[0]
            d["bestaetigt"] = con.execute(
                "SELECT count(*) FROM eintrag WHERE status='bestaetigt'"
            ).fetchone()[0]
            d["runden"] = [dict(r) for r in con.execute(
                "SELECT nr, register, stand, seiten FROM runde "
                "WHERE stand<>'fertig' ORDER BY nr")]
            from . import kontingent
            d["budget_dollar"] = kontingent.budget(con)
            d["verbraucht_dollar"] = kontingent.verbraucht(con)
        finally:
            con.close()
    except sqlite3.Error as e:
        d["fehler"] = str(e)
    return d


def liste(wurzel=WURZEL):
    """Alle Instanzen unter der Wurzel – erkannt an start.py + daten/."""
    if not Path(wurzel).is_dir():
        return []
    return [stand(p) for p in sorted(Path(wurzel).iterdir())
            if p.is_dir() and (p / "start.py").is_file()]


# -------------------------------------------------------- Betriebsdateien
STARTEN = """#!/bin/sh
# Diese Instanz starten. Gehört bleibt 127.0.0.1 – nach außen kommt sie
# nur über den Reverse Proxy. Die Anmeldung macht daten/nutzer.txt.
cd "$(dirname "$0")" || exit 1
exec python3 start.py --port {port} --kein-browser
"""

DOCKERFILE = """# Die Instanz im Container – dasselbe Bild wie die
# Vorführinstanz, nur ohne Demo-Sperre. Das Verzeichnis wird eingehängt,
# nicht eingebacken.
FROM python:3.12-slim
RUN pip install --no-cache-dir pillow numpy gedcom7
WORKDIR /app
EXPOSE {port}
CMD ["python3", "start.py", "--port", "{port}", "--kein-browser"]
"""

COMPOSE = """# docker compose up -d
# `network_mode: host` wie bei der Vorführinstanz: Die App bindet
# 127.0.0.1, dort holt der Reverse Proxy sie ab (Ziel 127.0.0.1:{port}).
services:
  ofb-{slug}:
    build:
      context: ..
      dockerfile: betrieb/Dockerfile
    container_name: ofb-{slug}
    volumes:
      - ..:/app
    network_mode: host
    # Nur nötig, wenn über die API gelesen wird; der Weg über das
    # Abonnement des Bearbeiters braucht keinen Schlüssel.
    # environment:
    #   ANTHROPIC_API_KEY: "..."
    restart: unless-stopped
"""

LIESMICH = """# Instanz {name}

Angelegt von `python3 -m werkstatt.instanz --neu`. Port: {port}.

    ./starten.sh                          am Rechner
    cd betrieb && docker compose up -d    im Container

Reverse Proxy: Quelle HTTPS <name>.example 443 → Ziel HTTP
127.0.0.1:{port}, Proxy-Timeout 300 s. Die Anmeldung macht die Instanz
selbst über `daten/nutzer.txt`; Konten verwaltet der Redakteur im
Zahnrad. Das KI-Kontingent setzt das Portal (`ki.budget_dollar`).
"""


def _betriebsdateien(ziel, slug, port):
    (ziel / "starten.sh").write_text(STARTEN.format(port=port),
                                     encoding="utf-8")
    (ziel / "starten.sh").chmod(0o755)
    b = ziel / "betrieb"
    b.mkdir(exist_ok=True)
    (b / "port").write_text(f"{port}\n", encoding="utf-8")
    (b / "Dockerfile").write_text(DOCKERFILE.format(port=port),
                                  encoding="utf-8")
    (b / "compose.yaml").write_text(COMPOSE.format(slug=slug, port=port),
                                    encoding="utf-8")
    (ziel / "LIESMICH-instanz.md").write_text(
        LIESMICH.format(name=ziel.name, port=port), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--neu", metavar="PAROCHIE")
    ap.add_argument("--wurzel", type=Path, default=WURZEL)
    ap.add_argument("--gedcom", help="Kontext-GEDCOM, wird als Beleg "
                    "eingelesen")
    ap.add_argument("--redakteur", help="Name des ersten Redakteurskontos")
    ap.add_argument("--passwort", help="sonst wird verdeckt gefragt")
    ap.add_argument("--port", type=int)
    ap.add_argument("--liste", action="store_true")
    a = ap.parse_args()
    wurzel = a.wurzel.expanduser().resolve()
    if a.neu:
        pw = a.passwort
        if a.redakteur and not pw:
            import getpass
            pw = getpass.getpass(f"Passwort für {a.redakteur}: ")
            if pw != getpass.getpass("Noch einmal: "):
                raise SystemExit("Die Eingaben stimmen nicht überein.")
        neu(a.neu, wurzel, a.gedcom, a.redakteur, pw, a.port)
        return
    if a.liste:
        instanzen = liste(wurzel)
        if not instanzen:
            print(f"Keine Instanzen unter {wurzel}.")
            return
        for i in instanzen:
            offen = ", ".join(f"{r['register']} {r['stand']}"
                              for r in i["runden"]) or "-"
            print(f"  {i['name']:20} Port {i['port'] or '-':<6} "
                  f"{i['personen'] or 0:6} Personen   offen: {offen}")
        return
    ap.print_help()


if __name__ == "__main__":
    main()
