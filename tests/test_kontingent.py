"""Der Kostendeckel: Vorgabe, Abschaltung, Bestandsschutz.

Der Deckel ist Opt-out. Eine frische Werkstatt liest für höchstens
`VORGABE`, wer mehr will, hebt an, wer keinen Deckel will, schreibt `aus`.
Das Feld leer zu lassen genügt nicht: Die Einstellungsmaske löscht leere
Werte, und eine fehlende Zeile heißt hier „nie entschieden".
"""
import sqlite3
import unittest

from werkstatt import db, einstellungen, kontingent


def datenbank(deckel=None, verbraucht=0.0):
    """Eine Datenbank mit genau den zwei Tabellen, die hier zählen."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE einstellung (schluessel TEXT PRIMARY KEY, "
                "wert TEXT, geaendert TEXT)")
    con.execute("CREATE TABLE auftrag (id INTEGER PRIMARY KEY, quelle TEXT, "
                "dollar REAL, tokens_ein INT, tokens_aus INT)")
    if verbraucht:
        con.execute("INSERT INTO auftrag (quelle, dollar, tokens_ein, "
                    "tokens_aus) VALUES (?,?,0,0)", ("api", verbraucht))
    if deckel is not None:
        einstellungen.setze(con, kontingent.SCHLUESSEL, deckel)
    return con


class Deckel(unittest.TestCase):

    def test_die_vorgabe_ist_eine_echte_grenze(self):
        """Erst die Konstante selbst prüfen, sonst prüft der Rest nichts.

        Ein Test, der `budget()` bloß gegen `VORGABE` hält, bleibt auch dann
        grün, wenn jemand `VORGABE = None` setzt und damit den ganzen Schutz
        abschaltet. Beides ist dann None und stimmt überein.
        """
        self.assertIsInstance(kontingent.VORGABE, (int, float))
        self.assertGreater(kontingent.VORGABE, 0)

    def test_frische_werkstatt_hat_eine_grenze(self):
        """Der eigentliche Punkt: ohne Zutun gilt eine Grenze, nicht Freifahrt."""
        grenze = kontingent.budget(datenbank())
        self.assertIsNotNone(grenze)
        self.assertGreater(grenze, 0)
        self.assertEqual(grenze, kontingent.VORGABE)

    def test_gesetzter_wert_gilt(self):
        self.assertEqual(kontingent.budget(datenbank("20")), 20.0)

    def test_deutsches_komma(self):
        self.assertEqual(kontingent.budget(datenbank("7,50")), 7.5)

    def test_abschalten_mit_wort(self):
        for wort in ("aus", "AUS", "unbegrenzt"):
            self.assertIsNone(kontingent.budget(datenbank(wort)), wort)

    def test_tippfehler_schaltet_nicht_ab(self):
        """Ein unlesbarer Wert fällt auf die Vorgabe zurück, nicht auf frei."""
        gefallen = kontingent.budget(datenbank("zwnzg"))
        self.assertIsNotNone(gefallen)
        self.assertEqual(gefallen, kontingent.VORGABE)


class Sperre(unittest.TestCase):

    def test_unter_der_grenze_darf_gelesen_werden(self):
        ok, meldung = kontingent.frei(datenbank("10", verbraucht=4.0))
        self.assertTrue(ok)
        self.assertIsNone(meldung)

    def test_ueber_der_grenze_wird_gesperrt(self):
        ok, meldung = kontingent.frei(datenbank("5", verbraucht=6.0))
        self.assertFalse(ok)
        self.assertIn("erschöpft", meldung)

    def test_testdaten_kosten_nichts_und_laufen_immer(self):
        ok, _ = kontingent.frei(datenbank("5", verbraucht=99.0), "testdaten")
        self.assertTrue(ok)


class Bestandsschutz(unittest.TestCase):
    """Wer schon gelesen hat, wird von der neuen Vorgabe nicht ausgesperrt."""

    def test_bestand_mit_verbrauch_bleibt_offen(self):
        con = datenbank(verbraucht=12.49)
        db._bestandsschutz_kontingent(con)
        self.assertIsNone(kontingent.budget(con))
        self.assertTrue(kontingent.frei(con)[0])

    def test_frische_datenbank_bekommt_die_vorgabe(self):
        con = datenbank()
        db._bestandsschutz_kontingent(con)
        grenze = kontingent.budget(con)
        self.assertIsNotNone(grenze)
        self.assertEqual(grenze, kontingent.VORGABE)

    def test_mehrfaches_wandern_aendert_nichts(self):
        con = datenbank(verbraucht=12.49)
        for _ in range(3):
            db._bestandsschutz_kontingent(con)
        self.assertIsNone(kontingent.budget(con))

    def test_gesetzter_wert_wird_nicht_ueberschrieben(self):
        con = datenbank("42", verbraucht=12.49)
        db._bestandsschutz_kontingent(con)
        self.assertEqual(kontingent.budget(con), 42.0)


if __name__ == "__main__":
    unittest.main()
