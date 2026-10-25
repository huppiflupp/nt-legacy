#!/usr/bin/env python3
"""Turns the image material in wallpaper/ into wallpaper packages.

    ./make-backgrounds.py            # all
    ./make-backgrounds.py --only tiles
    ./make-backgrounds.py --check    # only show what would be created

The raw images live in wallpaper/ and do not belong in the repository:
378 MB of PNG from an image model, generated with kachle.sh. What goes
into the repository are the packages under nt-legacy/wallpapers/ - the same
images as JPEG, 69 MB in total. 8 MB of that are landscapes; the
remaining 61 MB are tiles and large images, and those go into a
separate archive, not into the full package.

This script is the way from there to here. It does not run on every
build; build.py does not touch the packages created here.

Three kinds, three uses:

  Landscapes    One day and one night version per palette. They go into
                the package the respective variant already points to
                (contents/defaults, [Wallpaper] Image=) - whoever applies
                the theme gets the matching background right away.
  Tiles         Seamless, for the "Tiled" fill mode. Variant-neutral,
                hence their own packages.
  Large images  4096x4096, full-screen.
"""

import argparse
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
SOURCE = LAB / "wallpaper"
MAKER = LAB / "tools" / "make-wallpaper.py"

# The landscape per variant. The key is the file name in
# wallpaper/landschaften/, the value the package ID - and that must match
# ids()["wallpaper"] in build.py, otherwise the Global Theme points
# to a package that does not exist.
LANDSCAPES = {
    "teal":        ("ntlegacy",             "NT Legacy"),
    "teal-nacht":  ("ntlegacy-teal-nacht",  "NT Legacy Night"),
    "lilac":       ("ntlegacy-lilac",       "NT Legacy Lilac"),
    "lilac-nacht": ("ntlegacy-lilac-nacht", "NT Legacy Lilac Night"),
    "desert":      ("ntlegacy-desert",      "NT Legacy Desert"),
    "desert-nacht": ("ntlegacy-desert-nacht", "NT Legacy Desert Night"),
    "win98":       ("ntlegacy-win98",       "NT Legacy 98"),
    "win98-nacht": ("ntlegacy-win98-nacht", "NT Legacy 98 Night"),
    "win2k":       ("ntlegacy-win2k",       "NT Legacy 2000"),
    "win2k-nacht": ("ntlegacy-win2k-nacht", "NT Legacy 2000 Night"),
}

TILES = {
    "granit":             "Granite",
    "waschbeton":         "Exposed aggregate",
    "textiltapete":       "Textile wallpaper",
    "asphalt":            "Asphalt",
    "marmor-fein":        "Marble, fine",
    "marmor-blau":        "Marble, blue",
    "marmor-rot":         "Marble, red",
    "marmor-dunkelgruen": "Marble, dark green",
    "esd-blau":           "ESD mat, blue",
    "esd-beige":          "ESD mat, beige",
    "keltisch-knoten":    "Celtic knot",
    "keltisch-kreuz":     "Celtic cross",
}

LARGE_IMAGES = {
    "kies":    "Gravel",
    "marmor":  "Marble",
    "asphalt": "Asphalt, large",
    "asche":   "Ash",
}


def make(image: Path, pkg_id: str, name: str, quality: int,
         tile: bool, check: bool):
    if not image.is_file():
        print(f"  missing: {image.relative_to(LAB)}")
        return False
    if check:
        mb = image.stat().st_size / 1048576
        print(f"  {pkg_id:28s} <- {image.name:24s} ({mb:5.1f} MB raw)")
        return True
    cmd = [sys.executable, str(MAKER), str(image), "--id", pkg_id,
           "--name", name, "--quality", str(quality)]
    if tile:
        cmd.append("--tile")
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.rstrip() if r.returncode == 0
          else f"  ERROR {pkg_id}: {r.stderr.strip()[:120]}")
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=("landscapes", "tiles", "images"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if not SOURCE.is_dir():
        sys.exit(f"No image material: {SOURCE} is missing. The raw images are "
                 f"not in the repository - see wallpaper/README or "
                 f"kachle.sh.")

    n = 0
    if a.only in (None, "landscapes"):
        print("Landscapes (per variant, q92):")
        for file, (pkg_id, name) in LANDSCAPES.items():
            n += make(SOURCE / "landschaften" / f"{file}.png",
                      pkg_id, name, 92, False, a.check)

    if a.only in (None, "tiles"):
        # q95 instead of q92: noise textures are the hardest case for
        # JPEG, and a tile is shown twenty times side by side -
        # an artefact stands out twenty times there.
        print("\nTiles (seamless, q95):")
        for file, name in TILES.items():
            n += make(SOURCE / "kacheln" / f"{file}.png",
                      f"ntlegacy-kachel-{file}", f"NT Legacy - {name}",
                      95, True, a.check)

    if a.only in (None, "images"):
        print("\nLarge images (full-screen, q92):")
        for file, name in LARGE_IMAGES.items():
            # Prefix "gross-": make-package.sh excludes tiles and
            # large images from the full archive via exactly these two
            # patterns. Without the prefix the large image would be called
            # ntlegacy-asphalt and the tile ntlegacy-kachel-asphalt -
            # the first could not be told apart from a
            # variant.
            n += make(SOURCE / "bilder" / f"{file}.png",
                      f"ntlegacy-gross-{file}", f"NT Legacy - {name}",
                      92, False, a.check)

    dest = LAB / "nt-legacy" / "wallpapers"
    if not a.check and dest.is_dir():
        total = sum(p.stat().st_size for p in dest.rglob("*") if p.is_file())
        print(f"\n{n} packages, {total / 1048576:.0f} MB in "
              f"{dest.relative_to(LAB)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
