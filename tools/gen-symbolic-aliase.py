#!/usr/bin/env python3
"""Legt -symbolic-Aliase in einem Icon-Theme an.

Plasma 6 zieht fuer Seitenleisten, Werkzeugleisten und den Systembereich
monochrome Icons mit der Endung "-symbolic". Retro-Icon-Saetze haben die
so gut wie nie. Fehlt ein solcher Name, faellt Plasma auf Breeze zurueck
- und dann stehen flache graue Striche neben 16-Farben-Pixelart. Das ist
der sichtbarste Stilbruch in einem Retro-Theme.

Dieses Skript legt fuer jedes vorhandene Icon einen "-symbolic"-Alias an,
sodass Plasma die farbige Fassung findet statt der Breeze-Striche. Die
Icons werden dabei NICHT monochrom gemacht - genau das ist der Zweck:
lieber ein farbiges Icon im richtigen Stil als ein graues im falschen.

    ./gen-symbolic-aliase.py ~/.local/share/icons/NTLegacy
    ./gen-symbolic-aliase.py <theme> --probe   # nur zeigen, nichts tun
"""

import argparse
import os
from collections import Counter
from pathlib import Path

# Kontexte, in denen Plasma symbolische Icons erwartet. In places/ und
# mimes/ verwendet Plasma fast immer die farbigen - dort waeren Aliase
# unnoetiger Ballast.
# Bewusst NUR actions und status.
#
# Erster Versuch umfasste auch apps, devices, categories und places -
# das Ergebnis war schlechter als vorher: Plasma behandelt jedes Icon
# mit der Endung "-symbolic" als monochrom und faerbt es in der
# Textfarbe ein. Aus den gelben Win95-Ordnern wurden einfarbige
# Silhouetten. Die Breeze-Striche waren weg, die Chicago95-Farben aber
# auch.
#
# In actions und status ist das Einfaerben richtig - dort sind die
# Icons ohnehin klein und einfarbig gedacht (Pfeile, Lupe, Zahnrad).
# Ueberall sonst ist das farbige Original besser.
KONTEXTE = ["actions", "status"]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path, help="Verzeichnis des Icon-Themes")
    ap.add_argument("--probe", action="store_true",
                    help="nur berichten, nichts anlegen")
    args = ap.parse_args()

    if not (args.theme / "index.theme").exists():
        ap.error(f"{args.theme} sieht nicht nach einem Icon-Theme aus "
                 "(index.theme fehlt)")

    angelegt = 0
    uebersprungen = 0
    je_kontext = Counter()

    for kontext in KONTEXTE:
        wurzel = args.theme / kontext
        if not wurzel.is_dir():
            continue

        for datei in wurzel.rglob("*"):
            if datei.is_dir():
                continue
            if datei.suffix.lower() not in (".png", ".svg", ".svgz"):
                continue
            if datei.stem.endswith("-symbolic"):
                continue

            ziel = datei.with_name(f"{datei.stem}-symbolic{datei.suffix}")
            if ziel.exists() or ziel.is_symlink():
                uebersprungen += 1
                continue

            if not args.probe:
                # Relativer Symlink: das Theme bleibt verschiebbar und
                # laesst sich als Ganzes kopieren, ohne dass die Links
                # ins Leere zeigen.
                ziel.symlink_to(datei.name)
            angelegt += 1
            je_kontext[kontext] += 1

    was = "waeren anzulegen" if args.probe else "angelegt"
    print(f"{angelegt} Aliase {was}, {uebersprungen} schon vorhanden\n")
    for k, n in je_kontext.most_common():
        print(f"  {k:<16} {n:>5}")

    if not args.probe and angelegt:
        print("\nHinweis: Damit sieht Plasma die farbigen Icons auch dort,")
        print("wo es sonst Breeze-Striche einsetzen wuerde.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
