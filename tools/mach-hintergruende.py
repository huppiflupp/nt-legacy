#!/usr/bin/env python3
"""Ueberfuehrt das Bildmaterial aus wallpaper/ in Hintergrundpakete.

    ./mach-hintergruende.py            # alle
    ./mach-hintergruende.py --nur kacheln
    ./mach-hintergruende.py --pruefen  # nur zeigen, was entstuende

Die Rohbilder liegen in wallpaper/ und gehoeren nicht ins Repository:
378 MB PNG aus einem Bildmodell, erzeugt mit kachle.sh. Was ins
Repository geht, sind die Pakete unter nt-legacy/wallpapers/ - dieselben
Bilder als JPEG, zusammen 69 MB. Davon sind 8 MB Landschaften; die
restlichen 61 MB sind Kacheln und Grossbilder, und die stecken in einem
eigenen Archiv, nicht im Gesamtpaket.

Dieses Skript ist der Weg von dort nach hier. Es laeuft nicht bei jedem
Bau mit; build.py fasst die Pakete nicht an, die hier entstehen.

Drei Sorten, drei Verwendungen:

  Landschaften  Je Farbwelt eine Tag- und eine Nachtfassung. Sie gehen in
                das Paket, auf das die jeweilige Variante ohnehin schon
                zeigt (contents/defaults, [Wallpaper] Image=) - wer das
                Design anwendet, hat den passenden Hintergrund sofort.
  Kacheln       Nahtlos, fuer die Fuellart "Gekachelt". Variantenneutral,
                deshalb eigene Pakete.
  Grossbilder   4096x4096, ganzflaechig.
"""

import argparse
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
QUELLE = LAB / "wallpaper"
MACHER = LAB / "tools" / "mach-wallpaper.py"

# Die Landschaft je Variante. Der Schluessel ist der Dateiname in
# wallpaper/landschaften/, der Wert die Paketkennung - und die muss zu
# ids()["wallpaper"] in build.py passen, sonst zeigt das Global Theme
# auf ein Paket, das es nicht gibt.
LANDSCHAFTEN = {
    "teal":        ("ntlegacy",             "NT Legacy"),
    "teal-nacht":  ("ntlegacy-teal-nacht",  "NT Legacy Nacht"),
    "lilac":       ("ntlegacy-lilac",       "NT Legacy Flieder"),
    "lilac-nacht": ("ntlegacy-lilac-nacht", "NT Legacy Flieder Nacht"),
    "desert":      ("ntlegacy-desert",      "NT Legacy Wueste"),
    "desert-nacht": ("ntlegacy-desert-nacht", "NT Legacy Wueste Nacht"),
    "win98":       ("ntlegacy-win98",       "NT Legacy 98"),
    "win98-nacht": ("ntlegacy-win98-nacht", "NT Legacy 98 Nacht"),
    "win2k":       ("ntlegacy-win2k",       "NT Legacy 2000"),
    "win2k-nacht": ("ntlegacy-win2k-nacht", "NT Legacy 2000 Nacht"),
}

KACHELN = {
    "granit":             "Granit",
    "waschbeton":         "Waschbeton",
    "textiltapete":       "Textiltapete",
    "asphalt":            "Asphalt",
    "marmor-fein":        "Marmor, fein",
    "marmor-blau":        "Marmor, blau",
    "marmor-rot":         "Marmor, rot",
    "marmor-dunkelgruen": "Marmor, dunkelgruen",
    "esd-blau":           "ESD-Matte, blau",
    "esd-beige":          "ESD-Matte, beige",
    "keltisch-knoten":    "Keltischer Knoten",
    "keltisch-kreuz":     "Keltisches Kreuz",
}

GROSSBILDER = {
    "kies":    "Kies",
    "marmor":  "Marmor",
    "asphalt": "Asphalt, gross",
    "asche":   "Asche",
}


def mach(bild: Path, kennung: str, name: str, qualitaet: int,
         kachel: bool, pruefen: bool):
    if not bild.is_file():
        print(f"  fehlt: {bild.relative_to(LAB)}")
        return False
    if pruefen:
        mb = bild.stat().st_size / 1048576
        print(f"  {kennung:28s} <- {bild.name:24s} ({mb:5.1f} MB roh)")
        return True
    befehl = [sys.executable, str(MACHER), str(bild), "--id", kennung,
              "--name", name, "--qualitaet", str(qualitaet)]
    if kachel:
        befehl.append("--kachel")
    r = subprocess.run(befehl, capture_output=True, text=True)
    print(r.stdout.rstrip() if r.returncode == 0
          else f"  FEHLER {kennung}: {r.stderr.strip()[:120]}")
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nur", choices=("landschaften", "kacheln", "bilder"))
    ap.add_argument("--pruefen", action="store_true")
    a = ap.parse_args()

    if not QUELLE.is_dir():
        sys.exit(f"Kein Bildmaterial: {QUELLE} fehlt. Die Rohbilder liegen "
                 f"nicht im Repository - siehe wallpaper/README oder "
                 f"kachle.sh.")

    n = 0
    if a.nur in (None, "landschaften"):
        print("Landschaften (je Variante, q92):")
        for datei, (kennung, name) in LANDSCHAFTEN.items():
            n += mach(QUELLE / "landschaften" / f"{datei}.png",
                      kennung, name, 92, False, a.pruefen)

    if a.nur in (None, "kacheln"):
        # q95 statt q92: Rauschtexturen sind der schwerste Fall fuer
        # JPEG, und eine Kachel wird zwanzigmal nebeneinander gezeigt -
        # ein Artefakt faellt dort zwanzigmal auf.
        print("\nKacheln (nahtlos, q95):")
        for datei, name in KACHELN.items():
            n += mach(QUELLE / "kacheln" / f"{datei}.png",
                      f"ntlegacy-kachel-{datei}", f"NT Legacy - {name}",
                      95, True, a.pruefen)

    if a.nur in (None, "bilder"):
        print("\nGrossbilder (ganzflaechig, q92):")
        for datei, name in GROSSBILDER.items():
            # Praefix "gross-": mach-paket.sh nimmt Kacheln und
            # Grossbilder ueber genau diese beiden Muster aus dem
            # Gesamtarchiv heraus. Ohne Praefix hiesse das Grossbild
            # ntlegacy-asphalt und die Kachel ntlegacy-kachel-asphalt -
            # das erste liesse sich nicht von einer Variante
            # unterscheiden.
            n += mach(QUELLE / "bilder" / f"{datei}.png",
                      f"ntlegacy-gross-{datei}", f"NT Legacy - {name}",
                      92, False, a.pruefen)

    ziel = LAB / "nt-legacy" / "wallpapers"
    if not a.pruefen and ziel.is_dir():
        gesamt = sum(p.stat().st_size for p in ziel.rglob("*") if p.is_file())
        print(f"\n{n} Pakete, {gesamt / 1048576:.0f} MB in "
              f"{ziel.relative_to(LAB)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
