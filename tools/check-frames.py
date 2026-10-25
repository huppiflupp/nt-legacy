#!/usr/bin/env python3
"""Checks whether the window frame is closed at every border size.

Background: if the user picks a larger border size in System Settings,
KWin reports a wider border than the left/right/bottom elements of
decoration.svg draw. The difference falls into the center element. If
that is transparent, the desktop shows through there - a gap between
the frame and the window content.

The script takes a screenshot path and the desktop colour and reports
whether that colour still appears inside the window rectangle.

    ./check-frames.py image.png --row 400
"""

import argparse
import subprocess
from pathlib import Path


def read_row(image: Path, y: int, width: int):
    """Reads one image row as a list of (r,g,b)."""
    raw = subprocess.run(
        ["magick", str(image), "-crop", f"{width}x1+0+{y}", "+repage",
         "-depth", "8", "txt:-"],
        capture_output=True, text=True, check=True).stdout
    points = []
    for z in raw.splitlines()[1:]:
        # Format: "0,0: (192,192,192)  #C0C0C0  srgb(192,192,192)"
        part = z.split("(", 1)
        if len(part) < 2:
            continue
        values = part[1].split(")", 1)[0].split(",")
        points.append(tuple(int(w.strip()) for w in values[:3]))
    return points


def runs(points, tolerance=6):
    """Groups equal colours into runs: [(colour, start, end)]."""
    if not points:
        return []
    out = []
    start, current = 0, points[0]
    for i, p in enumerate(points[1:], 1):
        if max(abs(a - b) for a, b in zip(p, current)) > tolerance:
            out.append((current, start, i - 1))
            start, current = i, p
    out.append((current, start, len(points) - 1))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", type=Path)
    ap.add_argument("--row", type=int, required=True,
                    help="image row through the middle of the window")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--tolerance", type=int, default=6)
    args = ap.parse_args()

    points = read_row(args.image, args.row, args.width)
    if not points:
        print("Row not readable"); return 2
    rs = runs(points, args.tolerance)

    # The desktop colour is that of the first run - left of the window is
    # always desktop. More robust than a hard-coded colour, because
    # every variant has a different background.
    desktop = rs[0][0]

    # Window: from the end of the first to the start of the last
    # desktop run.
    desktop_runs = [l for l in rs
                    if max(abs(a - b) for a, b in zip(l[0], desktop)) <= args.tolerance]
    if len(desktop_runs) < 2:
        print("No window detected on this row"); return 2
    left, right = desktop_runs[0][2], desktop_runs[-1][1]

    # Only the runs BETWEEN the first and the last are gaps.
    # The first lies left of the window, the last right of it - both
    # are plain desktop and not errors.
    gaps = desktop_runs[1:-1]
    gap_starts = {l[1] for l in gaps}

    print(f"Desktop colour {desktop}, window from x={left+1} to x={right-1}")
    print("Colour sequence:")
    for colour, start, end in rs:
        if end < left or start > right:
            continue
        n = end - start + 1
        mark = "   <-- GAP: desktop shows through" if start in gap_starts else ""
        print(f"  x={start:4d}..{end:<4d} {n:3d}px  rgb{colour}{mark}")
    print()
    if gaps:
        print(f"ERROR: {len(gaps)} gap(s) in the frame.")
        return 1
    print("Frame closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
