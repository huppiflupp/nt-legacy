#!/usr/bin/env python3
"""Macht aus einem Bild ein Plasma-Hintergrundpaket.

    ./mach-wallpaper.py bild.png --id ntlegacy-granit \\
        --name "NT Legacy - Granit" [--kachel] [--qualitaet 95]

Ein Hintergrundpaket ist ein Verzeichnis mit metadata.json und
contents/images/<breite>x<hoehe>.<endung>. Mehr braucht Plasma nicht.

Warum das nicht in build.py steht: build.py erzeugt alles aus
Farbwerten, deterministisch und in Sekunden. Diese Bilder kommen aus
einem Bildmodell, brauchen eine GPU und ein paar Minuten. Sie werden
einmal erzeugt und liegen dann im Repo - ein Neubau des Themes soll sie
nicht jedesmal anfassen muessen.

Ausgegeben wird JPEG, nicht PNG. Die Rohbilder sind zusammen 378 MB;
als JPEG sind es 35. Ein Theme-Archiv, das mehrere hundert Megabyte
gross ist, laedt im Store niemand herunter.

  Landschaften   q92, 3840x2160  ~0,6 MB   gezeichneter Stil, wenig Rauschen
  Kacheln        q95, 2048x2048  ~3 MB     Rauschtexturen, brauchen mehr
  Grossbilder    q92, 4096x4096  ~4 MB

Zu den Kacheln: JPEG rechnet in Bloecken von 8x8 Pixeln. Weil 2048 durch
8 teilbar ist, liegen die Bloecke an beiden Kachelraendern gleich - die
Naht bleibt da, wo sie war. Bei einer krummen Kantenlaenge waere das
nicht so, dann muesste man PNG nehmen.

--kachel schreibt den Hinweis in den Namen. Plasma merkt sich die
Fuellart nicht im Paket, sondern in der Einstellung des Nutzers; der
Hinweis im Namen ist alles, was das Paket dazu beitragen kann.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

AUTOR = "huppiflupp"
LIZENZ = "GPL-2.0-or-later"


def groesse(bild: Path):
    r = subprocess.run(["magick", "identify", "-format", "%wx%h", str(bild)],
                       capture_output=True, text=True)
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bild", type=Path)
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--ziel", type=Path,
                    default=Path(__file__).resolve().parent.parent
                    / "nt-legacy" / "wallpapers")
    ap.add_argument("--kachel", action="store_true")
    ap.add_argument("--qualitaet", type=int, default=92)
    ap.add_argument("--verlustfrei", action="store_true",
                    help="PNG statt JPEG - nur fuer Bilder mit harten "
                         "Farbkanten, bei denen JPEG Raender saeumt")
    a = ap.parse_args()

    if not a.bild.is_file():
        sys.exit(f"Kein Bild: {a.bild}")

    paket = a.ziel / a.id
    bilder = paket / "contents" / "images"
    bilder.mkdir(parents=True, exist_ok=True)

    g = groesse(a.bild)
    if not g:
        sys.exit("magick konnte die Groesse nicht lesen")

    # Erst raeumen: liegt aus einem frueheren Lauf ein Bild derselben
    # Groesse in anderem Format daneben, hat Plasma zwei Kandidaten fuer
    # dieselbe Aufloesung und nimmt irgendeinen.
    for alt in bilder.glob(f"{g}.*"):
        alt.unlink()

    endung = "png" if a.verlustfrei else "jpg"
    ziel = bilder / f"{g}.{endung}"
    befehl = ["magick", str(a.bild)]
    if not a.verlustfrei:
        # -sampling-factor 1x1: keine Unterabtastung der Farbkanaele.
        # Bei 4:2:0 verlaufen gesaettigte Kanten - und genau die tragen
        # in den gezeichneten Landschaften die Form.
        befehl += ["-quality", str(a.qualitaet), "-sampling-factor", "1x1",
                   "-interlace", "none"]
    befehl.append(str(ziel))
    r = subprocess.run(befehl, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"magick: {r.stderr.strip()[:200]}")

    (paket / "metadata.json").write_text(json.dumps({
        "KPlugin": {
            "Authors": [{"Name": AUTOR}],
            "Id": a.id,
            "License": LIZENZ,
            "Name": a.name + (" (Kachel)" if a.kachel else ""),
        }}, indent=4, ensure_ascii=False) + "\n")

    mb = ziel.stat().st_size / 1048576
    print(f"  wallpapers/{a.id}/  ({g}, {mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
