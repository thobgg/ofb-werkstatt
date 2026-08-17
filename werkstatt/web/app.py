#!/usr/bin/env python3
"""Lokaler Webserver: Startbildschirm, Lesen, Korrektur, Übergabe.

    python3 start.py            -> http://127.0.0.1:8765
    python3 start.py --port 9000

Eine Seite je Kopfhaltung des Durchlaufs:

    /               Stand und der nächste Schritt als EIN Knopf
    /lesen          Tranche planen und lesen lassen, mit Fortschritt
    /korrektur      die Maske, eingeschränkt auf die gerade gelesene Runde
    /uebergabe      Probelauf zeigen, auf zweiten Klick schreiben
    /ausgabe        GEDCOM – Fortschreibung oder Neuausgabe
    /einstellungen  Reihenfolge, Seitenzahl, Bildordner, Autopilot

Der Zustand liegt in der Datenbank, nicht im Prozess: Der Läufer arbeitet
im Hintergrund weiter, wenn das Browserfenster zugeht, und ein Abbruch
hinterlässt einen lesbaren Zustand statt eines Rätsels.

Läuft nur auf 127.0.0.1; der Webteil kommt aus der Standardbibliothek,
für Bildvorschauen wird Pillow gebraucht.
Beenden mit Strg-C.
"""
import argparse
import json
import os
import re
import sqlite3
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .seite import SEITE
from .start import STARTSEITE
from .. import (abgleich, ausgabe, db, einrichtung, einstellungen,
                dubletten, gespraech, katalog, nachlesen, perioden,
                spaltenraster,
                import_gedcom,
                import_wortschatz, konfig, lesen,
                runde as _runde,
                pruefung, seiten, suche, testdaten, vorlage)

ROOT = konfig.WURZEL
DB = ROOT / "daten" / "erfassung.sqlite"

# Bedienelemente, die nur am eigenen Rechner Sinn haben. In der
# Vorführinstanz schneidet `_nur_lokal` sie heraus, bevor die Seite
# hinausgeht. Ein Knopf, der beim Drücken 403 sagt, wäre schlechter als
# keiner: Der Besucher hat dann etwas kaputtgemacht, was gar nicht kaputt
# ist.
_MARKE = re.compile(r"<!--nur-lokal-->.*?<!--/nur-lokal-->", re.S)


def _nur_lokal(html):
    return _MARKE.sub("", html) if konfig.demo() else html


# Was ein Fremder in der Vorführinstanz nicht darf. Zwei Gruende, und sie
# sind verschieden:
#
#   *auf fremde Rechnung handeln* – jeder Aufruf, der Claude anruft. Der
#   Weg ueber `vorlage.werkzeug()` ist schon zu, aber der endet in einem
#   Traceback; hier steht stattdessen ein Satz, der den Grund nennt.
#
#   *an den Rechner des Betreibers kommen* – `quelle` und `entpacken`
#   nehmen einen Dateipfad aus dem Aufruf entgegen und lesen ihn,
#   `einrichten` schreibt konfig.toml und richtet die Bildordner neu aus.
#   Am eigenen Rechner ist das genau richtig. Hinter einem Proxy ist es
#   ein Blick in fremde Verzeichnisse.
#
# Bewusst *nicht* gesperrt: speichern, feld, dubletten, perioden,
# uebergib, ausgabe. Das ist die Arbeit, die vorgefuehrt werden soll, und
# sie fasst nur die Datenbank an - die wird stuendlich zurueckgesetzt.
GESPERRT = {
    "/api/beenden": "Der Server lässt sich von hier aus nicht beenden.",
    "/api/lesen-lassen": "Das Lesen ist abgeschaltet; gezeigt werden die "
                         "mitgelieferten Lesungen des Pilotlaufs.",
    "/api/anmelden": "Es wird kein Claude-Konto angemeldet.",
    "/api/nachlesen": "Das zweite Lesen ruft Claude auf und ist abgeschaltet.",
    "/api/frage": "Das Gespräch ruft Claude auf und ist abgeschaltet.",
    "/api/quelle": "Es lassen sich keine Quellen vom Rechner nachladen.",
    "/api/quelle-weg": "Der mitgelieferte Beispielbestand bleibt stehen.",
    "/api/entpacken": "Es lassen sich keine PDF vom Rechner entpacken.",
    "/api/einrichten": "Die Einrichtung steht fest.",
}


# Ein gemeinsames Passwort für die Vorführinstanz, aus der Umgebung.
# Eigentlich gehört Basic Auth an den Proxy – aber der Reverse Proxy der
# Synology kann keine, nur IP-Filter. Bevor die Instanz deshalb offen ins
# Netz geht, prüft sie selbst: ein Passwort, kein Benutzername, keine
# Verwaltung. Das ist keine Anmeldung im Sinne von „was nicht gebaut
# wird" – es ist die Tür, hinter der die Eingeladenen unter sich sind.
_PASSWORT = os.environ.get("OFB_DEMO_PASSWORT", "")


def verbinde():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    return con


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _zutritt(self):
        """Basic Auth, wenn ein Demo-Passwort gesetzt ist. True = weiter."""
        if not (konfig.demo() and _PASSWORT):
            return True
        import base64
        import binascii
        import hmac
        kopf = self.headers.get("Authorization", "")
        if kopf.startswith("Basic "):
            try:
                _, _, kennwort = (base64.b64decode(kopf[6:])
                                  .decode("utf-8").partition(":"))
            except (binascii.Error, UnicodeDecodeError):
                kennwort = ""
            # compare_digest, damit sich das Passwort nicht über die
            # Antwortzeit erraten lässt.
            if hmac.compare_digest(kennwort, _PASSWORT):
                return True
        body = "Zugang nur mit Passwort.".encode("utf-8")
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="OFB-Werkstatt"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return False

    # ------------------------------------------------------------ Technik
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

    @property
    def _frage(self):
        return urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

    def _zahl(self, name):
        v = (self._frage.get(name) or [""])[0].strip()
        return int(v) if v.isdigit() else None

    def _klein(self, ziel, kante):
        """Verkleinerte Fassung, einmal gerechnet und aufgehoben."""
        try:
            from PIL import Image
        except Exception:
            return None
        cache = ROOT / "daten" / "schau"
        cache.mkdir(parents=True, exist_ok=True)
        name = f"{ziel.stem}_{kante}.jpg"
        p = cache / name
        if p.exists() and p.stat().st_mtime >= ziel.stat().st_mtime:
            return p
        try:
            with Image.open(ziel) as im:
                im = im.convert("RGB")
                im.thumbnail((kante, kante))
                im.save(p, quality=85)
        except Exception:
            return None
        return p

    def _rumpf(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    # -------------------------------------------------------------- GET
    def do_GET(self):
        if not self._zutritt():
            return
        pfad = urllib.parse.urlparse(self.path).path
        if pfad in ("/", "/index.html", "/lesen", "/uebergabe", "/ausgabe",
                    "/formular", "/einstellungen"):
            return self._send(200, "text/html; charset=utf-8",
                              _nur_lokal(STARTSEITE))
        if pfad == "/api/gespraech":
            con = db.verbinde()
            try:
                return self._json(gespraech.verlauf(con, self._zahl("eintrag")))
            finally:
                con.close()
        if pfad == "/api/anmeldestand":
            # neu=True: die Antwort wird gemerkt, hier will der Browser aber
            # gerade wissen, ob sich im Anmeldefenster etwas getan hat.
            return self._json(vorlage.bereitschaft(neu=True))
        if pfad == "/api/einstellungen":
            con = db.verbinde()
            try:
                reihe = einstellungen.reihenfolge(con)
                register = []
                for art in reihe:
                    o = einstellungen.ordner(con, art)
                    register.append(dict(
                        register=art,
                        titel=konfig.register(art).get("titel", art),
                        ordner=str(o),
                        vorgabe_ordner=str(konfig.bilderordner(art)),
                        da=o.exists(),
                        bilder=len(seiten.bilder(o)),
                        pdfs=len(seiten.pdfs(o)),
                        entpackt=(o / seiten.ENTPACKT).is_dir(),
                        seiten=einstellungen.seitenzahl(con, art)))
                import os
                modell = einstellungen.wert(con, "ki.modell", lesen.MODELL)
                return self._json(dict(
                    reihenfolge=reihe,
                    alle_register=list(konfig.register()),
                    register=register,
                    autopilot=einstellungen.wert(con, "autopilot"),
                    autopilot_text=einstellungen.AUTOPILOT,
                    grenzen=einstellungen.grenzen(con),
                    pruefgrenzen=[
                        dict(schluessel=k, wert=einstellungen.zahl(
                                 con, f"pruef.{k}", v),
                             vorgabe=v, einheit=e, quelle=q,
                             beschriftung=b, erlaeuterung=x)
                        for k, v, e, q, b, x in pruefung.GRENZWERTE],
                    regeln=[dict(schluessel=k, schwere=s, titel=t)
                            for k, s, t in pruefung.REGELN],
                    aktkarten={a: katalog.uebersicht(a, con)
                               for a in sorted(katalog.KATALOG)},
                    tag_amt=katalog.AMT,
                    pdf_werkzeug=bool(seiten.pdf_werkzeug()),
                    ueber=self.ueber(),
                    demo=konfig.demo(),
                    ki=dict(
                        modell=modell,
                        modelle=lesen.MODELLE,
                        max_kante=int(einstellungen.wert(
                            con, "ki.max_kante", lesen.MAX_KANTE)),
                        max_tokens=int(einstellungen.wert(
                            con, "ki.max_tokens", 8000)),
                        batch=einstellungen.wert(con, "ki.batch", "0") == "1",
                        # Nie den Schlüssel selbst ausliefern – nur ob einer
                        # da ist. In der Vorführinstanz ist keiner da, auch
                        # wenn einer in der Umgebung stünde: Was gesperrt
                        # ist, darf die Maske nicht anbieten.
                        schluessel=(not konfig.demo()
                                    and bool(os.environ.get("ANTHROPIC_API_KEY"))),
                        cli=vorlage.bereitschaft(),
                        verbrauch=self._verbrauch(con, modell)),
                    eigen=einstellungen.alle(con)))
            finally:
                con.close()
        if pfad == "/api/ausgabe":
            con = db.verbinde()
            try:
                ok, meldung, _ = ausgabe.leerlauf(con)
                hid, datei = ausgabe.quelle_id(con)
                d = dict(vorlage=datei, leerlauf=ok, leerlauf_text=meldung)
                if hid:
                    daten, z = ausgabe.fortschreiben(con, schreib=False)
                    d.update(art="fort", zahlen=z, bytes=len(daten))
                else:
                    daten, z = ausgabe.neuausgabe(con, schreib=False)
                    d.update(art="neu", zahlen=z, bytes=len(daten))
                return self._json(d)
            finally:
                con.close()
        if pfad == "/korrektur":
            return self._send(200, "text/html; charset=utf-8",
                              _nur_lokal(SEITE))
        if pfad == "/api/stand":
            return self._json(self.stand())
        if pfad == "/api/fortschritt":
            con = verbinde()
            try:
                rid = self._zahl("runde")
                return self._json(_runde.fortschritt(con, rid) or {})
            finally:
                con.close()
        if pfad == "/api/spaltenraster":
            art = (self._frage.get("register") or [""])[0]
            con = db.verbinde()
            try:
                from . import app as _self          # noqa: F401
                v = spaltenraster.vorschlag(con, art)
                ordner = einstellungen.ordner(con, art)
                bilder = seiten.bilder(ordner)
                erste = bilder[0] if bilder else None
                geo = None
                if erste:
                    from .. import raster as _raster
                    r = _raster.vorschlag(str(erste))
                    geo = dict(groesse=r["groesse"], falz=r["falz"],
                               seiten=[dict(x0=s["x0"], x1=s["x1"],
                                            y0=s["y0"], y1=s["y1"])
                                       for s in r["seiten"]])
                return self._json(dict(
                    register=art, vorschlag=v.get("haelften", []),
                    gespeichert=spaltenraster.hole(con, art),
                    spalten=v.get("spalten") or [],
                    bild=konfig.kurz(erste) if erste else None,
                    geometrie=geo, fehler=v.get("fehler")))
            finally:
                con.close()
        if pfad == "/api/eintraege":
            return self._json(self.eintraege(self._zahl("runde"),
                                             self._frage.get("nur", [""])[0]))
        if pfad == "/api/uebergabe":
            con = db.verbinde()
            try:
                rid = self._zahl("runde")
                return self._json(dict(probe=_runde.uebergib(con, rid, False),
                                       offen=_runde.offen_in_runde(con, rid)))
            finally:
                con.close()
        if pfad == "/api/suche":
            q = self._frage
            return self._json({
                "namen": suche.namen_treffer((q.get("q") or [""])[0]),
                "personen": suche.personen_treffer((q.get("q") or [""])[0],
                                                   sex=(q.get("sex") or [None])[0]),
            })
        if pfad == "/api/anbindung":
            # person.id ist ganzzahlig; aus der URL kommt Text. Ohne die
            # Wandlung greift keine Zuordnung in suche.familien() – sie
            # schlüge stillschweigend fehl statt zu melden.
            v, m = self._zahl("vater"), self._zahl("mutter")
            d = suche.anbindung(v, m)
            d["herkunft_vater"] = suche.herkunft(v) if v else []
            d["herkunft_mutter"] = suche.herkunft(m) if m else []
            return self._json(d)
        if pfad.startswith("/bild/"):
            rel = urllib.parse.unquote(pfad[len("/bild/"):])
            # Nicht `resolve()`: Die Scans liegen ueblicherweise als
            # Symlink im Projekt und in Wirklichkeit woanders – auf einer
            # zweiten Platte, im Archivordner. `resolve()` folgt dem Link,
            # und die Herkunftspruefung schlaegt dann fehl. Die volle Seite
            # kam so nie an; die Seitenschau blieb weiss, und es sah nach
            # einem Problem der Bildgroesse aus.
            #
            # Geprueft wird deshalb der Pfad *ohne* Linkaufloesung, nur
            # normalisiert – das haelt `../` genauso ab, laesst aber
            # Symlinks zu, die der Bearbeiter selbst gelegt hat.
            import os
            ziel = Path(os.path.normpath(str(ROOT / rel)))
            if not str(ziel).startswith(str(ROOT)) or not ziel.is_file():
                return self._send(404, "text/plain", "nicht gefunden")
            typ = ("image/jpeg" if ziel.suffix.lower() in (".jpg", ".jpeg")
                   else "image/png")
            # Die vollen Aufnahmen sind 24 Megapixel. Roh ausgeliefert
            # friert der Browser ein – beim ersten Versuch blieb die
            # Seitenschau weiss und die Bildaufnahme lief in die
            # Zeitgrenze. Also verkleinert, und das Ergebnis gemerkt.
            k = self._zahl("kante")
            if k and k < 8000:
                klein = self._klein(ziel, k)
                if klein:
                    return self._send(200, "image/jpeg", klein.read_bytes())
            return self._send(200, typ, ziel.read_bytes())
        self._send(404, "text/plain", "nicht gefunden")

    # ------------------------------------------------------------- POST
    def do_POST(self):
        if not self._zutritt():
            return
        pfad = urllib.parse.urlparse(self.path).path
        if konfig.demo() and pfad in GESPERRT:
            return self._json(
                {"ok": False, "fehler": "Vorführinstanz: " + GESPERRT[pfad],
                 "meldung": "Vorführinstanz: " + GESPERRT[pfad]}, 403)
        if pfad == "/api/speichern":
            return self.speichern()
        if pfad == "/api/runde/plane":
            d = self._rumpf()
            quelle = d.get("quelle", "api")
            if konfig.demo() and quelle != "testdaten":
                return self._json(
                    {"fehler": "Vorführinstanz: Es wird ausschließlich aus "
                     "den mitgelieferten Lesungen des Pilotlaufs geplant."},
                    403)
            con = db.verbinde()
            try:
                rid = _runde.plane(con, d["register"], int(d.get("seiten", 20)),
                                   quelle)
                _runde.starte(rid)
                return self._json({"runde": rid})
            except SystemExit as e:
                return self._json({"fehler": str(e)}, 400)
            finally:
                con.close()
        if pfad == "/api/beenden":
            # Erst antworten, dann abschalten – sonst bekommt der Browser
            # keine Bestaetigung mehr und zeigt einen Verbindungsfehler,
            # wo alles richtig gelaufen ist. `shutdown()` muss aus einem
            # anderen Faden kommen: Es wartet auf das Ende der Schleife,
            # in der dieser Aufruf gerade steckt.
            import threading
            self._json({"ok": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if pfad == "/api/anmelden":
            return self._json(vorlage.anmelden())
        if pfad == "/api/lesen-lassen":
            d = self._rumpf()
            rid = int(d["runde"])
            # Im Hintergrund, sonst haengt der Browser an einer Sitzung, die
            # Minuten dauern kann.
            import threading

            def arbeite():
                c = db.verbinde()
                try:
                    vorlage.lesen_lassen(c, rid, still=True, zeitlimit=7200)
                    _runde.lauf(rid)
                finally:
                    c.close()
            threading.Thread(target=arbeite, daemon=True,
                             name=f"lesen-{rid}").start()
            return self._json({"ok": True, "gestartet": True})
        if pfad == "/api/einlesen":
            d = self._rumpf()
            rid = int(d["runde"])
            import threading
            threading.Thread(target=_runde.lauf, args=(rid,), daemon=True,
                             name=f"einlesen-{rid}").start()
            return self._json({"ok": True, "gestartet": True})
        if pfad == "/api/runde/uebergib":
            d = self._rumpf()
            con = db.verbinde()
            try:
                z = _runde.uebergib(con, int(d["runde"]), True)
                return self._json({"ok": True, "zahlen": z})
            finally:
                con.close()
        if pfad == "/api/ausgabe":
            d = self._rumpf()
            con = db.verbinde()
            try:
                hid, _ = ausgabe.quelle_id(con)
                neu = d.get("art") == "neu" or hid is None
                daten, z = (ausgabe.neuausgabe if neu
                            else ausgabe.fortschreiben)(con, schreib=True)
                name = d.get("datei") or (
                    f"{konfig.konfig().get('gemeinde', {}).get('name', 'OFB')}"
                    + ("_neuausgabe" if neu else "_fortgeschrieben") + ".ged")
                ziel = (ROOT / "ausgabe" / Path(name).name)
                ziel.parent.mkdir(parents=True, exist_ok=True)
                ziel.write_bytes(daten)
                return self._json(dict(ok=True, datei=str(
                    ziel.relative_to(ROOT)), bytes=len(daten), zahlen=z))
            finally:
                con.close()
        if pfad == "/api/einstellungen":
            d = self._rumpf()
            if konfig.demo() and any(
                    k.startswith("ordner.") for k in (d.get("werte") or {})):
                # Die übrigen Einstellungen sind Datenbankwerte und der
                # stündliche Rücksetzer räumt sie ab. `ordner.*` ist ein
                # Pfad: Die Blockschneider legen Ausschnitte daraus unter
                # der Projektwurzel ab, wo `/bild/` sie ausliefert – ein
                # umgebogener Ordner machte so beliebige Bilder vom
                # Rechner des Betreibers sichtbar.
                return self._json(
                    {"ok": False, "fehler": "Vorführinstanz: Die Bildordner "
                     "stehen fest."}, 403)
            con = db.verbinde()
            try:
                for k, v in (d.get("werte") or {}).items():
                    if v in (None, ""):
                        con.execute("DELETE FROM einstellung WHERE schluessel=?",
                                    (k,))
                        con.commit()
                    else:
                        einstellungen.setze(con, k, v)
                return self._json({"ok": True})
            finally:
                con.close()
        if pfad == "/api/einrichten":
            d = self._rumpf()
            try:
                einrichtung.schreibe(
                    (d.get("gemeinde") or "").strip(),
                    d.get("register") or [], (d.get("ort") or "").strip() or None,
                    (d.get("religion") or "").strip() or None)
            except SystemExit as e:
                return self._json({"fehler": str(e)}, 400)
            except Exception as e:
                return self._json({"fehler": f"{type(e).__name__}: {e}"}, 400)
            # Die Bildordner anlegen, damit der erste Blick nicht auf
            # "Ordner fehlt" faellt – leer ist kein Fehler, fehlend schon.
            # Den Beispielbestand einlesen, wenn gewuenscht. Ohne ihn
            # bleibt in der Demo alles gelb, und der Anker – der Kern des
            # Verfahrens – ist nicht zu sehen.
            if d.get("bestand"):
                b = einrichtung.beispielbestand()
                if b:
                    con = db.verbinde()
                    try:
                        import_gedcom.importiere(b, con, still=True)
                        con.execute(
                            "UPDATE herkunft SET gilt='beleg', name=? "
                            "WHERE art='gedcom' AND datei=?",
                            ("Auszug OFB Haberschlacht (Beispiel)",
                             Path(b).name))
                        con.commit()
                        db.kontext_anwenden(con)
                    finally:
                        con.close()
            # Die abgewaehlten Felder gleich beim Anlegen festhalten. Wer
            # sie erst nach der ersten Runde abschaltet, hat sie schon
            # gelesen und muss die Werte einzeln wieder loswerden.
            con = db.verbinde()
            try:
                for art, namen in (d.get("felder_aus") or {}).items():
                    for n in namen:
                        katalog.setze(con, art, n, aktiv=0)
            finally:
                con.close()
            for r in d.get("register") or []:
                o = Path((r.get("ordner") or "").strip()).expanduser()
                if r.get("ordner"):
                    (o if o.is_absolute() else ROOT / o).mkdir(
                        parents=True, exist_ok=True)
            # Die Spaltenueberschriften der Beispielseiten uebernehmen,
            # damit die Kopfzeile in der Maske nicht leer bleibt. Das
            # Segmentieren fragt sonst das Modell, und die Demo laeuft
            # ohne Schluessel.
            con = db.verbinde()
            try:
                for r in d.get("register") or []:
                    if r.get("art"):
                        perioden.aus_testdaten(con, r["art"])
            except Exception:
                pass
            finally:
                con.close()
            return self._json(dict(ok=True))
        if pfad == "/api/spaltenraster":
            d = self._rumpf()
            con = db.verbinde()
            try:
                n = spaltenraster.merke(con, d["register"],
                                        d.get("haelften") or [])
                return self._json({"ok": True, "linien": n})
            finally:
                con.close()
        if pfad == "/api/perioden":
            d = self._rumpf()
            con = db.verbinde()
            try:
                # Das Modell liest nur die gedruckten Koepfe, nicht die
                # Seiten. Trotzdem im Hintergrund, weil ein Register bis zu
                # 17 Stichproben hat und der Browser sonst wartet.
                import threading
                art = d.get("register")

                def arbeite():
                    c = db.verbinde()
                    try:
                        perioden.pruefe(c, art, still=True)
                    except Exception:
                        pass
                    finally:
                        c.close()
                threading.Thread(target=arbeite, daemon=True).start()
                return self._json(dict(ok=True, laeuft=art))
            finally:
                con.close()
        if pfad == "/api/dubletten":
            d = self._rumpf()
            con = db.verbinde()
            try:
                if d.get("bild"):
                    dubletten.entscheide(con, d["bild"],
                                         bool(d.get("dublette")))
                    return self._json(dict(ok=True))
                return self._json(dubletten.pruefe(
                    con, d.get("register"), still=True))
            finally:
                con.close()
        if pfad == "/api/feld":
            d = self._rumpf()
            con = db.verbinde()
            try:
                art, name = d.get("art"), (d.get("name") or "").strip()
                if art not in katalog.KATALOG or not name:
                    return self._json({"fehler": "Aktart und Name nötig"}, 400)
                if not re.fullmatch(r"[a-z0-9_]{2,40}", name):
                    return self._json({"fehler": (
                        "Feldname: nur Kleinbuchstaben, Ziffern und "
                        "Unterstrich – er wird zum Schlüssel in der "
                        "Datenbank und im Leseauftrag.")}, 400)
                katalog.setze(con, art, name,
                              **{k: v for k, v in d.items()
                                 if k not in ("art", "name")})
                return self._json(dict(ok=True))
            finally:
                con.close()
        if pfad == "/api/feld-leeren":
            d = self._rumpf()
            con = db.verbinde()
            try:
                n = katalog.leeren(con, d.get("art"), d.get("name"))
                return self._json(dict(ok=True, geloescht=n))
            finally:
                con.close()
        if pfad == "/api/feld-weg":
            d = self._rumpf()
            con = db.verbinde()
            try:
                katalog.zuruecksetzen(con, d.get("art"), d.get("name"))
                return self._json(dict(ok=True))
            finally:
                con.close()
        if pfad == "/api/nachlesen":
            d = self._rumpf()
            con = db.verbinde()
            try:
                return self._json(nachlesen.vergleiche(
                    con, int(d["eintrag"])))
            except Exception as e:
                return self._json({"ok": False,
                                   "meldung": f"{type(e).__name__}: {e}"}, 400)
            finally:
                con.close()
        if pfad == "/api/frage":
            d = self._rumpf()
            con = db.verbinde()
            try:
                return self._json(gespraech.frage(
                    con, int(d["eintrag"]), (d.get("frage") or "").strip()))
            except Exception as e:
                return self._json({"ok": False,
                                   "antwort": f"{type(e).__name__}: {e}"}, 400)
            finally:
                con.close()
        if pfad == "/api/quelle":
            d = self._rumpf()
            con = db.verbinde()
            try:
                p = Path((d.get("datei") or "").strip()).expanduser()
                if not p.exists():
                    return self._json({"fehler": f"{p} gibt es nicht"}, 400)
                if d.get("art") == "gedcom":
                    hid = import_gedcom.importiere(str(p), con, still=True)
                    con.execute(
                        "UPDATE herkunft SET gilt=?, name=?, parochien=? "
                        "WHERE id=?",
                        (d.get("gilt") if d.get("gilt") in ("beleg",
                                                            "vokabular")
                         else "vokabular",
                         (d.get("name") or "").strip() or p.name,
                         (d.get("parochien") or "").strip() or None, hid))
                else:
                    hid = import_wortschatz.importiere(
                        str(p), con, name=(d.get("name") or "").strip() or None,
                        still=True)
                con.commit()
                # Ohne das rankt der laufende Server bis zum Neustart nach
                # dem alten Stand, und die frisch eingelesene Quelle wirkt
                # scheinbar nicht.
                suche.frisch()
                # Was schon gelesen und noch nicht bestätigt ist, bekommt
                # die neue Quelle nachträglich zu sehen. Bestätigte
                # Einträge bleiben unberührt – eine Entscheidung des
                # Bearbeiters darf ein Import nicht überschreiben.
                z = abgleich.runde_pruefen(con, nur_offen=True)
                return self._json(dict(ok=True, herkunft=hid, neu_geprueft=z))
            except SystemExit as e:
                return self._json({"fehler": str(e)}, 400)
            except Exception as e:
                return self._json({"fehler": f"{type(e).__name__}: {e}"}, 400)
            finally:
                con.close()
        if pfad == "/api/quelle-weg":
            d = self._rumpf()
            con = db.verbinde()
            try:
                hid = int(d["herkunft"])
                r = con.execute("SELECT art, datei FROM herkunft WHERE id=?",
                                (hid,)).fetchone()
                if not r:
                    return self._json({"fehler": "gibt es nicht"}, 400)
                # Die eigene Erfassung ist kein Import, sondern das Ergebnis
                # der Arbeit. Sie zu loeschen wuerde bestaetigte Eintraege
                # mitnehmen.
                if r["art"] == "erfassung":
                    return self._json(
                        {"fehler": "Die eigene Erfassung bleibt"}, 400)
                # Eine Quelle, an der schon Entscheidungen haengen, darf
                # nicht verschwinden – sonst zeigen bestaetigte Felder ins
                # Leere und die Uebergabe faende die Person nicht mehr.
                haengt = con.execute(
                    "SELECT count(*) FROM feld f JOIN person p ON p.id=f.person "
                    "WHERE p.herkunft=?", (hid,)).fetchone()[0]
                if haengt:
                    return self._json({"fehler": (
                        f"{haengt} bestätigte Felder zeigen auf diese Quelle. "
                        "Erst die betroffenen Runden verwerfen.")}, 400)
                con.execute("DELETE FROM ereignis WHERE person IN "
                            "(SELECT id FROM person WHERE herkunft=?)", (hid,))
                con.execute("DELETE FROM kind WHERE person IN "
                            "(SELECT id FROM person WHERE herkunft=?)", (hid,))
                con.execute("DELETE FROM familie WHERE herkunft=?", (hid,))
                con.execute("DELETE FROM person WHERE herkunft=?", (hid,))
                con.execute("DELETE FROM herkunft WHERE id=?", (hid,))
                con.commit()
                suche.frisch()
                z = abgleich.runde_pruefen(con, nur_offen=True)
                return self._json(dict(ok=True, datei=r["datei"],
                                       neu_geprueft=z))
            finally:
                con.close()
        if pfad == "/api/entpacken":
            d = self._rumpf()
            con = db.verbinde()
            try:
                art = d.get("register")
                z = seiten.entpacken(einstellungen.ordner(con, art), still=True)
                return self._json(dict(ok="fehler" not in z, zahlen=z))
            finally:
                con.close()
        if pfad == "/api/abgleich":
            d = self._rumpf()
            con = db.verbinde()
            try:
                return self._json(abgleich.runde_pruefen(con, d.get("runde")))
            finally:
                con.close()
        self._send(404, "text/plain", "nicht gefunden")

    # ------------------------------------------------------------- Daten
    def ueber(self):
        """Was die Über-Seite zeigt – Stand aus der Datenbank, nicht aus Text.

        Zahlenstände gehören in die Datenbank, nicht in Markdown, sonst
        veralten sie unbemerkt (Regel aus doku/landkarte.md). Das gilt für
        eine Über-Seite genauso.
        """
        import subprocess
        con = db.verbinde()
        try:
            stand = db.stand(con)
            fassung = {}
            try:
                g = subprocess.run(
                    ["git", "log", "-1", "--format=%h|%ad|%s", "--date=short"],
                    cwd=ROOT, capture_output=True, text=True, timeout=5)
                if g.returncode == 0 and "|" in g.stdout:
                    h, d, s = g.stdout.strip().split("|", 2)
                    n = subprocess.run(["git", "rev-list", "--count", "HEAD"],
                                       cwd=ROOT, capture_output=True,
                                       text=True, timeout=5).stdout.strip()
                    fassung = dict(commit=h, datum=d, betreff=s, anzahl=n)
            except Exception:
                pass
            quellen = [dict(r) for r in con.execute(
                "SELECT COALESCE(name, datei) AS name, art, gilt, parochien, "
                "(SELECT count(*) FROM person p WHERE p.herkunft=herkunft.id) n "
                "FROM herkunft ORDER BY gilt, id")]
            doku = sorted(p.name for p in (ROOT / "doku").glob("*.md"))
            return dict(
                name="OFB-Werkstatt",
                zweck="Ortsfamilienbuch aus Kirchenbüchern: Seite lesen "
                      "lassen, gegen den Bestand abgleichen, anbinden oder "
                      "neu anlegen, als GEDCOM ausgeben.",
                lizenz="MIT", autor="Thomas Bugge",
                fassung=fassung,
                gemeinde=konfig.konfig().get("gemeinde", {}).get("name", "–"),
                bestand=stand,
                quellen=quellen,
                doku=doku,
                wurzel=str(ROOT),
                datenbank=str(DB.relative_to(ROOT)),
                eingerichtet=einrichtung.eingerichtet(),
                einrichtung=einrichtung.vorschlag(),
                felder=einrichtung.feldvorschlag(),
                beispielbestand=einrichtung.beispielbestand(),
                aufwand=self._aufwand(con),
                dubletten=dubletten.gemeldet(con),
                perioden=perioden.gemeldet(con),
                haende={a: perioden.haende(con, a)
                        for a in konfig.register()},
                testdaten=len(testdaten.seiten()),
                pdf_werkzeug=bool(seiten.pdf_werkzeug()),
            )
        finally:
            con.close()

    def _aufwand(self, con):
        """Wie viel Arbeit die Eintraege gemacht haben – je Register.

        Der ehrlichere Massstab als eine Trefferquote: Eine Quote misst
        das Buch, diese Zahlen messen das Werkzeug. Sie fallen beim
        Arbeiten an, ohne dass jemand eine geprueft Wahrheit
        danebenlegen muesste.
        """
        try:
            rows = list(con.execute(
                "SELECT e.register, count(*) n, "
                "SUM(a.tasten) t, SUM(a.klicks) k, SUM(a.sekunden) s "
                "FROM aufwand a JOIN eintrag e ON e.id=a.eintrag "
                "GROUP BY e.register"))
        except Exception:
            return []
        z = []
        for r in rows:
            n = r["n"] or 1
            z.append(dict(register=r["register"], eintraege=r["n"],
                          tasten=r["t"] or 0, klicks=r["k"] or 0,
                          sekunden=r["s"] or 0,
                          tasten_je=round((r["t"] or 0) / n),
                          klicks_je=round((r["k"] or 0) / n),
                          sekunden_je=round((r["s"] or 0) / n)))
        return z

    def _verbrauch(self, con, modell):
        """Was bisher tatsächlich verbraucht wurde – aus den Aufträgen.

        Geschätzte Kosten stehen in jeder Doku; gemessene nirgends. Die
        Auftragstabelle zählt die Token ohnehin mit, also wird hier
        gerechnet statt vermutet.
        """
        z = []
        for q in ("api", "datei"):
            r = con.execute(
                "SELECT COALESCE(SUM(tokens_ein),0) e, "
                "COALESCE(SUM(tokens_aus),0) a, COALESCE(SUM(tokens_cache),0) c, "
                "COALESCE(SUM(dollar),0) d, COALESCE(SUM(seiten_fertig),0) s, "
                "COALESCE(SUM(dauer_ms),0) ms FROM auftrag "
                "WHERE COALESCE(quelle,'api')=? AND (tokens_ein>0 OR dollar>0)",
                (q,)).fetchone()
            if not (r["e"] or r["d"]):
                continue
            # Ueber die API rechnen wir aus Token und Preisliste, ueber die
            # Sitzung meldet `claude -p` den Betrag selbst. Beides ist
            # gemessen, keins geschaetzt – aber nur der erste wird auch
            # berechnet. Der zweite sagt, was derselbe Lauf gekostet haette.
            d = r["d"] or (lesen.kosten(modell, r["e"], r["a"]) or 0.0)
            z.append(dict(
                quelle=q, tokens_ein=r["e"], tokens_aus=r["a"],
                tokens_cache=r["c"], seiten=r["s"], dollar=round(d, 4),
                minuten=round(r["ms"] / 60000, 1) if r["ms"] else None,
                je_seite=round(d / r["s"], 4) if r["s"] else None,
                bezahlt=q == "api"))
        gesamt = sum(x["dollar"] for x in z)
        seiten = sum(x["seiten"] for x in z)
        return dict(wege=z, dollar=round(gesamt, 4), seiten=seiten,
                    tokens_ein=sum(x["tokens_ein"] for x in z),
                    tokens_aus=sum(x["tokens_aus"] for x in z),
                    je_seite=round(gesamt / seiten, 4) if seiten else None)

    def stand(self):
        con = db.verbinde()
        try:
            r = _runde.offene_runde(con)
            quelle = r["quelle"] if r else ("testdaten" if testdaten.vorhanden()
                                            else "api")
            v = _runde.vorschlag(con, quelle)
            k = konfig.konfig().get("gemeinde", {})
            quellen = []
            for h in con.execute(
                    "SELECT h.id, h.art, h.datei, h.gilt, h.parochien, h.name, "
                    "(SELECT count(*) FROM person p WHERE p.herkunft=h.id) n, "
                    "(SELECT count(*) FROM wortschatz w WHERE w.herkunft=h.id) "
                    "woerter "
                    "FROM herkunft h ORDER BY h.gilt, h.id"):
                quellen.append(dict(h))
            # Eingetragen heisst nicht eingelesen. Eine Quelle, die in
            # konfig.toml steht und nie importiert wurde, wirkt nicht – und
            # das sah man bisher nirgends, weil die Tabelle nur zeigt, was
            # schon in der Datenbank liegt.
            drin = {Path(q["datei"] or "").name for q in quellen}
            fehlend = [dict(name=q["name"], art=q["art"], datei=q["datei"],
                            gilt=q["gilt"],
                            liest_wer=(
                                "import_gedcom" if q["art"] == "gedcom" else
                                "import_wortschatz" if q["art"] in (
                                    "wortschatz", "csv", "tsv", "txt",
                                    "xlsx", "ods", "docx") else None))
                       for q in konfig.kontext()
                       if q["datei"] and Path(q["datei"]).name not in drin]
            return dict(
                gemeinde=k.get("name", "–"),
                register=_runde.stand(con),
                quellen=quellen,
                quellen_fehlend=fehlend,
                eingerichtet=einrichtung.eingerichtet(),
                einrichtung=einrichtung.vorschlag(),
                felder=einrichtung.feldvorschlag(),
                beispielbestand=einrichtung.beispielbestand(),
                aufwand=self._aufwand(con),
                dubletten=dubletten.gemeldet(con),
                perioden=perioden.gemeldet(con),
                haende={a: perioden.haende(con, a)
                        for a in konfig.register()},
                testdaten=len(testdaten.seiten()),
                runde=r,
                vorschlag=v,
                fortschritt=_runde.fortschritt(con, r["id"]) if r else None,
                vorlage=(vorlage.stand(con, r["id"])
                         if r and r["quelle"] == "datei" else None),
                # Nur anbieten, wenn auch angemeldet – ein installiertes,
                # aber unangemeldetes Claude Code liest keine Seite. None
                # heisst "nicht feststellbar" und zaehlt als anbieten.
                claude_code=vorlage.bereitschaft()["angemeldet"] is not False,
                demo=konfig.demo(),
                offen=_runde.offen_in_runde(con, r["id"]) if r else None,
                bestand=db.stand(con),
            )
        finally:
            con.close()

    def eintraege(self, runde_id=None, nur=""):
        con = verbinde()
        raus = []
        spalten = {}                 # je Seite einmal nachschlagen, nicht je Eintrag
        wo, par = "1=1", []
        if runde_id:
            wo, par = "runde=?", [runde_id]
        for e in con.execute(
                f"SELECT * FROM eintrag WHERE {wo} ORDER BY register, bild, "
                "CAST(nr AS INTEGER), nr", par):
            # Der Titel kommt aus der Aktkarte. Ohne ihn stand in der Maske
            # `braeutigam_beruf` – klein, mit Unterstrichen, und der
            # Bearbeiter musste sich den Feldnamen des Programms merken.
            def titel(n):
                x = katalog.feld(e["register"], n)
                if x and x.titel:
                    return x.titel
                return " ".join(w.capitalize() for w in n.split("_"))

            def art(n):
                """Was die Maske ueber das Feld wissen muss."""
                x = katalog.feld(e["register"], n)
                if not x:
                    return dict(kb=True, verweis=False, hinweis=None)
                return dict(kb=bool(x.kb), verweis=katalog.ist_verweis(x),
                            hinweis=x.hinweis)

            felder = [dict(name=f["name"], titel=titel(f["name"]),
                           **art(f["name"]),
                           wert=f["korrigiert"] if f["korrigiert"] is not None
                           else f["gelesen"],
                           kb_form=f["kb_form"], beleg=f["beleg"],
                           person=f["person"], status=f["status"],
                           ampel=f["ampel"], zuversicht=f["zuversicht"],
                           rolle=f["rolle"], entscheidung=f["entscheidung"])
                      for f in con.execute(
                          "SELECT * FROM feld WHERE eintrag_id=? "
                          "ORDER BY reihe, id", (e["id"],))]
            # Felder ohne Zeile ergaenzen. Eine Zeile entsteht nur, wenn
            # das Modell das Feld geliefert hat – was es nicht liefert,
            # hatte in der Maske keinen Ort, und der Mädchenname liess sich
            # nicht nachtragen, obwohl die Aktkarte ihn fuehrt.
            da = {f["name"] for f in felder}
            for name in konfig.felder(e["register"], con):
                if name not in da:
                    felder.append(dict(
                        name=name, titel=titel(name), **art(name), wert=None,
                        kb_form=None, beleg=None,
                        person=None, status="gelesen", ampel="grau",
                        zuversicht=None, rolle=_runde._rolle(e["register"],
                                                             name),
                        entscheidung="offen"))
            if nur == "offen" and e["status"] == "bestaetigt":
                continue
            raus.append(dict(id=e["id"], register=e["register"], band=e["band"],
                             bild=e["bild"], nr=e["nr"], jahr=e["jahr"],
                             ausschnitt=e["ausschnitt"], status=e["status"],
                             kasten=(e["kasten"] if "kasten" in e.keys()
                                     else None),
                             seite=(e["seite"] if "seite" in e.keys()
                                    else None),
                             kopf=(e["kopf"] if "kopf" in e.keys() else None),
                             # "Zeilenraster unsicher" stand bisher nur in
                             # der Datenbank. Der Streifen sieht dann
                             # trotzdem ordentlich aus - er ist ja gleich
                             # hoch geschnitten -, und niemand konnte
                             # wissen, dass die Grenzen geraten sind.
                             bemerkung=(e["bemerkung"]
                                        if "bemerkung" in e.keys() else None),
                             spalten=spalten.setdefault(
                                 (e["register"], e["bild"]),
                                 perioden.zur_seite(con, e["register"],
                                                    e["bild"])),
                             runde=e["runde"], felder=felder))
        con.close()
        return raus

    def speichern(self):
        d = self._rumpf()
        con = verbinde()
        try:
            # Wie viel Arbeit dieser Eintrag gemacht hat. Faellt beim
            # Arbeiten an; niemand muss dafuer etwas tun.
            a = d.get("aufwand")
            if a and d.get("bestaetigt"):
                from datetime import datetime, timezone
                geaendert = sum(
                    1 for n, v in (d.get("felder") or {}).items()
                    if (v.get("wert") or "").strip())
                con.execute(
                    "INSERT INTO aufwand (eintrag, tasten, klicks, sekunden, "
                    "felder, beendet) VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(eintrag) DO UPDATE SET "
                    " tasten=tasten+excluded.tasten, "
                    " klicks=klicks+excluded.klicks, "
                    " sekunden=sekunden+excluded.sekunden, "
                    " felder=excluded.felder, beendet=excluded.beendet",
                    (d["id"], int(a.get("tasten") or 0),
                     int(a.get("klicks") or 0), int(a.get("sekunden") or 0),
                     geaendert,
                     datetime.now(timezone.utc).isoformat(timespec="seconds")))
            for name, v in d.get("felder", {}).items():
                row = con.execute(
                    "SELECT id, gelesen, status FROM feld "
                    "WHERE eintrag_id=? AND name=?", (d["id"], name)).fetchone()
                if not row:
                    # Erst beim Schreiben entstehen: Wer ein Feld
                    # nachtraegt, das die Lesung nicht geliefert hat, soll
                    # es eintragen koennen – nicht ins Leere tippen.
                    con.execute(
                        "INSERT OR IGNORE INTO feld (eintrag_id, name, reihe) "
                        "VALUES (?,?,99)", (d["id"], name))
                    row = con.execute(
                        "SELECT id, gelesen, status FROM feld "
                        "WHERE eintrag_id=? AND name=?",
                        (d["id"], name)).fetchone()
                    if not row:
                        continue
                wert = (v.get("wert") or "").strip()
                korr = None if wert == (row["gelesen"] or "") else wert
                status = "bestaetigt" if d.get("bestaetigt") else row["status"]
                ents = v.get("entscheidung")
                pers = v.get("person")
                # Die Kirchenbuchform nur anfassen, wenn die Maske sie
                # ueberhaupt geschickt hat. Felder ohne rechte Spalte
                # schicken keine - und ein `kb: null` loeschte sonst eine
                # vorhandene Form, die niemand angefasst hat.
                sql = "UPDATE feld SET korrigiert=?, status=?"
                par = [korr, status]
                if "kb" in v and v["kb"] is not None:
                    sql += ", kb_form=?"
                    par.append((v.get("kb") or "").strip() or None)
                if ents:
                    sql += ", entscheidung=?"
                    par.append(ents)
                if pers is not None:
                    sql += ", person=?"
                    par.append(int(pers) if str(pers).strip().isdigit() else None)
                # Was ein Mensch bestätigt hat, ist grün – unabhängig davon,
                # was der Abgleich vorher gefunden hat.
                if d.get("bestaetigt"):
                    sql += ", ampel='gruen'"
                con.execute(sql + " WHERE id=?", par + [row["id"]])
            if d.get("bestaetigt"):
                con.execute("UPDATE eintrag SET status='bestaetigt' WHERE id=?",
                            (d["id"],))
            con.commit()
        finally:
            con.close()
        self._send(200, "application/json", b'{"ok":true}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    if not DB.exists():
        print("daten/erfassung.sqlite fehlt – erst python3 -m werkstatt.db --init")
        return
    # Threading, damit ein langsamer Aufruf nicht die ganze Oberflaeche
    # anhaelt. Gemessen ist das Laden der Bildstreifen *nicht* das Problem
    # – 20 Streifen brauchen ueber die Loopback-Schnittstelle 20 ms, ob
    # nacheinander oder parallel. Es geht um die wenigen Aufrufe, die
    # wirklich dauern: das erste Verkleinern einer 24-MP-Seite (0,4 s) und
    # der GEDCOM-Probelauf. Waehrend die liefen, stand alles still.
    #
    # Jede Anfrage oeffnet ihre eigene Datenbankverbindung, deshalb
    # vertraegt sich das; gegen gleichzeitige Schreibvorgaenge steht die
    # Wartezeit in db.verbinde().
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Werkstatt läuft:  http://127.0.0.1:{a.port}    (Strg-C beendet)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbeendet")
    else:
        # serve_forever kehrt nur zurueck, wenn shutdown() gerufen wurde –
        # also ueber den Knopf in der Oberflaeche.
        print("beendet – über die Werkstatt geschlossen")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
