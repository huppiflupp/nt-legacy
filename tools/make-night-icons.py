#!/usr/bin/env python3
"""Creates a second copy of the icon set for the night variants.

The images are the same in both sets. Exactly one line differs:
the fallback chain in index.theme.

Why this is needed: our set covers about 150 names. Everything else in
the panel comes from the inherited theme - updates, clipboard,
brightness, network, battery. Breeze draws these icons in #232629. On
the light NT panel that is exactly right; on the dark panel of the
night versions it meant dark grey on dark grey. Measured in the test VM:
icon colour #2C3233 on panel background #151A1B, a contrast of
1.3:1. Half of the system tray was simply invisible.

Why a second theme and not a second Inherits: an icon theme has
exactly one fallback chain; it cannot switch it depending on the colour scheme.
And a night theme with `Inherits=NTLegacyIcons,breeze-dark` does not help -
the lookup walks the chain depth-first, so it goes through
NTLegacyIcons into its own `Inherits=breeze` and finds the light
Breeze before breeze-dark ever gets its turn.

Why copies and not links: `install.sh` copies with `cp -r`, and that
writes through links. That is exactly how an icon in this project was
destroyed once before (see the comment on the links
in gen-icons.py). The set is 184 KB - storing it twice is
cheaper than the debugging.

    ./make-night-icons.py nt-legacy/icons-nt/NTLegacyIcons
    ./make-night-icons.py <source> --dest <dir>   # otherwise <source>Nacht
"""

import argparse
import shutil
import sys
from pathlib import Path

# What gets replaced in index.theme. The light Breeze version is dropped,
# breeze-dark goes in front - breeze stays as the second level,
# because breeze-dark does not know every name.
CHAIN_LIGHT = "Inherits=breeze,hicolor"
CHAIN_DARK = "Inherits=breeze-dark,breeze,hicolor"

NAME_LIGHT = "Name=NT Legacy Icons"
NAME_DARK = "Name=NT Legacy Icons Night"

COMMENT = (
    "Comment=Icons in the style of Windows NT 4.0, fully generated - "
    "version for the dark variants")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path, help="the finished light icon set")
    ap.add_argument("--dest", type=Path, default=None)
    args = ap.parse_args()

    source = args.source
    dest = args.dest or source.with_name(source.name + "Nacht")

    if not (source / "index.theme").is_file():
        sys.exit(f"Not an icon set: {source} (index.theme missing)")
    if dest.resolve() == source.resolve():
        sys.exit("Source and destination are the same directory.")

    # Completely fresh, so that a deleted icon does not live on in the
    # night version.
    if dest.exists():
        shutil.rmtree(dest)
    # symlinks=True: the extra names are links and should stay links
    # - otherwise every alias would become a real copy and the set
    # twice as large.
    shutil.copytree(source, dest, symlinks=True)

    idx = dest / "index.theme"
    text = idx.read_text()
    if CHAIN_LIGHT not in text:
        sys.exit(f"Unexpected index.theme: '{CHAIN_LIGHT}' is not in it. "
                 f"Has gen-icons.py changed?")
    text = text.replace(CHAIN_LIGHT, CHAIN_DARK)
    text = text.replace(NAME_LIGHT, NAME_DARK)
    # Replace the comment, do not append - otherwise there would be two
    # Comment lines and KConfig takes the first.
    lines = [COMMENT if z.startswith("Comment=") else z
             for z in text.splitlines()]
    idx.write_text("\n".join(lines) + "\n")

    files = sum(1 for p in dest.rglob("*") if p.is_file() or p.is_symlink())
    print(f"  {dest.name}/  ({files} files, {CHAIN_DARK})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
