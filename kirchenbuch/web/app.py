#!/usr/bin/env python3
"""Korrekturmaske: lokaler Webserver gegen daten/erfassung.sqlite.

Zeigt je Registereintrag den Bildstreifen und daneben meine Lesung.
Aendern, 'Bestätigt' druecken — der Wert gilt danach als fix und wird
von mir nicht mehr ueberschrieben.

  python3 skripte/maske.py            -> http://127.0.0.1:8765
  python3 skripte/maske.py --port 9000

Laeuft nur auf 127.0.0.1, keine Abhaengigkeiten ausser der Standardbibliothek.
Beenden mit Strg-C.
"""
import argparse
import json
import sys
import sqlite3
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .seite import SEITE
from .. import suche
from .. import konfig as _k

ROOT = _k.WURZEL
DB = ROOT / "daten" / "erfassung.sqlite"



class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, typ, body):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        pfad = urllib.parse.urlparse(self.path).path
        if pfad in ("/", "/index.html"):
            return self._send(200, "text/html; charset=utf-8", SEITE)
        if pfad == "/api/eintraege":
            return self._send(200, "application/json; charset=utf-8",
                              json.dumps(self.eintraege(), ensure_ascii=False))
        if pfad == "/api/suche":
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            begriff = (q.get("q") or [""])[0]
            sex = (q.get("sex") or [None])[0]
            return self._send(200, "application/json; charset=utf-8", json.dumps({
                "namen": suche.namen_treffer(begriff),
                "personen": suche.personen_treffer(begriff, sex=sex),
            }, ensure_ascii=False))
        if pfad == "/api/anbindung":
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            v = (q.get("vater") or [None])[0] or None
            m = (q.get("mutter") or [None])[0] or None
            d = suche.anbindung(v, m)
            d["herkunft_vater"] = suche.herkunft(v) if v else []
            d["herkunft_mutter"] = suche.herkunft(m) if m else []
            return self._send(200, "application/json; charset=utf-8",
                              json.dumps(d, ensure_ascii=False))
        if pfad.startswith("/bild/"):
            rel = urllib.parse.unquote(pfad[len("/bild/"):])
            ziel = (ROOT / rel).resolve()
            if not str(ziel).startswith(str(ROOT.resolve())) or not ziel.is_file():
                return self._send(404, "text/plain", "nicht gefunden")
            typ = "image/jpeg" if ziel.suffix.lower() in (".jpg", ".jpeg") else "image/png"
            return self._send(200, typ, ziel.read_bytes())
        self._send(404, "text/plain", "nicht gefunden")

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/speichern":
            return self._send(404, "text/plain", "nicht gefunden")
        n = int(self.headers.get("Content-Length", 0))
        d = json.loads(self.rfile.read(n) or b"{}")
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
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
                ofb = v.get("ofb_id")
                sql = "UPDATE feld SET korrigiert=?, kb_form=?, status=?"
                par = [korr, kb, status]
                if ents:
                    sql += ", entscheidung=?"
                    par.append(ents)
                if ofb is not None:
                    sql += ", ofb_id=?"
                    par.append(ofb or None)
                con.execute(sql + " WHERE id=?", par + [row["id"]])
            if d.get("bestaetigt"):
                con.execute("UPDATE eintrag SET status='bestaetigt' WHERE id=?",
                            (d["id"],))
            con.commit()
        finally:
            con.close()
        self._send(200, "application/json", b'{"ok":true}')

    def eintraege(self):
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        raus = []
        for e in con.execute(
                "SELECT * FROM eintrag ORDER BY register, bild, "
                "CAST(nr AS INTEGER), nr"):
            felder = [dict(name=f["name"],
                           wert=f["korrigiert"] if f["korrigiert"] is not None
                           else f["gelesen"],
                           kb_form=f["kb_form"], beleg=f["beleg"],
                           ofb_id=f["ofb_id"], status=f["status"],
                           rolle=f["rolle"], entscheidung=f["entscheidung"])
                      for f in con.execute(
                          "SELECT * FROM feld WHERE eintrag_id=? "
                          "ORDER BY reihe, id", (e["id"],))]
            raus.append(dict(id=e["id"], register=e["register"], band=e["band"],
                             bild=e["bild"], nr=e["nr"], jahr=e["jahr"],
                             ausschnitt=e["ausschnitt"], status=e["status"],
                             felder=felder))
        con.close()
        return raus


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    if not DB.exists():
        print("daten/erfassung.sqlite fehlt — erst skripte/erfassung.py --init")
        return
    srv = HTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Maske läuft:  http://127.0.0.1:{a.port}    (Strg-C beendet)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbeendet")


if __name__ == "__main__":
    main()
