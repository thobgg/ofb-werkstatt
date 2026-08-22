"""Mehrparochienbetrieb: Wirt, Portal, Instanzen, Sicherung.

Vier Module, die nur gebraucht werden, wenn mehrere Leute an mehreren
Parochien arbeiten. Der Einzelplatz aus dem README fasst nichts davon an,
und die Web-App auch nicht: `web/app.py` importiert aus diesem Paket
keine Zeile.

Sie liegen hier zusammen, damit man beim Lesen des Codes sieht, was man
überspringen kann. Es ist derselbe Code und derselbe Zweig wie der
Einzelplatz, nur einsortiert - die Gleichwertigkeit der beiden
Betriebsarten haengt daran, dass es eben *keine* zweite Fassung gibt.

    instanz    eine Parochie anlegen, provisionieren, auflisten
    wirt       alle Instanzen als Prozesse in einem Container
    portal     die Betreiber-Oberflaeche darueber
    sicherung  eine Instanz als ZIP sichern und zurueckholen

Aufgerufen wird jedes wie bisher, nur mit dem Paket davor:

    python3 -m werkstatt.verein.instanz --liste
    OFB_PORTAL_PASSWORT=... python3 -m werkstatt.verein.portal
"""
