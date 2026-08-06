#!/bin/sh
# OFB-Werkstatt starten — diese Datei anklicken oder im Terminal aufrufen.
# Läuft eine Werkstatt schon, wird nur das Fenster geöffnet statt eine
# zweite zu starten; sonst scheitert sie am belegten Port.
set -e
cd "$(dirname "$0")"
PORT=8765
URL="http://127.0.0.1:$PORT"

# Nicht ueber /dev/tcp — das kann nur die bash, und hier laeuft sh.
laeuft() {
  python3 -c "import socket,sys
s=socket.socket(); s.settimeout(1)
sys.exit(s.connect_ex(('127.0.0.1',$PORT)) != 0)" 2>/dev/null
}

if laeuft; then
  echo "Die Werkstatt läuft schon — öffne $URL"
  xdg-open "$URL" >/dev/null 2>&1 &
  exit 0
fi

python3 -c 'import PIL' 2>/dev/null || {
  echo "Bildbibliothek Pillow fehlt — wird geholt ..."
  python3 -m pip install --quiet Pillow
}

command -v claude >/dev/null || cat <<'ENDE'

  Hinweis: Claude Code ist nicht installiert. Die Werkstatt läuft trotzdem,
  aber Lesen geht dann nur mit API-Schlüssel oder Testdaten.
  Einrichten: claude.com/download

ENDE

echo "Die Werkstatt läuft gleich unter $URL — zum Beenden Strg+C."
( sleep 3; xdg-open "$URL" >/dev/null 2>&1 ) &
exec python3 start.py --port "$PORT"
