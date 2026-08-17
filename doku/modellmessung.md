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
