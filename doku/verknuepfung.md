# Verknüpfungskaskade – der anspruchsvollste Teil

Nicht das Lesen ist die OFB-Arbeit, sondern das **Verknüpfen**: Zu jedem
Registereintrag muss entschieden werden, welche der genannten Personen im
Bestand schon existieren und welche neu sind. Die Kaskade ist je Aktart
verschieden.

Belege unten stammen aus einem Test gegen `~/ofb-ki/kirchenbuch.db`,
Parochie Haberschlacht.

## Der stärkste Anker: die Familienbuch-Nummer

Die letzte Spalte der Register ab 1808 nennt die **Seitenzahl des
Familienregisters**. Beispiel Taufregister Bd. 4, Bild 00361:

    Nr.  7   150      Nr. 10   26
    Nr.  8    38      Nr. 11   69
    Nr.  9   146      Nr. 12   78

**Alle Einträge mit derselben Nummer gehören zur selben Familie** – ohne
Namensabgleich, ohne Datumsvergleich, ohne Wahrscheinlichkeitsrechnung. Der
Verweis stammt vom Pfarrer selbst und ist damit die höchste verfügbare
Autorität.

Der Nutzen entsteht **auch ohne das Familienbuch selbst**, weil die Nummer
register-übergreifend verbindet:

    FB 69   Ehe   1798  Faller ⚭ Maier
            Taufe 1808  Nr. 11, Johannes
            Taufe 18xx  Geschwister
            Tod   1844  Johannes Faller

Damit fallen Taufe, Ehe und Tod derselben Familie von selbst zusammen – die
Kaskade unten wird dort überflüssig, wo die Nummer lesbar ist.

### In allen drei Registern vorhanden

| Register | Spalte |
|---|---|
| Taufen Bd. 4 | 9, letzte – *Seitenzahl des Familien-Registers* |
| Sterberegister | letzte Spalte |
| Eheregister Bd. 6 | letzte Spalte (zu prüfen) |

Damit verbindet die Nummer nicht nur innerhalb eines Registers, sondern **über
alle drei hinweg** – genau die Kette Taufe → Ehe → Tod, für die sonst die
Kaskade nötig ist.

### Vorbehalte

1. **Kleine Ziffern, teils unsicher.** Bei Nr. 9 ist `146` oder `445` lesbar.
   Ein Lesefehler verknüpft falsch. Prüfbar dadurch, dass die Nummern über die
   Jahrgänge meist aufsteigen und mehrere Einträge derselben Familie sich
   gegenseitig bestätigen.
2. **Nur innerhalb einer Parochie gültig.** Familienbuch Haberschlacht ist
   nicht Familienbuch Bönnigheim. Die Nummer muss immer mit der Parochie
   zusammen geführt werden.
3. **Nicht jeder Eintrag trägt eine.** Uneheliche Geburten, Auswärtige und
   Durchreisende bleiben ohne – dort greift weiter die Kaskade.

### Rang unter den Ankern

    1  Familienbuch-Nummer     vom Schreiber gesetzt, register-übergreifend
    2  Geburtsdatum + Ort      tagesgenau, im Eheregister Spalte 6
    3  Elternehe               Mutter wird abgeleitet statt gesucht
    4  Chronologie, Kontext    kostenlos, bestandsunabhängig
    5  Vokabular               rankt, bestätigt nie

### Schreibweisen stabilisieren sich ab ~1810

Gegenüber dem 16./17. Jahrhundert sind die Namensformen ab etwa 1810 gefestigt.
Das wirkt zweifach:

**Für die Lesung günstig** – kleinerer Lösungsraum. Ein gelesenes `Kröneck` ist
um 1830 wahrscheinlich genau so geschrieben; 1650 stehen `Krönich`, `Kroneck`,
`Krönegk` nebeneinander.

**Für den Rückbezug entscheidend** – und deshalb bleiben die Äquivalenzklassen
nötig, nur in umgekehrter Richtung als zunächst gedacht: Die **stabile Form von
1830 muss die variablen alten Formen finden**, wenn Eltern und Großeltern in
Beständen von 1750 gesucht werden. `Bierle` muss `Bührlen`, `Bürle`, `Bierlen`
treffen.

Das erklärt, warum `kirchenbuch.db` mit 21.565 Namensvarianten aus dem
16.–18. Jahrhundert für die Arbeit ab 1808 wertvoll bleibt, obwohl die
Zeiträume sich nicht überschneiden.

## Taufe

    Vater  ──► suche Person (Name + Ort + plausibles Alter)
           ──► seine Ehe(n) vor dem Taufdatum
    Mutter ──► bestätigt sich aus der Ehe, statt eigenständig gesucht zu werden
    Familie ─► gemeinsame Familie von Vater und Mutter
    Kind   ──► immer neu, dort eingehängt

**Der Elternehe-Anker.** Die Mutter wird nicht gesucht, sondern *abgeleitet* –
deshalb trägt er auch, wenn ihr Name falsch gelesen wurde. Im Pilotlauf fand er
vier Fälle, in denen der *Vater*name falsch war und der Treffer allein über die
Vornamen der Mutter kam.

Fehlt die gemeinsame Familie, obwohl beide Eltern gefunden sind: **nicht still
neu anlegen** – das ist entweder eine Zweitehe oder eine Fehlzuordnung.

## Heirat

    Bräutigam ──► Geburtsdatum + Ort stehen im Register (Spalte 6)
              ──► Taufe suchen, tagesgenau
              ──► daraus seine Eltern
    Vater d. Br. ─► gegen die Vaterangabe des Eheeintrags prüfen (zweiter Beleg)
    Braut     ──► dasselbe
    Familie   ──► neu; beide als Kind ihrer Herkunftsfamilie verknüpfen

Der stärkste Anker überhaupt, weil das Geburtsdatum tagesgenau im Eintrag steht
und **beide** Hauptpersonen betrifft.

## Tod, Kind

    Alter ──► Geburtsjahr
          ──► Taufe suchen
    Eltern im Sterbeeintrag ──► gegen die Eltern der Taufe prüfen
    Sterbedatum an die getaufte Person anhängen

## Tod, Erwachsener

    Alter ("39 Jahre, 5 Monate, 24 Tage") ──► Geburtsdatum, oft TAGESGENAU
          ──► Taufe suchen
    "weyl." / Witwe / Witwer ──► Ehe suchen ──► Partner
    zwei unabhängige Belege: Taufe UND Ehe

**Belegter Treffer:**

    † 14.01.1800  Catharina Dorothea Schneider, Alter 39 J 5 M 24 T
      → errechnet geb. 21.07.1760
      → Taufe 21.07.1760 – auf den Tag
      → Eltern Joh. Friedrich Schneider ⚭ Christina Susanna Felger
      → im Sterbeeintrag genannter Vater: derselbe ✓

## Die drei Fehlschläge – und was daraus folgt

| Fall | Ursache | Konsequenz |
|---|---|---|
| Johannes Meßner, keine Taufe am Ort | Zuzug | Nichtfinden ist **kein Fehler**, sondern Information: Person kam von auswärts |
| Catharina Magdalena Würz ⚭ Wilhelm Würz | heißt Würz **durch Heirat**, Taufe steht unter unbekanntem Mädchennamen | bei verheirateten Frauen **zuerst die Ehe suchen**, daraus den Mädchennamen, dann die Taufe |
| „Johannes Bierle" → Taufe *Carl Heinrich* Bierle | nur Nachname + Jahr gematcht | **Vorname ist Pflichtbedingung**, sonst stille Fehlverknüpfung |

Der dritte ist der gefährliche: Ein Falschtreffer sieht aus wie ein Erfolg und
wird nie wieder geprüft. Deshalb:

> **Ein Match braucht mindestens zwei übereinstimmende Merkmale, von denen
> eines nicht der Nachname ist.** Nachname + Jahr genügt nie.

## Machbarkeitsnachweis – gemessen 04.08.2026

`werkstatt/kaskade_tod.py`, gemessen gegen `~/ofb-ki/kirchenbuch.db`,
Parochie Haberschlacht. Ohne Bilder, ohne API – die Testdaten waren vorhanden.

| Zeitraum | Einträge | Treffer | Umweg nötig | kein Treffer | mehrdeutig |
|---|---|---|---|---|---|
| 1800–1807 | 117 | **59,8 %** | 12,8 % | 26,5 % | 0,9 % |
| 1750–1807 | 788 | **49,5 %** | 14,0 % | 34,4 % | 2,2 % |

Laufzeit für 788 Einträge: wenige Sekunden.

### Der richtige Maßstab

Nicht „wie viel findet die Maschine allein", sondern **wie viel Arbeit spart
sie**. Danach gerechnet liefert sie bei rund drei Vierteln der Fälle eine
verwertbare Auskunft:

    Treffer       fertiger Vorschlag mit Begründung -> bestätigen
    Umweg         "verheiratete Frau, such über die Ehe" -> gezielter Hinweis
    mehrdeutig    zwei Kandidaten, Entscheidung vorgelegt
    kein Treffer  teils korrekt (siehe unten), teils Hinweis auf Zuzug

Die Alternative ist, jeden Eintrag von Hand zu durchsuchen.

### Nichtfinden ist oft richtig

Belegt am Fall der Zwillinge Wolff, † 11. und 19.03.1801 nach 14 bzw. 22 Tagen:
Die Kaskade findet keine Taufe – und im kuratierten OFB steht bei beiden
`BIRT CAL 25 FEB 1801` **ohne** `CHR`. Sie wurden vermutlich nur nottauft.
Das Nichtfinden ist die korrekte Auskunft, kein Fehler des Verfahrens.

### Die 26,5 % ohne Treffer, aufgeschlüsselt

    verheiratet, Mädchenname nicht erschließbar   21
    Kind ohne Taufeintrag im Bestand              18
    erwachsen, keine Taufe am Ort (Zuzug)         13

Nur die mittlere Gruppe ist teilweise ein Bestandsproblem: `kirchenbuch.db`
führt für Haberschlacht 1795–1807 **271** Taufen, der kuratierte OFB **392**
Tauf- und Geburtsereignisse. Für diese Parochie ist der OFB die vollständigere
Quelle – ein Argument dafür, mehrere Bestände gestaffelt abzufragen.

### Zwei Bugs, die der Test aufgedeckt hat

1. **Geschlechtsprüfung vor dem Mädchennamen-Umweg.** `geschl_verst` ist in
   835 von 1.292 Einträgen leer; die Prüfung verhinderte den Umweg fast immer.
   Entfernt – ein genannter Ehepartner genügt als Anlass. Wirkung: Treffer von
   53,8 auf 59,8 %.
2. **Naiver Nachname-plus-Jahr-Match.** Hätte `Johannes Bierle` mit
   `Carl Heinrich Bierle` verknüpft. Verhindert durch die Pflichtregel.

## Regeln für die Umsetzung

1. **Errechnete Geburtsdaten aus Altersangaben sind stark**, wenn sie Monate und
   Tage enthalten – dann taggenau vergleichbar. Nur „65 Jahre" heißt ±1 Jahr.
2. **Verheiratete Frauen** über die Ehe erschließen, nicht über den Nachnamen.
3. **Nichtfinden ist ein Ergebnis.** Zuzug, andere Parochie, Lücke im Buch – das
   gehört vermerkt, nicht als Fehler behandelt.
4. **Kein stiller Match.** Jede Verknüpfung trägt ihre Begründung, jede
   Mehrdeutigkeit wird vorgelegt.
