#!/usr/bin/env python3
"""Creates -symbolic aliases in an icon theme.

For sidebars, toolbars and the system tray, Plasma 6 uses monochrome
icons with the suffix "-symbolic". Retro icon sets almost never have
them. If such a name is missing, Plasma falls back to Breeze
- and then flat grey strokes sit next to 16-colour pixel art. That is
the most visible break in style in a retro theme.

This script creates a "-symbolic" alias for every existing icon,
so that Plasma finds the coloured version instead of the Breeze strokes. The
icons are NOT made monochrome - that is exactly the point:
better a coloured icon in the right style than a grey one in the wrong one.

    ./gen-symbolic-aliases.py ~/.local/share/icons/NTLegacy
    ./gen-symbolic-aliases.py <theme> --probe   # only show, do nothing
"""

import argparse
import os
from collections import Counter
from pathlib import Path

# Contexts in which Plasma expects symbolic icons. In places/ and
# mimes/ Plasma almost always uses the coloured ones - aliases there
# would be needless ballast.
# Deliberately ONLY actions and status.
#
# The first attempt also covered apps, devices, categories and places -
# the result was worse than before: Plasma treats every icon
# with the suffix "-symbolic" as monochrome and tints it in the
# text colour. The yellow Win95 folders turned into single-colour
# silhouettes. The Breeze strokes were gone, but so were the Chicago95
# colours.
#
# In actions and status the tinting is right - the icons there
# are meant to be small and single-coloured anyway (arrows, magnifier, cog).
# Everywhere else the coloured original is better.
CONTEXTS = ["actions", "status"]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path, help="directory of the icon theme")
    ap.add_argument("--probe", action="store_true",
                    help="only report, create nothing")
    args = ap.parse_args()

    if not (args.theme / "index.theme").exists():
        ap.error(f"{args.theme} does not look like an icon theme "
                 "(index.theme missing)")

    created = 0
    skipped = 0
    per_context = Counter()

    for context in CONTEXTS:
        root = args.theme / context
        if not root.is_dir():
            continue

        for file in root.rglob("*"):
            if file.is_dir():
                continue
            if file.suffix.lower() not in (".png", ".svg", ".svgz"):
                continue
            if file.stem.endswith("-symbolic"):
                continue

            target = file.with_name(f"{file.stem}-symbolic{file.suffix}")
            if target.exists() or target.is_symlink():
                skipped += 1
                continue

            if not args.probe:
                # Relative symlink: the theme stays relocatable and
                # can be copied as a whole without the links
                # pointing nowhere.
                target.symlink_to(file.name)
            created += 1
            per_context[context] += 1

    what = "would be created" if args.probe else "created"
    print(f"{created} aliases {what}, {skipped} already present\n")
    for k, n in per_context.most_common():
        print(f"  {k:<16} {n:>5}")

    if not args.probe and created:
        print("\nNote: this lets Plasma see the coloured icons even where")
        print("it would otherwise use Breeze strokes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
