#!/usr/bin/env python3
"""Turns an image into a Plasma wallpaper package.

    ./make-wallpaper.py image.png --id ntlegacy-granit \\
        --name "NT Legacy - Granite" [--tile] [--quality 95]

A wallpaper package is a directory with metadata.json and
contents/images/<width>x<height>.<ext>. Plasma needs nothing more.

Why this is not in build.py: build.py generates everything from
colour values, deterministically and in seconds. These images come from
an image model and need a GPU and a few minutes. They are
generated once and then live in the repo - a rebuild of the theme should
not have to touch them every time.

The output is JPEG, not PNG. The raw images total 378 MB;
as JPEG they are 35. Nobody in the store downloads a theme archive
that is several hundred megabytes in size.

  Landscapes     q92, 3840x2160  ~0.6 MB   drawn style, little noise
  Tiles          q95, 2048x2048  ~3 MB     noise textures, need more
  Large images   q92, 4096x4096  ~4 MB

About the tiles: JPEG works in blocks of 8x8 pixels. Because 2048 is
divisible by 8, the blocks line up the same at both tile edges - the
seam stays where it was. With an odd edge length that would
not be the case, and you would have to use PNG.

--tile writes the hint into the name. Plasma does not store the
fill mode in the package but in the user's settings; the
hint in the name is all the package can contribute.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

AUTHOR = "huppiflupp"
LICENSE = "GPL-2.0-or-later"


def size(image: Path):
    r = subprocess.run(["magick", "identify", "-format", "%wx%h", str(image)],
                       capture_output=True, text=True)
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", type=Path)
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--dest", type=Path,
                    default=Path(__file__).resolve().parent.parent
                    / "nt-legacy" / "wallpapers")
    ap.add_argument("--tile", action="store_true")
    ap.add_argument("--quality", type=int, default=92)
    ap.add_argument("--lossless", action="store_true",
                    help="PNG instead of JPEG - only for images with hard "
                         "colour edges where JPEG fringes the borders")
    a = ap.parse_args()

    if not a.image.is_file():
        sys.exit(f"Not an image: {a.image}")

    package = a.dest / a.id
    images = package / "contents" / "images"
    images.mkdir(parents=True, exist_ok=True)

    g = size(a.image)
    if not g:
        sys.exit("magick could not read the size")

    # Clean up first: if an image of the same size in another format is
    # left over from an earlier run, Plasma has two candidates for
    # the same resolution and picks either one.
    for old in images.glob(f"{g}.*"):
        old.unlink()

    ext = "png" if a.lossless else "jpg"
    dest = images / f"{g}.{ext}"
    cmd = ["magick", str(a.image)]
    if not a.lossless:
        # -sampling-factor 1x1: no chroma subsampling.
        # With 4:2:0 saturated edges bleed - and those are exactly what
        # carries the shapes in the drawn landscapes.
        cmd += ["-quality", str(a.quality), "-sampling-factor", "1x1",
                "-interlace", "none"]
    cmd.append(str(dest))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"magick: {r.stderr.strip()[:200]}")

    (package / "metadata.json").write_text(json.dumps({
        "KPlugin": {
            "Authors": [{"Name": AUTHOR}],
            "Id": a.id,
            "License": LICENSE,
            "Name": a.name + (" (Tile)" if a.tile else ""),
        }}, indent=4, ensure_ascii=False) + "\n")

    mb = dest.stat().st_size / 1048576
    print(f"  wallpapers/{a.id}/  ({g}, {mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
