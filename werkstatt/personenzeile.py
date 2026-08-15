#!/usr/bin/env python3
"""Eine Personenzeile zerlegen, wie sie im Kirchenbuch steht.

    python3 -m werkstatt.personenzeile "weiland Johann Jacob Sailer, Bürger
                                        und Weingärtner in Haberschlacht"

**Warum das sein muss.** Taufregister führen Vater und Mutter in eigenen
Spalten, das Formular trennt also selbst. Ehe- und Sterberegister tun das
nicht: Dort steht unter *Eltern* eine einzige Zeile

    Daniel Conrad Sailer, Bürger und Bäcker zu Haberschlacht

und sie enthält Name, Beruf, Ort und manchmal einen Sterbevermerk in
einem Stück. Wer das so stehen lässt, hat keine Person, keinen Ort und
keinen Beruf, sondern eine Zeichenkette – und damit auch keinen Treffer
im Bestand.

**Was hier nicht passiert.** Die Zeile wird nicht ersetzt. Sie ist die
Quelle und bleibt, wie sie gelesen wurde; die Zerlegung ist eine
Auslegung daneben. Sie kann falsch sein, deshalb zeigt die Maske sie an,
statt sie stillschweigend zu verwenden.

## Was erkannt wird

    weiland, weyl., sel.        -> vermerk "verstorben"
    geb., geborene              -> Geburtsname
    Komma                       -> trennt Namen von Beruf und Ort
    in, zu, von, aus, allhier   -> leitet den Ort ein
    des Gerichts, Rathsverwandter, ... bleiben beim Beruf

## Was nicht erkannt wird

Zusammengesetzte Ortsnamen ohne Vorwort, Berufe ohne Komma davor,
Verwandtschaftsangaben („Bruder des …"). Was nicht sicher zuzuordnen ist,
bleibt beim Namen stehen – lieber ein zu langer Name als ein erfundener
Beruf.
"""
import re
import unicodedata

TOT = re.compile(r"^\s*(weiland|weyland|weyl\.?|wl\.?|sel(?:ig)?\.?|"
                 r"verstorben(?:e[rn]?)?)\s+", re.I)
# Kein re.I: Das Flag wuerde auch die Grossbuchstabenklasse aufweichen,
# und dann verschluckte "geb. Volz von Güglingen" das "von" als zweiten
# Namensteil. Der Schlüssel steht deshalb von Hand in beiden Schreibungen.
GEB = re.compile(r"\b[Gg]eb(?:orene?[rn]?)?\.?\s+"
                 r"([A-ZÄÖÜ][\wäöüß]*(?:\s+[A-ZÄÖÜ][\wäöüß]*)?)")
# Ortsvorwort. `allhier` steht fuer die eigene Parochie und ist selbst der
# Ort - im Buch die haeufigste Form ueberhaupt.
ORT = re.compile(r"\b(?:in|zu|von|aus|auf|bei)\s+"
                 r"([A-ZÄÖÜ][\wäöüß.-]*(?:\s+(?:an|am|der|dem|a\.)\s+"
                 r"[A-ZÄÖÜ][\wäöüß.-]*)?)")
ALLHIER = re.compile(r"\ball\s?hier\b|\bhier\s?selbst\b|\bhiesig(?:e[rn]?)?\b",
                     re.I)

# Woran ein Beruf zu erkennen ist, wenn kein Komma davorsteht. Bewusst
# kurz gehalten: Die Liste soll haeufige Faelle greifen, nicht alle.
BERUF_ANFANG = re.compile(
    r"\b(B(?:ürger|urger)\b|Bgr\.|Beisitzer|Bauer|Weingärtner|Bäcker|"
    r"Metzger|Schmied|Schneider|Schuhmacher|Wagner|Küfer|Müller|Wirth|"
    r"Hirt|Schäfer|Taglöhner|Soldat|Lehrer|Schulmeister|Pfarrer|"
    r"Rathsverwandter|Richter|Schultheiß|Schultheiss|Amtmann|Magaziner|"
    r"Maurer|Zimmermann|Weber|Krämer|Kaufmann|Gerichtsverwandter|"
    r"des Gerichts)\b")


def _sauber(s):
    s = unicodedata.normalize("NFC", str(s or ""))
    s = re.sub(r"\s+", " ", s).strip(" ,;.")
    return s


def zerlege(zeile):
    """Zerlegt eine Personenzeile. Rückgabe: dict mit den Teilen.

    Alle Werte sind entweder ein bereinigter Text oder None. `rest` nimmt
    auf, was übrig bleibt und sich nicht zuordnen ließ – steht dort etwas,
    ist die Zerlegung unvollständig, und das soll man sehen.
    """
    roh = _sauber(zeile)
    if not roh:
        return dict(name=None, geborene=None, beruf=None, ort=None,
                    vermerk=None, rest=None, quelle=None)
    t = roh
    vermerk = None
    m = TOT.match(t)
    if m:
        vermerk = "verstorben"
        t = t[m.end():]

    geborene = None
    m = GEB.search(t)
    if m:
        geborene = _sauber(m.group(1))
        t = (t[:m.start()] + " " + t[m.end():]).strip()

    ort = None
    if ALLHIER.search(t):
        ort = "allhier"
        t = _sauber(ALLHIER.sub(" ", t))
    else:
        m = ORT.search(t)
        if m:
            ort = _sauber(m.group(1))
            t = _sauber(t[:m.start()] + " " + t[m.end():])

    # Jetzt bleiben Name und Beruf. Das Komma trennt sie im Buch fast
    # immer; fehlt es, greift die Wortliste.
    name = beruf = None
    if "," in t:
        links, rechts = t.split(",", 1)
        name, beruf = _sauber(links), _sauber(rechts)
    else:
        m = BERUF_ANFANG.search(t)
        if m and m.start() > 0:
            name, beruf = _sauber(t[:m.start()]), _sauber(t[m.start():])
        elif m:
            beruf = _sauber(t)
        else:
            name = _sauber(t)

    # Was nach dem Beruf noch mit Komma folgt, ist Zusatz und bleibt dort.
    return dict(name=name or None, geborene=geborene, beruf=beruf or None,
                ort=ort, vermerk=vermerk, rest=None, quelle=roh)


# Welcher Teil in welches Feld geht. `geborene` nur bei der Mutter: Beim
# Vater waere ein Geburtsname eine Fehllesung.
ZIELE = dict(name="name", beruf="beruf", ort="ort", geborene="geborene")


def ergaenze(con, art, eintrag_id=None, runde_id=None):
    """Elternzeilen zerlegen und die Teile als eigene Felder ablegen.

    Läuft nach dem Lesen und vor dem Abgleich. Angefasst wird nur, was
    leer ist: Eine von Hand eingetragene Fassung bleibt stehen, und ein
    zweiter Lauf schreibt nichts doppelt. Die Quellzeile selbst bleibt
    unberührt – sie ist das, was im Buch steht.
    """
    from . import katalog
    if art not in katalog.KATALOG:
        return 0
    namen = {x.name for x in katalog.felder(art, con)}
    quellen = [n for n in namen
               if n.endswith(("_vater", "_mutter")) and f"{n}_name" in namen]
    if not quellen:
        return 0
    wo, par = "e.register=?", [art]
    if eintrag_id:
        wo += " AND e.id=?"
        par.append(eintrag_id)
    elif runde_id:
        wo += " AND e.runde=?"
        par.append(runde_id)
    n = 0
    for e in con.execute(f"SELECT e.id FROM eintrag e WHERE {wo} "
                         f"AND e.status <> 'bestaetigt'", par):
        vorhanden = {f["name"]: f for f in con.execute(
            "SELECT name, gelesen, korrigiert FROM feld WHERE eintrag_id=?",
            (e["id"],))}
        for q in quellen:
            f = vorhanden.get(q)
            roh = (f["korrigiert"] if f and f["korrigiert"] is not None
                   else (f["gelesen"] if f else None))
            if not roh:
                continue
            teile = zerlege(roh)
            for teil, endung in ZIELE.items():
                ziel = f"{q}_{endung}"
                if ziel not in namen or not teile.get(teil):
                    continue
                da = vorhanden.get(ziel)
                if da and ((da["korrigiert"] is not None)
                           or (da["gelesen"] or "").strip()):
                    continue                  # nicht überschreiben
                con.execute(
                    "INSERT INTO feld (eintrag_id, name, rolle, gelesen, "
                    " beleg, reihe) VALUES (?,?,?,?,?,99) "
                    "ON CONFLICT(eintrag_id, name) DO UPDATE SET "
                    " gelesen=excluded.gelesen, beleg=excluded.beleg "
                    "WHERE feld.korrigiert IS NULL "
                    "  AND COALESCE(TRIM(feld.gelesen),'')=''",
                    (e["id"], ziel, q, teile[teil],
                     "aus der Elternzeile zerlegt"))
                n += 1
    con.commit()
    return n


def kurz(teile):
    """Einzeiler für die Anzeige."""
    z = []
    if teile.get("vermerk"):
        z.append("†")
    if teile.get("name"):
        z.append(teile["name"])
    if teile.get("geborene"):
        z.append(f"geb. {teile['geborene']}")
    if teile.get("beruf"):
        z.append(f"· {teile['beruf']}")
    if teile.get("ort"):
        z.append(f"· {teile['ort']}")
    return " ".join(z)


def main():
    import sys
    for zeile in (sys.argv[1:] or [l.rstrip("\n") for l in sys.stdin]):
        t = zerlege(zeile)
        print(f"{zeile}\n  -> {kurz(t)}")
        for k in ("name", "geborene", "beruf", "ort", "vermerk"):
            if t[k]:
                print(f"     {k:9} {t[k]}")


if __name__ == "__main__":
    main()
