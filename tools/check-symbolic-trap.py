#!/usr/bin/env python3
"""Finds icon names that our set captures without serving them.

Why this exists: in 0.2.2 the volume control in the panel showed a
sheet of paper with a musical note. The reason was not that an icon was
missing - the reason was that one too many was there.

An incomplete set is worse than none at all: it overrides the fallback
to Breeze without providing a replacement. Two paths lead there, both
measured in the test VM with kiconfinder6:

  1. The lookup shortens an unknown name at the hyphens:
     go-previous-skip -> go-previous. Usually harmless, because the
     shorter icon means the same thing.

  2. It falls back to the class icon <class>-x-generic:

         audio-volume-high  ->  audio-x-generic
         audio-card         ->  audio-x-generic
         image-rotate-left  ->  image-x-generic

     That is the dangerous case. A sheet of paper with a note is the
     right answer for an MP3 file and the wrong one for a volume
     control - and because the hit comes from our own set, Breeze is
     never asked.

    ./check-symbolic-trap.py nt-legacy/icons-nt/NTLegacyIcons
    ./check-symbolic-trap.py <dir> --all    # also list case 1
"""

import argparse
import sys
from pathlib import Path

BREEZE = Path("/usr/share/icons/breeze")


def names(directory: Path) -> set:
    """All icon names of a theme, without size and extension."""
    return set(with_context(directory))


def with_context(directory: Path) -> dict:
    """Icon name -> context (mimetypes, actions, apps, status, devices).

    The context separates the real hits from the harmless ones. A name
    from mimetypes/ is a file type - that text-css gets our
    text-x-generic is exactly right. A name from actions/ or status/ is
    not a file type: application-exit is the "Quit" menu item, and a
    sheet of paper is simply wrong there.
    """
    # Links count too. An alias is a delivered icon - skipping them
    # reports names as captured that have long been served.
    # That is exactly what happened here once.
    out = {}
    for p in directory.rglob("*"):
        if p.suffix.lower() in (".png", ".svg", ".svgz"):
            # .../<context>/<size>/<name>.png
            parts = p.relative_to(directory).parts
            out[p.stem] = parts[0] if len(parts) > 1 else "?"
    return out


def show(title, hits, limit=6):
    print(f"{title}\n")
    for short in sorted(hits, key=lambda k: -len(hits[k])):
        long = sorted(hits[short])
        rest = f"  (+{len(long) - limit})" if len(long) > limit else ""
        print(f"  {short:<24} captures  {', '.join(long[:limit])}{rest}")
    print()


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path)
    ap.add_argument("--all", action="store_true",
                    help="also list the shortening at hyphens")
    ap.add_argument("--compare", type=Path, default=BREEZE,
                    help=f"fallback theme (default: {BREEZE})")
    args = ap.parse_args()

    if not args.theme.is_dir():
        sys.exit(f"Not a directory: {args.theme}")
    if not args.compare.is_dir():
        sys.exit(f"Fallback theme not found: {args.compare}")

    ours = names(args.theme)
    # Symbolic duplicates do not matter - they point to the same
    # image as the name without the suffix.
    contexts = {n: k for n, k in with_context(args.compare).items()
                if not n.endswith(("-symbolic", "-rtl", "-symbolic-rtl"))}
    foreign = set(contexts)

    # Case 2: the class icon captures its whole class. File types
    # do not count - that is exactly what the class icon is meant for.
    classes = {}
    for n in ours:
        if n.endswith("-x-generic"):
            k = n[:-len("-x-generic")]
            open_ = sorted(f for f in foreign
                           if f.startswith(k + "-")
                           and f not in ours
                           and not f.startswith(k + "-x-")
                           and contexts[f] != "mimetypes")
            if open_:
                classes[n] = open_

    # Case 1: shortening at hyphens.
    short_long = {}
    for short in ours:
        if short.endswith("-x-generic"):
            continue
        open_ = [f for f in foreign
                 if f.startswith(short + "-") and f not in ours]
        if open_:
            short_long[short] = open_

    if classes:
        show(f"{len(classes)} class icons capture names that mean something "
             f"else\n(these names show a wrong "
             f"image in use):", classes)

    if args.all and short_long:
        show(f"{len(short_long)} icons capture longer names "
             f"(usually a sensible generalisation):", short_long)
    elif short_long:
        print(f"Plus {len(short_long)} cases of hyphen shortening - "
              f"list them with --all.\n")

    if not classes:
        print("No class icons capture foreign names.")
        return 0

    print("Either draw the missing names as well or drop the "
          "class icon,\nso that the fallback to Breeze "
          "works again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
