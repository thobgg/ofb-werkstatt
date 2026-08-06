# Der Arbeitsablauf — Vorschlag zum Festzurren

Stand 5. August 2026. Diese Datei beschreibt **einen Arbeitstag an der
Werkstatt** von der ersten Seite bis zur GEDCOM-Ausgabe.

Zwei Zeichen trennen, was schon geht, von dem, was ich vorschlage:

    ✓  gebaut und gelaufen
    ○  vorgeschlagen, noch nicht gebaut
    ?  offene Entscheidung — hier ist Ihr Wort gefragt

---

## Die Grundfigur

Nicht „Seite lesen, Seite prüfen, nächste Seite", sondern **Tranchen**. Eine
Runde ist ein Block Seiten EINES Registers, der zusammen durch alle Schritte
geht:

    ┌─ Runde ──────────────────────────────────────────────┐
    │  planen → lesen → abgleichen → korrigieren → übergeben │
    └──────────────────────────────────────────────────────┘
              ↓
       nächstes Register

Der Grund ist kein Geschmack, sondern eine Messung. Der Elternehe-Anker trägt
im Taufjahr 1808 noch 94 %, 1813 noch 53 %, 1820 nur 18 % — **es sei denn,
die Ehen ab 1808 sind vorher übergeben.** Dann wächst er mit. Wer die Taufen
vorzieht, prüft sie später ein zweites Mal.

Deshalb: **Ehen → Taufen → Tode**, und erst dann die nächste Tranche.

---

## 0. Einrichten — einmal je Ort

✓ **Register beschreiben.** `konfig.toml` nennt Registerarten, ihre Felder und
die Personenrollen. Nichts davon steht im Code.

✓ **Bilder ablegen.** `bilder/ehe/`, `bilder/taufe/`, `bilder/tod/`. Die
Werkstatt liest, was da liegt, und schreibt nie hinein.

✓ **Kontextquellen eintragen** — der wichtigste Schritt der Einrichtung.
Jede Quelle bekommt ihren Rang:

    gilt = "beleg"       darf bestätigen  → ein Treffer macht grün
    gilt = "vokabular"   rankt nur        → ein Treffer bleibt gelb

Eigene Pfade in `konfig.local.toml` (gitignoriert). Keine Quelle eingetragen
heißt Nullstart — alles bleibt gelb, jedes Feld wird vorgelegt. Langsam, aber
nicht falsch.

○ **Bestände importieren.** Bisher nur GEDCOM. XLSX, CSV und DOCX sind im
Entwurf gezeichnet und nicht gebaut — genau die Formate, in denen die
Nachbarorte vorliegen (Frauenzimmern, Güglingen, Zabergäu).

○ **Quellwissen importieren.** Der Fehlerkatalog dieser Hand steht in
`wissen/haberschlacht.md` und muss abgetippt werden, statt eingelesen zu
werden. Er gehört in den Prompt, bevor die erste Seite gelesen wird.

○ **Spaltenraster ziehen**, einmal je Buch. Voraussetzung für die Lupe.
Die Zeilen sitzen automatisch (22/22 bei ±40 px), die Spalten nicht.

---

## 1. Runde planen  ✓

Der Startbildschirm zeigt den Stand und **einen** Knopf. Er sagt auch, warum:

    Als Nächstes: ehe — erste Runde, Ehen zuerst, sie bauen den Anker

Zu wählen sind Register, Seitenzahl und Quelle. Vorbelegt ist, was der
Vorschlag nennt.

**? Tranchengröße.** Ich habe 20 Seiten vorbelegt, weil `ROADMAP.md` von
~12 Jahren je Tranche und 35–40 Buchöffnungen über alle drei Register
spricht. Ob 20 die richtige Portion ist, weiß ich nicht — das hängt daran,
wie lange Sie am Stück korrigieren wollen. Bei 20 Ehe-Seiten kommen grob
100 Einträge und 600 Personenfelder zusammen.

**Die Reihenfolge wird erzwungen, nicht empfohlen.** Solange eine Runde offen
ist, lässt sich keine zweite beginnen. Nach „fertig" schaltet der Vorschlag
auf das nächste Register.

---

## 2. Lesen  ✓

Der Läufer arbeitet die Seiten im Hintergrund ab. Das Browserfenster darf
zugehen; der Zustand liegt in der Datenbank.

    Runde 3 · ehe wird gelesen
    ████████████░░░░░░░  12 von 20 Seiten · gerade 1184798-00929
    fertig   1184798-00917   5 Einträge
    fehler   1184798-00922   ⚠ HTTPError 529
    laeuft   1184798-00929

**Fehler gelten je Seite, nicht je Lauf.** Bricht Seite 7 ab, laufen 8 bis 20
trotzdem durch, und die siebte trägt ihre Meldung. In einem Hintergrund-Thread
wäre ein Abbruch sonst ein stiller Tod.

**Zwei Quellen.** `api` schickt die Bilder an das Modell. `testdaten` spielt
die 22 Piloteinträge ein und kostet nichts — dafür da, dass sich der ganze
Ablauf ohne Schlüssel prüfen lässt.

○ **Batch statt Einzelanfragen.** Halbiert die Kosten (0,13 → 0,07 $/Seite).
Der Rundenautomat ist bereits die Struktur, die Batch braucht: eine Liste
eingereichter Einheiten mit Zustand. Wer synchron baut und später nachrüstet,
baut sie zweimal.

○ **Was im Prompt mitgeht** — heute unvollständig: Fehlerkatalog dieser Hand,
Nachbardaten für den Chronologie-Anker, Nachbarzeilen als Kontext, und die
Bitte, je Feld die **Position** zu nennen (welches Zeilenband, welche Spalte).

---

## 3. Abgleichen  ✓ — läuft von selbst, ohne Zutun

Sobald die letzte Seite gelesen ist, läuft der Abgleich durch und setzt je
Feld die Ampel. **Das ist der eigentliche Wert der Werkstatt**, nicht das
Lesen.

| | |
|---|---|
| **grün** | ein Anker bestätigt, aus einer Quelle die bestätigen darf |
| **gelb** | gelesen, aber nichts bestätigt es |
| **rot** | kein Kandidat, oder die Kandidaten widersprechen sich |

Drei Dinge machen ausdrücklich **nicht** grün, alle drei teuer gelernt:

* Die **Selbsteinschätzung des Modells** — bei `Koch`/`Roth` war es viermal
  sicher und viermal falsch.
* **Häufigkeit und Wortschatz** — `Roth` kommt 59-mal im Bestand vor und
  stand doch für `Koch`.
* **Ein Treffer aus einer Vokabularquelle**, auch wenn er perfekt passt.

✓ Kaskade für die **Taufe**: Elternehe-Anker, mit Lebensgrenzen.
○ Kaskaden für **Ehe** und **Tod** — für die rankt der Abgleich derzeit nur
Nachnamen und macht nie grün. `kaskade_tod.py` liegt fertig und ist nicht
angeschlossen (59,8 % Treffer gemessen).

○ **Der Familienbuch-Anker fehlt ganz.** Die letzte Registerspalte nennt die
Seite des Familienregisters; gleiche Nummer heißt gleiche Familie, gesetzt
vom Pfarrer. Der stärkste Anker überhaupt, und er verbindet Taufe, Ehe und
Tod über die Register hinweg. `eintrag.fam_reg` existiert seit gestern, wird
aber weder gelesen noch ausgewertet.

---

## 4. Korrigieren  ✓ — hier arbeitet der Mensch

Die Maske zeigt **genau diese Runde**, nicht den ganzen Bestand.

    ┌────────────────────────────────────────────────────┐
    │ Nr. 11   1808   1184798-00361                      │
    ├────────────────────────────────────────────────────┤
    │ [ Zeilenstreifen des Eintrags, volle Breite ]      │
    ├────────────────────────────────────────────────────┤
    │ ● VATER    [Faller        ]  I2799  Elternehe F1149│
    │ ● MUTTER   [Maier         ]  I2800  Elternehe F1149│
    │ ○ KIND     [Johannes      ]  wird neu angelegt     │
    ├────────────────────────────────────────────────────┤
    │ Familie  F1149  Faller ⚭ Maier · 1798 · 3 Kinder   │
    │          → Kind hier einhängen                     │
    └────────────────────────────────────────────────────┘

**Der Zeilenstreifen bleibt immer sichtbar**, auch bei grünen Feldern. Wer
mitliest, will hinsehen können — und dieselbe Hand schreibt in jedem Eintrag
`B. u. Weingärtner in Haberschlacht`, woran man die Buchstaben eicht.
Bestätigtes wird eingeklappt, nicht versteckt.

Je Feld gibt es drei Wege: **übernehmen** (find and use), **neu anlegen**,
oder den Wert ändern. Beim Tippen schlägt die Suche Namen und Personen vor.

**? Wie viel Vorlage ist richtig?** Gemessen an den Testdaten brauchten
24 von 102 Feldern eine Entscheidung. Ich schlage vor: Die Maske springt von
Rot zu Rot, dann zu Gelb, Grün wird nur durchgeblättert. Ob Sie lieber alles
der Reihe nach sehen wollen, ist Ihre Entscheidung — Sie lesen die Hand.

○ **Die Lupe fehlt.** Heute gibt es den ganzen Zeilenstreifen, nicht den
Ausschnitt am Feld. Vereinbart ist die Arbeitsteilung: Das Modell sagt,
*welche* Zeile und *welche* Spalte — das braucht keine Pixel, weil Einträge
und Zeilenbänder dieselbe Reihenfolge haben —, die Geometrie liefert die
Pixel. Nachbarzeilen werden abgedunkelt, nicht weggeschnitten.

○ **Der Chronologie-Anker wird nicht genutzt.** Register sind chronologisch
geführt; ein Datum außerhalb des Nachbarintervalls ist widerlegt, ohne dass
etwas nachgeschlagen wird. Die Sicht `chronologie` existiert, die Maske
zeigt sie nicht.

---

## 5. Übergeben  ✓ — zwei Klicks, dazwischen die Wahrheit

Erst der Probelauf, der zeigt, **was entstehen wird**:

    Einträge             22
    Personen neu         45
    Personen verknüpft   20
    Familien             22
    Kinder eingehängt    22
    Ereignisse            0

Dann erst der Knopf, der schreibt.

**Nur bestätigte Einträge gehen über.** Was das Modell gelesen und niemand
geprüft hat, wird nicht zum Anker für die nächste Tranche — sonst verfestigen
sich Lesefehler stillschweigend.

**Die Zahl „Personen neu" ist die wichtige.** Sie sagt, wie viele Menschen
angelegt werden, die es womöglich schon gibt. Bei 46 % Trefferquote entstanden
aus 44 Elternplätzen 24 vermutliche Dubletten. Diese Zahl ist der beste
verfügbare Gradmesser für die Qualität des Abgleichs.

○ **Eine Runde verwerfen** geht heute nur auf der Kommandozeile
(`runde --verwirf N`), nicht in der Oberfläche.

---

## 6. Registerwechsel  ✓

Nach der Übergabe schaltet der Vorschlag weiter: Ehen → Taufen → Tode → Ehen.
Der Bestand ist gewachsen; die nächste Runde ankert gegen die vorige.

Das ist der Mechanismus **„die ersten hundert tragen die nächsten tausend"**.
Ohne die Übergabe dazwischen bringt die Tranchenordnung nichts.

---

## 7. Ausgeben  ○ — noch gar nicht da

Die auffälligste Lücke: **Die Werkstatt gibt derzeit nichts heraus.**

Zwei Arten sind nötig, und beide werden gebraucht:

| | für wen | wie |
|---|---|---|
| **Fortschreibung** | wer ein OFB hat | unberührte Records zeichengleich aus `person.raw` durchreichen, nur berührte neu schreiben. Leerlauftest: leeres Journal → byte-identisch |
| **Neuausgabe** | Nullstart | alles aus `person`/`familie`/`ereignis`, mit `_KB_NAME`, `_BERUF_KB`, `_NOTE_TAUFE` |

**? Wann wird ausgegeben?** Ich schlage vor: nach jeder Tranche, nicht am
Ende. Dann ist der Zwischenstand jederzeit in einem Format, das jedes andere
Programm liest — und ein Fehler fällt nach einer Tranche auf, nicht nach
dreißig.

---

## Wer entscheidet was

| | Modell | Skript | Mensch |
|---|---|---|---|
| Handschrift lesen | ✓ | | |
| Kandidaten einschätzen | ✓ | | |
| Abgleich gegen den Bestand | | ✓ | |
| Regelentscheidungen | | ✓ | |
| Daten ändern, zusammenlegen, ausgeben | | ✓ | |
| Paläographie im Zweifel | | | ✓ |
| Mehrdeutige Zuordnung | | | ✓ |
| Kanonische Namensform festlegen | | | ✓ |
| Umfang, Reihenfolge, Kosten | | | ✓ |

**Was Daten verändert, muss reproduzierbar sein.** Ein Modell entscheidet bei
jedem Durchlauf womöglich anders. Also schlägt das Modell vor, das Skript
führt aus, das Journal hält beides fest.

---

## Der Kreislauf, der das Ganze besser macht

    Modell liest  ──►  Mensch korrigiert  ──►  Korrektur wird Wissen
         ▲                                              │
         └──────────  fließt in den Prompt  ◄───────────┘

✓ Die Sicht `fehlerkatalog` wertet `gelesen` gegen `korrigiert` aus.
✓ `lesen.py` schreibt sie in den Prompt.
○ Vorhandenes Wissen wird noch nicht importiert — der Katalog dieser Hand
liegt als Text vor und müsste abgetippt werden.

Nach zwanzig Seiten weiß die Werkstatt, dass diese Hand `Koch` wie `Roth`
schreibt, und sagt es dem Modell, bevor es die einundzwanzigste liest.
Lernen ohne Modelltraining.

---

## Was ich zum Festzurren vorlege

Sieben Punkte, bei denen ich eine Meinung habe, aber Sie entscheiden:

1. **Tranchengröße 20 Seiten.** Bei Ehen sind das ~100 Einträge und ~600
   Personenfelder — vermutlich zu viel für eine Sitzung. Vorschlag: 10 für
   Ehen, 20 für Taufen und Tode, weil ein Eheeintrag sechs Personen hat und
   ein Taufeintrag drei.
2. **Korrekturreihenfolge Rot → Gelb → Grün** statt der Reihe nach.
3. **GEDCOM nach jeder Tranche**, nicht am Ende.
4. **Der Familienbuch-Anker zuerst**, vor den Kaskaden für Ehe und Tod. Er
   ist billiger und stärker: eine Zahl aus der letzten Spalte, vom Pfarrer
   gesetzt, gültig über alle drei Register.
5. **Erst die Ausgabe, dann alles andere.** Ein Werkzeug, das nichts
   herausgibt, ist nicht benutzbar, auch wenn es innen fertig ist.
6. **Der Qualitätstest vor dem weiteren Ausbau.** Eine Eheseite mit bekannter
   Wahrheit, gegen das Modell. Bisher ist ungeprüft, wie gut es liest — alle
   Zahlen messen die Verknüpfung.
7. **Kein Ausbau der Oberfläche**, bis 5 und 6 stehen.

Was davon anders soll, sagen Sie mir. Danach zurren wir es fest und ich
arbeite es der Reihe nach ab.
