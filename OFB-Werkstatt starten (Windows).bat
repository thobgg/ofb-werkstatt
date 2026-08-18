@echo off
rem OFB-Werkstatt unter Windows starten - diese Datei doppelt anklicken.
rem Sie prueft der Reihe nach, was fehlt, und sagt es im Klartext,
rem statt sich mit einer Fehlermeldung zu schliessen.
setlocal
cd /d "%~dp0"
title OFB-Werkstatt

if not exist "start.py" (
  echo.
  echo   Hier fehlt start.py - diese Datei liegt nicht im Projektordner.
  echo   Haeufigster Grund: Das ZIP wurde nur angeschaut, nicht ausgepackt.
  echo   Bitte im Explorer Rechtsklick auf das ZIP, "Alle extrahieren",
  echo   und die Startdatei im ausgepackten Ordner anklicken.
  echo.
  pause
  exit /b 1
)

where py >nul 2>&1 && (set PY=py) || (set PY=python)
%PY% --version >nul 2>&1
if errorlevel 1 goto kein_python
goto python_da

:kein_python
rem Python fehlt. Auf Windows 10/11 kann winget es holen - dann entfaellt
rem der Gang zu python.org samt dem beruechtigten PATH-Haekchen.
where winget >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Python ist nicht installiert oder nicht im Suchpfad.
  echo   Holen unter python.org/downloads - beim Installieren bitte
  echo   "Add python.exe to PATH" ankreuzen, dann diese Datei erneut starten.
  echo.
  pause
  exit /b 1
)
echo.
echo   Python ist noch nicht installiert. Es kann jetzt automatisch
echo   geholt werden - ueber winget, die App-Verwaltung von Windows;
echo   die Quelle ist das offizielle python.org.
echo.
choice /C JN /M "  Python jetzt installieren (J) oder selbst kuemmern (N)"
if errorlevel 2 (
  echo.
  echo   Dann bitte von Hand: python.org/downloads, beim Installieren
  echo   "Add python.exe to PATH" ankreuzen, danach diese Datei erneut
  echo   anklicken.
  echo.
  pause
  exit /b 1
)
echo.
echo   Das dauert ein bis zwei Minuten ...
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --override "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1"
if errorlevel 1 (
  echo.
  echo   Das hat nicht geklappt. Dann bitte von Hand:
  echo   python.org/downloads, "Add python.exe to PATH" ankreuzen.
  echo.
  pause
  exit /b 1
)
echo.
echo   Python ist installiert. Bitte dieses Fenster schliessen und die
echo   Startdatei ERNEUT anklicken - erst ein neues Fenster kennt den
echo   neuen Suchpfad.
echo.
pause
exit /b 0

:python_da

rem Fehlende Pakete holt start.py selbst und sagt dabei, was es tut.

where claude >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Hinweis: Claude Code ist nicht installiert.
  echo   Ohne das laeuft die Werkstatt, aber Lesen geht nur mit
  echo   API-Schluessel oder Testdaten. Einrichten: claude.com/download,
  echo   danach einmal  claude auth login  eingeben.
  echo.
)

echo.
echo   Die Werkstatt laeuft gleich unter http://127.0.0.1:8765
echo   Zum Beenden dieses Fenster schliessen.
echo.
%PY% start.py
pause
