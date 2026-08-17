# Die eigenen Tags der OFB-Werkstatt

*Erzeugt von `python3 -m werkstatt.ausgabe7 --tags`. Die URIs im
`HEAD.SCHMA` einer GEDCOM-7-Ausgabe zeigen auf die Abschnitte
dieser Datei.*

Ein Ortsfamilienbuch führt die Form des Kirchenbuchs neben der
normalisierten: `Fallerin` steht im Buch, `Faller` ist der Name.
GEDCOM kennt dafür keine Tags, also gibt es eigene. In GEDCOM
5.5.1 stehen sie unerklärt in der Datei und jedes lesende
Programm muss raten; in GEDCOM 7 nennt das Schema im Kopf für
jeden eine URI, und die zeigt hierher.

Die Konvention stammt aus dem gedruckten Ortsfamilienbuch
Haberschlacht und wird nicht geändert, damit Neues zum
Bestehenden passt. Wer sie liest, verliert nichts, wenn er sie
übergeht: Alles Wesentliche steht auch in den Standardtags.

## _ALTER_KB

Die Altersangabe, wie sie im Eintrag steht, oft auf Jahre, Monate und Tage genau. Ein daraus errechnetes Geburtsdatum gehört nicht hierher, sondern unter BIRT.DATE mit CAL.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_alter_kb

Felder der Aktkarte, die hierher schreiben:

- ehe: Braut: Altersangabe
- ehe: Bräutigam: Altersangabe
- tod: Verstorbener: Altersangabe

## _ASSO

Platzhalter für einen Verweis auf eine beteiligte Person. Solange es den Datensatz nicht gibt, bleibt das Feld leer und der Wortlaut steht in `_GODP`.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_asso

Felder der Aktkarte, die hierher schreiben:

- ehe: Trauzeugen und Beistände
- taufe: Paten

## _BERUF_KB

Die Berufsbezeichnung im Wortlaut des Kirchenbuchs, etwa „Bürger und Weingärtner“.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_beruf_kb

Felder der Aktkarte, die hierher schreiben:

- ehe: Braut: Beruf und Stellung
- ehe: Braut: Mutter, Beruf
- ehe: Braut: Vater, Beruf
- ehe: Bräutigam: Beruf und Stellung
- ehe: Bräutigam: Mutter, Beruf
- ehe: Bräutigam: Vater, Beruf
- taufe: Mutter: Beruf und Stellung
- taufe: Vater: Beruf und Stellung
- tod: Verstorbener: Beruf und Stellung
- tod: Verstorbener: Mutter, Beruf
- tod: Verstorbener: Vater, Beruf

## _FAMREG

Die Seitenzahl des Familienregisters, auf die der Eintrag verweist.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_famreg

Felder der Aktkarte, die hierher schreiben:

- ehe: Seitenzahl des Familienregisters
- taufe: Seitenzahl des Familienregisters
- tod: Seitenzahl des Familienregisters

## _GODP

Die Paten im Wortlaut des Eintrags. Als eigene Datensätze werden sie erst geführt, wenn die Werkstatt Verweise anlegt.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_godp

Felder der Aktkarte, die hierher schreiben:

- taufe: Paten

## _KB_DATUM

Die Datumsangabe im Wortlaut, wenn sie sich nicht verlustfrei in ein GEDCOM-Datum bringen lässt.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_kb_datum

Felder der Aktkarte, die hierher schreiben:

- ehe: Traudatum
- taufe: Geburtsdatum
- taufe: Taufdatum
- taufe: Tod des Täuflings
- tod: Begräbnisdatum
- tod: Sterbedatum

## _KB_ELTERN

Eltern, wie der Eintrag sie nennt, samt Beruf, Ort und Vermerken. Solange die Werkstatt daraus keine eigenen Datensätze bildet, bleibt es Text.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_kb_eltern

Felder der Aktkarte, die hierher schreiben:

- ehe: Braut: Mutter
- ehe: Braut: Vater
- ehe: Bräutigam: Mutter
- ehe: Bräutigam: Vater
- taufe: Mutter: Herkunft
- tod: Verstorbener: Mutter
- tod: Verstorbener: Vater
- tod: bei Kindern: Eltern

## _KB_NAME

Der Name in der Schreibweise des Kirchenbuchs, neben der normalisierten Form unter NAME. Beide werden geführt: `Fallerin` im Buch, `Faller` als Name.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_kb_name

Felder der Aktkarte, die hierher schreiben:

- ehe: Braut: Geburtsname
- ehe: Braut: Mutter, Name
- ehe: Braut: Mutter: Geburtsname
- ehe: Braut: Name
- ehe: Braut: Vater, Name
- ehe: Bräutigam: Mutter, Name
- ehe: Bräutigam: Mutter: Geburtsname
- ehe: Bräutigam: Name
- ehe: Bräutigam: Vater, Name
- taufe: Kind: Vornamen
- taufe: Mutter: Geburtsname
- taufe: Mutter: Name
- taufe: Vater: Name
- tod: Verstorbener: Mutter, Name
- tod: Verstorbener: Mutter: Geburtsname
- tod: Verstorbener: Name
- tod: Verstorbener: Vater, Name

## _KB_RELI

Die Konfessionsangabe im Wortlaut des Eintrags.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_kb_reli

Felder der Aktkarte, die hierher schreiben:

- ehe: Braut: Religion
- ehe: Bräutigam: Religion
- ehe: Konfession
- taufe: Konfession
- taufe: Mutter: Religion
- taufe: Vater: Religion
- tod: Konfession
- tod: Verstorbener: Religion

## _NOTE_BEGR

Bemerkung zum Begräbniseintrag.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_note_begr

Felder der Aktkarte, die hierher schreiben:

- tod: Art des Begräbnisses
- tod: Ehegatte
- tod: Hinterbliebene
- tod: Sterbestunde

## _NOTE_HEIRAT

Bemerkung zum Traueintrag, meist die Fundstelle: „Ehereg. Bd. 6, Bild 2, Nr. 1“.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_note_heirat

Felder der Aktkarte, die hierher schreiben:

- ehe: Aufgebote
- ehe: Trauzeugen und Beistände
- ehe: Verwandtschaft / Dispens
- ehe: wievielte Ehe

## _NOTE_ORT

Die Ortsangabe im Wortlaut, etwa „von Hausen bei Brackenheim“, wo PLAC nur den Ort führt.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_note_ort

Felder der Aktkarte, die hierher schreiben:

- ehe: Braut: Mutter, Wohnort
- ehe: Braut: Vater, Wohnort
- ehe: Braut: Wohnort
- ehe: Bräutigam: Mutter, Wohnort
- ehe: Bräutigam: Vater, Wohnort
- ehe: Bräutigam: Wohnort
- ehe: Trauort
- taufe: Geburtsort
- taufe: Mutter: Wohnort
- taufe: Taufort
- taufe: Vater: Wohnort
- tod: Begräbnisort
- tod: Sterbeort
- tod: Verstorbener: Mutter, Wohnort
- tod: Verstorbener: Vater, Wohnort
- tod: Verstorbener: Wohnort

## _NOTE_STAND

Der Personenstand im Wortlaut, etwa „Wittwer“, „lediger Sohn“.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_note_stand

Felder der Aktkarte, die hierher schreiben:

- ehe: Braut: Personenstand
- ehe: Bräutigam: Personenstand
- taufe: Mutter: Personenstand
- taufe: Vater: Personenstand
- tod: Verstorbener: Personenstand

## _NOTE_TAUFE

Bemerkung zum Taufeintrag, für die es kein eigenes Feld gibt.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_note_taufe

Felder der Aktkarte, die hierher schreiben:

- ehe: trauender Geistlicher
- taufe: Geburtsstunde
- taufe: Zwilling/Drilling
- taufe: angegebener Vater
- taufe: taufender Geistlicher
- taufe: tot geboren / Nottaufe
- taufe: unehelich
- tod: beerdigender Geistlicher

## _RUFNAME

Der Name, mit dem die Person gerufen wurde, wenn das Kirchenbuch ihn eigens nennt.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_rufname

Felder der Aktkarte, die hierher schreiben:

- ehe: Braut: Rufname
- ehe: Bräutigam: Rufname
- taufe: Kind: Rufname
- taufe: Mutter: Rufname
- taufe: Vater: Rufname
- tod: Verstorbener: Rufname

## _STAT

Ein Vermerk zum Stand des Eintrags, etwa „unehelich“.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_stat

Felder der Aktkarte, die hierher schreiben:

- taufe: unehelich

## _TODURSACHE

Die Todesursache im Wortlaut des Kirchenbuchs.

    https://github.com/thobgg/ofb-werkstatt/blob/main/doku/gedcom7-tags.md#_todursache

Felder der Aktkarte, die hierher schreiben:

- tod: Todesursache

