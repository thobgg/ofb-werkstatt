# Das Admin-Portal im Container - fuer den Wirt (NAS oder Vereinsserver),
# wo das System-Python zu alt ist. git gehoert ins Bild: Die
# Provisionierung klont die Werkstatt aus `git ls-files`, und pillow/
# numpy braucht der kurz gestartete Instanz-Klon beim Einrichten.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pillow numpy gedcom7 \
    # Das Repo ist eingehaengt und gehoert einem anderen Benutzer als
    # root im Container - ohne safe.directory verweigert git ls-files
    # mit "dubious ownership", und die Provisionierung steht.
    && git config --global --add safe.directory /repo
WORKDIR /repo
EXPOSE 8767
CMD ["python3", "-m", "werkstatt.portal", "--wurzel", "/instanzen", \
     "--port", "8767"]
