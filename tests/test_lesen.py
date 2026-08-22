"""Die Modellanbindung, soweit sie ohne Netz prüfbar ist.

Zwei Dinge lassen sich hier festhalten: was ein Lauf kostet, und dass die
Antwort auch dann ankommt, wenn das Modell sie in Zäune packt oder etwas
davorschreibt.
"""
import unittest

from werkstatt import lesen


class Kosten(unittest.TestCase):

    def test_rechnung_aus_der_preisliste(self):
        """Je eine Million Token hinein und heraus, zum Listenpreis."""
        m = lesen.MODELLE["claude-opus-5"]
        self.assertAlmostEqual(
            lesen.kosten("claude-opus-5", 1_000_000, 1_000_000),
            m["ein"] + m["aus"])

    def test_batch_halbiert(self):
        voll = lesen.kosten("claude-opus-5", 500_000, 100_000)
        self.assertAlmostEqual(
            lesen.kosten("claude-opus-5", 500_000, 100_000, batch=True),
            voll / 2)

    def test_unbekanntes_modell_gibt_keine_zahl(self):
        """Lieber keine Angabe als eine erfundene."""
        self.assertIsNone(lesen.kosten("modell-das-es-nicht-gibt", 100, 100))

    def test_jedes_modell_hat_eine_bildkante(self):
        """Ohne Kante wüsste `bild_teil()` nicht, worauf zu verkleinern ist."""
        for name, m in lesen.MODELLE.items():
            self.assertIn("kante", m, name)
            self.assertGreater(m["kante"], 0, name)


class AntwortSchaelen(unittest.TestCase):

    def test_nacktes_json(self):
        self.assertEqual(lesen.json_aus('{"eintraege": []}'), {"eintraege": []})

    def test_in_zaeunen(self):
        self.assertEqual(lesen.json_aus('```json\n{"a": 1}\n```'), {"a": 1})

    def test_mit_vorspann(self):
        """Modelle stellen gern einen Satz voran, obwohl der Prompt es verbietet."""
        self.assertEqual(lesen.json_aus('Gern, hier: {"a": 2}'), {"a": 2})

    def test_ohne_json_kein_absturz(self):
        self.assertEqual(lesen.json_aus("Das kann ich nicht lesen."), {})


if __name__ == "__main__":
    unittest.main()
