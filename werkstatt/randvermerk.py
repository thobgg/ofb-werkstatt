#!/usr/bin/env python3
"""Randvermerke lesen: was am Rand steht, ist eine Angabe wie jede andere.

Im Taufregister trägt der Pfarrer später an den Rand, was aus dem Kind
geworden ist — meistens sein Tod, oft mit Datum:

    † 11. Februar 1808
    gest. 3. Merz 1809
    + 14.5.1812
    starb den 2. Jenner 1810

Das stand bisher als Text in `randvermerk` und kam nirgends an. Ein
Sterbedatum, das im Buch steht und nicht im Bestand landet, ist verschenkte
Quelle — dieselbe Angabe muss der Bearbeiter später mühsam im
Sterberegister suchen.

**Vorgeschlagen, nicht gesetzt.** Was hier herauskommt, füllt das Feld
`sterbe_datum` mit einem Beleg, aus dem hervorgeht, woher es stammt. Grün
wird es davon nicht: Ob der Vermerk wirklich dem Täufling gilt und nicht
etwa der Mutter, entscheidet der Blick aufs Bild.
"""
import re

MONATE = {
    "jan": 1, "januar": 1, "jenner": 1, "jänner": 1,
    "feb": 2, "februar": 2, "hornung": 2,
    "mar": 3, "mär": 3, "maerz": 3, "märz": 3, "merz": 3,
    "apr": 4, "april": 4,
    "mai": 5, "may": 5,
    "jun": 6, "juni": 6, "junius": 6, "brachmonat": 6,
    "jul": 7, "juli": 7, "julius": 7, "heumonat": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9, "herbstmonat": 9,
    "okt": 10, "oct": 10, "oktober": 10, "october": 10, "weinmonat": 10,
    "nov": 11, "november": 11, "wintermonat": 11,
    "dez": 12, "dec": 12, "dezember": 12, "december": 12, "christmonat": 12,
}
GEDCOM_MONAT = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()

# Was einen Tod anzeigt. Das Kreuz steht meist voran, die Wörter auch.
# `+` nur am Anfang, sonst fängt es Rechenzeichen und Silbentrenner ein.
TOD = re.compile(
    r"(†|✝|\bgest(?:orben|\.)?\b|\bstarb\b|\bverstorben\b|\bobiit\b|\bmortuus\b"
    r"|^\s*\+)", re.IGNORECASE)

# Ein Vermerk kann auch etwas ganz anderes sein. Wo eines davon steht,
# ohne Todeszeichen, wird nichts vorgeschlagen.
ANDERES = re.compile(
    r"\b(copul|getraut|verheirat|ehelich|conf(irm)?|firm|ausgewandert|"
    r"emigr|legitim)", re.IGNORECASE)

# Ordnungszahlen werden im Kirchenbuch ausgeschrieben angehaengt: „4.te",
# „2.ten", „21.sten". Ohne diese Gruppe faellt das Datum auf das blosse
# Jahr zurueck — gemessen an „† 4.te Februar 1808", das als „1808" ankam.
_ORDNUNG = r"(?:\s*\.?\s*(?:s?te[nrms]?|ste))?"
_TAG_MONAT_JAHR = re.compile(
    r"(\d{1,2})\s*\.?" + _ORDNUNG +
    r"\s*([A-Za-zÄÖÜäöü]{3,12})\.?\s*(\d{4})?")

# 7ber, 8ber, 9ber, Xber — die alten Zählmonate. Sie stammen aus dem
# römischen Jahr, das im März begann: September ist der siebte. In
# württembergischen Kirchenbüchern stehen sie durchgehend, und wer sie
# wörtlich nimmt, verlegt einen Tod um zwei Monate.
_ZAEHLMONAT = re.compile(
    r"(\d{1,2})\s*\.?\s*(7|8|9|10|X|xa?)\s*(?:ber|bris)\.?\s*(\d{4})?",
    re.IGNORECASE)
_ZAEHLUNG = {"7": 9, "8": 10, "9": 11, "10": 12, "x": 12, "xa": 12}
_ZIFFERN = re.compile(r"(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{2,4})")


def _gedcom(tag, monat, jahr):
    if not jahr:
        return None
    if monat and tag:
        return f"{tag} {GEDCOM_MONAT[monat - 1]} {jahr}"
    if monat:
        return f"{GEDCOM_MONAT[monat - 1]} {jahr}"
    return str(jahr)


def sterbedatum(text, jahr_vorgabe=None):
    """Sterbedatum aus einem Randvermerk — oder None.

    `jahr_vorgabe` ist das Jahr des Eintrags. Späte Nachträge nennen oft nur
    Tag und Monat, weil das Jahr aus dem Zusammenhang klar ist. Das Jahr des
    Eintrags einzusetzen ist die einzige belastbare Annahme — und sie ist
    nicht immer richtig, weshalb der Beleg sie ausdrücklich nennt.
    """
    t = (text or "").strip()
    if not t or not TOD.search(t) or ANDERES.search(t):
        return None
    m = _ZIFFERN.search(t)
    if m:
        tag, monat, j = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if j < 100:
            j += 1800
        if 1 <= monat <= 12:
            return _gedcom(tag, monat, j)
    m = _ZAEHLMONAT.search(t)
    if m:
        monat = _ZAEHLUNG.get(m.group(2).lower())
        if monat:
            return _gedcom(int(m.group(1)), monat,
                           int(m.group(3)) if m.group(3) else jahr_vorgabe)
    m = _TAG_MONAT_JAHR.search(t)
    if m:
        monat = MONATE.get(m.group(2).lower().replace("ä", "ae")
                           .replace("ö", "oe").replace("ü", "ue"))
        if monat is None:
            monat = MONATE.get(m.group(2).lower())
        if monat:
            j = int(m.group(3)) if m.group(3) else jahr_vorgabe
            return _gedcom(int(m.group(1)), monat, j)
    j = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", t)
    if j:
        return str(int(j.group(1)))
    return None


def beleg(text, geraten_jahr=False):
    kern = " ".join((text or "").split())[:60]
    z = f"aus dem Randvermerk „{kern}“"
    if geraten_jahr:
        z += " — Jahr aus dem Eintrag ergänzt, im Vermerk steht keines"
    return z + "; ob der Vermerk dem Täufling gilt, sagt nur das Bild"
