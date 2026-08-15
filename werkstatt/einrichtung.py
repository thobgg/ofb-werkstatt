#!/usr/bin/env python3
"""Das erste Mal: aus einem leeren Ordner ein Projekt machen.

Bisher war der Einstieg eine Datei. Wer die Werkstatt frisch auspackte,
sah „Musterhausen" und leere Register und musste erst `konfig.local.toml`
von Hand schreiben — genau dort bricht ab, wer kein Programmierer ist.

Hier wird dieselbe Datei geschrieben, nur aus drei Angaben: wie die
Gemeinde heißt, welche Register geführt werden, wo die Scans liegen.
Alles Weitere bleibt, wo es steht: Feldlisten, Rollen und Kaskaden stehen
in `konfig.toml` und sind nichts, was man beim ersten Start entscheidet.

**Ein Projekt ist ein Ordner.** Eine zweite Pfarrei bekommt eine zweite
Auspackung — eigene Datenbank, eigene Bilder, eigene lokale Konfiguration.
Das ist keine Notlösung, sondern hält zwei Bestände sauber getrennt; nichts
kann versehentlich vom einen in den anderen wandern.
"""
import re
from pathlib import Path

from . import konfig


def eingerichtet():
    """Steht schon ein eigener Name da, oder noch das Beispiel?"""
    return konfig.LOKAL.exists() and bool(
        (konfig.konfig().get("gemeinde") or {}).get("name")
        ) and konfig.konfig()["gemeinde"]["name"] != "Musterhausen"


def _wert(s):
    """Eine Zeichenkette so einpacken, dass TOML sie wieder herausbekommt.

    Von Hand, weil die Standardbibliothek TOML nur lesen kann. Es geht
    ausschließlich um Zeichenketten — deshalb reicht der einfache
    Grundstock: Rückstrich und Anführungszeichen schützen, Steuerzeichen
    fliegen raus.
    """
    s = re.sub(r"[\x00-\x1f]", " ", str(s)).strip()
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def schreibe(gemeinde, register, ort=None, religion=None):
    """konfig.local.toml erzeugen. Gibt den geschriebenen Text zurück.

    `register` ist eine Liste aus `{art, ordner}`. Nur bekannte Arten
    werden übernommen — eine erfundene hätte keine Feldliste und würde
    beim ersten Lesen scheitern, dann aber unverständlich.
    """
    bekannt = list(konfig.register())
    zeilen = [
        "# Lokale Konfiguration — steht in .gitignore und geht in kein Repo.",
        "# Von der Einrichtung geschrieben; von Hand ändern ist erlaubt.",
        "",
        "[gemeinde]",
        f"name        = {_wert(gemeinde)}",
        f"ort_default = {_wert(ort or gemeinde)}",
    ]
    if religion:
        zeilen.append(f"religion_default = {_wert(religion)}")
    genommen = []
    for r in register:
        art = (r.get("art") or "").strip()
        if art not in bekannt:
            continue
        ordner = (r.get("ordner") or "").strip()
        if not ordner:
            continue
        zeilen += ["", f"[register.{art}]", f"ordner = {_wert(ordner)}"]
        genommen.append(art)
    if not genommen:
        raise SystemExit("Kein Register mit Bildordner angegeben.")
    text = "\n".join(zeilen) + "\n"
    konfig.LOKAL.write_text(text, encoding="utf-8")
    # Die Konfiguration wird einmal gelesen und gemerkt. Ohne das Leeren
    # arbeitet der laufende Server bis zum Neustart mit „Musterhausen"
    # weiter — und niemand versteht, warum die Einrichtung nichts bewirkt.
    konfig.konfig.cache_clear()
    return text


# Was viele Forscher nicht erfassen wollen, ohne dass es falsch waere.
# Bewusst nicht abgeschaltet, sondern nur vorgeschlagen: Wer Paten sammelt,
# sammelt sie oft gerade wegen der Verwandtschaftsgeflechte.
ENTBEHRLICH = {
    "taufe": ["paten", "taufender", "religion", "vater_religion",
              "mutter_religion", "geburt_zeit"],
    "ehe": ["proklamation", "zeugen", "trauender", "textus", "religion",
            "braeutigam_religion", "braut_religion"],
    "tod": ["beerdigender", "leichenpredigt", "begraebnisart", "religion",
            "verstorbener_religion", "sterbe_zeit"],
}


def feldvorschlag():
    """Je Aktart die Felder mit dem Vermerk, ob sie meist gebraucht werden.

    Damit die Einrichtung fragen kann, was erfasst werden soll — statt dass
    der Bearbeiter es nach der ersten Runde in der Aktkarte nachholt und
    die schon gelesenen Werte wieder loswerden muss.
    """
    from . import katalog
    z = {}
    for art in katalog.KATALOG:
        z[art] = [dict(name=x.name, titel=x.titel, rolle=x.rolle,
                       vorgeschlagen=x.name not in ENTBEHRLICH.get(art, []))
                  for x in katalog.felder(art)]
    return z


def beispielbestand():
    """Der mitgelieferte Bestandsauszug, falls vorhanden.

    Ohne ihn zeigt die Demo den Nullstart: alles gelb, der Elternehe-Anker
    unsichtbar. Gemessen an denselben Seiten — ohne Auszug null grün, mit
    Auszug sechzehn.
    """
    p = konfig.WURZEL / "demo" / "bestand.ged"
    return str(p) if p.exists() else None


def vorschlag():
    """Was die Einrichtung anbietet, wenn sie nichts weiß.

    Liegen die Beispielseiten bei, werden ihre Ordner vorgeschlagen — dann
    hat ein frisch ausgepacktes Projekt vom ersten Klick an etwas zu tun.
    Wer eigene Bücher hat, trägt deren Ordner ein; die Beispiele bleiben
    unberührt.
    """
    z = []
    for art in konfig.register():
        r = konfig.register(art) or {}
        beispiel = konfig.WURZEL / "demo" / "bilder" / art
        hat = beispiel.is_dir() and any(beispiel.glob("*.jpg"))
        z.append(dict(art=art, titel=r.get("titel", art),
                      ordner=(f"demo/bilder/{art}" if hat
                              else r.get("ordner", f"bilder/{art}")),
                      beispiel=hat))
    return z
