-- Datenbasis. EINE Struktur, viele Eingangstüren:
-- GEDCOM, XLSX, CSV, DOCX und die eigene Erfassung schreiben hierher.
-- Die Suche kennt keine Herkunft – nur den Inhalt.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- Herkunft
-- Woher stammt ein Datensatz. Wird für die Belegführung gebraucht und nimmt
-- später auch auf, WER etwas eingetragen hat (dann Mehrbenutzer ohne Umbau).
--
-- `gilt` trägt die Regel aus doku/landkarte.md, die vorher nur dort stand:
--
--     kirchenbuch.db ist außerhalb von Haberschlacht und Neipperg
--     Vokabular, kein Beweis. Es darf ranken, nie bestätigen.
--
-- Damit ist der Rang einer Quelle eine Eigenschaft der Quelle, keine
-- Sonderlogik im Abgleich: Ein Treffer macht grün, wenn die Herkunft des
-- getroffenen Datensatzes 'beleg' ist und die Parochie passt. Alles andere
-- rankt die Vorschlagsliste und bleibt gelb.
--
-- Ein Bestand kann beides sein – `kirchenbuch.db` belegt für zwei Parochien
-- und ist für die übrigen 32 nur Wortschatz. Deshalb wird er zweimal
-- eingetragen, einmal je Rang, mit unterschiedlicher Parochienliste.
CREATE TABLE IF NOT EXISTS herkunft (
  id        INTEGER PRIMARY KEY,
  art       TEXT NOT NULL,          -- gedcom | xlsx | csv | docx | erfassung
  datei     TEXT,                   -- Dateiname oder Registerangabe
  bearbeiter TEXT,                  -- leer = lokaler Einzelplatz
  angelegt  TEXT NOT NULL,
  notiz     TEXT,
  gilt      TEXT NOT NULL DEFAULT 'vokabular',  -- beleg | vokabular
  parochien TEXT,                   -- kommagetrennt; leer = überall gültig
  name      TEXT,                   -- Anzeigename aus konfig.toml
  -- Beschaffenheit der Quelldatei, damit die Ausgabe sie zeichengleich
  -- wiederherstellen kann. Ohne diese drei Angaben unterscheidet sich das
  -- Ergebnis im ersten und im letzten Byte, ohne dass ein Feld anders wäre.
  bom       INTEGER NOT NULL DEFAULT 0,
  zeilenende TEXT NOT NULL DEFAULT 'lf',  -- lf | crlf
  schluss   INTEGER NOT NULL DEFAULT 1,   -- endet die Datei mit einem Umbruch
  UNIQUE(art, datei)
);

-- Die Quelldatei, vollständig und in Reihenfolge.
--
-- `person.raw` und `familie.raw` bewahren zwar jeden INDI- und FAM-Record,
-- aber eine GEDCOM-Datei besteht nicht nur daraus. Gemessen am Bestand
-- Haberschlacht: 5.615 Records, davon 4.111 INDI und 1.346 FAM – und 158
-- weitere, die niemand aufhob: HEAD, SUBM, 35 SOUR, **120 _LOC** und TRLR.
-- Die _LOC-Records sind die Ortsdefinitionen, auf die jede Person mit
-- `3 _LOC @L1@` zeigt; ohne sie hat die Ausgabe tote Verweise.
--
-- Deshalb hier die ganze Datei, Record für Record, unverändert. Die
-- Fortschreibung läuft darüber und ersetzt nur, was ein Vorgang berührt.
CREATE TABLE IF NOT EXISTS rec (
  id       INTEGER PRIMARY KEY,
  herkunft INTEGER NOT NULL REFERENCES herkunft(id) ON DELETE CASCADE,
  seq      INTEGER NOT NULL,
  xref     TEXT,
  typ      TEXT NOT NULL,
  raw      TEXT NOT NULL,
  UNIQUE(herkunft, seq)
);
CREATE INDEX IF NOT EXISTS ix_rec_xref ON rec(herkunft, xref);

-- ---------------------------------------------------------------- Personen
CREATE TABLE IF NOT EXISTS person (
  id         INTEGER PRIMARY KEY,
  xref       TEXT,                  -- @I123@ aus der Quelldatei, falls vorhanden
  name       TEXT,                  -- vollständig, wie in der Quelle
  givn       TEXT,
  surn       TEXT,                  -- Nachname, Schreibung der Quelle
  surn_kanon TEXT,                  -- kanonische Form der Äquivalenzklasse
  sex        TEXT,
  herkunft   INTEGER REFERENCES herkunft(id),
  raw        TEXT,                  -- vollständiger Quellrecord, verlustfrei
  UNIQUE(herkunft, xref)
);
CREATE INDEX IF NOT EXISTS ix_person_surn  ON person(surn);
CREATE INDEX IF NOT EXISTS ix_person_kanon ON person(surn_kanon);

-- Abweichende Namensformen: Kirchenbuchform, Rufname, Schreibvarianten
CREATE TABLE IF NOT EXISTS namensform (
  id      INTEGER PRIMARY KEY,
  person  INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  art     TEXT NOT NULL,            -- kb | rufname | variante
  wert    TEXT NOT NULL,
  UNIQUE(person, art, wert)
);

-- ---------------------------------------------------------------- Familien
CREATE TABLE IF NOT EXISTS familie (
  id       INTEGER PRIMARY KEY,
  xref     TEXT,
  mann     INTEGER REFERENCES person(id),
  frau     INTEGER REFERENCES person(id),
  herkunft INTEGER REFERENCES herkunft(id),
  raw      TEXT,
  UNIQUE(herkunft, xref)
);
CREATE INDEX IF NOT EXISTS ix_familie_mann ON familie(mann);
CREATE INDEX IF NOT EXISTS ix_familie_frau ON familie(frau);

CREATE TABLE IF NOT EXISTS kind (
  familie INTEGER NOT NULL REFERENCES familie(id) ON DELETE CASCADE,
  person  INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  PRIMARY KEY (familie, person)
);
CREATE INDEX IF NOT EXISTS ix_kind_person ON kind(person);

-- --------------------------------------------------------------- Ereignisse
-- Gilt für Personen und Familien; genau eines von beiden ist gesetzt.
CREATE TABLE IF NOT EXISTS ereignis (
  id       INTEGER PRIMARY KEY,
  person   INTEGER REFERENCES person(id) ON DELETE CASCADE,
  familie  INTEGER REFERENCES familie(id) ON DELETE CASCADE,
  art      TEXT NOT NULL,           -- BIRT CHR MARR DEAT BURI OCCU ...
  datum    TEXT,                    -- wie in der Quelle
  jahr     INTEGER,                 -- ausgewertet, für Bereichssuchen
  exakt    INTEGER NOT NULL DEFAULT 1,  -- 0 bei BEF/AFT/ABT/CAL/EST
  ort      TEXT,
  wert     TEXT,                    -- z.B. Berufsbezeichnung bei OCCU
  quelle   TEXT,                    -- SOUR/PAGE der Quelle
  CHECK (person IS NOT NULL OR familie IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS ix_ereignis_person  ON ereignis(person, art);
CREATE INDEX IF NOT EXISTS ix_ereignis_familie ON ereignis(familie, art);
CREATE INDEX IF NOT EXISTS ix_ereignis_jahr    ON ereignis(jahr);

-- ---------------------------------------------------- Erfassung aus Registern
CREATE TABLE IF NOT EXISTS eintrag (
  id         INTEGER PRIMARY KEY,
  register   TEXT NOT NULL,         -- Schlüssel aus konfig.toml
  band       TEXT,
  bild       TEXT,
  nr         TEXT,
  jahr       INTEGER,
  ausschnitt TEXT,                  -- Zeilenstreifen, relativ zur Wurzel
  -- Wo der Streifen auf der Seite sitzt: "x,y,w,h". Ohne das laesst sich
  -- die ganze Buchoeffnung nicht mit der Zeile darin zeigen – und genau
  -- die braucht, wer einen Buchstaben an anderer Stelle nachschlagen
  -- will. Der Streifen allein nimmt die Eichung weg.
  kasten     TEXT,
  seite      TEXT,                  -- die volle Aufnahme, relativ zur Wurzel
  -- Der gedruckte Spaltenkopf derselben Seite, auf dieselbe Breite
  -- geschnitten wie der Streifen. Ohne ihn sieht man ab dem zweiten
  -- Eintrag nur Zellen und weiss nicht mehr, welche was bedeutet – und
  -- rechts stehen "Zeit der Geburt" und "Ort und Tag der Taufe"
  -- nebeneinander, beide mit einem Datum darin.
  kopf       TEXT,
  fam_reg    TEXT,                  -- Seitenzahl des Familienregisters:
                                    -- der stärkste Anker, vom Pfarrer gesetzt.
                                    -- Gleiche Nummer = gleiche Familie,
                                    -- gilt nur innerhalb einer Parochie.
  schreiber  TEXT,                  -- Hand; der Fehlerkatalog gilt je Hand,
                                    -- nicht global (Pfarrerwechsel Haberschlacht 1827)
  status     TEXT NOT NULL DEFAULT 'gelesen',
  herkunft   INTEGER REFERENCES herkunft(id),
  runde      INTEGER REFERENCES runde(id),   -- welche Tranche hat ihn gelesen
  bemerkung  TEXT,
  UNIQUE(register, bild, nr)
);

CREATE TABLE IF NOT EXISTS feld (
  id         INTEGER PRIMARY KEY,
  eintrag_id INTEGER NOT NULL REFERENCES eintrag(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  rolle      TEXT,                  -- vater | mutter | kind | braeutigam ...
  gelesen    TEXT,                  -- Rohlesung des Modells, bleibt erhalten
  korrigiert TEXT,                  -- vom Menschen geändert
  kb_form    TEXT,                  -- Kirchenbuchform, wörtlich
  kanonisch  TEXT,                  -- normalisierte Form
  beleg      TEXT,                  -- woran die Aussage hängt
  person     INTEGER REFERENCES person(id),   -- find and use
  entscheidung TEXT NOT NULL DEFAULT 'offen', -- offen|verknuepft|neu
  ampel      TEXT NOT NULL DEFAULT 'grau',    -- grau|rot|gelb|gruen
  status     TEXT NOT NULL DEFAULT 'gelesen',
  zuversicht REAL,                  -- Selbsteinschätzung des Modells 0..1
  bild_x     INTEGER,               -- Ausschnitt im Zeilenstreifen
  bild_y     INTEGER,
  bild_w     INTEGER,
  bild_h     INTEGER,
  reihe      INTEGER NOT NULL DEFAULT 0,
  UNIQUE(eintrag_id, name)
);
CREATE INDEX IF NOT EXISTS ix_feld_eintrag ON feld(eintrag_id);
CREATE INDEX IF NOT EXISTS ix_feld_person  ON feld(person);

-- ------------------------------------------------------------ Der Durchlauf
-- Eine Runde ist eine Tranche: so und so viele Seiten EINES Registers,
-- die zusammen gelesen, zusammen korrigiert und zusammen übergeben werden.
--
-- Der Zustand liegt in der Datenbank und nicht im Prozess. Das entscheidet
-- mehr, als es aussieht: Ein Abbruch mitten in zwanzig Seiten hinterlässt
-- einen lesbaren Zustand statt eines Rätsels, der Browser darf geschlossen
-- werden, und die Einschränkung der Korrekturmaske auf die gerade gelesene
-- Tranche ist ein WHERE statt eines Sonderfalls.
--
-- Die Reihenfolge Ehen → Taufen → Tode ist kein Vorschlag, sondern Bedingung:
-- Der Elternehe-Anker trägt im Taufjahr 1808 noch 94 %, 1813 noch 53 %,
-- 1820 nur 18 % – es sei denn, die Ehen ab 1808 sind vorher übergeben.
-- Deshalb prüft runde.py, ob die Vorgängerrunde 'uebergeben' ist.
CREATE TABLE IF NOT EXISTS runde (
  id       INTEGER PRIMARY KEY,
  nr       INTEGER NOT NULL,
  register TEXT NOT NULL,
  von_bild TEXT,
  bis_bild TEXT,
  seiten   INTEGER NOT NULL DEFAULT 0,
  quelle   TEXT NOT NULL DEFAULT 'api',      -- api | testdaten
  stand    TEXT NOT NULL DEFAULT 'geplant',
           -- geplant → liest → korrigieren → uebergeben → fertig
  begonnen TEXT,
  beendet  TEXT
);

-- Ein Auftrag ist der laufende Vorgang einer Runde; er überlebt das
-- Browserfenster. Die Kosten stehen hier statt in einer Konsolenzeile,
-- die niemand mehr sieht.
CREATE TABLE IF NOT EXISTS auftrag (
  id            INTEGER PRIMARY KEY,
  runde         INTEGER REFERENCES runde(id) ON DELETE CASCADE,
  art           TEXT NOT NULL,              -- lesen | uebergabe
  stand         TEXT NOT NULL DEFAULT 'wartet',
                -- wartet | laeuft | fertig | fehler | abgebrochen
  seiten_gesamt INTEGER NOT NULL DEFAULT 0,
  seiten_fertig INTEGER NOT NULL DEFAULT 0,
  aktuell       TEXT,
  meldung       TEXT,
  tokens_ein    INTEGER NOT NULL DEFAULT 0,
  tokens_aus    INTEGER NOT NULL DEFAULT 0,
  -- Auch der Weg ueber das Abonnement laesst sich beziffern: `claude -p
  -- --output-format json` meldet, was derselbe Lauf ueber die API
  -- gekostet haette. Fuer den Bearbeiter faellt keine Rechnung an; fuer
  -- jeden, der sich fragt, ob sich das lohnt, ist es die einzige ehrliche
  -- Zahl. Deshalb wird sie mitgeschrieben, auch wenn niemand sie zahlt.
  tokens_cache  INTEGER NOT NULL DEFAULT 0,
  dollar        REAL NOT NULL DEFAULT 0,
  quelle        TEXT,                       -- api | datei | testdaten
  dauer_ms      INTEGER NOT NULL DEFAULT 0,
  begonnen      TEXT,
  beendet       TEXT
);

-- Fehler gelten je Seite, nicht je Lauf. Bricht Seite 7 von 20 ab, sind die
-- ersten sechs gespeichert, die siebte trägt ihre Meldung, und der Lauf geht
-- weiter – in einem Hintergrund-Thread wäre ein SystemExit ein stiller Tod.
CREATE TABLE IF NOT EXISTS auftrag_seite (
  id        INTEGER PRIMARY KEY,
  auftrag   INTEGER NOT NULL REFERENCES auftrag(id) ON DELETE CASCADE,
  bild      TEXT NOT NULL,
  stand     TEXT NOT NULL DEFAULT 'wartet',  -- wartet|laeuft|fertig|fehler
  eintraege INTEGER NOT NULL DEFAULT 0,
  felder    INTEGER NOT NULL DEFAULT 0,
  meldung   TEXT,
  UNIQUE(auftrag, bild)
);
CREATE INDEX IF NOT EXISTS ix_auftrag_runde ON auftrag(runde);

-- ------------------------------------------------------------ Einstellungen
-- Was sich im Betrieb ändert, steht hier; was die Struktur ausmacht, in
-- konfig.toml. Die Trennlinie ist nicht willkürlich:
--
--     konfig.toml   Registerarten, Felder, Rollen, Kontextquellen
--                   -> Struktur. Ändert man einmal beim Einrichten.
--     einstellung   Seitenzahl je Runde, Reihenfolge, Bildordner, Autopilot
--                   -> Betrieb. Ändert man beim Arbeiten.
--
-- Betriebswerte in die TOML-Datei zurückzuschreiben hieße, sie bei jedem
-- Klick neu zu erzeugen – und dabei ihre Kommentare zu verlieren, die den
-- halben Erklärwert der Datei ausmachen. Was hier fehlt, kommt weiterhin
-- aus konfig.toml; die Einstellung überschreibt nur.
CREATE TABLE IF NOT EXISTS einstellung (
  schluessel TEXT PRIMARY KEY,
  wert       TEXT,
  geaendert  TEXT
);

-- ------------------------------------------------------------------ Journal
-- Jede Ergänzung und jede Korrektur als Vorgang. `werkstatt.ausgabe` wendet
-- sie beim Fortschreiben auf die unveränderten Records an.
--
-- Steht bewusst in DERSELBEN Datei wie alles andere. Die Vorgängerfassung
-- schrieb nach `daten/aenderung.sqlite`; über zwei Dateien hinweg kann ein
-- Bestätigen aber nicht das Feld UND den Vorgang in einer Transaktion
-- schreiben – bei einem Abbruch dazwischen stimmen sie nicht mehr überein.
--
-- Rücknahme heißt `aktiv=0`, nicht löschen. Der Ausgangszustand bleibt
-- jederzeit rekonstruierbar, und jeder Vorgang trägt seinen Beleg statt
-- bloß ein Urteil.
CREATE TABLE IF NOT EXISTS vorgang (
  id        INTEGER PRIMARY KEY,
  art       TEXT NOT NULL,   -- neu_person | neu_familie | merge | feld | kind
  ziel      TEXT,            -- betroffene Record-Kennung
  ziel2     TEXT,            -- zweite Kennung (merge: der aufgehende Record)
  daten     TEXT,            -- JSON: Feldwerte bzw. Parameter
  quelle    TEXT,            -- z.B. 'Taufreg. Bd. 4 Bild 00361 Nr. 11'
  beleg     TEXT,            -- woran es hängt, im Klartext
  bemerkung TEXT,
  aktiv     INTEGER NOT NULL DEFAULT 1,
  angelegt  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_vorgang_ziel ON vorgang(ziel);
CREATE INDEX IF NOT EXISTS ix_vorgang_art  ON vorgang(art);

-- Chronologie-Anker: Datum jedes Eintrags gegen seine Nachbarn.
-- Register sind chronologisch geführt – ein Datum außerhalb des
-- Nachbarintervalls ist widerlegt, ohne dass etwas nachgeschlagen wird.
CREATE VIEW IF NOT EXISTS chronologie AS
  SELECT e.id, e.register, e.bild, e.nr, e.jahr,
         f.name  AS feld,
         COALESCE(f.korrigiert, f.gelesen) AS datum,
         LAG(COALESCE(f.korrigiert, f.gelesen))
             OVER (PARTITION BY e.register, f.name
                   ORDER BY e.bild, CAST(e.nr AS INTEGER)) AS davor,
         LEAD(COALESCE(f.korrigiert, f.gelesen))
             OVER (PARTITION BY e.register, f.name
                   ORDER BY e.bild, CAST(e.nr AS INTEGER)) AS danach
  FROM eintrag e JOIN feld f ON f.eintrag_id = e.id
  WHERE f.name LIKE '%datum%';

-- ------------------------------------------------------------- Wortschatz
-- Wörter ohne Person. Eine Namensliste, ein Ortsverzeichnis, eine
-- Berufstabelle – alles, was Schreibweisen kennt, aber keine Lebensdaten
-- hat und deshalb nie bestätigen kann.
--
-- Getrennt von `person`, weil sonst jede Zeile einer Tabelle eine erfundene
-- Person würde. Der Abgleich zählt sie mit, die Ampel nicht: die Herkunft
-- solcher Quellen ist `vokabular`, und ein Vokabulartreffer bleibt gelb.
CREATE TABLE IF NOT EXISTS wortschatz (
  id       INTEGER PRIMARY KEY,
  herkunft INTEGER NOT NULL REFERENCES herkunft(id) ON DELETE CASCADE,
  klasse   TEXT NOT NULL,     -- nachname | vorname | ort | beruf | offen
  wort     TEXT NOT NULL,     -- Schreibweise wie in der Quelle
  gefaltet TEXT NOT NULL,     -- Vergleichsform, siehe suche.falte()
  anzahl   INTEGER NOT NULL DEFAULT 1,
  woher    TEXT,              -- Datei und Spalte, für den Beleg im Zweifel
  UNIQUE(herkunft, klasse, wort)
);
CREATE INDEX IF NOT EXISTS ix_wortschatz_gef ON wortschatz(gefaltet);
CREATE INDEX IF NOT EXISTS ix_wortschatz_klasse ON wortschatz(klasse);

-- ----------------------------------------------------------- Aktkarten
-- Der Feldkatalog in katalog.py gibt den Vorrat vor. Hier steht, was der
-- Bearbeiter daran geaendert hat: Felder abgeschaltet, Ziele umgehaengt,
-- eigene Felder ergaenzt.
--
-- Warum nicht alles hier: Ein leerer Vorrat waere kein Schutz vor
-- Wildwuchs. Der Katalog ist der gemeinsame Nenner aller Bestaende; was
-- hier steht, ist die Abweichung dieses einen Projekts – und die ist
-- damit auch benennbar, wenn der Bestand einmal weitergegeben wird.
CREATE TABLE IF NOT EXISTS feldwahl (
  art      TEXT NOT NULL,          -- taufe | ehe | tod
  name     TEXT NOT NULL,
  aktiv    INTEGER NOT NULL DEFAULT 1,
  ziel     TEXT,                   -- ueberschreibt das Ziel des Katalogs
  ziel_kb  TEXT,
  titel    TEXT,
  hinweis  TEXT,
  rolle    TEXT,
  feldart  TEXT,                   -- text | datum | ort | name
  kb       INTEGER,
  eigen    INTEGER NOT NULL DEFAULT 0,   -- 1 = nicht im Katalog
  nach     TEXT,                   -- Einordnung: hinter welchem Feld
  angelegt TEXT,
  PRIMARY KEY (art, name)
);

-- ------------------------------------------------------------- Merkmale
-- Alles, was zu einer Person gehoert und kein Ereignis ist: Beruf,
-- Wohnort, Religion, Rufname, Unehelichkeit – und zu jedem davon die
-- Kirchenbuchform, wo sie sich unterscheidet.
--
-- Als eigene Tabelle statt als Spalten, weil der Feldkatalog waechst und
-- jede neue Angabe sonst eine Schemaaenderung braeuchte. `tag` ist das
-- GEDCOM-Ziel aus dem Katalog; die Ausgabe schreibt es unveraendert.
CREATE TABLE IF NOT EXISTS merkmal (
  id       INTEGER PRIMARY KEY,
  person   INTEGER REFERENCES person(id) ON DELETE CASCADE,
  familie  INTEGER REFERENCES familie(id) ON DELETE CASCADE,
  tag      TEXT NOT NULL,          -- OCCU, RESI, _BERUF_KB, _KB_NAME ...
  wert     TEXT NOT NULL,
  feld     TEXT,                   -- aus welchem Feld der Aktkarte
  kb       INTEGER NOT NULL DEFAULT 0,   -- 1 = Kirchenbuchform
  quelle   TEXT,
  UNIQUE(person, familie, tag, wert)
);
CREATE INDEX IF NOT EXISTS ix_merkmal_person ON merkmal(person);

-- ------------------------------------------------------------- Aufwand
-- Wie viel Arbeit ein Eintrag gemacht hat: Tastendruecke, Klicks,
-- Sekunden. Das ist der ehrlichere Massstab als eine Trefferquote – die
-- misst das Buch, nicht das Werkzeug.
--
-- Bei schwerer Hand tippt der Bearbeiter viel, bei klarer Schrift
-- bestaetigt er nur. Beides ist brauchbar; die Frage ist, wie viel Arbeit
-- uebrig bleibt. Und anders als die Lesequalitaet faellt diese Zahl beim
-- Arbeiten von selbst an, ohne dass jemand eine geprueft Wahrheit
-- danebenlegen muesste.
CREATE TABLE IF NOT EXISTS aufwand (
  eintrag   INTEGER PRIMARY KEY REFERENCES eintrag(id) ON DELETE CASCADE,
  tasten    INTEGER NOT NULL DEFAULT 0,   -- Zeichen, die getippt wurden
  klicks    INTEGER NOT NULL DEFAULT 0,
  sekunden  INTEGER NOT NULL DEFAULT 0,   -- am Eintrag verbrachte Zeit
  felder    INTEGER NOT NULL DEFAULT 0,   -- wie viele geaendert wurden
  beendet   TEXT
);

-- Bequemer Zugriff auf den geltenden Wert
CREATE VIEW IF NOT EXISTS wert AS
  SELECT e.register, e.bild, e.nr, e.jahr, f.name, f.rolle,
         COALESCE(f.korrigiert, f.gelesen) AS wert,
         f.kb_form, f.kanonisch, f.beleg, f.person, f.entscheidung,
         f.ampel, f.status
  FROM feld f JOIN eintrag e ON e.id = f.eintrag_id;

-- Fehlerkatalog: Auswertung, keine gepflegte Datei.
-- Speist den Transkriptionsprompt.
CREATE VIEW IF NOT EXISTS fehlerkatalog AS
  SELECT f.gelesen, f.korrigiert, e.register, count(*) AS anzahl
  FROM feld f JOIN eintrag e ON e.id = f.eintrag_id
  WHERE f.korrigiert IS NOT NULL
    AND f.gelesen IS NOT NULL
    AND f.korrigiert <> f.gelesen
    AND trim(f.gelesen) <> ''
  GROUP BY f.gelesen, f.korrigiert, e.register
  ORDER BY anzahl DESC;
