# Der Arbeitsablauf — Vorschlag zum Festzurren

Stand 5. August 2026. Diese Datei beschreibt **einen Arbeitstag an der
Werkstatt** von der ersten Seite bis zur GEDCOM-Ausgabe.

Zwei Zeichen trennen, was schon geht, von dem, was ich vorschlage:

    ✓  gebaut und gelaufen
    ○  vorgeschlagen, noch nicht gebaut
    ?  offene Entscheidung — hier ist Ihr Wort gefragt

---

## Die Grundfigur: zwei Taktgeber, nicht einer

Der erste Entwurf hatte hier einen Fehler: Er steckte **Lesen** und
**Vorlegen** in dieselbe Portionsgröße. Zwanzig Seiten lesen, dann zwanzig
Seiten vorlegen. Das ist falsch, weil beide Schritte aus entgegengesetzten
Gründen ihre Größe haben.

    Lesen legt zu    ganze Seite, im Voraus, im Hintergrund
                     · das Modell braucht die Nachbarzeilen als Eichung
                     · Batch ist seitenweise und halb so teuer
                     · niemand sieht dabei zu

    Vorlegen nimmt   EIN Eintrag, jetzt, im Vordergrund
                     · ein Mensch entscheidet immer nur eines
                     · was vorbei ist, soll vom Bildschirm

Dazwischen liegt eine **Schlange**: Der Läufer füllt sie seitenweise, der
Bearbeiter leert sie eintragsweise. Beide arbeiten gleichzeitig. Während Sie
Eintrag 7 entscheiden, wird Seite 4 gelesen.

    Läufer ──► [ Eintrag · Eintrag · Eintrag · … ] ──► Bearbeiter
      Seiten            die Schlange                 ein Eintrag
      im Voraus                                       zur Zeit

Damit stimmt beides: der Zusammenhang beim Lesen und die Ruhe beim Entscheiden.

## Die Tranche bleibt — aber als Reihenfolge, nicht als Wartezeit

Die Tranche ordnet, **in welcher Reihenfolge** die Register drankommen, nicht
wann Sie etwas zu sehen bekommen.

    ┌─ Tranche 1808–1820 ────────────────────────────┐
    │  Ehen  ──►  Taufen  ──►  Tode                  │
    │    ↓          ↓           ↓                    │
    │  übergeben  übergeben   übergeben              │
    └────────────────────────────────────────────────┘
                      ↓
              Tranche 1821–1832

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

## 1. Weitermachen, wo man war  ◑ teilweise gebaut

Beim Start soll **ein** Knopf dastehen, und er soll wissen, wo es weitergeht:

    ▸ Weiter — Taufregister, Eintrag 7 von 118

✓ Der Startbildschirm zeigt Stand und Vorschlag samt Begründung:
„erste Runde — Ehen zuerst, sie bauen den Anker".

○ **Der Merkpunkt ist zu grob.** Gemerkt wird die Runde, nicht der Eintrag.
Für „weiter, wo ich aufgehört habe" fehlt eine Zeile in der Datenbank.

○ **Beim neuen Projekt** sollte statt des Knopfes eine kurze Einrichtung
stehen: Wo liegen die Bilder, wie heißen die Register, welche Bestände gibt
es und **was davon darf bestätigen**. Heute ist das Handarbeit in
`konfig.toml`.

**Die Reihenfolge wird erzwungen, nicht empfohlen.** Solange eine Runde offen
ist, lässt sich keine zweite beginnen.

**? Tranchengröße.** Vorbelegt sind 20 Seiten. Bei Ehen sind das grob 100
Einträge und 600 Personenfelder — vermutlich zu viel. Vorschlag: **10 bei
Ehen, 20 bei Taufen und Toden**, weil ein Eheeintrag sechs Personen nennt und
ein Taufeintrag drei. Die Zahl steht ohnehin in den Einstellungen; sie
bestimmt nur, wie oft übergeben wird, nicht wie lange Sie warten.

---

## 2. Lesen — im Voraus, im Hintergrund  ✓

Der Läufer arbeitet die Seiten ab, während Sie an den vorigen Einträgen
sitzen. Das Browserfenster darf zugehen; der Zustand liegt in der Datenbank.

○ **Vorlauf statt Wartezeit.** Heute wird erst die ganze Runde gelesen und
dann vorgelegt. Richtig wäre: Sobald die erste Seite fertig ist, geht es los,
und der Läufer bleibt drei Seiten voraus. Bei 20 Seiten spart das die
Anfangswartezeit fast vollständig.

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

## 4. Vorlegen — die Bedienschleife  ◑ teilweise gebaut

Hier arbeitet der Mensch, und hier entscheidet sich, ob das Werkzeug taugt.

**Ein Eintrag füllt den Bildschirm.** Nicht zwanzig Seiten, nicht eine Seite —
ein Eintrag. Was entschieden ist, verschwindet; der nächste rückt nach. Die
Schlange dahinter ist unsichtbar.

    ┌──────────────────────────────────────────────────────────┐
    │  Taufe · Nr. 11 · 1808        Eintrag 7 von 118    ▓▓░░░░ │
    ├──────────────────────────────────────────────────────────┤
    │  [ Zeilenstreifen, volle Breite, Nachbarzeilen gedimmt ]  │
    │                        ▲                                  │
    │                   die fragliche Stelle markiert           │
    │              ┌─────────────┐                              │
    │              │  Ausschnitt │  ← Lupe daneben              │
    │              └─────────────┘                              │
    ├──────────────────────────────────────────────────────────┤
    │  gelesen und stimmig — nichts zu tun                      │
    │  ● Kind      Johannes          ● geb. 3. Febr.            │
    │  ● Vater     Bürger u. Weingärtner in Haberschlacht       │
    │                                                           │
    │  BITTE PRÜFEN                                             │
    │  ◐ Vatername   [Faller         ]                          │
    │      Vorschlag  Johann Georg Faller ⚭ Rosina Maier        │
    │                 oo 1798 · 3 Kinder · F1149                │
    │                                                           │
    │      [ Ja, dieser ]   [ anderer… ]   [ neu anlegen ]      │
    └──────────────────────────────────────────────────────────┘
                              ↓  Enter
                          nächster Eintrag

**Was sicher ist, wird nicht gefragt.** Datum, Vorname, Beruf und Ort waren im
Pilotlauf praktisch fehlerfrei — sie stehen da, sichtbar, aber ohne Frage.
Gefragt wird bei Familiennamen und bei allem, was der Abgleich nicht trägt.

**Der Zeilenstreifen bleibt immer sichtbar**, auch bei den stillen Feldern.
Wer mitliest, will hinsehen können — und dieselbe Hand schreibt in jedem
Eintrag `B. u. Weingärtner in Haberschlacht`, woran man die Buchstaben eicht.

**Ein Tastendruck je Entscheidung.** `Enter` nimmt den Vorschlag und geht
weiter, `N` legt neu an, `Pfeil` blättert durch Alternativen. Tippen nur,
wenn wirklich etwas anderes dasteht.

### Was angeboten wird — je Registerart verschieden

Das ist die eigentliche OFB-Arbeit. Zu jeder genannten Person muss entschieden
werden: gibt es sie schon, oder ist sie neu?

| Register | wer wird angebunden | woran |
|---|---|---|
| **Ehe** | Bräutigam, Braut | Geburtsdatum + Ort stehen im Eintrag → Taufe tagesgenau. Der stärkste Anker, und er trifft **beide** Hauptpersonen |
| | deren Eltern | über die gefundene Taufe — und die Vaterangabe des Eheeintrags prüft sie gegen |
| | die neue Familie | wird angelegt, beide als Kind ihrer Herkunftsfamilie verknüpft |
| **Taufe** | Vater, Mutter | Elternehe im Bestand. Die Mutter wird *abgeleitet*, nicht gesucht — deshalb trägt der Anker auch, wenn ihr Name falsch gelesen wurde |
| | Kind | immer neu, in die Elternfamilie eingehängt |
| **Begräbnis** | Verstorbener | Alter → Geburtsdatum, bei Monats- und Tagesangabe oft tagesgenau → Taufe |
| | bei „weyl.", Witwe, Witwer | erst die Ehe, daraus der Partner — und bei verheirateten Frauen der Mädchenname, ohne den die Taufe nicht zu finden ist |
| | genannte Eltern | gegen die Eltern der gefundenen Taufe geprüft |

✓ gebaut: Taufe.  ○ offen: Ehe und Begräbnis. Für die rankt der Abgleich
derzeit nur Nachnamen und macht nie grün.

**Zwei Regeln, die dabei nie fallen dürfen:**

> Ein Match braucht **mindestens zwei übereinstimmende Merkmale, von denen
> eines nicht der Nachname ist.** Nachname + Jahr genügt nie — sonst wird aus
> „Johannes Bierle" die Taufe von *Carl Heinrich* Bierle.

> **Nichtfinden ist ein Ergebnis, kein Fehler.** Zuzug, andere Parochie, Lücke
> im Buch. Das gehört vermerkt, nicht weggedrückt.

○ **Die Lupe fehlt.** Heute gibt es den ganzen Zeilenstreifen, nicht den
Ausschnitt am Feld. Vereinbart ist die Arbeitsteilung: Das Modell sagt,
*welche* Zeile und *welche* Spalte — das braucht keine Pixel, weil Einträge
und Zeilenbänder dieselbe Reihenfolge haben —, die Geometrie liefert die
Pixel. Nachbarzeilen werden abgedunkelt, nicht weggeschnitten.

○ **Der Chronologie-Anker wird nicht genutzt.** Register sind chronologisch
geführt; ein Datum außerhalb des Nachbarintervalls ist widerlegt, ohne dass
etwas nachgeschlagen wird. Die Sicht `chronologie` existiert, die Maske
zeigt sie nicht.

○ **Eintragsweise Wiederaufnahme.** Heute merkt sich die Werkstatt die Runde,
nicht den Eintrag. „Weiter, wo ich aufgehört habe" heißt derzeit „diese
Runde", nicht „Eintrag 7 von 118".

---

## Wie viel darf die Maschine allein entscheiden?  ○

Das ist die Stellschraube, an der alles hängt, und sie gehört in die
Einstellungen — nicht in den Code und nicht in mein Urteil.

    [gang]
    autopilot = "normal"

| Stufe | läuft ohne Frage durch | wird vorgelegt |
|---|---|---|
| `streng` | nichts | jedes Feld |
| `normal` | grün | gelb und rot |
| `zuegig` | grün + gelb mit genau einem Kandidaten | rot und Mehrdeutiges |

**Jede Stufe höher tauscht Tempo gegen stille Fehler.** Das ist keine
Vermutung: Beim ersten Lauf ordnete der Abgleich einer Taufe von **1809** ein
Paar zu, das 1699 und 1703 geboren wurde und dessen Frau 1767 starb —
einziger gemeinsamer Nachname, kein Trauungsdatum, und damit grün. Gefunden
hat ihn nur die Messung gegen die geprüfte Wahrheit. Von innen sah er wie ein
Erfolg aus.

Deshalb bleibt eine Grenze fest, unabhängig von der Stufe:

> **Die Selbsteinschätzung des Modells darf nie grün machen.** Sie darf
> bestimmen, was zuerst gezeigt wird — nicht, was als bestätigt gilt.
> Bei `Koch`/`Roth` war das Modell viermal sicher und viermal falsch.

Weitere Einstellungen, die ich vorsehen würde:

    [gang]
    autopilot        = "normal"
    tranche_ehe      = 10        # Seiten je Runde
    tranche_taufe    = 20
    tranche_tod      = 20
    vorauslesen      = 3         # Seiten Vorlauf vor dem Bearbeiter
    ausgabe_je_tranche = true    # GEDCOM nach jeder Tranche

    [grenzen]
    mutter_alter = [14, 50]      # für die Plausibilitätsprüfung
    vater_alter  = [16, 70]

**? Sollen bestätigte Entscheidungen zurückwirken?** Wenn Sie einmal sagen,
`Bührlin` ist `Bierle`, gilt das fortan — jede Bestätigung ist eine neue Kante
im Klassengraphen. Vorsicht dabei: Die Relation ist **nicht transitiv**. Eine
einzige falsche Kante (`Bührle → Müller`, ein einziger Beleg) verschmolz im
Pilotbestand zwei fremde Familien zu einer Klasse von 231 Personen. Ich würde
solche Kanten sammeln und erst nach Schreibnähe plus Belegzahl übernehmen,
nicht sofort.

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

## 7. Ausgeben  ✓

Zwei Arten, beide gebaut und gemessen:

| | für wen | Ergebnis am Bestand Haberschlacht |
|---|---|---|
| **Fortschreibung** | wer ein OFB hat | 5.605 Records zeichengleich durchgereicht, 9 ergänzt, 57 neu, **0 verloren, 0 tote Verweise** |
| **Neuausgabe** | Nullstart | 4.156 Personen, 1.358 Familien — aber nur **31 % der Dateigröße** |

**Der Leerlauftest ist der Beleg.** Ohne Änderungen muss die Ausgabe Byte für
Byte der Vorlage entsprechen:

    ✓ Leerlauftest: 3444327 Byte, zeichengleich

Er misst nicht, ob die Ausgabe plausibel aussieht, sondern ob überhaupt etwas
verloren ging — und zeigt bei Abweichung die Bytestelle.

**Warum Durchreichen die Voreinstellung ist**, sieht man an den 31 %: Ein
gewachsenes Ortsfamilienbuch enthält Jahrzehnte Handarbeit in Feldern, die
diese Werkstatt gar nicht kennt — Quellenangaben, Notizen, Paten, Bilder,
Ortsdefinitionen. Wer aus den eigenen Tabellen neu schreibt, wirft zwei
Drittel davon weg. Die Oberfläche fragt vor der Neuausgabe deshalb nach.

○ **Noch nicht ausgewertet: das Journal.** Es füllt sich (57 Vorgänge je
Runde, jeder mit seinem Beleg), aber die Fortschreibung leitet ihre
Ergänzungen bisher aus den Daten ab, nicht aus den Vorgängen. Nötig wird das
erst, wenn Records nicht nur ergänzt, sondern **geändert** werden — bei
Korrekturen an vorhandenen Personen und beim Zusammenlegen von Dubletten.

**? Wann wird ausgegeben?** Vorschlag: nach jeder Tranche, nicht am Ende.
Dann liegt der Zwischenstand jederzeit in einem Format, das jedes andere
Programm liest, und ein Fehler fällt nach einer Tranche auf, nicht nach
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

## Der Abstand zwischen heute und diesem Bild

Ehrlich aufgeschrieben, was zwischen dem Gebauten und dem Beschriebenen liegt:

| | heute | beschrieben |
|---|---|---|
| Vorlegen | ganze Runde auf einer langen Seite | **ein Eintrag zur Zeit** |
| Wiederaufnahme | „diese Runde" | **„Eintrag 7 von 118"** |
| Lesen | erst alles, dann vorlegen | **Vorlauf, drei Seiten voraus** |
| Bild | ganzer Zeilenstreifen | **Lupe am Feld** |
| Anbindung | nur Taufe | **alle drei Register** |
| Bedienung | klicken, tippen | **eine Taste je Entscheidung** |
| Autopilot | fest verdrahtet | **Einstellung, drei Stufen** |
| ~~Ausgabe~~ | ~~keine~~ | **erledigt am 6. August** |

Das ist mehr Arbeit als das, was bisher steht — aber es ist kein Umbau. Die
Datenbank trägt es bereits: Die Schlange ist `SELECT … WHERE runde=? AND
status<>'bestaetigt' ORDER BY …  LIMIT 1`, der Merkpunkt eine Spalte, der
Vorlauf ein Startsignal an den Läufer nach der ersten Seite statt nach der
letzten.

---

## Was ich zum Festzurren vorlege

Neun Punkte, bei denen ich eine Meinung habe, aber Sie entscheiden:

1. **Ein Eintrag zur Zeit**, nicht die ganze Runde auf einer Seite. Der
   Läufer bleibt drei Seiten voraus, die Schlange ist unsichtbar.
2. **Eine Taste je Entscheidung.** `Enter` nimmt den Vorschlag, `N` legt neu
   an, Pfeile blättern Alternativen. Tippen nur im Ausnahmefall.
3. **Autopilot als Einstellung**, drei Stufen, Vorgabe `normal`. Aber die
   Selbsteinschätzung des Modells macht auf keiner Stufe grün.
4. **Tranchengröße 10 bei Ehen, 20 bei Taufen und Toden** — sechs Personen
   je Eheeintrag gegen drei je Taufeintrag.
5. **GEDCOM nach jeder Tranche**, nicht am Ende.
6. **Der Familienbuch-Anker zuerst**, vor den Kaskaden für Ehe und Tod. Er
   ist billiger und stärker: eine Zahl aus der letzten Spalte, vom Pfarrer
   gesetzt, gültig über alle drei Register.
7. **Erst die Ausgabe, dann alles andere.** Ein Werkzeug, das nichts
   herausgibt, ist nicht benutzbar, auch wenn es innen fertig ist.
8. **Bestätigte Namensgleichungen sammeln, nicht sofort übernehmen.** Eine
   falsche Kante verschmolz im Pilotbestand 231 Personen zu einer Klasse.

**Zurückgestellt: der Qualitätstest.** Eine Eheseite mit bekannter Wahrheit
gegen das Modell — die einzige Messung, die etwas über die *Lesequalität*
sagen würde. Braucht `ANTHROPIC_API_KEY` und kostet Geld. Auf Entscheidung
vom 5. August vertagt.

Folge, damit sie später nicht überrascht: **Alle Zahlen der Werkstatt messen
bis dahin die Verknüpfung, nicht das Lesen.** Die 46 % Wiederfindungsquote
stammen aus bereits korrigierten Lesungen. Solange das so bleibt, gehört in
kein README eine Aussage darüber, wie gut das Werkzeug liest.

Für den Bau ist das kein Hindernis: Die Testquelle trägt den ganzen Ablauf
ohne Schlüssel. Was fehlt, ist nur das Urteil über die Rohlesung.

---

## Festgezurrte Reihenfolge

    1  Ausgabe            ✓ erledigt 6. August
    2  Bedienschleife     ein Eintrag, eine Taste     ← als Nächstes
    3  Familienbuch-Anker billiger und stärker als die Kaskaden
    4  Kaskaden Ehe/Tod
    …  Qualitätstest      wenn Sie so weit sind

Punkt 2 lässt sich gegen die Testquelle bauen und prüfen, braucht also
weiterhin keinen Schlüssel.

### Was die Ausgabe nebenbei aufgedeckt hat

Drei Fehler, die still in die GEDCOM-Datei gewandert wären:

1. **Der Import verwarf 158 Records.** HEAD, SUBM, 35 SOUR, 120 `_LOC` und
   TRLR wurden nie gespeichert, obwohl der Docstring „verlustfrei" behauptete.
   Die `_LOC`-Records sind die Ortsdefinitionen, auf die jede Person mit
   `3 _LOC @L1@` zeigt. Jetzt liegt die ganze Datei in `rec`.
2. **Die Übergabe legte Familien doppelt an.** Von 22 übergebenen Familien
   gab es 10 mit denselben Eltern bereits im Bestand — der Elternehe-Anker
   fand sie, und die Übergabe legte sie daneben noch einmal neu an.
3. **Der Täufling bekam seinen Vornamen als Nachnamen.**
   `Georg Christian /Georg Christian/`. Im Taufregister hat das Kind keinen
   Nachnamen; er kommt vom Vater. 21 Kinder erben ihn jetzt.

Alle drei wären ohne die Ausgabe unentdeckt geblieben — sie werden erst
sichtbar, wenn etwas das Haus verlässt.

Was noch anders soll, sagen Sie mir — sonst arbeite ich das der Reihe nach ab.
