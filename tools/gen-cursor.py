#!/usr/bin/env python3
"""Erzeugt ein X11-Mauszeiger-Thema aus Pixelmustern.

NT-Zeiger sind Pixel-Art: der weisse Pfeil mit schwarzem Rand, der
I-Balken, die Sanduhr. Deshalb sind sie hier als Zeichenraster notiert
statt als Vektorgrafik - das ist die ehrlichere Darstellung und laesst
sich pixelgenau in jede Groesse hochskalieren (Nearest Neighbor, damit
die Kanten hart bleiben).

    ' '  transparent
    'X'  Randfarbe (schwarz)
    '.'  Fuellfarbe (weiss, oder die Akzentfarbe der Variante)
    'o'  Schattenfarbe (fuer Sanduhr-Fuellung)

    ./gen-cursor.py -o nt-legacy/cursors/ --name NTLegacy
    ./gen-cursor.py -o nt-legacy/cursors/ --name NTLegacyRot --fuellung "#c03028"

Braucht xcursorgen (Paket: xcursorgen) und ImageMagick.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# --------------------------------------------------------------------------
# Die Zeiger. Jeder mit Muster und Hotspot (Spalte, Zeile) im Raster.
# --------------------------------------------------------------------------

ZEIGER = {
    "left_ptr": {
        "hotspot": (0, 0),
        "muster": [
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
        "muster": [
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
        # Die Sanduhr - das Wahrzeichen von Windows vor XP
        "hotspot": (6, 8),
        "muster": [
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
        "muster": [
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
        "muster": [
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
        "muster": [
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
        "muster": [
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
        "muster": [
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
        # Der Link-Zeiger. Nach dem Pfeil der am haeufigsten
        # angeforderte ueberhaupt - jeder Hyperlink im Browser.
        "hotspot": (5, 0),
        "muster": [
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
        # Diagonaler Doppelpfeil von oben-links nach unten-rechts.
        # Erster Versuch war eine Ecke mit Punkt - das ist die Form,
        # die X11 "ul_angle" nennt, nicht der Groessenaenderungszeiger.
        "hotspot": (7, 7),
        "muster": [
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
        # Dieselbe Form, gespiegelt: unten-links nach oben-rechts.
        "hotspot": (7, 7),
        "muster": [
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
        "muster": [
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

# Namen, die auf einen der obigen zeigen. Ohne diese Aliase fallen viele
# Programme auf den Standardzeiger des Systems zurueck - und dann hat man
# mitten in der Arbeit wieder Breeze unter dem Finger.
ALIASE = {
    "left_ptr": ["default", "arrow", "top_left_arrow", "left_arrow"],
    "text": ["xterm", "ibeam"],
    "wait": ["watch"],
    "left_ptr_watch": [],          # eigener Eintrag unten
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
              # Legacy-Hashes aus der X11-Cursor-Schriftart. GTK-Programme
              # und Firefox fordern Zeiger unter diesen Namen an - ohne sie
              # sieht man mitten im NT-Theme einen Breeze-Zeiger.
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

GROESSEN = [24, 32, 48, 64]


def bild(muster, gr, farben, ziel: Path):
    """Zeichnet ein Muster als PNG in der gewuenschten Kantenlaenge."""
    h = len(muster)
    w = max(len(z) for z in muster)
    # Pixelgroesse so waehlen, dass das Muster in die Zielgroesse passt
    f = max(1, gr // max(w, h))
    from PIL import Image
    bi = Image.new("RGBA", (w * f, h * f), (0, 0, 0, 0))
    px = bi.load()
    for y, zeile in enumerate(muster):
        for x, c in enumerate(zeile):
            if c == " ":
                continue
            farbe = farben.get(c)
            if not farbe:
                continue
            for dy in range(f):
                for dx in range(f):
                    px[x * f + dx, y * f + dy] = farbe
    # Auf exakte Zielgroesse legen, ohne zu skalieren - so bleiben die
    # Kanten hart. Der Rest ist transparent.
    aus = Image.new("RGBA", (gr, gr), (0, 0, 0, 0))
    aus.paste(bi, (0, 0))
    aus.save(ziel)
    return f


def hexrgba(h, alpha=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def main():
    ap = argparse.ArgumentParser(description="Erzeugt ein Mauszeiger-Thema.")
    ap.add_argument("-o", "--ausgabe", type=Path, required=True)
    ap.add_argument("--name", required=True, help="Verzeichnis- und Themename")
    ap.add_argument("--anzeige", help="Anzeigename (sonst wie --name)")
    ap.add_argument("--fuellung", default="#ffffff", help="Farbe der Flaeche")
    ap.add_argument("--rand", default="#000000", help="Farbe der Kontur")
    ap.add_argument("--schatten", default="#808080", help="Fuellung der Sanduhr")
    args = ap.parse_args()

    if not shutil.which("xcursorgen"):
        print("FEHLER: xcursorgen fehlt (Paket: xcursorgen)", file=sys.stderr)
        return 1
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("FEHLER: python3-pillow fehlt", file=sys.stderr)
        return 1

    farben = {
        "X": hexrgba(args.rand),
        ".": hexrgba(args.fuellung),
        "o": hexrgba(args.schatten),
    }

    ziel = args.ausgabe / args.name
    (ziel / "cursors").mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for name, spec in ZEIGER.items():
            muster = spec["muster"]
            h = len(muster)
            w = max(len(z) for z in muster)
            zeilen = []
            for gr in GROESSEN:
                png = tmp / f"{name}-{gr}.png"
                f = bild(muster, gr, farben, png)
                hx, hy = spec["hotspot"]
                # xcursorgen erwartet: groesse xhot yhot datei
                zeilen.append(f"{gr} {hx * f} {hy * f} {png}")
            cfg = tmp / f"{name}.cursor"
            cfg.write_text("\n".join(zeilen) + "\n")
            r = subprocess.run(["xcursorgen", str(cfg), str(ziel / "cursors" / name)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(f"FEHLER bei {name}: {r.stderr}", file=sys.stderr)
                return 1

        # "Arbeitet im Hintergrund" ist der Pfeil - eine eigene Animation
        # waere Zierrat, den NT auch nicht hatte.
        quelle = ziel / "cursors" / "left_ptr"
        for extra in ["left_ptr_watch", "progress", "half-busy"]:
            z = ziel / "cursors" / extra
            if not z.exists():
                z.symlink_to("wait" if extra != "left_ptr_watch" else "left_ptr")

    # Aliase als relative Symlinks
    n = 0
    for original, namen in ALIASE.items():
        if not (ziel / "cursors" / original).exists():
            continue
        for alias in namen:
            z = ziel / "cursors" / alias
            if not z.exists() and not z.is_symlink():
                z.symlink_to(original)
                n += 1

    anzeige = args.anzeige or args.name
    (ziel / "index.theme").write_text(
        f"[Icon Theme]\nName={anzeige}\nComment=Mauszeiger im Stil von "
        f"Windows NT 4.0\nInherits=breeze_cursors\n")
    # Kein cursor.theme: die Datei verweist von einem ICON-Theme auf ein
    # Cursor-Theme. Hier laege sie im Cursor-Theme selbst und wuerde von
    # sich selbst erben. breeze_cursors hat sie ebenfalls nicht.

    print(f"  {ziel.name}/  ({len(ZEIGER)} Zeiger, {n} Aliase)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
