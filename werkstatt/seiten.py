#!/usr/bin/env python3
"""Bildsichtung: Vollständigkeit, Dubletten, Auflösung.

Erster Arbeitsschritt jeder Runde. Prüft, was tatsächlich vorliegt, bevor
gelesen wird – Scans enthalten regelmäßig dieselbe Buchöffnung zweimal, und
Nummernlücken weisen auf fehlende Seiten hin.

    python3 -m werkstatt.seiten ehe
    python3 -m werkstatt.seiten ehe --uebersicht     erzeugt kleine Vorschauen

Ohne Fremdbibliotheken ausser Pillow; ImageMagick wird nicht gebraucht.
"""
import argparse
import re
import shutil
import statistics
import subprocess
from pathlib import Path

from . import konfig

try:
    from PIL import Image
except ImportError:
    Image = None

BILD = (".jpg", ".jpeg", ".png", ".tif", ".tiff")

# PDFs sind Behälter, keine Bilder: Ein Archion-Download enthält oft den
# halben Band. Sie werden einmal in Einzelseiten zerlegt und danach wie
# gewöhnliche Bilder behandelt.
AUFLOESUNG = 300          # dpi; darunter leidet die Lesbarkeit der Hand
ENTPACKT = "entpackt"     # Unterordner neben den PDFs

# Dublettenschwelle als Anteil des MEDIANS dieses Registers, nicht absolut.
# Begruendung: Der uebliche Abstand zweier Nachbarseiten haengt vom Layout ab.
# Im Taufregister Haberschlacht liegt der Median bei ~21000, im Eheregister
# bei ~18500 (andere Spaltenaufteilung). Eine aus einem Buch uebernommene
# absolute Schwelle meldete dort 20 Fehlalarme; relativ zum Median trennen
# sich echte Dubletten sauber bei rund 50 %.
DUBLETTE = 0.55
VERDACHT = 0.70


def bilder(ordner):
    """Alle Seitenbilder eines Registers, entpackte PDF-Seiten eingeschlossen."""
    p = Path(ordner)
    if not p.exists():
        return []
    raus = [f for f in p.iterdir()
            if f.is_file() and f.suffix.lower() in BILD]
    e = p / ENTPACKT
    if e.is_dir():
        raus += [f for f in e.iterdir()
                 if f.is_file() and f.suffix.lower() in BILD]
    return sorted(raus, key=lambda f: (nummer(f) or 0, f.name))


def pdfs(ordner):
    p = Path(ordner)
    if not p.exists():
        return []
    return sorted(f for f in p.iterdir()
                  if f.is_file() and f.suffix.lower() == ".pdf")


def pdf_werkzeug():
    return shutil.which("pdftoppm")


def pdf_seitenzahl(pdf):
    werkzeug = shutil.which("pdfinfo")
    if not werkzeug:
        return None
    try:
        aus = subprocess.run([werkzeug, str(pdf)], capture_output=True,
                             text=True, timeout=60).stdout
    except Exception:
        return None
    m = re.search(r"^Pages:\s+(\d+)", aus, re.M)
    return int(m.group(1)) if m else None


def entpacken(ordner, still=False):
    """PDFs in Einzelseiten zerlegen – einmal, danach wie Bilder behandelt.

    Bereits entpackte PDFs werden übersprungen; der Aufruf ist damit
    beliebig oft wiederholbar und kostet dann nichts.
    """
    werkzeug = pdf_werkzeug()
    if not werkzeug:
        return dict(fehler="pdftoppm nicht gefunden – Paket poppler-utils")
    ziel = Path(ordner) / ENTPACKT
    z = dict(pdfs=0, seiten_neu=0, uebersprungen=0)
    for pdf in pdfs(ordner):
        z["pdfs"] += 1
        marke = f"{pdf.stem}-"
        da = [f for f in ziel.iterdir()] if ziel.is_dir() else []
        if any(f.name.startswith(marke) for f in da):
            z["uebersprungen"] += 1
            continue
        ziel.mkdir(parents=True, exist_ok=True)
        if not still:
            n = pdf_seitenzahl(pdf)
            print(f"  entpacke {pdf.name}"
                  + (f" ({n} Seiten)" if n else "") + " …", flush=True)
        subprocess.run([werkzeug, "-r", str(AUFLOESUNG), "-jpeg",
                        "-jpegopt", "quality=92", str(pdf),
                        str(ziel / pdf.stem)], check=False, timeout=3600)
        z["seiten_neu"] += sum(1 for f in ziel.iterdir()
                               if f.name.startswith(marke))
    return z


def nummer(pfad):
    m = re.search(r"(\d{3,6})(?=\D*$)", pfad.stem)
    return int(m.group(1)) if m else None


def luecken(dateien):
    ns = sorted(n for n in (nummer(f) for f in dateien) if n is not None)
    if not ns:
        return [], None, None
    return [n for n in range(ns[0], ns[-1] + 1) if n not in ns], ns[0], ns[-1]


def miniatur(pfad, kante=400):
    im = Image.open(pfad).convert("L")
    return im.resize((kante, kante))


def abstand(a, b):
    """RMSE zweier Miniaturen. 0 = identisch."""
    pa, pb = a.tobytes(), b.tobytes()
    s = sum((x - y) ** 2 for x, y in zip(pa, pb))
    return (s / len(pa)) ** 0.5 * 257  # Skala wie ImageMagick RMSE (0..65535)


def dubletten(dateien):
    """Nachbarpaare mit auffaellig geringem Abstand – relativ zum Median."""
    if Image is None or len(dateien) < 3:
        return [], None
    minis = [miniatur(f) for f in dateien]
    paare = [(abstand(a, b), dateien[i], dateien[i + 1])
             for i, (a, b) in enumerate(zip(minis, minis[1:]))]
    med = statistics.median(v for v, _, _ in paare)
    raus = []
    for v, a, b in sorted(paare):
        anteil = v / med if med else 1
        if anteil < VERDACHT:
            raus.append((v, anteil, a, b, "dublette" if anteil < DUBLETTE else "verdacht"))
    return raus, med


def sichte(art, uebersicht=False, ordner=None):
    ordner = ordner or konfig.bilderordner(art)
    if pdfs(ordner):
        entpacken(ordner)
    fs = bilder(ordner)
    titel = konfig.register(art).get("titel", art)
    print(f"=== {titel} ===  {ordner}")
    if not fs:
        print("  keine Bilder")
        return
    lk, von, bis = luecken(fs)
    print(f"  {len(fs)} Bilder, Nummern {von}–{bis}")
    if lk:
        print(f"  ⚠ {len(lk)} Nummernlücken: {lk[:20]}{' …' if len(lk) > 20 else ''}")
    else:
        print("  keine Nummernlücken")

    if Image is not None:
        mps = []
        for f in fs:
            with Image.open(f) as im:
                mps.append(im.size[0] * im.size[1] / 1e6)
        mps.sort()
        mitte = statistics.median(mps)
        print(f"  Auflösung {mitte:.1f} MP im Mittel "
              f"(kleinste {mps[0]:.1f}, größte {mps[-1]:.1f})")
        if mps[0] < 15:
            schwach = sum(1 for m in mps if m < 15)
            print(f"  ⚠ {schwach} Bild(er) unter 15 MP – höhere Auflösung suchen")

        dub, med = dubletten(fs)
        echte = [d for d in dub if d[4] == "dublette"]
        print(f"  Nachbarabstand: Median {med:.0f}")
        if dub:
            for v, a, f1, f2, art_ in dub:
                zeichen = "⚠" if art_ == "dublette" else "·"
                print(f"   {zeichen} {f1.name} ↔ {f2.name}   {v:.0f} = {a*100:.0f} % des Medians")
        print(f"  → {len(echte)} Dublette(n), netto {len(fs)-len(echte)} Buchöffnungen")

    if uebersicht and Image is not None:
        ziel = konfig.WURZEL / "daten" / "uebersicht" / art
        ziel.mkdir(parents=True, exist_ok=True)
        for f in fs:
            with Image.open(f) as im:
                im.thumbnail((1250, 1250))
                im.convert("L").save(ziel / f"{f.stem}.jpg", quality=85)
        print(f"  Übersichten: {konfig.kurz(ziel)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("register", nargs="*", help="leer = alle aus konfig.toml")
    ap.add_argument("--uebersicht", action="store_true")
    ap.add_argument("--entpacken", action="store_true",
                    help="nur PDFs in Einzelseiten zerlegen")
    a = ap.parse_args()
    arten = a.register or list(konfig.register())
    for i, art in enumerate(arten):
        if i:
            print()
        if art not in konfig.register():
            print(f"unbekanntes Register: {art}")
            continue
        if a.entpacken:
            o = konfig.bilderordner(art)
            print(f"=== {art} ===  {o}")
            z = entpacken(o)
            print("  " + " · ".join(f"{k} {v}" for k, v in z.items()))
            continue
        sichte(art, a.uebersicht)


if __name__ == "__main__":
    main()
