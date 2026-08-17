"""HTML der Korrekturmaske.

Der Inhalt liegt in static/korrektur.html - als echte HTML-Datei statt
als Python-String. Gelesen wird einmal beim Import.
"""
from pathlib import Path

SEITE = (Path(__file__).resolve().parent / "static"
         / "korrektur.html").read_text(encoding="utf-8")
