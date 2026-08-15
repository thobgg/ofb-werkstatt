#!/bin/sh
# OFB-Werkstatt starten – anklicken oder im Terminal aufrufen:
#     ./"OFB-Werkstatt starten (Linux+Mac).command"
#
# Das ist ein Shell-Skript, kein Python. Wer lieber tippt, nimmt direkt
#     python3 start.py
# – das tut inzwischen dasselbe, Browser inbegriffen.
set -e
cd "$(dirname "$0")"

python3 -c 'import PIL' 2>/dev/null || {
  echo "Bildbibliothek Pillow fehlt – wird geholt ..."
  python3 -m pip install --quiet Pillow
}

python3 -c 'import numpy' 2>/dev/null || {
  echo "numpy fehlt – wird geholt ..."
  python3 -m pip install --quiet numpy
}

command -v claude >/dev/null || cat <<'ENDE'

  Hinweis: Claude Code ist nicht installiert. Die Werkstatt läuft trotzdem,
  aber Lesen geht dann nur mit API-Schlüssel oder Testdaten.
  Einrichten: claude.com/download

ENDE

exec python3 start.py "$@"
