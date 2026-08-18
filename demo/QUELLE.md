# Die Beispielseiten

Zwölf Seiten aus den drei Registern der Pfarrei Haberschlacht
(Dekanat Brackenheim, Württemberg). Sie sind hier, damit sich die Werkstatt
ausprobieren lässt, ohne eigene Bücher zu haben – ohne Bilder gibt es keine
Streifen, keinen Spaltenkopf, keine Seitenschau, und dann sieht man von der
Arbeitsweise nichts.

## Woher

    Taufregister    Bd. 4, Bilder 1184798-00359 bis 00363, Jahrgänge 1808/09
    Eheregister     Bd. 6, Bilder 1184798-00917 bis 00921, ab 1808
    Sterberegister  Bd. 7, Bilder 1184799-00018 und 00022, ab 1808

Vom Sterberegister lagen zunächst fünf Bilder bei; `00019` bis `00021`
waren aber weitere Aufnahmen derselben Buchöffnung wie `00018` – Ancestry
fotografiert manche Öffnung mehrfach. Ihre Lesungen standen als eigene
Seiten in den Testdaten, und jeder der acht Einträge landete vierfach im
Bestand. Aufgefallen ist das beim Import in Ahnenblatt, dessen
Plausibilitätsprüfung die Doppelten meldete. Seitdem liegt je Öffnung
eine Aufnahme bei.

    Evangelische Kirchengemeinde Haberschlacht, Kirchenbücher.
    Digitalisate über Ancestry.

Aus Bild `1184798-00917` (Eheregister, Eintrag Nr. 1 von 1808,
Elternspalte) sind auch die freigestellten Schriftbilder geschnitten:
`doku/schrift-dunkel.png` und `-hell.png` im README, `kurrent.png` und
`kurrent-block.png` als Schriftband der Oberfläche.

Die Bücher selbst stammen aus dem frühen 19. Jahrhundert und sind
gemeinfrei; nach § 68 UrhG gilt das seit 2021 auch für originalgetreue
Reproduktionen gemeinfreier Werke. Zitiert wird nach der obigen Angabe.

## Wozu sie taugen – und wozu nicht

Sie zeigen das **württembergische Normalformular ab 1808**: eine Doppelseite
mit neun Spalten beim Taufregister, zwölf beim Eheregister. Genau daran
hängt die halbe Mechanik der Werkstatt – Zeilenerkennung, Blöcke,
Spaltenkopf über dem Streifen, die Erkennung der Formularperioden.

Sie zeigen **nicht**, wie gut die Lesung ist. Dafür bräuchte es eine
geprüfte Wahrheit, und die liegt bewusst nicht bei: Die 39 von Hand
geprüften Personenverweise des Pilotlaufs bleiben zurück, damit der
Abgleich sie selbst wiederfinden muss. Wer sie mitliefert, misst hinterher
nur, dass er sie mitgeliefert hat.

## Für den eigenen Versuch

Beim Einrichten eines Projekts stehen diese Ordner als Vorschlag da. Wer
eigene Bücher hat, trägt stattdessen deren Ordner ein – die Beispielseiten
werden dann nicht angefasst.

## Der Bestandsauszug

`bestand.ged` enthält 28 Personen, 15 Familien und die Quellen- und
Ortsdefinitionen, auf die sie zeigen, aus dem
Ortsfamilienbuch Haberschlacht 1659–1807 – genau die, die der Abgleich auf
den Beispielseiten trifft. Geschnitten mit `python3 -m werkstatt.auszug`,
die Records stehen wörtlich wie im Original.

Ohne ihn bleibt alles gelb: Es gibt nichts, wogegen geprüft werden könnte.
Mit ihm werden auf denselben Seiten 21 Felder grün, und zwar in allen
drei Registern: Taufe 10, Ehe 6, Tod 5 (seit den Kaskaden für Ehe und
Tod zählen dort auch taggenaue Geburtsdaten und der Ehegatten-Umweg).
Der erste Auszug war nur für die Taufrunde geschnitten – Ehe und Sterbeeinträge fanden deshalb nichts,
nicht weil der Anker nicht trüge, sondern weil die Eltern der Brautleute
im Auszug fehlten.

Dazu passen die Rohlesungen in `daten/pilot.json`: 69 Einträge, so wie ein
Modell sie gelesen hat, vor jeder Korrektur. Sie decken mehr Seiten ab, als
hier an Bildern liegen; gelesen wird nur, wozu auch ein Bild da ist, und das
sind 57 Einträge auf zehn Seiten – Taufe 23, Ehe 19, Tod 15. Das elfte
Bild, `1184798-00360`, ist dieselbe Buchöffnung wie `00359` und wird als
Dublette übersprungen; genau dafür liegt es bei.
Damit läuft der ganze Durchlauf ohne API-Schlüssel – Quelle *Testdaten*.
