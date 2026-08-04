#!/usr/bin/env python3
"""Verknüpfungskaskade für Sterbeeinträge.

    Alter ──► Geburtsdatum (oft taggenau, wenn Monate und Tage genannt sind)
          ──► Taufe suchen
    bei verheirateten Frauen: erst die Ehe, daraus der Mädchenname, dann die Taufe
    genannter Vater ──► gegen die Eltern der Taufe prüfen (zweiter Beleg)

**Pflichtregel:** Ein Treffer braucht mindestens zwei übereinstimmende Merkmale,
von denen eines **nicht** der Nachname ist. Nachname + Jahr genügt nie — sonst
wird `Johannes Bierle` still mit `Carl Heinrich Bierle` verknüpft.

    python3 -m werkstatt.kaskade_tod --parochie Haberschlacht --von 1800 --bis 1807
"""
import argparse
from dataclasses import dataclass, field

from . import bestand as B

# Bewertung der Merkmale
PUNKTE = {
    "datum_tag": 5,      # Taufdatum trifft das errechnete Geburtsdatum auf Tage
    "datum_jahr": 2,     # nur das Jahr passt
    "vorname": 3,
    "nachname": 1,       # allein nie ausreichend
    "vater": 4,          # im Sterbeeintrag genannter Vater = Vater der Taufe
    "ehe": 4,            # Mädchenname über die Ehe erschlossen
}
SCHWELLE = 6             # mind. so viele Punkte für einen Treffer


@dataclass
class Kandidat:
    eintrag_id: int
    datum: str
    vn: str
    fn: str
    vn_vater: str = ""
    fn_vater: str = ""
    vn_mutter: str = ""
    fn_mutter: str = ""
    merkmale: list = field(default_factory=list)

    @property
    def punkte(self):
        return sum(PUNKTE[m] for m in self.merkmale)

    @property
    def tragfaehig(self):
        """Zwei Merkmale, eines davon nicht der Nachname."""
        ohne_fn = [m for m in self.merkmale if m != "nachname"]
        return len(self.merkmale) >= 2 and ohne_fn and self.punkte >= SCHWELLE


@dataclass
class Ergebnis:
    art: str                 # treffer | mehrdeutig | kein_treffer | umweg_noetig
    kandidaten: list = field(default_factory=list)
    hinweis: str = ""
    maedchenname: str = ""

    @property
    def bester(self):
        return self.kandidaten[0] if self.kandidaten else None


def geburtsdatum(rec):
    """Errechnetes Geburtsdatum und ob es taggenau ist."""
    d = rec["dat_geburt"]
    if not d:
        return None, False
    genau = B.tage(d) is not None and "Tag" in (rec["alter_kb"] or "")
    return d, genau


def taufkandidaten(parochie_id, fn, vn, geb, taggenau):
    """Taufen mit passendem Nachnamen im Zeitfenster."""
    j = B.jahr(geb)
    if j is None:
        return []
    spanne = (j - 1, j + 1)
    raus = []
    for t in B.con().execute(
            """SELECT eintrag_id, dat_taufe, dat_geburt, vn_kind, fn_kind,
                      vn_vater, fn_vater, vn_mutter, fn_mutter
               FROM taufe_voll
               WHERE parochie_id=? AND substr(COALESCE(dat_taufe,dat_geburt),1,4) BETWEEN ? AND ?""",
            (parochie_id, str(spanne[0]), str(spanne[1]))):
        if not B.nachname_passt(t["fn_kind"], fn):
            continue
        k = Kandidat(t["eintrag_id"], t["dat_taufe"] or t["dat_geburt"],
                     t["vn_kind"] or "", t["fn_kind"] or "",
                     t["vn_vater"] or "", t["fn_vater"] or "",
                     t["vn_mutter"] or "", t["fn_mutter"] or "")
        k.merkmale.append("nachname")
        if B.vorname_passt(t["vn_kind"], vn):
            k.merkmale.append("vorname")
        # Datum
        a, b = B.tage(geb), B.tage(t["dat_geburt"] or t["dat_taufe"])
        if taggenau and a and b and abs(a - b) <= 5:
            k.merkmale.append("datum_tag")
        elif B.jahr(geb) == B.jahr(t["dat_taufe"] or t["dat_geburt"]):
            k.merkmale.append("datum_jahr")
        raus.append(k)
    return raus


def ehe_maedchenname(parochie_id, vn_frau, vn_mann, fn_mann, vor_jahr):
    """Mädchenname über die Ehe erschließen (verheiratete Frauen)."""
    for h in B.con().execute(
            """SELECT dat_trauung, vn_braeu, fn_braeu, vn_braut, fn_braut
               FROM heirat_voll WHERE parochie_id=? AND dat_trauung < ?""",
            (parochie_id, str(vor_jahr + 1))):
        if not B.nachname_passt(h["fn_braeu"], fn_mann):
            continue
        if vn_mann and not B.vorname_passt(h["vn_braeu"], vn_mann):
            continue
        if not B.vorname_passt(h["vn_braut"], vn_frau):
            continue
        return h["fn_braut"], h["dat_trauung"]
    return None, None


def verknuepfe(rec):
    """Kaskade für einen Sterbeeintrag. rec = Zeile aus tod_voll."""
    geb, taggenau = geburtsdatum(rec)
    vn, fn = rec["vn_verst"] or "", rec["fn_verst"] or ""
    pid = rec["parochie_id"]

    if not geb:
        return Ergebnis("kein_treffer", hinweis="kein Alter, kein Geburtsdatum")

    kand = taufkandidaten(pid, fn, vn, geb, taggenau)

    # Vater aus dem Sterbeeintrag als zweiter Beleg
    for k in kand:
        if rec["fn_vater_verst"] and B.nachname_passt(k["fn_vater"] if isinstance(k, dict)
                                                      else k.fn_vater,
                                                      rec["fn_vater_verst"]):
            if not rec["vn_vater_verst"] or B.vorname_passt(k.vn_vater, rec["vn_vater_verst"]):
                k.merkmale.append("vater")

    gut = sorted([k for k in kand if k.tragfaehig], key=lambda k: -k.punkte)

    if len(gut) == 1:
        return Ergebnis("treffer", gut)
    if len(gut) > 1:
        if gut[0].punkte > gut[1].punkte + 2:
            return Ergebnis("treffer", gut)
        return Ergebnis("mehrdeutig", gut, "mehrere gleichwertige Kandidaten")

    # Umweg: verheiratete Frau, Taufe steht unter dem Mädchennamen.
    # NICHT auf geschl_verst prüfen — das ist in 2 von 3 Einträgen leer.
    # Ein genannter Ehepartner genügt als Anlass, den Umweg zu versuchen.
    verheiratet = (rec["fn_ehepart_verst"] or rec["vn_ehepart_verst"])
    if verheiratet:
        mn, dat = ehe_maedchenname(pid, vn, rec["vn_ehepart_verst"],
                                   rec["fn_ehepart_verst"], B.jahr(rec["dat_tod"]) or 9999)
        if mn:
            k2 = taufkandidaten(pid, mn, vn, geb, taggenau)
            for k in k2:
                k.merkmale.append("ehe")
            gut2 = sorted([k for k in k2 if k.tragfaehig], key=lambda k: -k.punkte)
            if gut2:
                return Ergebnis("treffer", gut2,
                                f"über Ehe {dat}, Mädchenname {mn}", maedchenname=mn)
            return Ergebnis("umweg_noetig", [],
                            f"Mädchenname {mn} aus Ehe {dat}, aber keine Taufe gefunden",
                            maedchenname=mn)
        return Ergebnis("umweg_noetig", [],
                        "verheiratete Frau, Mädchenname nicht erschließbar")

    if kand:
        return Ergebnis("kein_treffer", kand,
                        "Kandidaten vorhanden, aber keiner tragfähig (Regel: zwei "
                        "Merkmale, eines nicht der Nachname)")
    return Ergebnis("kein_treffer", hinweis="keine Taufe am Ort — vermutlich Zuzug")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parochie", default="Haberschlacht")
    ap.add_argument("--von", type=int, default=1800)
    ap.add_argument("--bis", type=int, default=1807)
    ap.add_argument("--zeige", type=int, default=8)
    a = ap.parse_args()

    pid = next((i for i, n in B.parochien().items() if n == a.parochie), None)
    if pid is None:
        raise SystemExit(f"Parochie {a.parochie} nicht im Bestand")

    recs = list(B.con().execute(
        """SELECT * FROM tod_voll WHERE parochie_id=? AND dat_tod>=? AND dat_tod<?
           ORDER BY dat_tod""", (pid, str(a.von), str(a.bis + 1))))
    zaehl, gezeigt = {}, 0
    for r in recs:
        e = verknuepfe(r)
        zaehl[e.art] = zaehl.get(e.art, 0) + 1
        if gezeigt < a.zeige and e.art in ("treffer", "mehrdeutig", "umweg_noetig"):
            gezeigt += 1
            print(f"\n† {r['dat_tod']}  {r['vn_verst']} {r['fn_verst']}"
                  f"   [{r['alter_kb'] or '—'}]")
            print(f"   {e.art}{' · ' + e.hinweis if e.hinweis else ''}")
            for k in e.kandidaten[:3]:
                print(f"     {k.datum}  {k.vn} {k.fn}   {'+'.join(k.merkmale)}"
                      f" = {k.punkte}  ⟨{k.vn_vater} {k.fn_vater} ⚭ {k.vn_mutter} {k.fn_mutter}⟩")

    print("\n" + "=" * 62)
    print(f"{a.parochie} {a.von}–{a.bis}: {len(recs)} Sterbeeinträge")
    for k, v in sorted(zaehl.items(), key=lambda t: -t[1]):
        print(f"  {k:16} {v:5}  {v/len(recs)*100:5.1f} %")


if __name__ == "__main__":
    main()
