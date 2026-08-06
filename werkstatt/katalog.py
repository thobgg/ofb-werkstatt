#!/usr/bin/env python3
"""Feldkatalog: was in einer Aktart überhaupt vorkommen kann.

Bisher wuchsen die Feldlisten in `konfig.toml` von Hand, und was niemand
eingetragen hatte, ging verloren — der Tod des Täuflings im Randvermerk
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
führt. Was kein Feld hat — eine Bemerkung des Pfarrers, ein Trauspruch,
eine Randbedingung —, steht wenigstens dort und ist wiederfindbar.
"""
from collections import namedtuple

Feld = namedtuple("Feld", "name rolle art kb ziel ziel_kb titel hinweis")


def f(name, rolle=None, art="text", kb=False, ziel=None, ziel_kb=None,
      titel=None, hinweis=None):
    return Feld(name, rolle, art, kb, ziel, ziel_kb,
                titel or name.replace("_", " "), hinweis)


# --------------------------------------------------------------- Bausteine
# Eine Person kommt in jeder Aktart in denselben Facetten vor. Einmal
# beschrieben, dreimal verwendet — sonst driften die Register auseinander.
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
          hinweis="Nur wenn genannt — meist bei Andersgläubigen."),
    ]
    if stand:
        z.append(f(f"{r}_stand", r, "text", kb=True, ziel=None,
                   ziel_kb="_NOTE_STAND", titel=f"{titel}: Personenstand",
                   hinweis="ledig, Wittwer, Wittib, verwitwet, geschieden — "
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
        z += [
            f(f"{r}_vater", r, "name", kb=True, ziel=None,
              ziel_kb="_KB_ELTERN", titel=f"{titel}: Vater",
              hinweis="Mit allem, was dabeisteht: Beruf, Ort, „weiland“."),
            f(f"{r}_mutter", r, "name", kb=True, ziel=None,
              ziel_kb="_KB_ELTERN", titel=f"{titel}: Mutter",
              hinweis="Auch der Geburtsname, wenn genannt („geborene …“)."),
        ]
    return z


def geborene(r, titel):
    """Der Geburtsname — das Feld, das am häufigsten verschenkt wird.

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
              "gibt — Trauspruch, Bemerkung des Pfarrers, Sonderfall."),
    f("unleserlich", None, "text", titel="nicht entzifferbar",
      hinweis="Was im Eintrag steht, aber nicht gelesen werden konnte — "
              "mit Angabe der Stelle. Eine Lücke, die benannt ist, ist "
              "keine verlorene Angabe."),
]


# ------------------------------------------------------------------ Taufe
TAUFE = [
    f("lfd_nr", None, "text", titel="laufende Nummer"),
    f("tauf_datum", None, "datum", ziel="CHR.DATE", titel="Taufdatum"),
    f("tauf_ort", None, "ort", ziel="CHR.PLAC", titel="Taufort"),
    f("geburt_datum", "kind", "datum", ziel="BIRT.DATE", titel="Geburtsdatum"),
    f("geburt_zeit", "kind", "text", kb=True, ziel=None, ziel_kb="_NOTE_TAUFE",
      titel="Geburtsstunde",
      hinweis="„nachts um 2 Uhr“ — steht in vielen Formularen als eigene "
              "Spalte."),
    f("geburt_ort", "kind", "ort", ziel="BIRT.PLAC", titel="Geburtsort"),
    f("kind_vorname", "kind", "name", kb=True, ziel="GIVN",
      ziel_kb="_KB_NAME", titel="Kind: Vornamen"),
    f("kind_rufname", "kind", "text", ziel="_RUFNAME", titel="Kind: Rufname"),
    f("kind_geschlecht", "kind", "text", ziel="SEX", titel="Geschlecht"),
    f("mehrling", "kind", "text", kb=True, ziel=None, ziel_kb="_NOTE_TAUFE",
      titel="Zwilling/Drilling",
      hinweis="„Zwilling“, „der andere Zwilling“ — entscheidet über die "
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
              "Kindsvater Bezichtigten — als Angabe, nicht als Tatsache."),
    f("paten", None, "text", kb=True, ziel="_ASSO", ziel_kb="_GODP",
      titel="Paten",
      hinweis="Alle, mit Beruf und Ort. Im Bestand doppelt geführt: als "
              "Verweis (_ASSO + RELA Godparent) und im Wortlaut (_GODP)."),
    f("taufender", None, "text", ziel="CHR.AGNC", titel="taufender Geistlicher"),
    f("religion", None, "text", ziel="CHR.RELI", titel="Konfession"),
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
    f("trauung_datum", None, "datum", ziel="MARR.DATE", titel="Traudatum"),
    f("trauung_ort", None, "ort", ziel="MARR.PLAC", titel="Trauort",
      hinweis="Getraut wird oft in der Gemeinde der Braut."),
    *person("braeutigam", "Bräutigam", geburt=True, eltern=True),
    *person("braut", "Braut", geburt=True, eltern=True),
    *geborene("braut", "Braut"),
    f("verwandtschaft", None, "text", kb=True, ziel=None,
      ziel_kb="_NOTE_HEIRAT", titel="Verwandtschaft / Dispens",
      hinweis="„im dritten Grad verwandt“, „mit obrigkeitlicher "
              "Erlaubnis“ — bei nahen Verwandten brauchte es einen Dispens."),
    f("ehenummer", None, "text", kb=True, ziel=None, ziel_kb="_NOTE_HEIRAT",
      titel="wievielte Ehe",
      hinweis="„zum zweiten Mal“, „Wittwer“ — entscheidet, ob eine frühere "
              "Ehe im Bestand zu suchen ist."),
    f("zeugen", None, "text", kb=True, ziel="_ASSO", ziel_kb="_NOTE_HEIRAT",
      titel="Trauzeugen und Beistände"),
    f("trauender", None, "text", ziel="MARR.AGNC", titel="trauender Geistlicher"),
    f("textus", None, "text", ziel="MARR.NOTE", titel="Trauspruch",
      hinweis="„Textus: Prov. XIV. v.1.“ — der Bibelspruch der Traurede. "
              "Steht im Bestand im Volltext der Trauung."),
    f("religion", None, "text", ziel="MARR.RELI", titel="Konfession"),
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
      hinweis="„hinterläßt eine Wittib“, „des N.N. Ehefrau“ — der stärkste "
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
              "— sagt oft mehr über den Fall als die Todesursache."),
    f("religion", None, "text", ziel="BURI.RELI", titel="Konfession"),
    *ABSCHLUSS,
]


KATALOG = {"taufe": TAUFE, "ehe": EHE, "tod": TOD}


# ------------------------------------------------------------------ Zugriff
def felder(art):
    return KATALOG.get(art, [])


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


def als_prompt(art):
    """Der Katalog als Anweisung für das Lesen.

    Damit steht im Prompt, was vorkommen *kann* — nicht, was der letzte
    Bearbeiter zufällig eingetragen hat. Leere Felder sind erwünscht;
    fehlende Felder sind Verlust.
    """
    z = [f"Felder der Aktart „{art}“. Gib jedes Feld an, das im Eintrag "
         "vorkommt, und lass die übrigen leer — leer ist eine Aussage, "
         "Raten ist keine.", ""]
    for x in felder(art):
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
        print(f"=== {art} — {len(felder(art))} Felder, "
              f"{len(mit_kb(art))} davon mit Kirchenbuchform")
        for x in felder(art):
            print(f"  {x.name:26} {x.rolle or '—':13} {x.art:6} "
                  f"{'KB' if x.kb else '  '} {x.ziel or ''}")
        print()


if __name__ == "__main__":
    main()
