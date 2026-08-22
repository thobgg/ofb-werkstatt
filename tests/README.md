# Die schnellen Prüfungen

    python3 -m unittest discover tests -v

Standardbibliothek, keine zusätzlichen Pakete. Geprüft wird hier, was sich
ohne Modell, ohne Netz und ohne Bilder prüfen lässt: die Bausteine, auf
denen der Durchlauf steht.

Den Durchlauf selbst prüft `python3 -m werkstatt.probelauf`. Die beiden
ergänzen sich: Hier steht, was eine einzelne Funktion zusagt, dort, dass
das Ganze noch zusammenpasst.

Jeder Test hält eine Zusage fest, die im Projekt begründet ist, nicht
irgendein beliebiges Verhalten. Wer einen davon brechen muss, ändert eine
Zusage und sollte wissen, welche.
