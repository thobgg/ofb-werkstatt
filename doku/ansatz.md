# Ansatz

Festgehalten am 3. August 2026, nach einem Pilotlauf über 22 Taufeinträge
(Haberschlacht 1808/09). Die Zahlen darin sind gemessen, nicht geschätzt.

## Grundhaltung: kooperativ, nicht arbeitsteilig

Das Verfahren ist **KI und Mensch gemeinsam am selben Text**, nicht Maschine
liest und Mensch prüft stichprobenartig.

Belegt am Pilotlauf: Das Datum `30. Sept.` und die Form `Löbichin` hat der
Bearbeiter gelesen, das Modell nicht. Der Hinweis, dass der Nachbareintrag
(„Oktobr.") die Lesung erst ermöglicht, kam ebenfalls von ihm – daraus wurde
der Chronologie-Anker.

**Der Maßstab ist deshalb nicht** „wie viel schafft das Modell allein", sondern
**wie schnell beide gemeinsam zum richtigen Ergebnis kommen.** Die 42 % Rohfehler
bei Familiennamen sind in diesem Aufbau keine Fehlfunktion, sondern die
Aufgabenverteilung: Das Modell liefert Vorschlag und Kontext, der Bearbeiter
entscheidet dort, wo er die Hand besser liest.

Folge für die Oberfläche: Der Zeilenstreifen bleibt **immer** sichtbar, nicht
nur bei markierten Feldern. Bestätigte Felder werden zusammengefaltet, nicht
versteckt – wer mitliest, will hinsehen können.

## Arbeitsteilung: Modell schlägt vor, Skript entscheidet

| Aufgabe | LLM | deterministisches Skript |
|---|---|---|
| Handschrift lesen | ✓ | – |
| Kandidaten erkennen, Plausibilität einschätzen | ✓ | – |
| Abgleich gegen den Bestand | – | ✓ |
| Regelentscheidungen | – | ✓ |
| Daten verändern, zusammenlegen, exportieren | – | ✓ |

**Begründung aus dem Pilotlauf.** Acht doppelt angelegte Ehepaare wurden zuerst
einzeln diskutiert – langsam und ohne belastbares Ergebnis. Eine fünfzeilige
Regel entschied danach sechs davon allein und legte zwei zur Handprüfung.
Umgekehrt hätte kein Skript erkannt, dass `Roßin` in Wahrheit `Kochin` heißt.

**Sicherheitsregel:** Was Daten verändert, muss reproduzierbar sein. Ein Modell
entscheidet bei jedem Durchlauf womöglich anders. Also schlägt das Modell
Vorgänge vor, das Skript führt sie aus, das Journal hält beides fest.

## Dreischritt

    1  Transkribieren   Modell liest, markiert Unsicheres
                        Mensch ergänzt/korrigiert mit Bild daneben
                        Ergebnis: vollständiger Eintrag, noch ungeprüft

    2  Matching         der GANZE Eintrag als Suchschlüssel
                        Ergebnis: Zuordnungsvorschlag samt Begründung

    3  Bestätigen       Mensch entscheidet find-and-use oder create
                        erst hier wird etwas als gesichert markiert

**Warum erst vollständig lesen, dann matchen.** Die Anker, die im Pilotlauf
tatsächlich trafen, liefen fast nie über den Nachnamen:

| Eintrag | Treffer über | falsch gelesen war |
|---|---|---|
| Taufe 8/00361 | Vornamen der Frau (*Felicitas Heinrika*) | Nachname des Mannes |
| Taufe 7/00364 | Beruf *Schneidermeister* + *Eleonora Catharina* | Nachname des Mannes |
| Taufe 14/00365 | Beruf *Ratsverwandter* + *Maria Agnes* | Nachname des Mannes |
| Taufe 3/00363 | Beruf *Wirt und Gerichtsverwandter* | Nachname des Vaters |

> **Was gut lesbar ist – Vornamen, Datum, Beruf, Ort – trägt das Matching.
> Was schlecht lesbar ist – die Familiennamen – wird durch das Matching bestimmt.**

Feldweises Ankern während des Lesens würde beim falsch gelesenen Nachnamen
steckenbleiben.

## Ampel – Ergebnis des Matchings, keine Eigenschaft der Lesung

| Signal | Farbe | Folge |
|---|---|---|
| Anker bestätigt, Vornamen passen unabhängig | grün | still übernommen, eingeklappt |
| gelesen, aber nichts bestätigt es | gelb | Maske springt hin |
| unsicher gelesen, mehrere Kandidaten | rot | mit Bildausschnitt |

**Die Selbsteinschätzung des Modells darf nicht grün machen.** Bei `Koch`/`Roth`
war das Modell viermal sicher und viermal falsch – der Buchstabe ist eindeutig
lesbar, nur eben als der falsche.

**Vokabular und Häufigkeit machen ebenfalls nicht grün.** `Roth` kommt 59-mal im
Bestand vor und hätte jeden Plausibilitätstest bestanden.

### Kalibrierung nach Feldtyp (gemessen)

    Datum, Ort, Beruf, Formeln, Vornamen    praktisch fehlerfrei
    Familiennamen                           42 % falsch gelesen

Ein Familienname startet daher gelb, auch wenn er sauber lesbar wirkt.

## Anker aus der Registerordnung

Der billigste Anker – er braucht **weder Bestand noch Modell**, nur die
Struktur des Registers. Damit traegt er ab der ersten Seite, auch bei wem,
der bei Null anfaengt.

**Kirchenbuecher sind chronologisch gefuehrt.** Jedes Datum ist eingeklemmt
zwischen dem des vorigen und dem des naechsten Eintrags:

    Nr. 11   ...              <=
    Nr. 12   30. Sept.            <- gesucht
    Nr. 13   ... Oktobr.      >=

Ein gelesenes "30. Nov." ist damit sofort widerlegt, ohne Nachschlagen.
Dasselbe gilt fuer die **laufende Nummer**: lueckenlos, Sprung auf 1 bedeutet
Jahrgangswechsel.

| Nutzen | |
|---|---|
| **Pruefung** | Datum ausserhalb des Nachbarintervalls -> rot, unabhaengig von der Zuversicht des Modells |
| **Eingrenzung** | unleserliches Datum -> "zwischen 12. Sept. und 3. Okt." ist immer noch eine Aussage |
| **Prompt** | Nachbardaten mitgeben – schraenkt den Loesungsraum drastisch ein |
| **Vollstaendigkeit** | fehlende laufende Nummer = uebersprungener Eintrag oder fehlende Seite |

Im Pilotlauf blieb dieser Anker ungenutzt: Die Datumsspalten wurden gar nicht
gelesen. Belegt wurde er beim Durchsehen der Mockups – das Datum von Nr. 12
(00365) liess sich lesen, **weil im Eintrag darunter "Oktobr." steht**.

## Anker je Registerart

    Taufe        Eltern      → Elternehe im Bestand
    Ehe          Brautleute  → Geburtsdatum + Ort (tagesgenau, der stärkste)
                 Eltern      → über die Herkunftsfamilie der Brautleute
    Begräbnis    Verstorbener→ Name + Alter → Geburtsjahr rückgerechnet
                 Kinder      → genannter Vater → Elternfamilie
                 "weyl."     → Ehepartner

**Die Register verweisen aufeinander.** Der Täufling von 1809 ist der Bräutigam
von 1835 und der Verstorbene von 1880. Sind alle drei erfasst, schließen sich
die Ketten – ein stärkerer Anker als jeder Einzelabgleich, weil er unabhängige
Quellen verknüpft.

Der Elternehe-Anker verliert mit der Zeit an Kraft, wenn man **ein** Register
isoliert bearbeitet: Bei einem Bestand, der 1807 endet, tragen die Ehen im
Taufjahr 1808 noch 94 %, 1813 noch 53 %, 1820 nur 18 %. Werden die Ehen ab 1808
mit erfasst, versiegt er nicht – er wächst mit.

## Namensebenen

| Ebene | Beispiel | Zweck |
|---|---|---|
| gelesen | `Roßin` | Rohlesung, bleibt erhalten auch wenn falsch |
| Kirchenbuchform | `Kochin` | was dasteht, bestätigt → `_KB_NAME` |
| kanonisch | `Koch` | normalisiert, für Suche und Verknüpfung → `NAME` |

Die Rohlesung wegzuwerfen wäre ein Verlust – nur so lässt sich messen, wo die
Erkennung schlecht ist. Der `Koch`/`Roth`-Befund entstand genau daraus.

**Das Glattziehen darf die Kirchenbuchform nie überschreiben.** Sonst
verschwindet, dass dort `Krönich` steht und nicht `Kröneck`.

Der kanonische Name kommt beim Matching meist geschenkt: wird `I3037` zugeordnet,
ist deren `NAME` bereits `Bierle`.

## Wann der Mensch gefragt werden muss

    Match eindeutig        ein Kandidat, Anker stimmt          → durchlaufen
    Match mehrdeutig       zwei plausible Personen             → fragen
    Match widersprüchlich  beide Eltern da, keine gemeinsame
                           Familie                             → fragen (gefährlich)
    kein Match             kanonische Form festlegen           → vorschlagen, bestätigen

Nur der letzte Fall verlangt eine echte Namensentscheidung – und jede solche
Bestätigung ist eine neue Kante im Klassengraphen: gilt `Bührlin` einmal als
`Bierle`, gilt es fortan.

**Vorsicht dabei: Die Relation ist nicht transitiv.** Eine einzige falsche Kante
(`Bührle → Müller`, ein Beleg) verschmolz im Pilotbestand zwei fremde Familien
zu einer Klasse von 231 Personen. Bestätigte Kanten brauchen dieselbe Prüfung
wie importierte: Schreibnähe plus Belegzahl.

## Gezielter Bildausschnitt statt ganzer Seite

Der eigentliche Geschwindigkeitshebel: Bei jeder unsicheren Stelle wird genau
dieser Ausschnitt geschnitten und neben das Eingabefeld gelegt.

    heute      grosses Bild -> Stelle suchen -> hin und her -> tippen
    Ziel       kleiner Ausschnitt direkt am Feld -> tippen

**Nicht ueber Bounding Boxes des Modells** – die sind ungenau; beim Pilotlauf
traf die geschaetzte Position mehrfach daneben. Stattdessen deterministisch:

    Spaltenraster (einmal je Buch, von Hand gezogen)  -> horizontaler Bereich
    Zeilengrenze  (je Eintrag, ohnehin vorhanden)     -> vertikaler Bereich
    Modellhinweis (welche Textzeile in der Zelle)     -> Feinjustierung

Kirchenbuchformulare haben feste, gedruckte Spalten. Sind deren Grenzen einmal
bestimmt, ist fuer jedes Feld bekannt, wo es liegt – fuer den ganzen Band, oft
ueber Jahrzehnte.

### Automatik: taugt als Vorschlag

Register ab 1800 sind streng tabellarisch gedruckt – das sind gute
Voraussetzungen, besser als bei aelteren Fliesstexteintraegen. Gemessen an
vier Seiten mit 26 von Hand abgelesenen Grenzen:

| Verfahren | Treffer |
|---|---|
| Zeilenerkennung per Textprojektion | gescheitert (frueher) |
| proportional uebertragene Zeilenraster | gescheitert (frueher) |
| Bounding Boxes vom Modell schaetzen lassen | ungenau, Ausschnitte trafen daneben |
| laengster durchgehender Lauf, ueber die Doppelseite | 1/7 = **14 %** |
| Anteil dunkler Pixel, Seiten am Falz getrennt | 11/26 = **42 %** |
| dieselbe Methode, Seite sauber abgegrenzt | 5/7 = **71 %** |
| Abgrenzung ueber die Linien statt ueber die Helligkeit | 22/22 = **100 %** (±40 px) |

Zwei Fehler hatten die ersten Messungen verdorben: die Linien ueber die
**Doppelseite** zu messen, obwohl sie nur ueber je eine Seite laufen, und den
**laengsten durchgehenden Lauf** zu nehmen statt des Anteils dunkler Pixel –
jede Stelle, an der Handschrift eine Linie kreuzt, halbiert den Lauf.

### Warum Helligkeit die Seite nicht abgrenzen kann

Die Abgrenzung galt als der offene Knackpunkt. Gemessen an den vier Seiten
ist sie mit Helligkeit **grundsaetzlich** nicht loesbar:

    Formular   Median 250–252
    darueber   Median 244–251      <- die weisse Unterlage neben dem Buch
    darunter   Median   4– 46      <- Buchschnitt und Deckel

Die Unterlage ist so hell wie das Papier. Keine Schwelle trennt beide, auch
keine relative – der Fehler lag nicht in der Zahl 140, sondern im Merkmal.

Was das Formular auszeichnet, sind seine **gedruckten Linien**: dunkle Pixel
mit hellen Nachbarn quer zur Laufrichtung. Buchdeckel ist dunkel mit dunklen
Nachbarn, Unterlage hell ohne Struktur. Damit grenzt sich die Seite ueber
dasselbe Merkmal ab, das ohnehin gesucht wird.

Der **Falz** ist die dunkelste Spalte im mittleren Drittel – ueber alle
sieben Seiten x=3024–3072 bei Kontrast 5–46 gegen ein Papiermittel von ~220.
Das stabilste Merkmal der ganzen Seite. Die naheliegenderen Kandidaten
(staerkste senkrechte Linie, Unterbrechung der waagerechten) sprangen
dagegen um bis zu 400 px.

Ergebnis: 22 von 22 Zeilenlinien bei ±40 px, **ohne einen einzigen
ueberzaehligen Vorschlag** im Eintragsbereich. Nachpruefbar mit
`python3 -m werkstatt.messung`.

Zwei Einschraenkungen, damit die Zahl nicht mehr verspricht als sie traegt:
Die Sollwerte sind aus den von Hand geschnittenen Streifen zurueckgewonnen
und selbst nur auf ±40 px genau; und gemessen ist eine Hand, ein Formular,
sieben Seiten.

### Vorschlag plus Hand, mit Vererbung

    Spalten   einmal je Buch ziehen – das Formular bleibt ueber Jahrzehnte gleich
    Zeilen    auf der ersten Seite ziehen, auf Folgeseiten uebernehmen und
              nur nachjustieren

Bei einem Band mit fuenfzig gleichartigen Seiten faellt echte Arbeit nur einmal
an; danach ist es Nachschieben um wenige Pixel.

### Kontext ist Teil der Information

**Ein isolierter Ausschnitt ist schlechter lesbar als derselbe Ausschnitt im
Zusammenhang** – fuer den Menschen wie fuer das Modell.

Dieselbe Hand schreibt in jedem Eintrag `B. u. Weingaertner in Haberschlacht`.
An diesen wiederkehrenden Woertern eicht man die Buchstabenformen. Wer nur den
zweifelhaften Namen sieht, hat diese Eichung nicht.

Daraus zwei Regeln:

**Oberflaeche:** nicht Ausschnitt *statt* Streifen, sondern **Lupe** – der
Zeilenstreifen bleibt sichtbar, die fragliche Stelle ist darin markiert, die
Vergroesserung steht daneben. Nachbarzeilen werden abgedunkelt, nicht
weggeschnitten. Ausschnitte grosszuegig mit Rand, sonst werden Buchstaben
abgetrennt und die Zuordnung geht verloren.

**Prompt:** dem Modell nie einzelne Streifen isoliert vorlegen, sondern mit den
Nachbarzeilen. Ein Teil der 42 % Rohfehler des Pilotlaufs entstand vermutlich
genau dort – beim Nachzoomen auf eine Einzelstelle ging der Zusammenhang
verloren.

Sicherheitsnetz: ein Klick blendet die ganze Seite ein.

## Ein Bearbeiter, zwei Kopfhaltungen

Gebaut wird fuer **eine Person**, die ihre eigene Parochie abschreibt. Kein
Login, kein Hosting, kein Upload, keine Mehrbenutzerverwaltung.

Das ist keine Bescheidenheit, sondern die Lage: Wer ein Kirchenbuch abschreibt,
tut das aus persoenlichem Bezug zum Ort. Das sind Einzelne, keine Crowd – und
jeder hat sein eigenes Dorf, seinen eigenen Bestand, seine eigene Handschrift.
Ein gemeinsamer Dienst haette keinen gemeinsamen Gegenstand.

Der Bearbeiter bedient ein Startskript; ein Paket zum Doppelklick ist nicht
noetig. `http.server` aus der Standardbibliothek genuegt, es braucht kein
Web-Framework.

Was dennoch getrennt bleibt, sind die **Taetigkeiten**: Transkribieren ist
visuelle Arbeit am Bild, Zuordnen ist Entscheidungsarbeit an Daten. Sie im
selben Arbeitsschritt zu vermischen kostet Tempo – siehe Dreischritt oben.
Dieselbe Person, zwei Kopfhaltungen.

## Wissensbasis: waechst aus der Arbeit

Jede Transkription erzeugt Wissen ueber die Quelle. Das darf nicht in einer
von Hand gepflegten Textdatei liegen, sondern gehoert in die Anwendung – und
das meiste davon faellt ohnehin an:

| Wissen | Herkunft |
|---|---|
| Fehlerkatalog der Handschrift | **jede Korrektur** – `gelesen` gegen `korrigiert` |
| Namensinventar mit Haeufigkeit | Personentabelle |
| Orte, Berufe, Formeln, Abkuerzungen | erfasste Felder |
| Aequivalenzklassen | bestaetigte Zuordnungen |
| Movierungs-Ausnahmen | **Handpflege** – echte `-in`-Namen (Eberwein, Feuerstein) |
| Schreiber und Zeitraeume | **Handpflege** |

### Der Kreislauf

    Modell liest  ──►  Mensch korrigiert  ──►  Korrektur wird Wissen
         ▲                                              │
         └──────────  fliesst in den Prompt  ◄──────────┘

Lernen ohne Modelltraining. Nach zwanzig Seiten weiss die Anwendung, dass diese
Hand `Koch` wie `Roth` schreibt, und schreibt es dem Modell in den Prompt,
bevor es die einundzwanzigste Seite liest.

**Belegt aus dem Pilotlauf:** Der Fehlerkatalog existierte dort bereits als
Notiz, wurde aber nicht systematisch angewandt – Ergebnis 42 % Rohfehler.
Bei `Roßin` haette die notierte Regel "`R`↔`K`, `ß`↔`ch` bei dieser Hand belegt"
den Fehler sofort aufgeworfen.

### Auswertung, nicht Pflege

Der Fehlerkatalog ist eine Abfrage, keine Datei:

    SELECT gelesen, korrigiert, count(*)
    FROM feld
    WHERE korrigiert IS NOT NULL AND korrigiert <> gelesen
    GROUP BY gelesen, korrigiert
    ORDER BY count(*) DESC

Vorhandenes Wissen aus Vorarbeiten wird **importiert**, nicht abgetippt – es ist
der erste Datensatz, nicht die Ausnahme.

## Zielbild

Veroeffentlicht wird nicht ein Dienst, sondern **Software zum Selbstbetreiben**.
Nicht viele Helfer an einem Projekt, sondern viele Einzelne an ihren eigenen.
Die Architektur bleibt damit Einzelplatz; teilbar muss nur die Einrichtung sein.

**Zielgruppe, realistisch:** einige hundert aktive Ortsfamilienbuch-Projekte im
deutschsprachigen Raum, davon ein kleiner Teil – Dutzende, nicht Tausende.
Denkbar darueber hinaus: Forscher im Ausland, die dieselben Quellen bearbeiten
und meist ohne bestehenden Bestand beginnen – ein Grund mehr, warum der Fall
"bei Null anfangen" sauber funktionieren muss, aber keine Zielgruppe, auf die
hin gebaut wird.

### Sprache

Deutsch ist Standard, Englisch die zweite Sprache. Anzeigetexte gehoeren
deshalb von Anfang an in Sprachdateien:

    sprache/de.json      Standard
    sprache/en.json
    konfig.toml          sprache = "de"

Rund sechzig Texte – heute eine ueberschaubare Arbeit, nachtraeglich muessten
sie aus HTML, Python und Fehlermeldungen zusammengesucht werden.

**Nicht uebersetzt wird:** die Register selbst (das ist die Quelle), die
Kirchenbuchformen, und die Feldnamen in `konfig.toml` – die sind frei waehlbar.
Die Software behandelt Feldnamen als beliebige Zeichenketten; nur die **Rollen**
(`personen = [...]`) sind bedeutungstragend, weil die Anbindungslogik daran
haengt. Ein englischsprachiger Nutzer definiert sein Register vollstaendig auf
Englisch, solange die Rollen stimmen.

### Spaeter erweiterbar, nicht jetzt

Mehrbenutzerbetrieb ist nicht ausgeschlossen, wird aber nicht auf Vorrat gebaut.
Es genuegt **eine** Vorkehrung, die ohnehin noetig ist: eine `herkunft`-Spalte
je Datensatz. Sie wird fuer die Belegfuehrung gebraucht – woher stammt dieser
Wert – und kann spaeter auch aufnehmen, *wer* ihn eingetragen hat. Damit wird
aus der Erweiterung eine Spalte statt eines Umbaus.

Login, Sitzungen, Rechte, Sperren bei gleichzeitigem Bearbeiten: erst wenn
gebraucht.

## Eine Datenbasis, viele Eingangstüren

    GEDCOM ─┐
    XLSX   ─┤
    CSV    ─┼──►  person / familie  ◄── eigene Erfassung
    DOCX   ─┘            ▲
                         └── find-and-use sucht ausschließlich hier

Import ist ein Vorgang, kein Dauerzustand. Die Suche kennt keine Herkunft.
Damit ist kein Startbestand nötig: Wer bei Null anfängt, füllt die Tabelle durch
Erfassen – die ersten hundert Einträge tragen die nächsten tausend.

Erhalten bleiben muss die **Quelle je Person und je Feld**, sonst lässt sich
später weder gewichten noch zurückverfolgen, und beim Export nicht unterscheiden,
was neu ist und was schon da war.
