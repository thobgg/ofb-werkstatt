# Verknüpfungskaskade — der anspruchsvollste Teil

Nicht das Lesen ist die OFB-Arbeit, sondern das **Verknüpfen**: Zu jedem
Registereintrag muss entschieden werden, welche der genannten Personen im
Bestand schon existieren und welche neu sind. Die Kaskade ist je Aktart
verschieden.

Belege unten stammen aus einem Test gegen `~/ofb-ki/kirchenbuch.db`,
Parochie Haberschlacht.

## Taufe

    Vater  ──► suche Person (Name + Ort + plausibles Alter)
           ──► seine Ehe(n) vor dem Taufdatum
    Mutter ──► bestätigt sich aus der Ehe, statt eigenständig gesucht zu werden
    Familie ─► gemeinsame Familie von Vater und Mutter
    Kind   ──► immer neu, dort eingehängt

**Der Elternehe-Anker.** Die Mutter wird nicht gesucht, sondern *abgeleitet* —
deshalb trägt er auch, wenn ihr Name falsch gelesen wurde. Im Pilotlauf fand er
vier Fälle, in denen der *Vater*name falsch war und der Treffer allein über die
Vornamen der Mutter kam.

Fehlt die gemeinsame Familie, obwohl beide Eltern gefunden sind: **nicht still
neu anlegen** — das ist entweder eine Zweitehe oder eine Fehlzuordnung.

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
      → Taufe 21.07.1760 — auf den Tag
      → Eltern Joh. Friedrich Schneider ⚭ Christina Susanna Felger
      → im Sterbeeintrag genannter Vater: derselbe ✓

## Die drei Fehlschläge — und was daraus folgt

| Fall | Ursache | Konsequenz |
|---|---|---|
| Johannes Meßner, keine Taufe am Ort | Zuzug | Nichtfinden ist **kein Fehler**, sondern Information: Person kam von auswärts |
| Catharina Magdalena Würz ⚭ Wilhelm Würz | heißt Würz **durch Heirat**, Taufe steht unter unbekanntem Mädchennamen | bei verheirateten Frauen **zuerst die Ehe suchen**, daraus den Mädchennamen, dann die Taufe |
| „Johannes Bierle" → Taufe *Carl Heinrich* Bierle | nur Nachname + Jahr gematcht | **Vorname ist Pflichtbedingung**, sonst stille Fehlverknüpfung |

Der dritte ist der gefährliche: Ein Falschtreffer sieht aus wie ein Erfolg und
wird nie wieder geprüft. Deshalb:

> **Ein Match braucht mindestens zwei übereinstimmende Merkmale, von denen
> eines nicht der Nachname ist.** Nachname + Jahr genügt nie.

## Regeln für die Umsetzung

1. **Errechnete Geburtsdaten aus Altersangaben sind stark**, wenn sie Monate und
   Tage enthalten — dann taggenau vergleichbar. Nur „65 Jahre" heißt ±1 Jahr.
2. **Verheiratete Frauen** über die Ehe erschließen, nicht über den Nachnamen.
3. **Nichtfinden ist ein Ergebnis.** Zuzug, andere Parochie, Lücke im Buch — das
   gehört vermerkt, nicht als Fehler behandelt.
4. **Kein stiller Match.** Jede Verknüpfung trägt ihre Begründung, jede
   Mehrdeutigkeit wird vorgelegt.
