#!/usr/bin/env python3
"""Seitenraster: Spalten je Buch, Zeilen je Seite.

Daraus ergibt sich für jedes Feld der Bildausschnitt — deterministisch,
ohne dass ein Modell Koordinaten schätzen muss.

## Warum Helligkeit nicht trennt

Die Vorgängerfassung suchte das Papier über eine feste Helligkeitsschwelle.
Das kann nicht funktionieren, gemessen an den vier Taufregisterseiten:

    Formular   Median 250–252
    darüber    Median 244–251      ← die weiße Unterlage neben dem Buch
    darunter   Median   4– 46      ← Buchschnitt und Deckel

Die Unterlage ist so hell wie das Papier. Was das Formular auszeichnet, ist
nicht seine Helligkeit, sondern seine **gedruckten Linien**: dunkle Pixel mit
hellen Nachbarn quer zur Laufrichtung. Buchdeckel ist dunkel mit dunklen
Nachbarn, die Unterlage hell ohne Struktur. `linienmaske` trennt genau das,
und zwar relativ zum Papierniveau der jeweiligen Aufnahme — keine feste Zahl.

## Die drei Abgrenzungen

    Falz      dunkelste Spalte im mittleren Drittel. Über alle vier Seiten
              x=3024–3052 bei Kontrast 5–46 gegen Papiermittel ~220 —
              das mit Abstand stabilste Merkmal der ganzen Seite.
    links     erste und letzte kräftige senkrechte Linie
    /rechts
    oben      Zeilen, über die senkrechte Spaltenlinien laufen; nach unten
    /unten    bis zur Helligkeitskante verlängert, weil die Tabelle am
              Papierende ausläuft statt mit einer Linie abzuschließen

**Waagerechte Linien werden je Buchseite gemessen, nie über den Falz hinweg.**
Sie laufen nur über je eine Seite; über die Doppelseite gemessen verschmieren
sie. Ebenso zählt der **Anteil dunkler Pixel**, nicht die längste
durchgehende Lauflänge — jede Stelle, an der Handschrift eine Linie kreuzt,
halbiert den Lauf.

## Stand der Messung

`python3 -m werkstatt.messung` misst gegen `daten/soll_zeilen.json` — vier
Taufregisterseiten mit 26 von Hand gezogenen Grenzen, davon 22 gedruckte
Linien und 4 das Ende der Erfassung.

    Zeilenlinien   ±25 px  18/22 =  82 %
                   ±40 px  22/22 = 100 %
    ueberzaehlige Vorschlaege im Eintragsbereich:  0
    Papierkante unterhalb der Erfassung:         4/4
    Falz ueber alle sieben Seiten:      x=3024–3072

Die Sollwerte sind aus den von Hand geschnittenen Eintragsstreifen
zurueckgewonnen und selbst nur auf etwa ±40 px genau — unterhalb dieser
Toleranz misst man teilweise den Rekonstruktionsfehler mit. Die ±25-px-Zahl
ist deshalb eine Untergrenze, nicht das Koennen des Verfahrens.

Zum Vergleich die frueheren Messungen: 14 % (laengster Lauf ueber die
Doppelseite), 42 % (Anteil dunkler Pixel, Seiten getrennt), 71 % (dieselbe
Methode bei sauber abgegrenzter Seite).

**Offen:** Die aeusserste linke Randlinie wird nicht immer erfasst — auf
00365 beginnt der erkannte Block bei x=1264 statt 1160. Fuer die Zeilen
folgenlos, fuer das Spaltenraster nicht; das wird ohnehin von Hand gezogen.

**Verwendung: Vorschlag, nicht Entscheidung.** Der Rastereditor zeigt die
gefundenen Linien vor, der Bearbeiter zieht fehlende nach. Zusätzlich erbt
jede Folgeseite das Raster der vorigen — das Formular bleibt über Jahrzehnte
gleich, es ist nur Nachschieben um wenige Pixel.

    python3 -m werkstatt.raster bilder/taufe/seite.jpg
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ZIELBREITE = 1400        # Analysebreite; darunter zerfallen die dünnen Linien


def graustufen(pfad):
    """Bild als Graustufenfeld plus Skalierungsfaktor zur Vollauflösung."""
    b = Image.open(pfad).convert("L")
    sk = max(1, round(b.width / ZIELBREITE))
    k = b.resize((b.width // sk, b.height // sk), Image.BILINEAR)
    return np.asarray(k, dtype=np.float64), sk, (b.width, b.height)


def papierniveau(a):
    """Helligkeit des Papiers — relativ zur Aufnahme, nicht fest verdrahtet."""
    return float(np.percentile(a, 90))


def linienmaske(a, achse, k=3, dunkel=0.80, hell=0.90):
    """Dünne dunkle Struktur mit hellen Nachbarn quer zur Laufrichtung.

    achse=0 → waagerechte Linien (Nachbarn ober- und unterhalb)
    achse=1 → senkrechte Linien  (Nachbarn links und rechts)

    Der Nachbarschaftstest ist der eigentliche Trick: er verwirft den
    Buchdeckel (dunkel, aber dunkle Nachbarn) und die Unterlage (helle
    Nachbarn, aber selbst nicht dunkel) ohne jede Helligkeitsannahme.
    """
    p = papierniveau(a)
    return ((a < dunkel * p)
            & (np.roll(a, k, axis=achse) > hell * p)
            & (np.roll(a, -k, axis=achse) > hell * p))


def gruppieren(idx, luecke):
    """Benachbarte Indizes zu je einer Linie zusammenfassen."""
    if not len(idx):
        return []
    g, akt = [], [int(idx[0])]
    for y in idx[1:]:
        if y - akt[-1] <= luecke:
            akt.append(int(y))
        else:
            g.append(akt)
            akt = [int(y)]
    g.append(akt)
    return g


def papier(a):
    """Papierblock finden und am Falz in Buchseiten teilen.

    Liefert (bloecke, falz). Jeder Block ist (x0, x1, y0, y1).
    Kein Falz erkannt → eine einzelne Buchseite, falz ist None.
    """
    senk = linienmaske(a, achse=1)
    sprof = senk.mean(axis=0)
    if sprof.max() <= 0:
        return [], None
    stark = np.where(sprof > 0.25 * sprof.max())[0]
    if len(stark) < 2:
        return [], None
    x0, x1 = int(stark[0]), int(stark[-1])

    # Falz: dunkelste Spalte im mittleren Drittel, nur wenn deutlich dunkler
    mittel = a[:, x0:x1].mean(axis=0)
    m0, m1 = int(0.35 * len(mittel)), int(0.65 * len(mittel))
    kerbe = m0 + int(np.argmin(mittel[m0:m1]))
    falz = x0 + kerbe if mittel[kerbe] < 0.6 * np.median(mittel) else None

    spalten = [(x0, x1)] if falz is None else [(x0, falz - 8), (falz + 8, x1)]
    bloecke = []
    for bx0, bx1 in spalten:
        if bx1 - bx0 < 40:
            continue
        y0, y1 = _hoehe(a, senk, bx0, bx1)
        if y1 - y0 > 40:
            bloecke.append((bx0, bx1, y0, y1))
    return bloecke, falz


def _hoehe(a, senk, x0, x1, anteil=0.25):
    """Obere und untere Papierkante einer Buchseite.

    Grundlage sind die senkrechten Spaltenlinien: sie laufen über die volle
    Formularhöhe und fehlen auf der Unterlage. Nach unten wird bis zur
    Helligkeitskante verlängert, weil die Tabelle am Papierende ausläuft.
    """
    prof = senk[:, x0:x1].mean(axis=1)
    drin = np.where(prof > anteil * prof.max())[0]
    if not len(drin):
        return 0, a.shape[0]
    y0, y1 = int(drin[0]), int(drin[-1])

    p = papierniveau(a)
    hell = (a[:, x0:x1] > 0.85 * p).mean(axis=1)
    while y1 + 1 < a.shape[0] and hell[y1 + 1] > 0.5:
        y1 += 1
    while y0 > 0 and hell[y0 - 1] > 0.5 and prof[y0 - 1] > 0:
        y0 -= 1
    return y0, y1


def _schaerfstes_profil(m, grenze=12, schritt=2):
    """Zeilenprofil bei der Schräglage, die den schärfsten Peak ergibt."""
    h, w = m.shape
    bestes = None
    for winkel in range(-grenze, grenze + 1, schritt):
        versch = np.round(np.linspace(-winkel / 2, winkel / 2, w)).astype(int)
        p = np.zeros(h)
        for x in range(w):
            p += np.roll(m[:, x], -versch[x])
        p /= w
        if bestes is None or p.max() > bestes.max():
            bestes = p
    return bestes


def zeilenlinien(a, block, mindest=0.45, luecke=3):
    """Waagerechte Linien einer Buchseite über den Anteil dunkler Pixel."""
    x0, x1, y0, y1 = block
    m = linienmaske(a, achse=0)[y0:y1 + 1, x0:x1]
    if m.size == 0:
        return []
    prof = _schaerfstes_profil(m)
    if prof.max() <= 0:
        return []
    kand = np.where(prof > mindest * prof.max())[0]
    return [y0 + int(np.mean(g)) for g in gruppieren(kand, luecke)]


def spaltenlinien(a, block, mindest=0.30, luecke=3):
    """Senkrechte Linien einer Buchseite — dieselbe Idee, um 90 Grad gedreht."""
    x0, x1, y0, y1 = block
    m = linienmaske(a, achse=1)[y0:y1 + 1, x0:x1]
    if m.size == 0:
        return []
    prof = m.mean(axis=0)
    if prof.max() <= 0:
        return []
    kand = np.where(prof > mindest * prof.max())[0]
    return [x0 + int(np.mean(g)) for g in gruppieren(kand, luecke)]


def vereinen(links, rechts, tol):
    """Zeilengrenzen beider Buchseiten vereinen — nahe Paare mitteln.

    Eine Eintragszeile läuft über beide Seiten. Was nur eine Seite findet,
    bleibt trotzdem stehen: fehlende Linien kosten mehr als überzählige,
    die der Bearbeiter wegklickt.
    """
    raus, rest = [], list(rechts)
    for l in links:
        nah = [x for x in rest if abs(x - l) <= tol]
        if nah:
            raus.append(int(round((l + nah[0]) / 2)))
            rest.remove(nah[0])
        else:
            raus.append(l)
    return sorted(raus + rest)


def vorschlag(pfad):
    """Rastervorschlag für eine Seite. Bewusst unvollständig."""
    a, sk, (bw, bh) = graustufen(pfad)
    bloecke, falz = papier(a)
    seiten = []
    for b in bloecke:
        x0, x1, y0, y1 = b
        seiten.append(dict(
            x0=x0 * sk, x1=x1 * sk, y0=y0 * sk, y1=y1 * sk,
            zeilen=[y * sk for y in zeilenlinien(a, b)],
            spalten=[x * sk for x in spaltenlinien(a, b)]))
    ganz = []
    if len(seiten) == 2:
        # Dieselbe Eintragszeile steht auf beiden Buchseiten unterschiedlich
        # hoch — gemessen bis 20 px Versatz durch die Buchkruemmung. Die
        # Toleranz muss darueber liegen, aber deutlich unter der Zeilenhoehe
        # (rund 450 px), sonst werden benachbarte Zeilen verschmolzen.
        ganz = [y * sk for y in vereinen(
            [y // sk for y in seiten[0]["zeilen"]],
            [y // sk for y in seiten[1]["zeilen"]], tol=max(4, 60 // sk))]
    elif seiten:
        ganz = list(seiten[0]["zeilen"])
    return dict(datei=Path(pfad).name, groesse=[bw, bh], skala=sk,
                falz=None if falz is None else falz * sk,
                seiten=seiten, zeilen=ganz)


def ausschnitt(raster, seite, zeile, spalte, rand=25):
    """Bildausschnitt für Zelle (Zeile, Spalte) — Basis der Lupe."""
    s = raster["seiten"][seite]
    zs, sp = sorted(s["zeilen"]), sorted(s["spalten"])
    y0 = zs[zeile] if zeile < len(zs) else s["y0"]
    y1 = zs[zeile + 1] if zeile + 1 < len(zs) else s["y1"]
    x0 = sp[spalte] if spalte < len(sp) else s["x0"]
    x1 = sp[spalte + 1] if spalte + 1 < len(sp) else s["x1"]
    return (max(0, x0 - rand), max(0, y0 - rand),
            (x1 - x0) + 2 * rand, (y1 - y0) + 2 * rand)


def main():
    ap = argparse.ArgumentParser(description="Rastervorschlag für eine Seite")
    ap.add_argument("bild")
    ap.add_argument("--json", action="store_true", help="nur JSON ausgeben")
    a = ap.parse_args()
    v = vorschlag(a.bild)
    if a.json:
        print(json.dumps(v, indent=2))
        return
    print(f"{v['datei']}  {v['groesse'][0]}x{v['groesse'][1]}  "
          f"Analyse 1:{v['skala']}  Falz {v['falz']}")
    for i, s in enumerate(v["seiten"]):
        print(f"  Buchseite {i + 1}: x{s['x0']}–{s['x1']}  y{s['y0']}–{s['y1']}")
        print(f"    Zeilenlinien  ({len(s['zeilen']):2}): {s['zeilen']}")
        print(f"    Spaltenlinien ({len(s['spalten']):2}): {s['spalten']}")
    print(f"  vereint ({len(v['zeilen'])}): {v['zeilen']}")
    print("\nVorschlag — unvollständig. Im Editor nachziehen und bestätigen.")


if __name__ == "__main__":
    main()
