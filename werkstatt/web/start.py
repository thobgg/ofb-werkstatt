"""HTML des Startbildschirms, der Leseseite und der Übergabe.

Der Inhalt liegt in static/start.html - als echte HTML-Datei mit
Highlighting, Diff und Werkzeugunterstützung, nicht mehr als
Python-String. Gelesen wird einmal beim Import; wer am Frontend
arbeitet, startet den Server neu, wie bisher auch.
"""
from pathlib import Path

STARTSEITE = (Path(__file__).resolve().parent / "static"
              / "start.html").read_text(encoding="utf-8")
