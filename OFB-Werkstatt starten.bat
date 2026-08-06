@echo off
rem OFB-Werkstatt unter Windows starten — diese Datei doppelt anklicken.
rem Sie prueft der Reihe nach, was fehlt, und sagt es im Klartext,
rem statt sich mit einer Fehlermeldung zu schliessen.
setlocal
cd /d "%~dp0"
title OFB-Werkstatt

where py >nul 2>&1 && (set PY=py) || (set PY=python)
%PY% --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Python ist nicht installiert oder nicht im Suchpfad.
  echo   Holen unter python.org/downloads — beim Installieren bitte
  echo   "Add python.exe to PATH" ankreuzen, dann diese Datei erneut starten.
  echo.
  pause
  exit /b 1
)

%PY% -c "import PIL" >nul 2>&1
if errorlevel 1 (
  echo   Bildbibliothek Pillow fehlt — wird jetzt geholt ...
  %PY% -m pip install --quiet Pillow
)

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
start "" http://127.0.0.1:8765
%PY% start.py --port 8765
pause
