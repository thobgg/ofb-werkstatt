"""Movierung: aus `Kochin` muss `Koch` als Kandidat fallen.

Weibliche Namen stehen im Kirchenbuch moviert. Abschneiden der Endung wäre
falsch, weil es echte Namen auf `-in` gibt (Eberwein, Feuerstein, Bürlin).
Deshalb werden *Kandidaten* gebildet und dem Bestand vorgelegt; entschieden
wird über den Treffer, nicht über die Form.

Der Fall, an dem das Verfahren hängt: `Kochin` wurde als `Rothin` gelesen.
Beide Namen gibt es, `Roth` sogar 59mal. Nur der Abgleich über Datum und Ort
deckt so etwas auf, und dafür muss `Koch` überhaupt erst unter den
Kandidaten sein.
"""
import unittest

from werkstatt import normalform


class Kandidaten(unittest.TestCase):

    def kand(self, kb):
        formen, _ = normalform.kandidaten(kb)
        return formen

    def test_grundform_faellt_ab(self):
        """Der Kernfall: die Grundform muss unter den Kandidaten sein."""
        self.assertIn("koch", self.kand("Kochin"))

    def test_umlaut_wird_zurueckgenommen(self):
        """`Kauffmännin` gehört zu `Kauffmann`, nicht zu `Kauffmänn`."""
        self.assertIn("kauffmann", self.kand("Kauffmännin"))

    def test_weitere_endungen(self):
        """Neben X-in auch X, X-e, X-er: welche gilt, sagt der Bestand."""
        formen = self.kand("Fallerin")
        for erwartet in ("faller", "fallere", "fallerer"):
            self.assertIn(erwartet, formen)

    def test_die_gelesene_form_bleibt_erhalten(self):
        """Die Lesung selbst darf nie verlorengehen.

        Sie ist die Rückgabe neben den Kandidaten und die einzige Form, die
        wirklich im Buch steht.
        """
        formen, kb = normalform.kandidaten("Kochin")
        self.assertEqual(kb, "Kochin")
        self.assertIn("kochin", formen)


class Falten(unittest.TestCase):
    """Vergleichsform: Umlaute auf, Großschreibung weg."""

    def test_umlaute(self):
        self.assertEqual(normalform.falte("Müller"), "muller")

    def test_gleiche_namen_falten_gleich(self):
        self.assertEqual(normalform.falte("MÜLLER"), normalform.falte("müller"))


if __name__ == "__main__":
    unittest.main()
