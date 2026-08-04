-- Datenbasis. EINE Struktur, viele Eingangstüren:
-- GEDCOM, XLSX, CSV, DOCX und die eigene Erfassung schreiben hierher.
-- Die Suche kennt keine Herkunft — nur den Inhalt.

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
-- Ein Bestand kann beides sein — `kirchenbuch.db` belegt für zwei Parochien
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
  UNIQUE(art, datei)
);

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
-- 1820 nur 18 % — es sei denn, die Ehen ab 1808 sind vorher übergeben.
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
  begonnen      TEXT,
  beendet       TEXT
);

-- Fehler gelten je Seite, nicht je Lauf. Bricht Seite 7 von 20 ab, sind die
-- ersten sechs gespeichert, die siebte trägt ihre Meldung, und der Lauf geht
-- weiter — in einem Hintergrund-Thread wäre ein SystemExit ein stiller Tod.
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

-- Chronologie-Anker: Datum jedes Eintrags gegen seine Nachbarn.
-- Register sind chronologisch geführt — ein Datum außerhalb des
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
