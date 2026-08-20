#!/usr/bin/env python3
"""Das Admin-Portal des Wirts – Betreiber-Handgriffe im Browser.

    OFB_PORTAL_PASSWORT=... python3 -m werkstatt.portal
    OFB_PORTAL_PASSWORT=... python3 -m werkstatt.portal --wurzel ~/ofb-instanzen --port 8767

**Was es ist.** Eine eigene kleine App auf dem Wirt, eigener Port hinter
dem Proxy, eigenes Admin-Passwort. Sie arbeitet über das **Dateisystem**
der Instanzverzeichnisse – es gibt keinen Superuser-Login in den
Instanzen; wer eine Parochie kompromittiert, hat weiterhin nur sie.

**Was es kann:**

    Projektliste       Instanzen mit Stand, aus deren Dateien gelesen
    Neues OFB anlegen  Name, Kontext-GEDCOM, erstes Redakteurskonto ->
                       werkstatt.instanz provisioniert
    Nutzerverwaltung   bearbeitet die nutzer.txt der Instanz - dieselbe
                       Datei wie der Zahnrad-Reiter des Redakteurs
    KI-Kontingent      setzt ki.budget_dollar in der Instanz-Datenbank;
                       geprüft wird dort, nicht hier

**Ohne Passwort startet es nicht.** Das Portal legt Konten an und
Projekte – offen betrieben wäre es der Generalschlüssel, den der
Bauplan ausdrücklich nicht will. Gehört bleibt 127.0.0.1; nach außen
kommt es nur über den Reverse Proxy, optional nur im LAN.

Jede Änderung steht in `portal.log` neben den Instanzen.
"""
import argparse
import base64
import binascii
import hmac
import json
import os
import re
import sqlite3
import threading
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import einstellungen, instanz, kontingent, sicherung, wirt
from . import nutzer as _nutzer

PORT = 8767
SEITE = (Path(__file__).resolve().parent / "web" / "static"
         / "portal.html").read_text(encoding="utf-8")

WURZEL = instanz.WURZEL
_PASSWORT = os.environ.get("OFB_PORTAL_PASSWORT", "")

# Was gerade angelegt wird: {slug: letzte Meldung}. Die Provisionierung
# dauert eine halbe Minute und mehr (GEDCOM-Import); der Browser pollt
# die Projektliste, statt an einem Aufruf zu hängen.
LAUFEND = {}
INSTANZEN = True                # der Wirt startet die Instanzen mit


def _log(zeile):
    try:
        with (WURZEL / "portal.log").open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} "
                    f"{zeile}\n")
    except OSError:
        pass


def _projekt_pfad(name):
    """Das Instanzverzeichnis zu einem Namen - oder None.

    Der Name kommt aus dem Browser; geprüft wird gegen die tatsächlich
    vorhandenen Verzeichnisse, nicht gegen ein Muster. Was nicht unter
    der Wurzel liegt, existiert für das Portal nicht.
    """
    if not re.fullmatch(r"[a-z0-9_-]{1,60}", name or ""):
        return None
    p = WURZEL / name
    return p if p.is_dir() and (p / "start.py").is_file() else None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    # ------------------------------------------------------------ Technik
    def _zutritt(self):
        kopf = self.headers.get("Authorization", "")
        if kopf.startswith("Basic "):
            try:
                _, _, kennwort = (base64.b64decode(kopf[6:])
                                  .decode("utf-8").partition(":"))
            except (binascii.Error, UnicodeDecodeError):
                kennwort = ""
            if hmac.compare_digest(kennwort, _PASSWORT):
                return True
        body = "Zugang nur mit dem Admin-Passwort.".encode("utf-8")
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="OFB-Portal"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return False

    def _send(self, code, typ, body):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, d, code=200):
        self._send(code, "application/json; charset=utf-8",
                   json.dumps(d, ensure_ascii=False, default=str))

    def _rumpf(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    @property
    def _frage(self):
        return urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

    # -------------------------------------------------------------- GET
    def do_GET(self):
        if not self._zutritt():
            return
        pfad = urllib.parse.urlparse(self.path).path
        if pfad in ("/", "/index.html"):
            return self._send(200, "text/html; charset=utf-8", SEITE)
        if pfad.startswith("/static/"):
            # Gestaltungsdateien (Kurrent-Schriftband) - nur Dateinamen,
            # nur Bildformate, derselbe Bestand wie in der Instanz.
            name = Path(urllib.parse.unquote(pfad[len("/static/"):])).name
            ziel = (Path(__file__).resolve().parent / "web" / "static"
                    / name)
            if (ziel.suffix.lower() in (".png", ".svg", ".webp")
                    and ziel.is_file()):
                return self._send(200, f"image/{ziel.suffix[1:].lower()}",
                                  ziel.read_bytes())
            return self._send(404, "text/plain", "nicht gefunden")
        if pfad == "/api/projekte":
            projekte = instanz.liste(WURZEL)
            for x in projekte:
                x["laeuft"] = wirt.laeuft(x["verzeichnis"])
            return self._json(dict(
                wurzel=str(WURZEL),
                projekte=projekte,
                entstehen=[dict(name=n, meldung=m)
                           for n, m in sorted(LAUFEND.items())]))
        if pfad == "/api/sicherungen":
            p = _projekt_pfad((self._frage.get("projekt") or [""])[0])
            if not p:
                return self._json({"fehler": "Kein solches Projekt."}, 400)
            return self._json(sicherung.liste(p))
        if pfad.startswith("/sicherung/"):
            # Download einer Sicherung: /sicherung/<projekt>/<datei>.
            # Beides wird gegen das geprüft, was wirklich daliegt.
            teile = pfad[len("/sicherung/"):].split("/")
            p = _projekt_pfad(teile[0]) if len(teile) == 2 else None
            datei = Path(urllib.parse.unquote(teile[1])).name if p else ""
            ziel = p / "sicherungen" / datei if p else None
            if not (ziel and datei.endswith(".zip") and ziel.is_file()):
                return self._send(404, "text/plain", "nicht gefunden")
            body = ziel.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition",
                             f'attachment; filename="{datei}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._send(404, "text/plain", "nicht gefunden")

    # ------------------------------------------------------------- POST
    def do_POST(self):
        if not self._zutritt():
            return
        pfad = urllib.parse.urlparse(self.path).path
        if pfad == "/api/projekt":
            return self.projekt_anlegen()
        if pfad == "/api/nutzer":
            return self.nutzer_verwalten()
        if pfad == "/api/budget":
            return self.budget_setzen()
        if pfad == "/api/support":
            return self.support_zugang()
        if pfad == "/api/sicherung":
            return self.sicherung_erstellen()
        if pfad == "/api/aktualisieren":
            # Bugfix-Verteilung als Knopf: den Code-Stand des Repos in
            # den Instanzordner kopieren (nur getrackte Dateien - die
            # Daten der Instanz stehen nicht im Git und bleiben
            # unberührt), dann neu starten.
            from .klon import baue
            d = self._rumpf()
            p = _projekt_pfad(d.get("projekt") or "")
            if not p:
                return self._json({"ok": False,
                                   "fehler": "Kein solches Projekt."}, 400)
            lief = wirt.status(p.name) == "laeuft"
            if lief:
                wirt.stoppe(p.name)
            try:
                n = baue(p)
            except Exception as e:
                return self._json({"ok": False, "fehler":
                                   f"{type(e).__name__}: {e}"}, 500)
            finally:
                if lief:
                    wirt.starte(p)
            _log(f"aktualisiert {p.name}: {n} Dateien")
            return self._json({"ok": True, "dateien": n,
                               "laeuft": wirt.laeuft(p)})
        if pfad == "/api/instanz":
            # Der Wirt: Instanzen starten und stoppen ohne Shell. Laeuft
            # eine Instanz als eigener Container (altes Modell), sagt
            # starte() nur "da antwortet schon jemand" und laesst sie.
            d = self._rumpf()
            p = _projekt_pfad(d.get("projekt") or "")
            if not p:
                return self._json({"ok": False,
                                   "fehler": "Kein solches Projekt."}, 400)
            aktion = d.get("aktion")
            if aktion in ("stoppen", "neustart"):
                wirt.stoppe(p.name)
            if aktion in ("starten", "neustart"):
                port = wirt.starte(p)
                if not port:
                    return self._json({"ok": False, "fehler":
                                       "startet nicht - betrieb/port "
                                       "fehlt oder wirt.log ansehen"}, 400)
            _log(f"instanz {p.name}: {aktion}")
            return self._json({"ok": True, "laeuft": wirt.laeuft(p)})
        self._send(404, "text/plain", "nicht gefunden")

    # ------------------------------------------------------ Neues Projekt
    def projekt_anlegen(self):
        d = self._rumpf()
        name = (d.get("name") or "").strip()
        redakteur = (d.get("redakteur") or "").strip()
        passwort = d.get("passwort") or ""
        if not name:
            return self._json({"ok": False, "fehler": "Name fehlt."}, 400)
        if not redakteur or len(passwort) < 8:
            # Ohne Konto ginge die Instanz ohne Anmeldung hinter den
            # Proxy - genau der Zustand, den der Kontenbetrieb verhindert.
            return self._json({"ok": False, "fehler":
                               "Erstes Redakteurskonto mit mindestens "
                               "8 Zeichen Passwort ist Pflicht."}, 400)
        try:
            slug = instanz._slug(name)
        except SystemExit as e:
            return self._json({"ok": False, "fehler": str(e)}, 400)
        if (WURZEL / slug).exists() or slug in LAUFEND:
            return self._json({"ok": False,
                               "fehler": f"{slug} gibt es schon."}, 400)

        # Das hochgeladene GEDCOM zuerst ablegen; instanz.neu kopiert es
        # dann in die Instanz. Base64 im JSON-Rumpf statt Multipart -
        # derselbe schlichte Weg wie überall in der Werkstatt.
        gedcom = None
        if d.get("gedcom_b64"):
            WURZEL.mkdir(parents=True, exist_ok=True)
            gedcom = WURZEL / f".hochgeladen-{slug}.ged"
            try:
                gedcom.write_bytes(base64.b64decode(d["gedcom_b64"]))
            except (binascii.Error, ValueError):
                return self._json({"ok": False,
                                   "fehler": "GEDCOM-Upload unlesbar."}, 400)

        LAUFEND[slug] = "legt an ..."
        _log(f"projekt {slug}: anlegen ({name})")

        def arbeite():
            try:
                ziel = instanz.neu(
                    name, WURZEL, gedcom, redakteur, passwort,
                    melde=lambda z: LAUFEND.update({slug: str(z)}))
                if INSTANZEN:
                    wirt.starte(ziel)
                _log(f"projekt {slug}: fertig")
                del LAUFEND[slug]
            except SystemExit as e:
                LAUFEND[slug] = f"Fehler: {e}"
                _log(f"projekt {slug}: Fehler: {e}")
            except Exception as e:
                LAUFEND[slug] = f"Fehler: {type(e).__name__}: {e}"
                _log(f"projekt {slug}: Fehler: {type(e).__name__}: {e}")
            finally:
                if gedcom and gedcom.exists():
                    gedcom.unlink()

        threading.Thread(target=arbeite, daemon=True,
                         name=f"anlegen-{slug}").start()
        return self._json({"ok": True, "projekt": slug, "gestartet": True})

    # ------------------------------------------------- Konten der Instanz
    def nutzer_verwalten(self):
        """Dieselben Regeln wie /api/nutzer in der Instanz - nur von oben."""
        d = self._rumpf()
        p = _projekt_pfad(d.get("projekt") or "")
        if not p:
            return self._json({"ok": False, "fehler": "Kein solches "
                               "Projekt."}, 400)
        datei = p / "daten" / "nutzer.txt"
        aktion = d.get("aktion")
        name = (d.get("name") or "").strip()
        konten = _nutzer.lade(datei)
        redakteure = [n for n, (_, r) in konten.items() if r == "redakteur"]
        try:
            if aktion == "anlegen":
                pw = d.get("passwort") or ""
                if len(pw) < 8:
                    return self._json({"ok": False, "fehler":
                                       "Mindestens 8 Zeichen."}, 400)
                rolle = d.get("rolle") or "bearbeiter"
                if not konten:
                    rolle = "redakteur"
                _nutzer.anlegen(name, pw, rolle, datei=datei)
            elif aktion == "rolle":
                if (name in redakteure and len(redakteure) == 1
                        and d.get("rolle") != "redakteur"):
                    return self._json({"ok": False, "fehler":
                        "Der letzte Redakteur bleibt Redakteur."}, 400)
                _nutzer.setze_rolle(name, d.get("rolle") or "", datei=datei)
            elif aktion == "weg":
                if name in redakteure and len(redakteure) == 1:
                    return self._json({"ok": False, "fehler":
                        "Der letzte Redakteur lässt sich nicht "
                        "entfernen."}, 400)
                _nutzer.entfernen(name, datei=datei)
            else:
                return self._json({"ok": False,
                                   "fehler": "unbekannte Aktion"}, 400)
        except SystemExit as e:
            return self._json({"ok": False, "fehler": str(e)}, 400)
        _log(f"nutzer {p.name}: {aktion} {name}")
        return self._json({"ok": True, "konten": [
            dict(name=n, rolle=r)
            for n, (_, r) in sorted(_nutzer.lade(datei).items())]})

    # ---------------------------------------------------------- Kontingent
    def budget_setzen(self):
        d = self._rumpf()
        p = _projekt_pfad(d.get("projekt") or "")
        if not p:
            return self._json({"ok": False, "fehler": "Kein solches "
                               "Projekt."}, 400)
        roh = str(d.get("dollar") or "").replace(",", ".").strip()
        if roh:
            try:
                wert = round(float(roh), 2)
                if wert < 0:
                    raise ValueError
            except ValueError:
                return self._json({"ok": False,
                                   "fehler": f"Kein Betrag: {roh}"}, 400)
        db = p / instanz.DB
        if not db.is_file():
            return self._json({"ok": False, "fehler":
                               "Die Instanz hat keine Datenbank."}, 400)
        # Direkt in die Instanz-Datenbank - dieselbe Tabelle, die dort
        # /api/einstellungen bedient. Kein Schema-Lauf: Das Schema gehört
        # der Instanz, das Portal schreibt nur den einen Wert.
        con = sqlite3.connect(db, timeout=10)
        con.row_factory = sqlite3.Row
        try:
            if roh:
                einstellungen.setze(con, kontingent.SCHLUESSEL, wert)
            else:
                con.execute("DELETE FROM einstellung WHERE schluessel=?",
                            (kontingent.SCHLUESSEL,))
                con.commit()
        finally:
            con.close()
        _log(f"budget {p.name}: {roh or 'keines'}")
        return self._json({"ok": True,
                           "budget_dollar": wert if roh else None})


    # ------------------------------------------------------ Support-Zugang
    def support_zugang(self):
        """Der Betreiber-Zugang mit einem Klick.

        Legt in der Instanz das Redakteurskonto `support` mit einem
        Zufallspasswort an - das Passwort wird genau einmal angezeigt.
        Kein stehender Generalschlüssel: Das Konto steht sichtbar in der
        Kontenliste der Instanz, jeder Schritt im portal.log, und nach
        getaner Arbeit nimmt derselbe Knopf es wieder weg.
        """
        import secrets
        d = self._rumpf()
        p = _projekt_pfad(d.get("projekt") or "")
        if not p:
            return self._json({"ok": False,
                               "fehler": "Kein solches Projekt."}, 400)
        datei = p / "daten" / "nutzer.txt"
        konten = _nutzer.lade(datei)
        if d.get("aktion") == "weg":
            if "support" not in konten:
                return self._json({"ok": False,
                                   "fehler": "Kein Support-Zugang da."}, 400)
            redakteure = [n for n, (_, r) in konten.items()
                          if r == "redakteur"]
            if redakteure == ["support"]:
                return self._json({"ok": False, "fehler":
                                   "support ist der einzige Redakteur - "
                                   "erst dem Projekt einen eigenen "
                                   "Redakteur anlegen."}, 400)
            _nutzer.entfernen("support", datei=datei)
            _log(f"support {p.name}: entfernt")
            return self._json({"ok": True, "weg": True})
        # Anlegen oder erneuern - ein frisches Passwort in beiden Fällen.
        passwort = secrets.token_urlsafe(9)
        _nutzer.anlegen("support", passwort, "redakteur", datei=datei)
        _log(f"support {p.name}: angelegt/erneuert")
        return self._json({"ok": True, "name": "support",
                           "passwort": passwort})

    # ----------------------------------------------------------- Sicherung
    def sicherung_erstellen(self):
        d = self._rumpf()
        p = _projekt_pfad(d.get("projekt") or "")
        if not p:
            return self._json({"ok": False,
                               "fehler": "Kein solches Projekt."}, 400)
        try:
            ziel = sicherung.erstellen(p)
        except SystemExit as e:
            return self._json({"ok": False, "fehler": str(e)}, 400)
        weg = sicherung.aufraeumen(p, behalten=10)
        _log(f"sicherung {p.name}: {ziel.name}"
             + (f", {weg} alte entfernt" if weg else ""))
        return self._json({"ok": True, "datei": ziel.name,
                           "sicherungen": sicherung.liste(p)})


def main():
    global WURZEL
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--wurzel", type=Path, default=WURZEL)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--ohne-instanzen", action="store_true",
                    help="nur das Portal - Instanzen laufen anderswo "
                    "(etwa als eigene Container)")
    a = ap.parse_args()
    WURZEL = a.wurzel.expanduser().resolve()
    instanz.WURZEL = WURZEL
    global INSTANZEN
    INSTANZEN = not a.ohne_instanzen
    if not _PASSWORT:
        raise SystemExit(
            "OFB_PORTAL_PASSWORT ist nicht gesetzt.\nDas Portal legt "
            "Projekte und Konten an - ohne eigenes Passwort startet es "
            "nicht.\n  OFB_PORTAL_PASSWORT=... python3 -m werkstatt.portal")
    WURZEL.mkdir(parents=True, exist_ok=True)
    # SIGTERM (docker stop, kill) soll denselben Weg gehen wie Strg-C -
    # sonst überleben die Instanz-Prozesse das Portal als Waisen.
    import signal

    def _ende(*_):
        raise SystemExit
    signal.signal(signal.SIGTERM, _ende)
    if INSTANZEN:
        n = wirt.alle_starten(WURZEL)
        wirt.ueberwachung(WURZEL)
        print(f"Wirt: {n} Instanz(en) gestartet")
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Portal läuft:  http://127.0.0.1:{a.port}    "
          f"Instanzen in {WURZEL}    (Strg-C beendet)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbeendet")
    finally:
        srv.server_close()
        wirt.alle_stoppen()


if __name__ == "__main__":
    main()
