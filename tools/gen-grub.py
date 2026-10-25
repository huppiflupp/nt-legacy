#!/usr/bin/env python3
"""Generates a GRUB theme from an NT Legacy palette.

The boot menu looks like an NT dialog: grey box with a 3D edge,
coloured title bar, selection bar in the accent colour. The same
design language as the splash screen (Splash.qml) and the window
decoration - whoever switches the machine on sees the same design
from the first second.

    ./gen-grub.py --name NTLegacyWin2k --display-name "NT Legacy 2000" \\
                  --palette '{"surface": "#d4d0c8", ...}' -o target/

GRUB draws the menu from a 9-patch: nine PNGs, of which the edges
are stretched and the corners drawn fixed. The title bar lives in
the top border (menu_n.png) - GRUB has no element of its own for it,
but the top border may be as tall as you like.

No full-screen background: 'desktop-color' in theme.txt is enough and
keeps the theme at a few kilobytes. A 1920x1080 PNG would be scaled
wrongly on a 4K screen anyway.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is missing (dnf install python3-pillow)", file=sys.stderr)
    sys.exit(1)

# Box dimensions. 1 px border outside, then the 3D edge, then surface -
# the same values as in gen-plasma-svg.py, so that boot menu and windows
# carry the same frame.
BORDER = 1      # black outer line
BEVEL = 2       # light or dark 3D edge
TITLE = 26      # height of the title bar
CORNER = 8      # edge length of the corner images
MENU_W = 620    # width of the menu box, also for the title image


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ttf(size, bold=False):
    for k in ["/usr/share/fonts/google-noto/NotoSans-Bold.ttf" if bold
              else "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
              "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf" if bold
              else "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"]:
        if Path(k).exists():
            try:
                return ImageFont.truetype(k, size)
            except OSError:
                pass
    return ImageFont.load_default()


class Grub:
    def __init__(self, palette, target, name, display_name):
        self.p = palette
        self.target = target
        self.name = name
        self.display_name = display_name

    def f(self, key, fallback="#000000"):
        return self.p.get(key, fallback)

    # ------------------------------------------------------------------
    def _box(self, prefix, top_height, title):
        """A 9-patch.

        prefix      file name prefix (menu, select)
        top_height  height of the top border
        title       draw the title bar into the top border?
        """
        surface = rgb(self.f("surface"))
        border = rgb(self.f("border"))
        light = rgb(self.f("light"))
        dark = rgb(self.f("dark"))
        head = rgb(self.f("title_active"))

        def image(width, height, draw):
            im = Image.new("RGBA", (width, height), surface + (255,))
            draw(ImageDraw.Draw(im), width, height)
            return im

        r, b = BORDER, BEVEL

        # Top corners: outer line, light edge, then title colour.
        #
        # The top-left corner carries the title text. That is not a
        # cosmetic flaw but the only reliable way:
        # GRUB does not draw a "+ label" above the menu (checked in the
        # test VM with two different fonts, including one that was
        # guaranteed to be loaded). The corners of a 9-patch, on the
        # other hand, GRUB does NOT stretch - what is there stays fixed.
        def corner_top(left):
            def z(d, w, h):
                d.rectangle([0, 0, w - 1, h - 1], fill=head + (255,))
                # Outer border on the respective outer side
                d.line([(0, 0), (w - 1, 0)], fill=border + (255,))
                x = 0 if left else w - 1
                d.line([(x, 0), (x, h - 1)], fill=border + (255,))
                # Light edge inside
                d.line([(r, r), (w - 1, r)], fill=light + (255,))
                xi = r if left else w - 1 - r
                d.line([(xi, r), (xi, h - 1)], fill=light + (255,))
            return image(CORNER, top_height, z)

        def corner_bottom(left):
            def z(d, w, h):
                d.rectangle([0, 0, w - 1, h - 1], fill=surface + (255,))
                d.line([(0, h - 1), (w - 1, h - 1)], fill=border + (255,))
                x = 0 if left else w - 1
                d.line([(x, 0), (x, h - 1)], fill=border + (255,))
                # Shadow edge inside
                d.line([(r, h - 1 - r), (w - 1, h - 1 - r)],
                       fill=dark + (255,))
                xi = r if left else w - 1 - r
                if not left:
                    d.line([(xi, 0), (xi, h - 1 - r)], fill=dark + (255,))
                else:
                    d.line([(xi, 0), (xi, h - 1 - r)], fill=light + (255,))
            return image(CORNER, CORNER, z)

        def edge_top(d, w, h):
            d.rectangle([0, 0, w - 1, h - 1], fill=head + (255,))
            d.line([(0, 0), (w - 1, 0)], fill=border + (255,))
            d.line([(0, r), (w - 1, r)], fill=light + (255,))
            if title:
                d.text((2, (h + BORDER + BEVEL) / 2), self.display_name,
                       font=ttf(15, True),
                       fill=rgb(self.f("selection_text")) + (255,),
                       anchor="lm")

        def edge_bottom(d, w, h):
            d.rectangle([0, 0, w - 1, h - 1], fill=surface + (255,))
            d.line([(0, h - 1), (w - 1, h - 1)], fill=border + (255,))
            d.line([(0, h - 1 - r), (w - 1, h - 1 - r)], fill=dark + (255,))

        def edge_left(d, w, h):
            d.rectangle([0, 0, w - 1, h - 1], fill=surface + (255,))
            d.line([(0, 0), (0, h - 1)], fill=border + (255,))
            d.line([(r, 0), (r, h - 1)], fill=light + (255,))

        def edge_right(d, w, h):
            d.rectangle([0, 0, w - 1, h - 1], fill=surface + (255,))
            d.line([(w - 1, 0), (w - 1, h - 1)], fill=border + (255,))
            d.line([(w - 1 - r, 0), (w - 1 - r, h - 1)], fill=dark + (255,))

        parts = {
            "nw": corner_top(True),
            "ne": corner_top(False),
            "sw": corner_bottom(True),
            "se": corner_bottom(False),
            "n": image(self.title_edge() if title else 1,
                       top_height, edge_top),
            "s": image(1, CORNER, edge_bottom),
            "w": image(CORNER, 1, edge_left),
            "e": image(CORNER, 1, edge_right),
            "c": image(1, 1, lambda d, w, h: d.point((0, 0), surface + (255,))),
        }
        for part, im in parts.items():
            im.save(self.target / f"{prefix}_{part}.png")

    def menu_box(self):
        """The menu box - the top border carries the title bar."""
        self._box("menu", BORDER + BEVEL + TITLE, title=True)

    def title_edge(self):
        """The top border of the box - with the title in it.

        Three approaches tried, two of them rejected in the test VM:

          1. "+ label" above the menu: is not drawn. Not even with a
             font that was demonstrably loaded.
          2. "+ image" above the menu: invisible as well - the
             boot_menu fills its area including the border and covers
             everything that comes after it.
          3. Title in the top-left corner: visible, but the corners
             determine the inner padding of the menu - with a 230 px
             title, half of every entry ended up outside the box.

        That leaves the top border (menu_n). GRUB stretches it between
        the corners, i.e. to MENU_W - 2 * CORNER pixels. It is drawn
        here at exactly that width - then the stretch is a 1:1 case
        and the text stays undistorted. That only holds as long as the
        menu width in theme.txt uses the same constant.
        """
        return MENU_W - 2 * CORNER

    def selection_box(self):
        """The selection bar. Solid accent colour, no border -
        this is how NT marks a selected entry in a list."""
        selection = rgb(self.f("selection")) + (255,)
        for part, (w, h) in {"c": (1, 1), "n": (1, 1), "s": (1, 1),
                             "w": (1, 1), "e": (1, 1), "nw": (1, 1),
                             "ne": (1, 1), "sw": (1, 1), "se": (1, 1)}.items():
            im = Image.new("RGBA", (w, h), selection)
            im.save(self.target / f"select_{part}.png")

    # ------------------------------------------------------------------
    def theme_txt(self):
        # No font of our own.
        #
        # The first draft shipped a .pf2 generated with grub2-mkfont
        # (90 KB per variant). In the test VM, according to grub.cfg,
        # it was loaded via loadfont, the name in the file header
        # matched item_font - and GRUB still drew its built-in font.
        # With 20 instead of 16 pixels as well: no difference in the
        # picture.
        #
        # Instead of dragging along 900 KB that do nothing, item_font
        # is left out. GRUB then uses its default font - exactly what
        # was visible anyway, and its bitmap character suits an NT
        # boot menu well.
        return f"""# NT Legacy - GRUB theme, generated by tools/gen-grub.py
#
# The boot menu in the theme's design language: an NT dialog with a
# title bar. Do not edit by hand - the next build.py run
# overwrites this file.

title-text: ""
desktop-color: "{self.f('desktop')}"

# The box. The title bar lives in the top border of the 9-patch,
# so the first entry sits {BORDER + BEVEL + TITLE} pixels below the top edge.
+ boot_menu {{
    left                       = 50%-{MENU_W // 2}
    top                        = 30%
    width                      = {MENU_W}
    height                     = 260
    item_color                 = "{self.f('text')}"
    selected_item_color        = "{self.f('selection_text')}"
    item_height                = 26
    item_padding               = 12
    item_spacing               = 2
    icon_width                 = 0
    icon_height                = 0
    menu_pixmap_style          = "menu_*.png"
    selected_item_pixmap_style = "select_*.png"
    scrollbar                  = false
}}

# The countdown, styled like an NT status line below the box.
+ label {{
    left  = 50%-{MENU_W // 2}
    top   = 30%+272
    width = {MENU_W}
    align = "center"
    id    = "__timeout__"
    text  = "Starting in %d s"
    color = "{self.f('selection_text')}"
}}
"""

    def generate(self):
        self.target.mkdir(parents=True, exist_ok=True)
        self.menu_box()
        self.selection_box()
        (self.target / "theme.txt").write_text(self.theme_txt())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="directory name, e.g. NTLegacyWin2k")
    ap.add_argument("--display-name", required=True, help="title in the boot menu")
    ap.add_argument("--palette", required=True, help="palette as JSON")
    ap.add_argument("-o", "--output", type=Path, required=True)
    args = ap.parse_args()

    palette = json.loads(args.palette)
    target = args.output / args.name
    Grub(palette, target, args.name, args.display_name).generate()
    print(f"  grub/{args.name}/  ({len(list(target.glob('*.png')))} images)")


if __name__ == "__main__":
    main()
