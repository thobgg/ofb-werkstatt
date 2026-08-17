# Modellmessung: Können offene Modelle das Lesen übernehmen?

*Gemessen am 17. August 2026, lokal, ohne GPU. Anlass war die Diskussion
im CompGen-Forum und die Frage von einem Forumsteilnehmer, ob ein
gemieteter GPU-Server (Hetzner GEX44, 234 Euro/Monat) für einen
Vereinsbetrieb sinnvoll wäre. Bis zu dieser Messung stand im README nur:
"Ob ein offenes Modell Kurrent brauchbar liest, ist eine Messung und
keine Meinung." Jetzt liegt die erste Messung vor.*

## Ziel

Drei Fragen, in dieser Reihenfolge:

1. Liest ein fertiges, kostenloses Handschrift-Erkennungsmodell (HTR)
   die Kirchenbücher Haberschlacht 1808?
2. Liest ein offenes multimodales Sprachmodell sie, wie es auf einem
   eigenen oder Vereins-Server laufen könnte?
3. Was folgt daraus für die Server-Frage, bevor jemand Geld bindet?

## Prüfstein

Taufeintrag **1184798-00361 Nr. 12**, Spalte Eltern. Für diesen Eintrag
existiert eine belegte Wahrheit aus dem Pilotprojekt: Die Mutter heißt
**Koch** (OFB-Anker I3542 Juditha Catharina Koch). Der Eintrag ist
zugleich der schwerste bekannte Fall des Bestands: Claude las den Namen
im Piloten als "Rossin", in einer früheren Lesung als "Rothin". Datum,
Ort und Vornamen las Claude fehlerfrei.

Getestet wurde auf dem Zeilenstreifen der Werkstatt und zusätzlich auf
einer von Tabellenlinien befreiten Einzelzelle (nur die Elternspalte),
damit die Segmentierung der HTR-Werkzeuge faire Bedingungen bekommt.

## Aufbau

| | |
|---|---|
| Rechner | Desktop, Intel i5-10400T, 12 Threads, 16 GB RAM, keine GPU |
| HTR | Kraken 7.1 in eigener venv (Python 3.11 über uv) |
| HTR-Modelle | german_handwriting (UB Mannheim, Zenodo 7933463); fanny (Kurrent-Briefe F. Mendelssohn, Zenodo 18207676) |
| Sprachmodell | Qwen2.5-VL 7B, 4-Bit-Quantisierung, über Ollama 0.32.14 (Nutzerinstallation, ohne root) |
| Prompt | wie in der Werkstatt: wörtlich transkribieren, Kurrentschrift, Kirchenbuch 1808 |

Alles liegt unter `~/Dokumente/Ahnenforschung/kraken-experiment/` und
ist jederzeit löschbar (rund 11 GB).

## Ergebnis

Wahrheit der Zelle (sinngemäß): *"[Christian An]dreas Selger, Bürger u.
Bauer in Haberschlacht, evangelischer Religion; Catharina Friderika geb.
Kochin von Haberschlacht, evangelischer Religion"*

| Leser | Ausgabe (Auszug) | Brauchbarkeit |
|---|---|---|
| Claude (Referenz, Pilot) | alles richtig bis auf "Rossin" statt Kochin | ~95 % |
| Qwen2.5-VL 7B, lokal | "Austab Selgen, Sohn v. Valr / ... / geb. Roßis. In Sa / bist selig fil religios" | ~30-40 %, 91 s je Zelle |
| Kraken german_handwriting | "enaggil", "1ngie", "enad" | 0 % |
| Kraken fanny | "d abthot", "388 Sa 9es" | 0 % |

Bei den HTR-Modellen scheitern beide Stufen: Die Segmentierung zerlegt
schon die linienfreie Einzelzelle in 26 Pseudozeilen, und die Erkennung
liefert auf den Fragmenten keinen deutschen Text. Die Vorlage (dünne
Feder, blasse Tinte, schräger Duktus, Bleistiftgitter) liegt erkennbar
außerhalb des Trainingsmaterials dieser Modelle.

## Erkenntnisse

1. **Die Klassenfrage ist entschieden.** HTR von der Stange liest diesen
   Bestand nicht. Multimodale Sprachmodelle lesen ihn grundsätzlich auch
   offen und lokal; der Abstand zwischen Qwen 7B und Claude ist eine
   Frage der Modellgröße, nicht des Prinzips.
2. **Der Beleg-Abgleich bleibt der Kern.** Qwen macht an der kritischen
   Stelle denselben Fehler wie Claude: "geb. Roßis" statt Kochin. Zwei
   unabhängige Modelle lesen dort R statt K. Solche Fehler behebt kein
   besseres Modell; sie werden nur durch den Anker im Bestand sichtbar
   (Ampel, OFB I3542).
3. **CPU reicht zum Messen, nicht zum Arbeiten.** 91 Sekunden je Zelle
   bedeuten Stunden je Seite. Für den Betrieb braucht die Modellklasse
   eine GPU; daher die Server-Frage.

## Kosten dieser Messung

0 Euro. Rund zwei Stunden Arbeitszeit, etwa 11 GB Plattenplatz, alles
auf vorhandener Hardware.

## Grenzen der Messung

Ein Eintrag, eine Hand, ein Register. Keine Vorverarbeitung optimiert,
Qwen nur in 4-Bit-Quantisierung. Die Zahlen taugen als
Richtungsentscheid, nicht als Trefferquote. Für eine belastbare Quote
müsste über die 57 Demo-Einträge gemessen werden.

## Nächster Schritt: die großen offenen Modelle

Vorbereitet in `kraken-experiment/gpu-test/`: fünf Testbilder aus allen
drei Registern und ein Skript, das auf einer gemieteten GPU-Maschine
(RunPod oder vast.ai, etwa 2 USD je Stunde) nacheinander **Gemma 3
27B**, **Qwen2.5-VL 32B** und **Qwen2.5-VL 72B** lädt, alle Bilder
liest und Ergebnisse samt Laufzeiten ablegt. Erwartete Kosten unter
5 Euro, Dauer ein bis zwei Stunden.

Erst wenn diese Zahlen vorliegen, ist die Frage nach gekaufter oder
gemieteter Hardware (GEX44 mit 20 GB trägt bis ~32B; zwei RTX 3090 mit
48 GB tragen 72B) sinnvoll zu beantworten.

## Nachtrag: die großen offenen Modelle auf gemieteter GPU (17. August, abends)

Gemessen auf einer RunPod RTX A6000 (48 GB VRAM, 0,53 USD je Stunde),
Gesamtkosten des Laufs etwa 3 USD. Gleiche Bilder, gleicher Prompt wie
oben; die Modelle jeweils in der 4-Bit-Fassung aus der Ollama-Bibliothek.

| Modell | Koch-Zelle | Tempo je Bild | Befund |
|---|---|---|---|
| Gemma 3 27B | "St. Illa, v.d. Rofis" | 6-25 s | Bruchstücke, wieder R statt K |
| Qwen2.5-VL 32B | "Andreas Selgen" + frei Erfundenes ("verst. d. 24. Juli 1808, J. F. Kästner, Pfarrer") | 3-33 s | flüssige Halluzination, gefährlichster Fehlertyp |
| Qwen2.5-VL 72B | nur Fragezeichen, alle fünf Bilder | 38-114 s | auf 48 GB nicht nutzbar: VRAM randvoll (48,1 von 49,1 GB), Bildverarbeitung liefert Müll |

Erkenntnisse aus dem GPU-Lauf:

1. **Auch die großen offenen Modelle lesen diesen Bestand nicht
   brauchbar.** Das 32B trifft Fragmente und erfindet den Rest in
   flüssigem Deutsch; solche Ausgaben sind schlimmer als erkennbares
   Scheitern, weil sie in der Korrektur durchrutschen können.
2. **48 GB tragen das 72B nicht.** Die Karte lief mit 48,1 von 49,1 GB
   randvoll, die Lesungen bestanden aus Ersatzzeichen. Damit ist auch
   die Frage nach zwei RTX 3090 (gleiche Speicherklasse) für dieses
   Modell beantwortet. Ob das 72B auf 80 GB brauchbar liest, ist offen;
   nach dem 32B-Ergebnis ist die Erwartung gedämpft.
3. **Der R/K-Fehler ist jetzt vierfach belegt**: Claude, Qwen 7B,
   Gemma 27B und die Erstlesung des Piloten lesen an derselben Stelle
   R statt K. Kein Modellwechsel ersetzt den Beleg-Abgleich.

**Konsequenz für die Vereinsserver-Frage:** Nach diesem Stand lohnt ein
GPU-Server (GEX44, 2x RTX 3090 oder Vergleichbares) für das *Lesen*
nicht - die offenen Modelle liefern keine Qualität, die die
Korrekturarbeit gegenüber Claude aufwiegen würde. Die Messung hat rund
3 USD gekostet; die Wiederholung mit künftigen Modellgenerationen
kostet dasselbe und ist mit dem Paket in `kraken-experiment/gpu-test/`
jederzeit reproduzierbar.

## Einordnung: Waren die Modelle überhaupt geeignet?

Zwei Nachfragen, die sich bei der Auswertung stellten:

**Sind die Fragezeichen des 72B ein Messfehler?** Der Testrahmen ist
validiert: Dasselbe Skript, derselbe Prompt und dieselbe Schnittstelle
lieferten beim 7B und 32B sinnvolle Ausgaben. Die Fragezeichen sind ein
Setup-Befund (Karte randvoll, Auslagerung korrumpiert die
Bildverarbeitung), kein Urteil über das Modell selbst. Als Urteil über
die 48-GB-Speicherklasse bleiben sie gültig.

**Wie schlimm die Halluzination wirklich ist**, zeigen die Streifen:
Gemma 27B machte aus dem Sterbeeintrag Johann Jakob Becks einen frei
erfundenen Eintrag "Joh. Gottlieb Seifert, Sohn des Johann Georg
Seifert und Anna Maria geb. Lehmann, getauft den 28. April 1808" und
aus der Löffler-Totgeburt eine "Margarethe Graff aus Graffenhayn".
Keine dieser Personen existiert. Solche Ausgaben sehen aus wie
Transkriptionen und sind keine.

**Prädestiniert war keines der Modelle - es gibt kein offenes Modell,
das auf deutsche Kurrent trainiert wäre.** Getestet wurden die besten
verfügbaren offenen Allzweck-Bildmodelle; ihr Training (moderne
Dokumente, Fotos, gedruckter Text) enthält historische deutsche
Handschrift praktisch nicht, und genau das zeigen die Ergebnisse.
Weitere Modelle derselben Klasse (InternVL, Llama Vision, Pixtral,
MiniCPM) teilen dieses Trainingsproblem; von ihnen ist dasselbe Bild zu
erwarten.

## Offene Prüfsteine

1. **Transkribus** ist der einzige verbliebene Kandidat mit echten
   Kurrent-Modellen (kommerzieller Dienst, Credits, Scans gehen in
   dessen Cloud - dieselbe Abwägung wie bei der Anthropic-API). Es gibt
   eine REST-API für die Erkennung, damit ließe sich das Messpaket
   analog zum GPU-Lauf anwenden. Zu beachten: Transkribus liefert Text
   ohne Felder; die Spaltenzuordnung bliebe Aufgabe der Werkstatt.
2. **Qwen 72B auf 80 GB** - der Vollständigkeit halber, Erwartung nach
   dem 32B-Ergebnis gedämpft. Kosten etwa 1 USD.
3. **Eigenes Training auf die Hand** (Kraken/PyLaia mit einigen hundert
   korrigierten Zeilen als Wahrheit) - der einzige Weg zu einem lokalen
   Kurrent-Leser, mit echtem Aufwand und offenem Ausgang.

## Methodische Schwäche und der saubere Messplan

Die Claude-Referenz (~95 %) stammt aus dem Pilotprojekt, nicht aus dem
Testrahmen dieser Messung: Dort bekam Claude ganze Seiten mit
Spaltenkopf und den strukturierten Feld-Prompt der Werkstatt, die
offenen Modelle hier nur nackte Streifen mit einem generischen
Transkriptionsauftrag. Der Größenvergleich ist damit unsauber; das
Urteil über die offenen Modelle bleibt bestehen, weil erfundene
Personen unabhängig vom Rahmen disqualifizieren.

Der saubere Messplan für die nächste Runde, mit vorhandenen Zutaten:

- **Ground Truth:** die validierten Transkriptionen der Pilotseiten
  00361, 00363, 00364, 00365 (geprüft, Feld für Feld, in der
  Pilotdatenbank des Nachbarprojekts).
- **Gleiche komplette Seiten, gleicher Prompt für alle Leser** -
  einschließlich Claude über die API im selben Rahmen (Kosten im
  Cent-Bereich).
- **Metrik:** Wortfehlerrate gegen die validierte Wahrheit, getrennt
  ausgewiesen: erfundene Inhalte, weil Halluzination schwerer wiegt
  als ein Lesefehler.

Erst damit entsteht eine Quote je Modell statt eines
Prüfstein-Eindrucks.
