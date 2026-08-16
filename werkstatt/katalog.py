#!/usr/bin/env python3
"""Feldkatalog: was in einer Aktart überhaupt vorkommen kann.

Bisher wuchsen die Feldlisten in `konfig.toml` von Hand, und was niemand
eingetragen hatte, ging verloren – der Tod des Täuflings im Randvermerk
fiel nur auf, weil ein Mensch ihn vermisste. Das ist die falsche
Reihenfolge: Die Werkstatt muss den möglichen Umfang kennen, nicht der
Bearbeiter ihn nachtragen.

Der Katalog nennt deshalb **alles, was in dieser Registerart stehen kann**,
nicht das, was üblich ist. Ein Feld, das leer bleibt, kostet nichts; ein
Feld, das fehlt, kostet die Angabe.

## Die zwei Formen jeder Angabe

Der Bestand führt beides nebeneinander, und der Katalog macht das zur Regel:

    kanonisch   1 NAME Christina Margaretha /Faller/
    Kirchenbuch 2 _KB_NAME Christina Margaretha /Fallerin/

    kanonisch   2 CAUS Entkräftung
    Kirchenbuch 1 _TODURSACHE Entkräftung

    Kirchenbuch 1 _ALTER_KB 63 Jahre, 7 Monate, 13 Tage
    daraus      2 DATE CAL 14 JUN 1710        (BIRT, berechnet)

`kb=True` heißt: Für dieses Feld wird die Form des Kirchenbuchs eigens
festgehalten, weil sie sich von der normalisierten unterscheiden kann und
weil sie die Quelle ist. `ziel_kb` sagt, unter welchem Tag sie landet.

## Und der Volltext

Kein Katalog fängt alles. Deshalb hat jede Aktart ein Feld `volltext`: der
Eintrag im Wortlaut, so wie ihn der Bestand als `2 NOTE` unter dem Ereignis
führt. Was kein Feld hat – eine Bemerkung des Pfarrers, ein Trauspruch,
eine Randbedingung –, steht wenigstens dort und ist wiederfindbar.
"""
from collections import namedtuple

Feld = namedtuple(
    "Feld", "name rolle art kb ziel ziel_kb titel hinweis traeger")


def f(name, rolle=None, art="text", kb=False, ziel=None, ziel_kb=None,
      titel=None, hinweis=None, traeger=None):
    """Ein Feld der Aktkarte.

    `traeger` sagt, an wem ein Ereignis haengt, wenn das nicht die Rolle
    des Feldes ist: Das Taufdatum gehoert dem Kind, obwohl das Feld
    keiner Rolle zugeordnet ist, und das Traudatum der Familie.
    """
    return Feld(name, rolle, art, kb, ziel, ziel_kb,
                titel or name.replace("_", " "), hinweis, traeger or rolle)


# --------------------------------------------------------------- Bausteine
# Eine Person kommt in jeder Aktart in denselben Facetten vor. Einmal
# beschrieben, dreimal verwendet – sonst driften die Register auseinander.
def person(r, titel, *, geburt=False, eltern=False, stand=True):
    z = [
        f(f"{r}_name", r, "name", kb=True, ziel="NAME", ziel_kb="_KB_NAME",
          titel=f"{titel}: Name",
          hinweis="Vor- und Nachname, wie im Buch. Movierte Frauenformen "
                  "(Fallerin, Kauffmännin) bleiben in der Kirchenbuchform "
                  "stehen und werden nicht aufgelöst."),
        f(f"{r}_rufname", r, "text", ziel="_RUFNAME",
          titel=f"{titel}: Rufname",
          hinweis="Nur wenn das Buch einen der Vornamen hervorhebt."),
        f(f"{r}_beruf", r, "text", kb=True, ziel="OCCU", ziel_kb="_BERUF_KB",
          titel=f"{titel}: Beruf und Stellung",
          hinweis="Auch Ämter und Zusätze: „B. und Weingärtner“, "
                  "„Rathsverwandter“, „des Gerichts“, „Wittwer und Bauer“."),
        f(f"{r}_ort", r, "ort", kb=True, ziel="RESI", ziel_kb="_NOTE_ORT",
          titel=f"{titel}: Wohnort",
          hinweis="Auch „allhier“, „von Bönnigheim“, mit Amtsangabe."),
        f(f"{r}_religion", r, "text", ziel="RELI",
          titel=f"{titel}: Religion",
          hinweis="Nur wenn genannt – meist bei Andersgläubigen."),
    ]
    if stand:
        z.append(f(f"{r}_stand", r, "text", kb=True, ziel=None,
                   ziel_kb="_NOTE_STAND", titel=f"{titel}: Personenstand",
                   hinweis="ledig, Wittwer, Wittib, verwitwet, geschieden – "
                           "und „weiland“/„weyl:“, wenn die Person zum "
                           "Zeitpunkt des Eintrags bereits tot war."))
    if geburt:
        z += [
            f(f"{r}_geburt_datum", r, "datum", ziel="BIRT.DATE",
              titel=f"{titel}: geboren am"),
            f(f"{r}_geburt_ort", r, "ort", ziel="BIRT.PLAC",
              titel=f"{titel}: Geburtsort"),
            f(f"{r}_alter", r, "text", kb=True, ziel="BIRT.DATE",
              ziel_kb="_ALTER_KB", titel=f"{titel}: Altersangabe",
              hinweis="Wortlaut: „63 Jahre, 7 Monate, 13 Tage“. Daraus wird "
                      "ein berechnetes Geburtsdatum (DATE CAL), niemals ein "
                      "genaues."),
        ]
    if eltern:
        # Die Zeile, wie sie im Buch steht: ein Stück, mit Beruf und Ort
        # darin. Sie bleibt die Quelle und wird nicht ersetzt.
        z += [
            f(f"{r}_vater", r, "name", kb=True, ziel=None,
              ziel_kb="_KB_ELTERN", titel=f"{titel}: Vater",
              hinweis="Mit allem, was dabeisteht: Beruf, Ort, „weiland“."),
            f(f"{r}_mutter", r, "name", kb=True, ziel=None,
              ziel_kb="_KB_ELTERN", titel=f"{titel}: Mutter",
              hinweis="Auch der Geburtsname, wenn genannt („geborene …“)."),
        ]
        # Und daneben die zerlegte Fassung. Ohne sie ist der Vater der
        # Braut kein Mensch, sondern eine Zeichenkette: kein Personensatz,
        # kein Ort, kein Beruf – und damit auch kein Treffer im Bestand.
        # Gemessen an der Demo: 19 Eheeinträge, null verknüpfte Personen,
        # null gefundene Familien, obwohl die Eltern vor 1808 geheiratet
        # haben und im Bestand stehen. Gefüllt wird das aus der Zeile
        # darüber (personenzeile.py), zu sehen und zu ändern in der Maske.
        for wer, gross in (("vater", "Vater"), ("mutter", "Mutter")):
            e = f"{r}_{wer}"
            z += [
                f(f"{e}_name", e, "name", kb=True, ziel="NAME",
                  ziel_kb="_KB_NAME", titel=f"{titel}: {gross}, Name",
                  hinweis="Aus der Elternzeile zerlegt. Ändern ändert nur "
                          "die Auslegung, nicht die Zeile im Buch."),
                f(f"{e}_beruf", e, "text", kb=True, ziel="OCCU",
                  ziel_kb="_BERUF_KB", titel=f"{titel}: {gross}, Beruf"),
                f(f"{e}_ort", e, "ort", kb=True, ziel="RESI",
                  ziel_kb="_NOTE_ORT", titel=f"{titel}: {gross}, Wohnort"),
            ]
            if wer == "mutter":
                z += geborene(e, f"{titel}: Mutter")
    return z


def geborene(r, titel):
    """Der Geburtsname – das Feld, das am häufigsten verschenkt wird.

    Im Buch steht er als „geb.“, „geborne“, „eine geborene“ oder gar nicht,
    dann aber in movierter Form am Namen selbst. Kanonisch ist er der
    Nachname der Frau; die Kirchenbuchform bleibt daneben stehen.
    """
    return [f(f"{r}_geborene", r, "name", kb=True, ziel="SURN",
              ziel_kb="_KB_NAME", titel=f"{titel}: Geburtsname",
              hinweis="„geb. Kauffmännin“, „eine geborne Frey“. Kanonisch "
                      "die Grundform (Kauffmann), im Kirchenbuchfeld der "
                      "Wortlaut.")]


ABSCHLUSS = [
    f("randvermerk", None, "text", ziel="NOTE", titel="Randvermerk",
      hinweis="Spätere Nachträge am Seitenrand: Tod, Trauung, Auswanderung, "
              "Konfirmation. Wortlaut übernehmen."),
    f("volltext", None, "text", ziel="NOTE", titel="Eintrag im Wortlaut",
      hinweis="Der ganze Eintrag, so wie er dasteht, mit Abkürzungen und "
              "alter Rechtschreibung. Fängt alles auf, wofür es kein Feld "
              "gibt – Trauspruch, Bemerkung des Pfarrers, Sonderfall."),
    f("unleserlich", None, "text", titel="nicht entzifferbar",
      hinweis="Was im Eintrag steht, aber nicht gelesen werden konnte – "
              "mit Angabe der Stelle. Eine Lücke, die benannt ist, ist "
              "keine verlorene Angabe."),
]


# ------------------------------------------------------------------ Taufe
TAUFE = [
    f("lfd_nr", None, "text", titel="laufende Nummer"),
    f("tauf_datum", None, "datum", ziel="CHR.DATE", titel="Taufdatum",
      traeger="kind"),
    f("tauf_ort", None, "ort", ziel="CHR.PLAC", titel="Taufort",
      traeger="kind"),
    f("geburt_datum", "kind", "datum", ziel="BIRT.DATE", titel="Geburtsdatum"),
    f("geburt_zeit", "kind", "text", kb=True, ziel=None, ziel_kb="_NOTE_TAUFE",
      titel="Geburtsstunde",
      hinweis="„nachts um 2 Uhr“ – steht in vielen Formularen als eigene "
              "Spalte."),
    f("geburt_ort", "kind", "ort", ziel="BIRT.PLAC", titel="Geburtsort"),
    f("kind_vorname", "kind", "name", kb=True, ziel="GIVN",
      ziel_kb="_KB_NAME", titel="Kind: Vornamen"),
    f("kind_rufname", "kind", "text", ziel="_RUFNAME", titel="Kind: Rufname"),
    f("kind_geschlecht", "kind", "text", ziel="SEX", titel="Geschlecht"),
    f("mehrling", "kind", "text", kb=True, ziel=None, ziel_kb="_NOTE_TAUFE",
      titel="Zwilling/Drilling",
      hinweis="„Zwilling“, „der andere Zwilling“ – entscheidet über die "
              "Zuordnung zweier Einträge zu einer Geburt."),
    f("totgeburt", "kind", "text", kb=True, ziel="DEAT", ziel_kb="_NOTE_TAUFE",
      titel="tot geboren / Nottaufe",
      hinweis="„todtgeboren“, „in der Noth getauft“, „starb gleich darauf“."),
    *person("vater", "Vater", stand=True),
    *person("mutter", "Mutter", stand=True),
    *geborene("mutter", "Mutter"),
    f("mutter_herkunft", "mutter", "name", kb=True, ziel=None,
      ziel_kb="_KB_ELTERN", titel="Mutter: Herkunft",
      hinweis="Vater der Mutter samt Beruf und Ort, wenn genannt."),
    f("unehelich", None, "text", ziel="_STAT", ziel_kb="_NOTE_TAUFE",
      titel="unehelich",
      hinweis="„unehelich“, „ledigen Standes“, „vaterloses Kind“. Im "
              "Bestand als FAM mit _STAT NOT MARRIED und _MARR N."),
    f("vater_angeblich", None, "name", kb=True, ziel=None,
      ziel_kb="_NOTE_TAUFE", titel="angegebener Vater",
      hinweis="Bei unehelichen Geburten nennt das Buch oft den vom "
              "Kindsvater Bezichtigten – als Angabe, nicht als Tatsache."),
    f("paten", None, "text", kb=True, ziel="_ASSO", ziel_kb="_GODP",
      titel="Paten",
      hinweis="Der **Wortlaut** gehört in die Kirchenbuchform – die ganze "
              "Aufzählung mit Beruf, Ort und Abkürzungen, so wie sie "
              "dasteht. Kanonisch nur die bereinigten Namen, durch "
              "Semikolon getrennt. Im Bestand doppelt geführt: als Verweis "
              "(_ASSO + RELA Godparent) und im Wortlaut (_GODP)."),
    f("taufender", None, "text", ziel="CHR.AGNC", titel="taufender Geistlicher"),
    f("religion", None, "text", ziel="CHR.RELI", titel="Konfession"),
    f("fam_reg", None, "text", ziel="_FAMREG", titel="Seitenzahl des Familienregisters",
      hinweis="Die letzte gedruckte Spalte des Formulars, meist eine blosse "
              "Zahl. Sie verweist auf die Seite im Familienregister, wo "
              "dieselbe Familie mit allen Kindern steht – der stärkste "
              "Anker, den das Buch selbst mitliefert, weil ihn der Pfarrer "
              "gezogen hat und nicht wir."),
    f("sterbe_datum", "kind", "datum", ziel="DEAT.DATE",
      titel="Tod des Täuflings",
      hinweis="Nicht gelesen, sondern aus dem Randvermerk erschlossen; "
              "siehe randvermerk.py."),
    *ABSCHLUSS,
]


# -------------------------------------------------------------------- Ehe
EHE = [
    f("lfd_nr", None, "text", titel="laufende Nummer"),
    f("proklamation", None, "text", kb=True, ziel=None,
      ziel_kb="_NOTE_HEIRAT", titel="Aufgebote",
      hinweis="Die drei Proklamationen mit Daten, oder der Dispens davon."),
    f("trauung_datum", None, "datum", ziel="MARR.DATE",
      titel="Traudatum", traeger="familie"),
    f("trauung_ort", None, "ort", ziel="MARR.PLAC", titel="Trauort",
      traeger="familie",
      hinweis="Getraut wird oft in der Gemeinde der Braut."),
    *person("braeutigam", "Bräutigam", geburt=True, eltern=True),
    *person("braut", "Braut", geburt=True, eltern=True),
    *geborene("braut", "Braut"),
    f("verwandtschaft", None, "text", kb=True, ziel=None,
      ziel_kb="_NOTE_HEIRAT", titel="Verwandtschaft / Dispens",
      hinweis="„im dritten Grad verwandt“, „mit obrigkeitlicher "
              "Erlaubnis“ – bei nahen Verwandten brauchte es einen Dispens."),
    f("ehenummer", None, "text", kb=True, ziel=None, ziel_kb="_NOTE_HEIRAT",
      titel="wievielte Ehe",
      hinweis="„zum zweiten Mal“, „Wittwer“ – entscheidet, ob eine frühere "
              "Ehe im Bestand zu suchen ist."),
    f("zeugen", None, "text", kb=True, ziel="_ASSO", ziel_kb="_NOTE_HEIRAT",
      titel="Trauzeugen und Beistände"),
    f("trauender", None, "text", ziel="MARR.AGNC", titel="trauender Geistlicher"),
    f("textus", None, "text", ziel="MARR.NOTE", titel="Trauspruch",
      hinweis="„Textus: Prov. XIV. v.1.“ – der Bibelspruch der Traurede. "
              "Steht im Bestand im Volltext der Trauung."),
    f("religion", None, "text", ziel="MARR.RELI", titel="Konfession"),
    f("fam_reg", None, "text", ziel="_FAMREG", titel="Seitenzahl des Familienregisters",
      hinweis="Die letzte gedruckte Spalte des Formulars, meist eine blosse "
              "Zahl. Sie verweist auf die Seite im Familienregister, wo "
              "dieselbe Familie mit allen Kindern steht – der stärkste "
              "Anker, den das Buch selbst mitliefert, weil ihn der Pfarrer "
              "gezogen hat und nicht wir."),
    *ABSCHLUSS,
]


# -------------------------------------------------------------------- Tod
TOD = [
    f("lfd_nr", None, "text", titel="laufende Nummer"),
    f("sterbe_datum", "verstorbener", "datum", ziel="DEAT.DATE",
      titel="Sterbedatum"),
    f("sterbe_zeit", "verstorbener", "text", kb=True, ziel=None,
      ziel_kb="_NOTE_BEGR", titel="Sterbestunde"),
    f("sterbe_ort", "verstorbener", "ort", ziel="DEAT.PLAC", titel="Sterbeort"),
    f("begraebnis_datum", "verstorbener", "datum", ziel="BURI.DATE",
      titel="Begräbnisdatum"),
    f("begraebnis_ort", "verstorbener", "ort", ziel="BURI.PLAC",
      titel="Begräbnisort"),
    *person("verstorbener", "Verstorbener", geburt=True, eltern=True),
    f("todesursache", "verstorbener", "text", kb=True, ziel="DEAT.CAUS",
      ziel_kb="_TODURSACHE", titel="Todesursache",
      hinweis="Wortlaut des Buchs: „Entkräftung“, „Schwindsucht“, "
              "„Brustfieber“, „an der Ruhr“."),
    f("ehegatte", "verstorbener", "name", kb=True, ziel=None,
      ziel_kb="_NOTE_BEGR", titel="Ehegatte",
      hinweis="„hinterläßt eine Wittib“, „des N.N. Ehefrau“ – der stärkste "
              "Anker, um den Verstorbenen im Bestand zu finden."),
    f("hinterbliebene", "verstorbener", "text", kb=True, ziel=None,
      ziel_kb="_NOTE_BEGR", titel="Hinterbliebene",
      hinweis="Zahl und Art: „hinterläßt 4 Kinder“, „einen unehelichen "
              "Buben“."),
    f("kind_von", "verstorbener", "name", kb=True, ziel=None,
      ziel_kb="_KB_ELTERN", titel="bei Kindern: Eltern",
      hinweis="Bei verstorbenen Kindern nennt das Buch die Eltern statt "
              "eines Berufs."),
    f("leichenpredigt", None, "text", ziel="BURI.NOTE",
      titel="Leichentext / Predigt",
      hinweis="Bibelstelle der Grabrede, wie beim Trauspruch."),
    f("beerdigender", None, "text", ziel="BURI.AGNC",
      titel="beerdigender Geistlicher"),
    f("begraebnisart", None, "text", kb=True, ziel=None, ziel_kb="_NOTE_BEGR",
      titel="Art des Begräbnisses",
      hinweis="„in der Stille“, „ohne Gesang“, „mit ganzer Leichenbegleitung“ "
              "– sagt oft mehr über den Fall als die Todesursache."),
    f("religion", None, "text", ziel="BURI.RELI", titel="Konfession"),
    f("fam_reg", None, "text", ziel="_FAMREG",
      titel="Seitenzahl des Familienregisters",
      hinweis="Die letzte gedruckte Spalte des Formulars, meist eine blosse "
              "Zahl. Sie verweist auf die Seite im Familienregister, wo "
              "dieselbe Familie mit allen Kindern steht – der stärkste "
              "Anker, den das Buch selbst mitliefert."),
    *ABSCHLUSS,
]


KATALOG = {"taufe": TAUFE, "ehe": EHE, "tod": TOD}


# ------------------------------------------------------------------ Zugriff
def felder(art, con=None):
    """Die Felder dieser Aktart – Vorrat, angepasst durch die Aktkarte.

    Ohne `con` der reine Katalog. Mit `con` das, was der Bearbeiter im
    Zahnrad daraus gemacht hat: Abgeschaltetes fehlt, geänderte Ziele
    gelten, eigene Felder stehen hinten oder an der gewählten Stelle.
    """
    z = list(KATALOG.get(art, []))
    if con is None:
        return z
    try:
        rows = list(con.execute(
            "SELECT * FROM feldwahl WHERE art=?", (art,)))
    except Exception:
        return z
    wahl = {r["name"]: r for r in rows}
    raus = []
    for x in z:
        w = wahl.pop(x.name, None)
        if w is None:
            raus.append(x)
            continue
        if not w["aktiv"]:
            continue
        raus.append(x._replace(
            ziel=w["ziel"] if w["ziel"] is not None else x.ziel,
            ziel_kb=w["ziel_kb"] if w["ziel_kb"] is not None else x.ziel_kb,
            titel=w["titel"] or x.titel,
            hinweis=w["hinweis"] if w["hinweis"] is not None else x.hinweis,
            kb=bool(w["kb"]) if w["kb"] is not None else x.kb))
    # Was übrig bleibt, kennt der Katalog nicht: eigene Felder.
    for w in wahl.values():
        if not w["aktiv"]:
            continue
        neu = f(w["name"], w["rolle"], w["feldart"] or "text",
                kb=bool(w["kb"]), ziel=w["ziel"], ziel_kb=w["ziel_kb"],
                titel=w["titel"], hinweis=w["hinweis"])
        stelle = next((i for i, x in enumerate(raus)
                       if x.name == (w["nach"] or "")), None)
        raus.insert(stelle + 1, neu) if stelle is not None else raus.append(neu)
    return raus


def setze(con, art, name, **w):
    """Ein Feld anpassen oder anlegen. Nur genannte Angaben ändern sich."""
    from datetime import datetime, timezone
    spalten = ("aktiv", "ziel", "ziel_kb", "titel", "hinweis", "rolle",
               "feldart", "kb", "eigen", "nach")
    da = con.execute("SELECT 1 FROM feldwahl WHERE art=? AND name=?",
                     (art, name)).fetchone()
    if not da:
        con.execute(
            "INSERT INTO feldwahl (art, name, eigen, angelegt) VALUES (?,?,?,?)",
            (art, name, 1 if feld(art, name) is None else 0,
             datetime.now(timezone.utc).isoformat(timespec="seconds")))
    for k, v in w.items():
        if k in spalten:
            con.execute(f"UPDATE feldwahl SET {k}=? WHERE art=? AND name=?",
                        (v, art, name))
    con.commit()


def leeren(con, art, name):
    """Die erfassten Werte eines Feldes löschen – endgültig.

    Abschalten laesst die Werte stehen; das ist die Voreinstellung, weil
    eine Einstellungsaenderung keine Daten kosten darf. Wer ein Feld aber
    gar nicht fuehren will, soll es auch wieder loswerden koennen –
    sonst schleppt die Ausgabe Angaben mit, die niemand mehr ansieht.

    Bestaetigte Eintraege bleiben unberuehrt: Was ein Mensch geprueft hat,
    wird nicht durch einen Klick in den Einstellungen entfernt.
    """
    n = con.execute(
        "SELECT count(*) FROM feld f JOIN eintrag e ON e.id=f.eintrag_id "
        "WHERE e.register=? AND f.name=? AND e.status <> 'bestaetigt'",
        (art, name)).fetchone()[0]
    con.execute(
        "DELETE FROM feld WHERE name=? AND eintrag_id IN "
        "(SELECT id FROM eintrag WHERE register=? AND status <> 'bestaetigt')",
        (name, art))
    con.commit()
    return n


def zuruecksetzen(con, art, name):
    """Die Anpassung entfernen – der Katalog gilt wieder.

    Bei einem eigenen Feld heißt das: es verschwindet. Bereits erfasste
    Werte bleiben in `feld` stehen; sie zu löschen wäre Datenverlust für
    eine Einstellungsänderung.
    """
    con.execute("DELETE FROM feldwahl WHERE art=? AND name=?", (art, name))
    con.commit()


def namen(art):
    return [x.name for x in felder(art)]


def feld(art, name):
    for x in felder(art):
        if x.name == name:
            return x
    return None


def rolle(art, name):
    x = feld(art, name)
    return x.rolle if x else None


def mit_kb(art):
    """Felder, für die die Kirchenbuchform eigens festgehalten wird."""
    return [x for x in felder(art) if x.kb]


def datumsfelder(art):
    return [x.name for x in felder(art) if x.art == "datum"]


def als_prompt(art, con=None):
    """Der Katalog als Anweisung für das Lesen.

    Damit steht im Prompt, was vorkommen *kann* – nicht, was der letzte
    Bearbeiter zufällig eingetragen hat. Leere Felder sind erwünscht;
    fehlende Felder sind Verlust.
    """
    z = [f"Felder der Aktart „{art}“. Gib jedes Feld an, das im Eintrag "
         "vorkommt, und lass die übrigen leer – leer ist eine Aussage, "
         "Raten ist keine.", ""]
    for x in felder(art, con):
        zeile = f"  {x.name:24} {x.titel}"
        if x.kb:
            zeile += "  [auch Kirchenbuchform angeben]"
        z.append(zeile)
        if x.hinweis:
            z.append(f"       {x.hinweis}")
    return "\n".join(z)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("art", nargs="?", choices=sorted(KATALOG))
    ap.add_argument("--prompt", action="store_true")
    a = ap.parse_args()
    arten = [a.art] if a.art else sorted(KATALOG)
    for art in arten:
        if a.prompt:
            print(als_prompt(art))
            continue
        print(f"=== {art} – {len(felder(art))} Felder, "
              f"{len(mit_kb(art))} davon mit Kirchenbuchform")
        for x in felder(art):
            print(f"  {x.name:26} {x.rolle or '–':13} {x.art:6} "
                  f"{'KB' if x.kb else '  '} {x.ziel or ''}")
        print()


if __name__ == "__main__":
    main()


# ------------------------------------------------------- Herkunft der Tags
# GEDCOM 5.5.1 kennt einen festen Vorrat an Tags. Alles, was mit einem
# Unterstrich beginnt, ist **per Definition nicht standardisiert** – die
# Norm gibt den Unterstrich für eigene Erweiterungen frei und sagt nichts
# darüber, was sie bedeuten. Ob ein anderes Programm sie versteht, hängt
# allein davon ab, ob es dieselbe Erweiterung kennt.
#
# Das ist für ein Ortsfamilienbuch keine Kleinigkeit: Wer den Bestand
# später nach Gramps, Ahnenblatt oder GEDCOM 7 überführt, verliert genau
# das, was niemand sonst kennt. Deshalb steht bei jedem Feld, in welche
# der drei Klassen sein Ziel fällt.
STANDARD = set("""
ABBR ADDR ADOP AFN AGE AGNC ALIA ANCE ANCI ANUL ASSO AUTH BAPL BAPM BARM
BASM BIRT BLES BURI CALN CAST CAUS CENS CHAN CHAR CHIL CHR CHRA CITY CONC
CONF CONL CONT COPR CORP CREM CTRY DATA DATE DEAT DESC DESI DEST DIV DIVF
DSCR EDUC EMAIL EMIG ENDL ENGA EVEN FACT FAM FAMC FAMF FAMS FAX FCOM FILE
FONE FORM GEDC GIVN GRAD HEAD HUSB IDNO IMMI INDI LANG LATI LEGA LONG MAP
MARB MARC MARL MARR MARS MEDI NAME NATI NATU NCHI NICK NMR NOTE NPFX NSFX
OBJE OCCU ORDI ORDN PAGE PEDI PHON PLAC POST PROB PROP PUBL QUAY REFN RELA
RELI REPO RESI RESN RETI RFN RIN ROLE ROMN SEX SLGC SLGS SOUR SPFX SSN
STAE STAT SUBM SUBN SURN TEMP TEXT TIME TITL TRLR TYPE VERS WIFE WILL WWW
""".split())

# Eigene Tags, die über dieses Projekt hinaus in Gebrauch sind – vor allem
# in deutschsprachigen Programmen. Kein Standard, aber die Aussicht, dass
# ein anderes Programm sie erkennt, ist erheblich besser als bei den
# hauseigenen. Die Einstufung ist eine Einschätzung, keine Norm.
VERBREITET = {"_RUFNAME", "_UID", "_LOC", "_STAT", "_MARR", "_GODP",
              "_ASSO", "_AKA", "_MARNM", "_MILT", "_CREA", "_FREL", "_MREL"}

AMT = {"offiziell": "GEDCOM 5.5.1",
       "verbreitet": "eigener Tag, in Programmen gebräuchlich",
       "hauseigen": "eigener Tag, nur in diesem Bestand"}


def einstufung(ziel):
    """Wie belastbar ist dieses Ziel beim Weitergeben des Bestands?"""
    if not ziel:
        return None
    tag = ziel.split(".")[-1]
    if not tag.startswith("_"):
        return "offiziell" if tag in STANDARD else "unbekannt"
    return "verbreitet" if tag in VERBREITET else "hauseigen"


def uebersicht(art, con=None):
    """Jedes Feld mit beiden Zielen und deren Einstufung – für das Zahnrad."""
    aus_katalog = {x.name for x in KATALOG.get(art, [])}
    abgeschaltet = []
    werte = {}
    if con is not None:
        try:
            abgeschaltet = [r["name"] for r in con.execute(
                "SELECT name FROM feldwahl WHERE art=? AND aktiv=0", (art,))]
        except Exception:
            abgeschaltet = []
        # Wie viele Werte zu einem Feld schon erfasst sind. Ohne diese Zahl
        # ist „Feld loeschen" ein Sprung ins Dunkle.
        werte = {r["name"]: r["n"] for r in con.execute(
            "SELECT f.name, count(*) n FROM feld f "
            "JOIN eintrag e ON e.id=f.eintrag_id WHERE e.register=? "
            "AND COALESCE(f.korrigiert, f.gelesen) IS NOT NULL "
            "GROUP BY f.name", (art,))}
    z = []
    for x in felder(art, con):
        z.append(dict(
            name=x.name, titel=x.titel, rolle=x.rolle, art=x.art, kb=x.kb,
            hinweis=x.hinweis,
            ziel=x.ziel, ziel_amt=einstufung(x.ziel),
            ziel_kb=x.ziel_kb, ziel_kb_amt=einstufung(x.ziel_kb),
            eigen=x.name not in aus_katalog, aktiv=True,
            werte=werte.get(x.name, 0)))
    # Abgeschaltetes bleibt sichtbar – sonst findet niemand wieder, was er
    # weggeklickt hat.
    for name in abgeschaltet:
        x = feld(art, name)
        z.append(dict(name=name, titel=x.titel if x else name,
                      rolle=x.rolle if x else None,
                      art=x.art if x else "text", kb=bool(x and x.kb),
                      hinweis=x.hinweis if x else None,
                      ziel=x.ziel if x else None,
                      ziel_amt=einstufung(x.ziel) if x else None,
                      ziel_kb=x.ziel_kb if x else None,
                      ziel_kb_amt=einstufung(x.ziel_kb) if x else None,
                      eigen=name not in aus_katalog, aktiv=False,
                      werte=werte.get(name, 0)))
    return z


def bilanz(art):
    """Wie viel des Bestands übersteht einen Programmwechsel."""
    z = dict(offiziell=0, verbreitet=0, hauseigen=0, unbekannt=0, ohne=0)
    for x in felder(art):
        for ziel in (x.ziel, x.ziel_kb if x.kb else None):
            if not ziel:
                continue
            z[einstufung(ziel)] = z.get(einstufung(ziel), 0) + 1
        if not x.ziel and not x.ziel_kb:
            z["ohne"] += 1
    return z


# ------------------------------------------------------------- Bauplan
# Welche zwei Rollen ein Paar bilden und welche das Kind ist, steht nicht
# im Feld, sondern in der Aktart. Das ist die einzige Angabe, die sich
# nicht aus den Feldern ableiten laesst.
# Diese Ziele traegt der Personendatensatz schon in eigenen Spalten. Sie
# zusaetzlich als Merkmal zu fuehren hiesse, sie in der Ausgabe zweimal zu
# schreiben – einmal aus `person`, einmal aus `merkmal`.
IN_PERSON = {"NAME", "GIVN", "SURN", "SEX"}

PAAR = {"ehe": ("braeutigam", "braut"), "taufe": ("vater", "mutter")}
KIND = {"taufe": "kind"}


def rollen(art, con=None):
    """Alle Personenrollen dieser Aktart, in der Reihenfolge des Katalogs."""
    z = []
    for x in felder(art, con):
        if x.rolle and x.rolle not in z and x.name in (
                f"{x.rolle}_name", f"{x.rolle}_vorname"):
            z.append(x.rolle)
    kind = KIND.get(art)
    if kind and kind not in z:
        z.insert(0, kind)
    return z


def bauplan(art, con=None):
    """Was die Uebergabe aus einem Eintrag macht – abgeleitet, nicht gepflegt.

    Ereignisse entstehen aus jedem Datumsfeld, dessen Ziel auf `.DATE`
    endet; der Ort kommt aus dem Feld mit demselben Tag und `.PLAC`. Damit
    zieht jede Aenderung an der Aktkarte sofort durch bis in die Ausgabe –
    vorher stand hier eine zweite, von Hand gepflegte Liste, und sie kannte
    das Sterbedatum aus dem Randvermerk nicht.

    `merkmale` sind die Angaben, die kein Ereignis sind: Beruf, Wohnort,
    Religion, Rufname und die Kirchenbuchformen. Sie haengen an der Person
    oder am Ereignis und landen als eigene Zeile im GEDCOM.
    """
    fs = felder(art, con)
    # Nach Ziel UND Traeger, nicht nur nach Ziel: In der Ehe haben
    # `braeutigam_geburt_ort` und `braut_geburt_ort` beide BIRT.PLAC, und
    # wer nur das Ziel nachschlaegt, gibt dem Braeutigam den Geburtsort
    # der Braut.
    nach_ziel = {(x.ziel, x.traeger): x for x in fs if x.ziel}
    ereignis, merkmal = [], []
    for x in fs:
        if not x.ziel:
            if x.kb and x.ziel_kb:
                merkmal.append(dict(feld=x.name, tag=x.ziel_kb, kb=True,
                                    traeger=x.traeger))
            continue
        tag, _, unter = x.ziel.partition(".")
        if x.art == "datum" and unter == "DATE":
            ort = nach_ziel.get((f"{tag}.PLAC", x.traeger))
            ereignis.append(dict(tag=tag, datum=x.name,
                                 ort=ort.name if ort else None,
                                 traeger=x.traeger or "kind"))
        elif unter in ("PLAC",):
            continue                      # gehoert schon zum Ereignis
        elif x.ziel not in IN_PERSON:
            merkmal.append(dict(feld=x.name, tag=x.ziel, kb=False,
                                traeger=x.traeger))
        if x.kb and x.ziel_kb:
            merkmal.append(dict(feld=x.name, tag=x.ziel_kb, kb=True,
                                traeger=x.traeger))
    # Paare und Kindbeziehungen. Bisher stand hier genau ein Paar je
    # Aktart – bei der Ehe das Brautpaar. Die Eltern der Brautleute
    # blieben damit Personen ohne Familie, und die Elternehe, der stärkste
    # Anker des Verfahrens, konnte für Eheeinträge gar nicht greifen.
    # Jede Rolle, die ein `_vater_name` und ein `_mutter_name` hat, ist
    # jetzt ein weiteres Paar, und die Rolle selbst dessen Kind.
    namen = {x.name for x in fs}
    r = rollen(art, con)
    paare = [PAAR[art]] if PAAR.get(art) else []
    kinder = [(KIND[art], PAAR[art])] if KIND.get(art) and PAAR.get(art) else []
    for rolle in r:
        v, m = f"{rolle}_vater", f"{rolle}_mutter"
        if f"{v}_name" in namen and f"{m}_name" in namen:
            paare.append((v, m))
            kinder.append((rolle, (v, m)))
    return dict(personen=r, paar=PAAR.get(art), kind=KIND.get(art),
                paare=paare, kinder=kinder,
                ereignis=ereignis, merkmal=merkmal)
