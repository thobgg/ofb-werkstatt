"""Elternzeilen zerlegen.

Ehe- und Sterberegister führen die Eltern in einer einzigen Zeile, mit
Beruf und Ort darin. Erst zerlegt sind sie Personen, gegen die der Abgleich
überhaupt etwas finden kann.
"""
import unittest

from werkstatt import personenzeile


class Zerlegen(unittest.TestCase):

    def test_name_beruf_ort(self):
        t = personenzeile.zerlege(
            "Christian Andreas Selger, Bürger und Weingärtner in Haberschlacht")
        self.assertEqual(t["name"], "Christian Andreas Selger")
        self.assertEqual(t["beruf"], "Bürger und Weingärtner")
        self.assertEqual(t["ort"], "Haberschlacht")

    def test_geborene_bleibt_in_kirchenbuchform(self):
        """`Kochin` wird hier nicht aufgelöst.

        Die Movierung ist Sache von `normalform.kandidaten()` und des
        Abgleichs. Wer hier abschneidet, verliert die Lesung.
        """
        t = personenzeile.zerlege(
            "Catharina Friderika geb. Kochin von Haberschlacht")
        self.assertEqual(t["name"], "Catharina Friderika")
        self.assertEqual(t["geborene"], "Kochin")
        self.assertEqual(t["ort"], "Haberschlacht")

    def test_ohne_ort(self):
        t = personenzeile.zerlege("Johann Georg Müller, Bauer")
        self.assertEqual(t["name"], "Johann Georg Müller")
        self.assertEqual(t["beruf"], "Bauer")
        self.assertIsNone(t["ort"])

    def test_die_quelle_bleibt_immer_erhalten(self):
        """Was im Buch stand, muss aus dem Ergebnis rekonstruierbar sein."""
        zeile = "Johann Georg Müller, Bauer"
        self.assertEqual(personenzeile.zerlege(zeile)["quelle"], zeile)


if __name__ == "__main__":
    unittest.main()
