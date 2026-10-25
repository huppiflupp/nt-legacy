#!/usr/bin/env python3
"""Generates an X11 mouse cursor theme from pixel patterns.

NT cursors are pixel art: the white arrow with a black outline, the
I-beam, the hourglass. That is why they are written down here as
character grids rather than vector graphics - that is the more honest
representation and scales up pixel-exactly to any size (nearest
neighbour, so the edges stay hard).

    ' '  transparent
    'X'  outline colour (black)
    '.'  fill colour (white, or the variant's accent colour)
    'o'  shadow colour (for the hourglass fill)

    ./gen-cursor.py -o nt-legacy/cursors/ --name NTLegacy
    ./gen-cursor.py -o nt-legacy/cursors/ --name NTLegacyRot --fill "#c03028"

Needs xcursorgen (package: xcursorgen) and ImageMagick.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# --------------------------------------------------------------------------
# The cursors. Each with a pattern and a hotspot (column, row) in the grid.
# --------------------------------------------------------------------------

CURSORS = {
    "left_ptr": {
        "hotspot": (0, 0),
        "pattern": [
            "X          ",
            "XX         ",
            "X.X        ",
            "X..X       ",
            "X...X      ",
            "X....X     ",
            "X.....X    ",
            "X......X   ",
            "X.......X  ",
            "X........X ",
            "X.....XXXXX",
            "X..X..X    ",
            "X.X X..X   ",
            "XX  X..X   ",
            "X    X..X  ",
            "     X..X  ",
            "      XX   ",
        ],
    },
    "text": {
        "hotspot": (3, 8),
        "pattern": [
            "XX XX",
            " X.X ",
            " X.X ",
            " X.X ",
            " X.X ",
            " X.X ",
            " X.X ",
            " X.X ",
            " X.X ",
            " X.X ",
            " X.X ",
            " X.X ",
            " X.X ",
            " X.X ",
            "XX XX",
        ],
    },
    "wait": {
        # The hourglass - the hallmark of Windows before XP
        "hotspot": (6, 8),
        "pattern": [
            "XXXXXXXXXXXXX",
            "X...........X",
            "X.ooooooooo.X",
            " X.ooooooo.X ",
            "  X.ooooo.X  ",
            "   X.ooo.X   ",
            "    X.o.X    ",
            "     X.X     ",
            "    X.o.X    ",
            "   X.ooo.X   ",
            "  X.o...o.X  ",
            " X.o.....o.X ",
            "X.ooooooooo.X",
            "X...........X",
            "XXXXXXXXXXXXX",
        ],
    },
    "crosshair": {
        "hotspot": (7, 7),
        "pattern": [
            "      X      ",
            "      X      ",
            "      X      ",
            "      X      ",
            "      X      ",
            "      X      ",
            "XXXXXX XXXXXX",
            "      X      ",
            "      X      ",
            "      X      ",
            "      X      ",
            "      X      ",
            "      X      ",
        ],
    },
    "fleur": {
        "hotspot": (10, 10),
        "pattern": [
            "         X         ",
            "        X.X        ",
            "       X...X       ",
            "      XXX.XXX      ",
            "        X.X        ",
            "        X.X        ",
            "        X.X        ",
            "   X    X.X    X   ",
            "  X.X   X.X   X.X  ",
            " X...XXXX.XXXX...X ",
            "XXXXX.........XXXXX",
            " X...XXXX.XXXX...X ",
            "  X.X   X.X   X.X  ",
            "   X    X.X    X   ",
            "        X.X        ",
            "        X.X        ",
            "        X.X        ",
            "      XXX.XXX      ",
            "       X...X       ",
            "        X.X        ",
            "         X         ",
        ],
    },
    "sb_v_double_arrow": {
        "hotspot": (5, 10),
        "pattern": [
            "     X     ",
            "    X.X    ",
            "   X...X   ",
            "  XXX.XXX  ",
            "    X.X    ",
            "    X.X    ",
            "    X.X    ",
            "    X.X    ",
            "    X.X    ",
            "    X.X    ",
            "    X.X    ",
            "  XXX.XXX  ",
            "   X...X   ",
            "    X.X    ",
            "     X     ",
        ],
    },
    "sb_h_double_arrow": {
        "hotspot": (10, 5),
        "pattern": [
            "     X     X     ",
            "    X.X   X.X    ",
            "   X..XXXXX..X   ",
            "  X...........X  ",
            " X.............X ",
            "XXXXXXXXXXXXXXXXX",
            " X.............X ",
            "  X...........X  ",
            "   X..XXXXX..X   ",
            "    X.X   X.X    ",
            "     X     X     ",
        ],
    },
    "question_arrow": {
        "hotspot": (0, 0),
        "pattern": [
            "X          ",
            "XX    XXX  ",
            "X.X  X...X ",
            "X..X X.X.X ",
            "X...X   X. ",
            "X....X XX  ",
            "X.....XX   ",
            "X......X   ",
            "X.......X  ",
            "X....XXX   ",
            "X..X..X X  ",
            "X.X X..X   ",
            "XX  X..X   ",
            "     X..X  ",
            "      XX   ",
        ],
    },
    "hand2": {
        # The link cursor. After the arrow the most frequently
        # requested one of all - every hyperlink in the browser.
        "hotspot": (5, 0),
        "pattern": [
            "    XX     ",
            "   X..X    ",
            "   X..X    ",
            "   X..X    ",
            "   X..X    ",
            "   X..XXX  ",
            "   X..X..XX",
            "   X..X..X.X",
            "XX X..X..X.X",
            "X..XX..X..XX",
            "X...X.....XX",
            " X........X ",
            "  X.......X ",
            "  X.......X ",
            "   X......X ",
            "   X.....X  ",
            "    X....X  ",
            "    XXXXXX  ",
        ],
    },
    "top_left_corner": {
        # Diagonal double arrow from top-left to bottom-right.
        # The first attempt was a corner with a dot - that is the shape
        # X11 calls "ul_angle", not the resize cursor.
        "hotspot": (7, 7),
        "pattern": [
            "XXXXXXXX       ",
            "X......X       ",
            "X.....X        ",
            "X....X         ",
            "X...X X        ",
            "X..X X.X       ",
            "X.X   X.X      ",
            "XX     X.X     ",
            "        X.X   X",
            "         X.X X.X",
            "          X.XX.X",
            "           X...X",
            "          X....X",
            "         X.....X",
            "        XXXXXXXX",
        ],
    },
    "top_right_corner": {
        # The same shape, mirrored: bottom-left to top-right.
        "hotspot": (7, 7),
        "pattern": [
            "       XXXXXXXX",
            "       X......X",
            "        X.....X",
            "         X....X",
            "        X X...X",
            "       X.X X..X",
            "      X.X   X.X",
            "     X.X     XX",
            "X   X.X        ",
            "X.X X.X        ",
            "X.XX.X         ",
            "X...X          ",
            "X....X         ",
            "X.....X        ",
            "XXXXXXXX       ",
        ],
    },
    "crossed_circle": {
        "hotspot": (8, 8),
        "pattern": [
            "    XXXXXXX    ",
            "  XX.......XX  ",
            " X...XXXXX...X ",
            " X..XX...XX..X ",
            "X..XX.....XX..X",
            "X.XX.......XX.X",
            "X.X.........X.X",
            "X.X.........X.X",
            "X.X.........X.X",
            "X.XX.......XX.X",
            "X..XX.....XX..X",
            " X..XX...XX..X ",
            " X...XXXXX...X ",
            "  XX.......XX  ",
            "    XXXXXXX    ",
        ],
    },
}

# Names that point to one of the above. Without these aliases many
# programs fall back to the system's default cursor - and then, in the
# middle of your work, you have Breeze under your finger again.
ALIASES = {
    "left_ptr": ["default", "arrow", "top_left_arrow", "left_arrow"],
    "text": ["xterm", "ibeam"],
    "wait": ["watch"],
    "left_ptr_watch": [],          # own entry below
    "crosshair": ["cross", "tcross", "cross_reverse"],
    "fleur": ["move", "all-scroll", "size_all", "grabbing", "closedhand",
              "dnd-move", "dnd-none"],
    "sb_v_double_arrow": ["size_ver", "v_double_arrow", "n-resize", "s-resize",
                          "ns-resize", "row-resize", "top_side", "bottom_side",
                          "double_arrow", "based_arrow_down", "based_arrow_up"],
    "sb_h_double_arrow": ["size_hor", "h_double_arrow", "e-resize", "w-resize",
                          "ew-resize", "col-resize", "left_side", "right_side"],
    "question_arrow": ["help", "whats_this", "dnd-ask", "left_ptr_help"],
    "crossed_circle": ["not-allowed", "forbidden", "no-drop", "circle",
                       "dnd-no-drop", "pirate",
                       "03b6e0fcb3499374a867c041f52298f0"],
    "hand2": ["pointer", "hand1", "pointing_hand", "hand", "grab", "openhand",
              "dnd-copy", "copy", "alias", "link", "context-menu", "cell",
              # Legacy hashes from the X11 cursor font. GTK programs
              # and Firefox request cursors under these names - without them
              # you see a Breeze cursor in the middle of the NT theme.
              "9d800788f1b08800ae810202380a0822",
              "e29285e634086352946a0e7090d73106",
              "5c6cd98b3f3ebcb1f9c7f1c204630408",
              "b66166c04f8c3109214a4fbd64a50fc8",
              "a2a266d0498c3104214a47bd64ab0fc8",
              "1081e37283d90000800003c07f3ef6bf",
              "6407b0e94181790501fd1e167b474872"],
    "top_left_corner": ["nw-resize", "size_fdiag", "size-fdiag",
                        "bottom_right_corner", "se-resize", "nwse-resize",
                        "c7088f0f3e6c8088236ef8e1e3e70000",
                        "38c5dff7c7b8962045400281044508d2"],
    "top_right_corner": ["ne-resize", "size_bdiag", "size-bdiag",
                         "bottom_left_corner", "sw-resize", "nesw-resize",
                         "fcf21c00b30f7e3f83fe0dfd12e71cff",
                         "fd_double_arrow", "bd_double_arrow"],
    "wait": ["watch", "00000000000000020006000e7e9ffc3f",
             "08e8e1c95fe2fc01f976f1e063a24ccd"],
    "text": ["vertical-text", "ibeam"],
    "fleur": ["closedhand", "grabbing", "dnd-move",
              "4498f0e0c1937ffe01fd06f973665830",
              "9081237383d90e509aa00f00170e968f"],
}

SIZES = [24, 32, 48, 64]


def render(pattern, size, colours, target: Path):
    """Draws a pattern as a PNG at the requested edge length."""
    h = len(pattern)
    w = max(len(z) for z in pattern)
    # Choose the pixel size so the pattern fits into the target size
    f = max(1, size // max(w, h))
    from PIL import Image
    bi = Image.new("RGBA", (w * f, h * f), (0, 0, 0, 0))
    px = bi.load()
    for y, row in enumerate(pattern):
        for x, c in enumerate(row):
            if c == " ":
                continue
            colour = colours.get(c)
            if not colour:
                continue
            for dy in range(f):
                for dx in range(f):
                    px[x * f + dx, y * f + dy] = colour
    # Place onto the exact target size without scaling - that keeps the
    # edges hard. The rest is transparent.
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(bi, (0, 0))
    out.save(target)
    return f


def hexrgba(h, alpha=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def main():
    ap = argparse.ArgumentParser(description="Generates a mouse cursor theme.")
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--name", required=True, help="directory and theme name")
    ap.add_argument("--display-name", help="display name (otherwise same as --name)")
    ap.add_argument("--display-name-de", help="German display name (Name[de]), "
                    "written only if it differs from the display name")
    ap.add_argument("--fill", default="#ffffff", help="colour of the surface")
    ap.add_argument("--outline", default="#000000", help="colour of the outline")
    ap.add_argument("--shadow", default="#808080", help="fill of the hourglass")
    args = ap.parse_args()

    if not shutil.which("xcursorgen"):
        print("ERROR: xcursorgen is missing (package: xcursorgen)", file=sys.stderr)
        return 1
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("ERROR: python3-pillow is missing", file=sys.stderr)
        return 1

    colours = {
        "X": hexrgba(args.outline),
        ".": hexrgba(args.fill),
        "o": hexrgba(args.shadow),
    }

    target = args.output / args.name
    (target / "cursors").mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for name, spec in CURSORS.items():
            pattern = spec["pattern"]
            h = len(pattern)
            w = max(len(z) for z in pattern)
            rows = []
            for size in SIZES:
                png = tmp / f"{name}-{size}.png"
                f = render(pattern, size, colours, png)
                hx, hy = spec["hotspot"]
                # xcursorgen expects: size xhot yhot file
                rows.append(f"{size} {hx * f} {hy * f} {png}")
            cfg = tmp / f"{name}.cursor"
            cfg.write_text("\n".join(rows) + "\n")
            r = subprocess.run(["xcursorgen", str(cfg), str(target / "cursors" / name)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(f"ERROR for {name}: {r.stderr}", file=sys.stderr)
                return 1

        # "Working in background" is the arrow - an animation of its own
        # would be decoration that NT did not have either.
        source = target / "cursors" / "left_ptr"
        for extra in ["left_ptr_watch", "progress", "half-busy"]:
            z = target / "cursors" / extra
            if not z.exists():
                z.symlink_to("wait" if extra != "left_ptr_watch" else "left_ptr")

    # Aliases as relative symlinks
    n = 0
    for original, names in ALIASES.items():
        if not (target / "cursors" / original).exists():
            continue
        for alias in names:
            z = target / "cursors" / alias
            if not z.exists() and not z.is_symlink():
                z.symlink_to(original)
                n += 1

    display_name = args.display_name or args.name
    name_de = (f"Name[de]={args.display_name_de}\n"
               if args.display_name_de and args.display_name_de != display_name else "")
    (target / "index.theme").write_text(
        f"[Icon Theme]\nName={display_name}\n{name_de}"
        f"Comment=Mouse cursors in the style of Windows NT 4.0\n"
        f"Comment[de]=Mauszeiger im Stil von Windows NT 4.0\n"
        f"Inherits=breeze_cursors\n")
    # No cursor.theme: that file points from an ICON theme to a cursor
    # theme. Here it would sit in the cursor theme itself and would
    # inherit from itself. breeze_cursors does not have it either.

    print(f"  {target.name}/  ({len(CURSORS)} cursors, {n} aliases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
