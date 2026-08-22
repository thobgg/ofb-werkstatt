"""Seitennummern aus Dateinamen – die stille Stolperfalle beim Einrichten.

`nummer()` bestimmt die Reihenfolge der Seiten und damit auch, welche
Lücken die Sichtung meldet. Sie liest die *letzte* Ziffernfolge im Namen.
Das ist bequem für Archivnamen wie `1184798-00359.jpg` und eine Falle für
selbst vergebene Namen mit Jahreszahl am Ende.
"""
import unittest
from pathlib import Path

from werkstatt import seiten


class Seitennummer(unittest.TestCase):

    def test_archionname(self):
        """Der übliche Fall: Bildnummer am Ende, führende Nullen egal."""
        self.assertEqual(seiten.nummer(Path("1184798-00359.jpg")), 359)

    def test_eigener_name_mit_nummer_am_ende(self):
        """Empfohlene Form: Jahr davor, Bildnummer zuletzt."""
        self.assertEqual(
            seiten.nummer(Path("winkel-taufen-1820-00017.jpg")), 17)

    def test_jahreszahl_am_ende_wird_zur_seitenzahl(self):
        """Die Falle, und sie ist Absicht dieses Tests, nicht ein Fehler.

        Steht die Jahreszahl zuletzt, wird sie als Seitennummer gelesen.
        Die Sichtung sortiert dann nach Jahr und meldet die Jahre dazwischen
        als fehlende Seiten. Wer das ändert, muss die Empfehlung in
        `doku/code.md` und im README mitändern.
        """
        self.assertEqual(seiten.nummer(Path("Winkel_Taufen_1820.jpg")), 1820)

    def test_ohne_ziffern(self):
        self.assertIsNone(seiten.nummer(Path("titelblatt.jpg")))

    def test_zu_kurze_ziffernfolge(self):
        """Unter drei Ziffern zählt nicht – sonst würde jedes `v2` greifen."""
        self.assertIsNone(seiten.nummer(Path("scan-v2.jpg")))


class Luecken(unittest.TestCase):

    def test_meldet_fehlende_nummern(self):
        da = [Path(f"buch-{n:05d}.jpg") for n in (10, 11, 13, 14)]
        fehlend, erste, letzte = seiten.luecken(da)
        self.assertEqual(fehlend, [12])
        self.assertEqual((erste, letzte), (10, 14))

    def test_ohne_nummern_keine_aussage(self):
        fehlend, erste, letzte = seiten.luecken([Path("a.jpg"), Path("b.jpg")])
        self.assertEqual(fehlend, [])
        self.assertIsNone(erste)


if __name__ == "__main__":
    unittest.main()
