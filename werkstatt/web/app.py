#!/usr/bin/env python3
"""Lokaler Webserver: Startbildschirm, Lesen, Korrektur, Übergabe.

    python3 start.py            -> http://127.0.0.1:8765
    python3 start.py --port 9000

Eine Seite je Kopfhaltung des Durchlaufs:

    /               Stand und der nächste Schritt als EIN Knopf
    /lesen          Tranche planen und lesen lassen, mit Fortschritt
    /korrektur      die Maske, eingeschränkt auf die gerade gelesene Runde
    /uebergabe      Probelauf zeigen, auf zweiten Klick schreiben
    /ausgabe        GEDCOM — Fortschreibung oder Neuausgabe
    /einstellungen  Reihenfolge, Seitenzahl, Bildordner, Autopilot

Der Zustand liegt in der Datenbank, nicht im Prozess: Der Läufer arbeitet
im Hintergrund weiter, wenn das Browserfenster zugeht, und ein Abbruch
hinterlässt einen lesbaren Zustand statt eines Rätsels.

Läuft nur auf 127.0.0.1, keine Abhängigkeiten außer der Standardbibliothek.
Beenden mit Strg-C.
"""
import argparse
import json
import re
import sqlite3
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .seite import SEITE
from .start import STARTSEITE
from .. import (abgleich, ausgabe, db, einrichtung, einstellungen,
                dubletten, gespraech, katalog, perioden,
                import_gedcom,
                import_wortschatz, konfig, lesen,
                runde as _runde,
                pruefung, seiten, suche, testdaten, vorlage)

ROOT = konfig.WURZEL
DB = ROOT / "daten" / "erfassung.sqlite"


def verbinde():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

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

    def _rumpf(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    # -------------------------------------------------------------- GET
    def do_GET(self):
        pfad = urllib.parse.urlparse(self.path).path
        if pfad in ("/", "/index.html", "/lesen", "/uebergabe", "/ausgabe",
                    "/formular", "/einstellungen"):
            return self._send(200, "text/html; charset=utf-8", STARTSEITE)
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
                    ki=dict(
                        modell=modell,
                        modelle=lesen.MODELLE,
                        max_kante=int(einstellungen.wert(
                            con, "ki.max_kante", lesen.MAX_KANTE)),
                        max_tokens=int(einstellungen.wert(
                            con, "ki.max_tokens", 8000)),
                        batch=einstellungen.wert(con, "ki.batch", "0") == "1",
                        # Nie den Schlüssel selbst ausliefern — nur ob einer da ist.
                        schluessel=bool(os.environ.get("ANTHROPIC_API_KEY")),
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
            return self._send(200, "text/html; charset=utf-8", SEITE)
        if pfad == "/api/stand":
            return self._json(self.stand())
        if pfad == "/api/fortschritt":
            con = verbinde()
            try:
                rid = self._zahl("runde")
                return self._json(_runde.fortschritt(con, rid) or {})
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
            # Wandlung greift keine Zuordnung in suche.familien() — sie
            # schlüge stillschweigend fehl statt zu melden.
            v, m = self._zahl("vater"), self._zahl("mutter")
            d = suche.anbindung(v, m)
            d["herkunft_vater"] = suche.herkunft(v) if v else []
            d["herkunft_mutter"] = suche.herkunft(m) if m else []
            return self._json(d)
        if pfad.startswith("/bild/"):
            rel = urllib.parse.unquote(pfad[len("/bild/"):])
            ziel = (ROOT / rel).resolve()
            if not str(ziel).startswith(str(ROOT.resolve())) or not ziel.is_file():
                return self._send(404, "text/plain", "nicht gefunden")
            typ = ("image/jpeg" if ziel.suffix.lower() in (".jpg", ".jpeg")
                   else "image/png")
            return self._send(200, typ, ziel.read_bytes())
        self._send(404, "text/plain", "nicht gefunden")

    # ------------------------------------------------------------- POST
    def do_POST(self):
        pfad = urllib.parse.urlparse(self.path).path
        if pfad == "/api/speichern":
            return self.speichern()
        if pfad == "/api/runde/plane":
            d = self._rumpf()
            con = db.verbinde()
            try:
                rid = _runde.plane(con, d["register"], int(d.get("seiten", 20)),
                                   d.get("quelle", "api"))
                _runde.starte(rid)
                return self._json({"runde": rid})
            except SystemExit as e:
                return self._json({"fehler": str(e)}, 400)
            finally:
                con.close()
        if pfad == "/api/beenden":
            # Erst antworten, dann abschalten — sonst bekommt der Browser
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
            # "Ordner fehlt" faellt — leer ist kein Fehler, fehlend schon.
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
            return self._json(dict(ok=True))
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
                        "Unterstrich — er wird zum Schlüssel in der "
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
                # Einträge bleiben unberührt — eine Entscheidung des
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
                # nicht verschwinden — sonst zeigen bestaetigte Felder ins
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
        """Was die Über-Seite zeigt — Stand aus der Datenbank, nicht aus Text.

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
                gemeinde=konfig.konfig().get("gemeinde", {}).get("name", "—"),
                bestand=stand,
                quellen=quellen,
                doku=doku,
                wurzel=str(ROOT),
                datenbank=str(DB.relative_to(ROOT)),
                eingerichtet=einrichtung.eingerichtet(),
                einrichtung=einrichtung.vorschlag(),
                felder=einrichtung.feldvorschlag(),
                dubletten=dubletten.gemeldet(con),
                perioden=perioden.gemeldet(con),
                haende={a: perioden.haende(con, a)
                        for a in konfig.register()},
                testdaten=len(testdaten.seiten()),
                pdf_werkzeug=bool(seiten.pdf_werkzeug()),
            )
        finally:
            con.close()

    def _verbrauch(self, con, modell):
        """Was bisher tatsächlich verbraucht wurde — aus den Aufträgen.

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
            # gemessen, keins geschaetzt — aber nur der erste wird auch
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
            # konfig.toml steht und nie importiert wurde, wirkt nicht — und
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
                gemeinde=k.get("name", "—"),
                register=_runde.stand(con),
                quellen=quellen,
                quellen_fehlend=fehlend,
                eingerichtet=einrichtung.eingerichtet(),
                einrichtung=einrichtung.vorschlag(),
                felder=einrichtung.feldvorschlag(),
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
                # Nur anbieten, wenn auch angemeldet — ein installiertes,
                # aber unangemeldetes Claude Code liest keine Seite. None
                # heisst "nicht feststellbar" und zaehlt als anbieten.
                claude_code=vorlage.bereitschaft()["angemeldet"] is not False,
                offen=_runde.offen_in_runde(con, r["id"]) if r else None,
                bestand=db.stand(con),
            )
        finally:
            con.close()

    def eintraege(self, runde_id=None, nur=""):
        con = verbinde()
        raus = []
        wo, par = "1=1", []
        if runde_id:
            wo, par = "runde=?", [runde_id]
        for e in con.execute(
                f"SELECT * FROM eintrag WHERE {wo} ORDER BY register, bild, "
                "CAST(nr AS INTEGER), nr", par):
            felder = [dict(name=f["name"],
                           wert=f["korrigiert"] if f["korrigiert"] is not None
                           else f["gelesen"],
                           kb_form=f["kb_form"], beleg=f["beleg"],
                           person=f["person"], status=f["status"],
                           ampel=f["ampel"], zuversicht=f["zuversicht"],
                           rolle=f["rolle"], entscheidung=f["entscheidung"])
                      for f in con.execute(
                          "SELECT * FROM feld WHERE eintrag_id=? "
                          "ORDER BY reihe, id", (e["id"],))]
            if nur == "offen" and e["status"] == "bestaetigt":
                continue
            raus.append(dict(id=e["id"], register=e["register"], band=e["band"],
                             bild=e["bild"], nr=e["nr"], jahr=e["jahr"],
                             ausschnitt=e["ausschnitt"], status=e["status"],
                             runde=e["runde"], felder=felder))
        con.close()
        return raus

    def speichern(self):
        d = self._rumpf()
        con = verbinde()
        try:
            for name, v in d.get("felder", {}).items():
                row = con.execute(
                    "SELECT id, gelesen, status FROM feld "
                    "WHERE eintrag_id=? AND name=?", (d["id"], name)).fetchone()
                if not row:
                    continue
                wert = (v.get("wert") or "").strip()
                kb = (v.get("kb") or "").strip() or None
                korr = None if wert == (row["gelesen"] or "") else wert
                status = "bestaetigt" if d.get("bestaetigt") else row["status"]
                ents = v.get("entscheidung")
                pers = v.get("person")
                sql = "UPDATE feld SET korrigiert=?, kb_form=?, status=?"
                par = [korr, kb, status]
                if ents:
                    sql += ", entscheidung=?"
                    par.append(ents)
                if pers is not None:
                    sql += ", person=?"
                    par.append(int(pers) if str(pers).strip().isdigit() else None)
                # Was ein Mensch bestätigt hat, ist grün — unabhängig davon,
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
        print("daten/erfassung.sqlite fehlt — erst python3 -m werkstatt.db --init")
        return
    srv = HTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Werkstatt läuft:  http://127.0.0.1:{a.port}    (Strg-C beendet)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbeendet")
    else:
        # serve_forever kehrt nur zurueck, wenn shutdown() gerufen wurde —
        # also ueber den Knopf in der Oberflaeche.
        print("beendet — über die Werkstatt geschlossen")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
