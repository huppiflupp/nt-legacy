#!/usr/bin/env python3
"""Generates the toolbar icons that ReactOS does not provide.

ReactOS has the shell icons (folders, drives, recycle bin), but no
usable toolbar icons: copy, paste, back, view modes. Those exist there
only as bitmap strips in program resources, or not at all.

Because exactly these icons are constantly visible in Dolphin and
PCManFM-Qt, and without them the Breeze fallback kicks in - flat grey
strokes next to pixel art - they are generated here. That has three
advantages: it is licence-clean (our own work under the theme licence),
stylistically controllable, and the colours come from the same palette
as the rest.

    ./gen-icons.py <icon-theme-directory>
    ./gen-icons.py <dir> --palette desert

The drawing is deliberately coarse: 16 px are 16 px. Fine lines vanish
when scaling, so all shapes sit on whole pixels and the stroke width
grows with the size.
"""

import argparse
import subprocess
from pathlib import Path

# The sizes Dolphin offers in its zoom slider - all of them.
#
# Up to 0.2.6 the series ended at 48, and above that a scalable
# directory was supposed to take over. It does not: judging by the
# files' access times, Dolphin reads the 48 PNG at 200 px and scales it
# up, while the SVG in the scalable folder stays untouched. With QIcon
# the fallback was correct - but KDE programs load icons through
# KIconLoader, and that decides differently. Reported twice by the
# community, reproduced here.
#
# Hence real bitmaps in every size now. That is more ballast (around
# 650 more files), but it does not depend on how an icon loader weights
# directories.
SIZES = (16, 22, 32, 48, 64, 96, 128, 256)

# Above 48 px the bitmap version stops. Dolphin offers 64, 96, 128 and
# 256, and because our set catches the name, Breeze is never asked -
# the loader takes the 48 PNG and scales it up. Reported by the
# community: "icons become pixelated when enlarging in Dolphin".
#
# Fixed with a scalable directory holding exactly the source the PNGs
# are made from. From MinSize on it wins, below that the bitmaps stay
# untouched - and they have to: the shapes sit on a 32 grid, at 16 px
# every edge is placed by hand. A continuous scalable from 8 to 512
# would have destroyed exactly that.
#
# MinSize 64, not 49: between 49 and 63 the 48 bitmap would be closer,
# and the loader would pick it anyway. This way the boundary sits where
# Dolphin has its next step.
SCALABLE_FROM = 64
SCALABLE_TO = 512

# The icon colours are deliberately NOT the colours of the interface.
#
# Windows NT did not recolour its icons with the colour scheme: the
# folder stayed yellow, the drive grey, whatever colour world was set.
# Exactly that is reproduced here - only line and accent colour follow
# the variant, the object colours stay.
OBJECT_COLOURS = {
    "folder_light":   "#FFE870",   # folder: light edge
    "folder_mid":  "#E8C020",   # folder: surface
    "folder_dark": "#8A6A10",   # folder: shadow edge
    "metal_light":   "#F0F0F0",   # metal/plastic: light edge
    "metal_mid":  "#C0C0C0",   # metal: surface - the Win95 grey
    "metal_dark": "#707070",   # metal: shadow edge
    "paper":   "#FFFFFF",
    "glass":     "#88B8C8",   # screens, CDs
    "red":      "#A83232",
    "green":    "#39734A",
}

PALETTES = {
    "teal":   {"line": "#202628", "surface": "#D8D8D0", "light": "#F0F0E8",
               "accent": "#287F8C", "warn": "#C87922", "good": "#39734A",
               "paper": "#FFFFFF", "gold": "#D6A23A"},
    "desert": {"line": "#2A2620", "surface": "#D8D0C0", "light": "#F0EADC",
               "accent": "#8C6A28", "warn": "#C87922", "good": "#5A6B32",
               "paper": "#FFFFFF", "gold": "#D6A23A"},
    "lilac":  {"line": "#252230", "surface": "#D8D8D0", "light": "#F0F0E8",
               "accent": "#6A5A8C", "warn": "#C87922", "good": "#39734A",
               "paper": "#FFFFFF", "gold": "#D6A23A"},
}
for _p in PALETTES.values():
    _p.update(OBJECT_COLOURS)


class Painter:
    """Draws on a 32x32 grid; the output gets scaled."""

    def __init__(self, p):
        self.p = p

    # -- Building blocks -----------------------------------------------
    def sheet(self, x=8, y=4, b=16, h=24, colour=None):
        """A document with a folded corner - the basic shape of many
        file icons."""
        f = colour or self.p["paper"]
        fold = 6
        return (f'<path d="M{x},{y} h{b-fold} l{fold},{fold} v{h-fold} '
                f'h{-b} z" fill="{f}" stroke="{self.p["line"]}" '
                f'stroke-width="1.5"/>'
                f'<path d="M{x+b-fold},{y} v{fold} h{fold} z" '
                f'fill="{self.p["surface"]}" stroke="{self.p["line"]}" '
                f'stroke-width="1.5"/>')

    def lines(self, x=11, y=13, b=10, n=3, colour=None):
        f = colour or self.p["line"]
        return "".join(
            f'<rect x="{x}" y="{y + i*4}" width="{b}" height="1.5" fill="{f}"/>'
            for i in range(n))

    def arrow(self, direction, colour=None, mx=16, my=16, size=9):
        """A solid triangle. At 16 px anything else is mush."""
        f = colour or self.p["accent"]
        points = {
            "left":  f"{mx-size},{my} {mx+size//2},{my-size} {mx+size//2},{my+size}",
            "right": f"{mx+size},{my} {mx-size//2},{my-size} {mx-size//2},{my+size}",
            "up":    f"{mx},{my-size} {mx-size},{my+size//2} {mx+size},{my+size//2}",
            "down":  f"{mx},{my+size} {mx-size},{my-size//2} {mx+size},{my-size//2}",
        }[direction]
        return (f'<polygon points="{points}" fill="{f}" '
                f'stroke="{self.p["line"]}" stroke-width="1.2" '
                f'stroke-linejoin="round"/>')

    def folder(self, x=3, y=8, b=26, h=18, colour=None):
        f = colour or self.p["gold"]
        return (f'<path d="M{x},{y+4} v{h-4} h{b} v{-h+2} h{-b//2} '
                f'l-3,-3 h{-b//2+3} z" fill="{f}" '
                f'stroke="{self.p["line"]}" stroke-width="1.5" '
                f'stroke-linejoin="round"/>')

    def magnifier(self, cx=14, cy=14, r=7):
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{self.p["light"]}" '
                f'stroke="{self.p["line"]}" stroke-width="2"/>'
                f'<line x1="{cx+r-1}" y1="{cy+r-1}" x2="{cx+r+7}" '
                f'y2="{cy+r+7}" stroke="{self.p["line"]}" stroke-width="3" '
                f'stroke-linecap="round"/>')

    def cross(self, cx=16, cy=16, r=8, colour=None):
        f = colour or self.p["line"]
        return (f'<line x1="{cx-r}" y1="{cy-r}" x2="{cx+r}" y2="{cy+r}" '
                f'stroke="{f}" stroke-width="3.5" stroke-linecap="round"/>'
                f'<line x1="{cx+r}" y1="{cy-r}" x2="{cx-r}" y2="{cy+r}" '
                f'stroke="{f}" stroke-width="3.5" stroke-linecap="round"/>')

    def plus(self, cx=16, cy=16, r=8, colour=None):
        f = colour or self.p["good"]
        return (f'<line x1="{cx-r}" y1="{cy}" x2="{cx+r}" y2="{cy}" '
                f'stroke="{f}" stroke-width="4" stroke-linecap="round"/>'
                f'<line x1="{cx}" y1="{cy-r}" x2="{cx}" y2="{cy+r}" '
                f'stroke="{f}" stroke-width="4" stroke-linecap="round"/>')

    def minus(self, cx=16, cy=16, r=8, colour=None):
        f = colour or self.p["warn"]
        return (f'<line x1="{cx-r}" y1="{cy}" x2="{cx+r}" y2="{cy}" '
                f'stroke="{f}" stroke-width="4" stroke-linecap="round"/>')

    def box(self, x, y, b, h, colour=None, outline=None):
        return (f'<rect x="{x}" y="{y}" width="{b}" height="{h}" '
                f'fill="{colour or self.p["light"]}" '
                f'stroke="{outline or self.p["line"]}" stroke-width="1.5"/>')

    # -- Building blocks for shell icons --------------------------------
    def nt_folder(self, opened=False, x=2, y=7, b=28, h=19):
        """The yellow folder - the most-seen icon of all.

        Built as in NT: back at the rear, tab at the top left, cover at
        the front, plus a light edge at the top and a shadow edge at the
        bottom.
        """
        p = self.p
        tab = b // 2
        back = (f'<path d="M{x},{y+3} v{h-3} h{b} v{-h+1} h{-tab} '
                   f'l-3,-3 z" fill="{p["folder_mid"]}" stroke="{p["line"]}" '
                   f'stroke-width="1.5" stroke-linejoin="round"/>')
        if not opened:
            edges = (f'<line x1="{x+2}" y1="{y+5}" x2="{x+b-2}" y2="{y+5}" '
                      f'stroke="{p["folder_light"]}" stroke-width="1.5"/>'
                      f'<line x1="{x+2}" y1="{y+h-1}" x2="{x+b-2}" '
                      f'y2="{y+h-1}" stroke="{p["folder_dark"]}" '
                      f'stroke-width="1.5"/>')
            return back + edges
        # Open: the cover tips forward and reveals the back.
        # It has to be clearly lighter than the back, otherwise the
        # folder at 16 px just looks like a skewed box.
        lid = (f'<path d="M{x+1},{y+h+3} l6,-13 h{b+1} l-6,13 z" '
                  f'fill="{p["folder_light"]}" stroke="{p["line"]}" '
                  f'stroke-width="1.5" stroke-linejoin="round"/>'
                  f'<line x1="{x+8}" y1="{y+h-8}" x2="{x+b+1}" y2="{y+h-8}" '
                  f'stroke="{p["folder_dark"]}" stroke-width="1"/>')
        return back + lid

    def badge(self, content, mx=22, my=21, r=8):
        """Small badge at the bottom right of a folder.

        That turns one folder into twenty: folder-music,
        folder-videos, folder-print. Drawing a separate icon per variant
        would be twenty times the work for the same recognition value.
        """
        return (f'<circle cx="{mx}" cy="{my}" r="{r}" '
                f'fill="{self.p["surface"]}" stroke="{self.p["line"]}" '
                f'stroke-width="1.5"/>'
                f'<g transform="translate({mx},{my}) scale(0.42) '
                f'translate(-16,-16)">{content}</g>')

    def device(self, x=3, y=10, b=26, h=13, colour=None):
        """A box with the NT-typical 3D edge: light at the top, dark at the bottom."""
        p = self.p
        f = colour or p["metal_mid"]
        return (f'<rect x="{x}" y="{y}" width="{b}" height="{h}" fill="{f}" '
                f'stroke="{p["line"]}" stroke-width="1.5"/>'
                f'<line x1="{x+1.5}" y1="{y+1.5}" x2="{x+b-1.5}" y2="{y+1.5}" '
                f'stroke="{p["metal_light"]}" stroke-width="1.5"/>'
                f'<line x1="{x+1.5}" y1="{y+h-1.5}" x2="{x+b-1.5}" '
                f'y2="{y+h-1.5}" stroke="{p["metal_dark"]}" stroke-width="1.5"/>')

    def monitor(self, glass=None):
        p = self.p
        return (self.box(3, 5, 26, 19, p["metal_mid"]) +
                f'<rect x="6" y="8" width="20" height="13" '
                f'fill="{glass or p["glass"]}" stroke="{p["line"]}" '
                f'stroke-width="1"/>' +
                self.box(12, 24, 8, 3, p["metal_dark"]) +
                self.box(8, 27, 16, 3, p["metal_mid"]))

    def disc(self, cx=16, cy=16, r=12, colour=None):
        p = self.p
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{colour or p["glass"]}" stroke="{p["line"]}" '
                f'stroke-width="1.5"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{r*0.45:.0f}" '
                f'fill="{p["surface"]}" stroke="{p["line"]}" '
                f'stroke-width="1"/>'
                f'<circle cx="{cx}" cy="{cy}" r="2" fill="{p["line"]}"/>')

    def person(self, cx=16, cy=16, s=1.0, colour=None):
        p = self.p
        f = colour or p["accent"]
        k, sx, sy = 5 * s, cx, cy - 6 * s
        return (f'<circle cx="{sx}" cy="{sy}" r="{k}" fill="{f}" '
                f'stroke="{p["line"]}" stroke-width="1.5"/>'
                f'<path d="M{cx-9*s},{cy+11*s} a{9*s},{9*s} 0 0 1 {18*s},0 z" '
                f'fill="{f}" stroke="{p["line"]}" stroke-width="1.5"/>')

    def circle_glyph(self, glyph, colour, text_colour="#FFFFFF"):
        p = self.p
        return (f'<circle cx="16" cy="16" r="12" fill="{colour}" '
                f'stroke="{p["line"]}" stroke-width="1.5"/>'
                f'<text x="16" y="23" text-anchor="middle" '
                f'font-family="sans-serif" font-size="19" font-weight="bold" '
                f'fill="{text_colour}">{glyph}</text>')


def icons(z: Painter):
    """Name -> SVG content. The names are the ones Dolphin and
    PCManFM-Qt actually request."""
    p = z.p
    s = {}

    # --- Navigation
    s["go-previous"] = z.arrow("left")
    s["go-next"] = z.arrow("right")
    s["go-up"] = z.arrow("up")
    s["go-down"] = z.arrow("down")
    s["go-parent-folder"] = z.arrow("up")
    s["go-home"] = (z.folder(colour=p["gold"]) +
                    f'<path d="M16,6 l9,8 h-4 v7 h-10 v-7 h-4 z" '
                    f'fill="{p["light"]}" stroke="{p["line"]}" '
                    f'stroke-width="1.5" stroke-linejoin="round"/>')

    # --- View modes: the most conspicuous gap in Dolphin's toolbar
    s["view-list-icons"] = "".join(
        z.box(4 + col * 12, 4 + row * 12, 9, 9, p["accent"])
        for row in range(2) for col in range(2))
    s["view-list-details"] = (
        "".join(z.box(4, 5 + i * 8, 6, 5, p["accent"]) for i in range(3)) +
        "".join(f'<rect x="13" y="{6 + i*8}" width="15" height="3" '
                f'fill="{p["line"]}"/>' for i in range(3)))
    s["view-list-text"] = s["view-list-details"]
    s["view-list-tree"] = (
        f'<line x1="7" y1="5" x2="7" y2="26" stroke="{p["line"]}" '
        f'stroke-width="1.5"/>' +
        "".join(f'<line x1="7" y1="{9 + i*8}" x2="13" y2="{9 + i*8}" '
                f'stroke="{p["line"]}" stroke-width="1.5"/>'
                f'<rect x="14" y="{6 + i*8}" width="13" height="6" '
                f'fill="{p["accent"]}" stroke="{p["line"]}" '
                f'stroke-width="1"/>' for i in range(3)))
    s["view-file-columns"] = "".join(
        z.box(4 + i * 9, 5, 7, 22, p["accent"] if i == 0 else p["light"])
        for i in range(3))
    s["view-preview"] = z.sheet() + z.magnifier(cx=20, cy=20, r=6)
    s["view-sort-ascending"] = (
        z.arrow("up", mx=8, my=16, size=6) +
        "".join(f'<rect x="16" y="{7 + i*7}" width="{6 + i*4}" height="3" '
                f'fill="{p["line"]}"/>' for i in range(3)))
    s["view-sort-descending"] = (
        z.arrow("down", mx=8, my=16, size=6) +
        "".join(f'<rect x="16" y="{7 + i*7}" width="{14 - i*4}" height="3" '
                f'fill="{p["line"]}"/>' for i in range(3)))
    s["view-sort"] = s["view-sort-ascending"]
    s["view-refresh"] = (
        f'<path d="M25,16 a9,9 0 1 1 -3,-6.7" fill="none" '
        f'stroke="{p["good"]}" stroke-width="3.5"/>'
        f'<polygon points="26,4 26,13 17,10" fill="{p["good"]}"/>')
    s["view-hidden"] = z.sheet() + z.cross(cx=20, cy=22, r=5, colour=p["warn"])
    s["view-visible"] = z.sheet() + z.magnifier(cx=20, cy=20, r=6)

    # --- Edit
    s["edit-copy"] = (z.sheet(x=4, y=3, b=14, h=20) +
                      z.sheet(x=13, y=9, b=14, h=20))
    s["edit-cut"] = (
        f'<line x1="9" y1="4" x2="21" y2="22" stroke="{p["line"]}" '
        f'stroke-width="2"/>'
        f'<line x1="23" y1="4" x2="11" y2="22" stroke="{p["line"]}" '
        f'stroke-width="2"/>'
        f'<circle cx="9" cy="25" r="4" fill="none" stroke="{p["line"]}" '
        f'stroke-width="2"/>'
        f'<circle cx="23" cy="25" r="4" fill="none" stroke="{p["line"]}" '
        f'stroke-width="2"/>')
    s["edit-paste"] = (
        z.box(6, 5, 20, 24, p["gold"]) +
        z.box(10, 2, 12, 6, p["surface"]) +
        z.box(10, 12, 12, 14, p["paper"]))
    s["edit-delete"] = z.sheet() + z.cross(cx=21, cy=22, r=6, colour="#A83232")
    s["edit-rename"] = (
        z.sheet() +
        f'<path d="M18,22 l7,-7 3,3 -7,7 -4,1 z" fill="{p["gold"]}" '
        f'stroke="{p["line"]}" stroke-width="1.2"/>')
    s["edit-find"] = z.magnifier()
    s["edit-clear"] = z.cross(colour=p["warn"])
    s["edit-undo"] = (
        f'<path d="M8,18 a9,9 0 1 1 9,9" fill="none" stroke="{p["accent"]}" '
        f'stroke-width="3.5"/><polygon points="3,17 13,17 8,25" '
        f'fill="{p["accent"]}"/>')
    s["edit-redo"] = (
        f'<path d="M24,18 a9,9 0 1 0 -9,9" fill="none" stroke="{p["accent"]}" '
        f'stroke-width="3.5"/><polygon points="29,17 19,17 24,25" '
        f'fill="{p["accent"]}"/>')
    s["edit-select-all"] = (
        f'<rect x="4" y="4" width="24" height="24" fill="none" '
        f'stroke="{p["line"]}" stroke-width="1.5" stroke-dasharray="3,2"/>' +
        z.box(9, 9, 14, 14, p["accent"]))

    # --- Files
    s["document-new"] = z.sheet() + z.plus(cx=22, cy=22, r=5)
    s["document-open"] = z.folder(colour=p["gold"])
    s["document-save"] = (
        z.box(4, 4, 24, 24, p["accent"]) +
        z.box(10, 4, 12, 9, p["surface"]) +
        z.box(8, 18, 16, 10, p["light"]))
    s["document-properties"] = z.sheet() + z.magnifier(cx=21, cy=21, r=5)
    s["folder-new"] = z.folder() + z.plus(cx=23, cy=21, r=5)
    s["list-add"] = z.plus()
    s["list-remove"] = z.minus()

    # --- Zoom
    s["zoom-in"] = z.magnifier() + (
        f'<line x1="10" y1="14" x2="18" y2="14" stroke="{p["line"]}" '
        f'stroke-width="2.5"/><line x1="14" y1="10" x2="14" y2="18" '
        f'stroke="{p["line"]}" stroke-width="2.5"/>')
    s["zoom-out"] = z.magnifier() + (
        f'<line x1="10" y1="14" x2="18" y2="14" stroke="{p["line"]}" '
        f'stroke-width="2.5"/>')
    s["zoom-original"] = z.magnifier()
    s["zoom-fit-best"] = z.magnifier() + (
        f'<rect x="10" y="10" width="8" height="8" fill="none" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>')

    # --- Windows and dialogs
    s["window-close"] = z.cross(colour="#A83232")
    s["dialog-close"] = s["window-close"]
    # The "Quit" menu item in every program. Without this icon the
    # lookup shortens application-exit to the class and returns our
    # file icon - in the File menu there was a sheet of paper next to
    # "Quit". A door with an arrow pointing out, as KDE has always shown it.
    s["application-exit"] = (
        z.box(6, 3, 13, 26, p["metal_mid"]) +
        f'<circle cx="16" cy="16" r="1.5" fill="{p["line"]}"/>' +
        f'<line x1="20" y1="16" x2="29" y2="16" stroke="{p["good"]}" '
        f'stroke-width="3" stroke-linecap="round"/>'
        f'<polyline points="25,11 30,16 25,21" fill="none" '
        f'stroke="{p["good"]}" stroke-width="3" stroke-linecap="round" '
        f'stroke-linejoin="round"/>')
    s["application-quit"] = s["application-exit"]
    s["dialog-ok"] = (
        f'<polyline points="6,17 13,24 26,8" fill="none" '
        f'stroke="{p["good"]}" stroke-width="4" stroke-linecap="round" '
        f'stroke-linejoin="round"/>')
    s["dialog-cancel"] = z.cross(colour="#A83232")
    s["tab-new"] = z.box(4, 8, 24, 20, p["light"]) + z.plus(cx=16, cy=18, r=5)
    s["tab-close"] = z.box(4, 8, 24, 20, p["light"]) + z.cross(cx=16, cy=18, r=5)

    # --- Menu and settings
    s["application-menu"] = "".join(
        f'<rect x="6" y="{7 + i*7}" width="20" height="3.5" '
        f'fill="{p["line"]}"/>' for i in range(3))
    s["open-menu"] = s["application-menu"]
    s["show-menu"] = s["application-menu"]
    # Cog wheel, not sun. Before, eight narrow strokes stood 2 px away
    # around a circle - the community called it "looks more like a gray
    # sun". Two things make the difference: the teeth have to touch the
    # rim (here they overlap it by 1 px), and they have to be wider than
    # the gaps. Plus a light hub, so there is a hole in the middle and
    # not a disc.
    s["configure"] = (
        f'<circle cx="16" cy="16" r="8" fill="{p["metal_mid"]}" '
        f'stroke="{p["line"]}" stroke-width="2"/>' +
        "".join(f'<rect x="13.5" y="1.5" width="5" height="7" '
                f'fill="{p["metal_mid"]}" stroke="{p["line"]}" '
                f'stroke-width="1.5" stroke-linejoin="round" '
                f'transform="rotate({a},16,16)"/>'
                for a in range(0, 360, 60)) +
        f'<circle cx="16" cy="16" r="8" fill="none" '
        f'stroke="{p["line"]}" stroke-width="2"/>'
        f'<circle cx="16" cy="16" r="3" fill="{p["surface"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>')
    s["settings-configure"] = s["configure"]
    s["configure-toolbars"] = s["configure"]

    # --- Other things from Dolphin's toolbar
    s["view-split-left-right"] = (
        z.box(3, 6, 12, 20, p["light"]) + z.box(17, 6, 12, 20, p["accent"]))
    s["swap-panels"] = (z.arrow("right", mx=16, my=10, size=7) +
                        z.arrow("left", mx=16, my=22, size=7))
    s["view-filter"] = (
        f'<polygon points="4,5 28,5 19,16 19,27 13,23 13,16" '
        f'fill="{p["accent"]}" stroke="{p["line"]}" stroke-width="1.5" '
        f'stroke-linejoin="round"/>')
    s["object-locked"] = (
        z.box(8, 14, 16, 14, p["gold"]) +
        f'<path d="M12,14 v-4 a4,4 0 0 1 8,0 v4" fill="none" '
        f'stroke="{p["line"]}" stroke-width="2.5"/>')
    s["object-unlocked"] = (
        z.box(8, 14, 16, 14, p["light"]) +
        f'<path d="M12,14 v-4 a4,4 0 0 1 8,0" fill="none" '
        f'stroke="{p["line"]}" stroke-width="2.5"/>')

    return s


def shell_icons(z: Painter):
    """Places, devices, file types and programs in NT style.

    Replaces the icons previously taken over from ReactOS. Their look was
    more modern than NT 4.0 - blue folders with gradients instead of
    yellow surfaces - and so did not match the rest of the theme.
    """
    p = z.p
    s = {}

    # ── Folders and places ─────────────────────────────────────────────
    s["folder"] = z.nt_folder()
    s["folder-open"] = z.nt_folder(opened=True)
    s["user-home"] = z.nt_folder() + z.badge(
        f'<path d="M16,5 l11,10 h-4 v10 h-14 v-10 h-4 z" fill="{p["red"]}" '
        f'stroke="{p["line"]}" stroke-width="2"/>')
    s["folder-documents"] = z.nt_folder() + z.badge(
        z.sheet(x=8, y=3, b=16, h=25) + z.lines(x=11, y=11, b=10, n=3))
    s["folder-music"] = z.nt_folder() + z.badge(
        f'<path d="M12,24 v-16 l12,-3 v16" fill="none" stroke="{p["line"]}" '
        f'stroke-width="3"/><circle cx="9" cy="24" r="4" fill="{p["line"]}"/>'
        f'<circle cx="21" cy="21" r="4" fill="{p["line"]}"/>')
    s["folder-videos"] = z.nt_folder() + z.badge(
        z.box(4, 8, 24, 16, p["line"]) +
        f'<polygon points="13,13 13,23 23,18" fill="{p["paper"]}"/>')
    s["folder-pictures"] = z.nt_folder() + z.badge(
        z.box(4, 7, 24, 18, p["glass"]) +
        f'<circle cx="11" cy="13" r="3" fill="{p["folder_light"]}"/>'
        f'<polygon points="6,24 14,15 20,24" fill="{p["green"]}"/>')
    s["folder-download"] = z.nt_folder() + z.badge(
        z.arrow("down", colour=p["good"], size=11))
    s["folder-publicshare"] = z.nt_folder() + z.badge(z.person(s=1.4))
    s["folder-print"] = z.nt_folder() + z.badge(
        z.device(x=4, y=12, b=24, h=12) + z.box(9, 4, 14, 9, p["paper"]))
    s["folder-saved-search"] = z.nt_folder() + z.badge(z.magnifier(cx=15, cy=14, r=9))
    s["folder-system"] = z.nt_folder() + z.badge(
        f'<circle cx="16" cy="16" r="7" fill="none" stroke="{p["line"]}" '
        f'stroke-width="4"/>' +
        "".join(f'<rect x="14" y="1" width="4" height="7" fill="{p["line"]}" '
                f'transform="rotate({a},16,16)"/>' for a in range(0, 360, 60)))
    s["folder-remote"] = z.nt_folder() + z.badge(
        f'<circle cx="16" cy="16" r="11" fill="{p["glass"]}" '
        f'stroke="{p["line"]}" stroke-width="2"/>'
        f'<ellipse cx="16" cy="16" rx="5" ry="11" fill="none" '
        f'stroke="{p["line"]}" stroke-width="2"/>'
        f'<line x1="5" y1="16" x2="27" y2="16" stroke="{p["line"]}" '
        f'stroke-width="2"/>')
    s["folder-network"] = s["folder-remote"]
    s["folder-applications"] = z.nt_folder() + z.badge(
        z.box(4, 6, 24, 20, p["glass"]) + z.box(4, 6, 24, 5, p["accent"]))
    s["folder-edit"] = z.nt_folder() + z.badge(
        f'<path d="M6,26 l3,-8 12,-12 5,5 -12,12 z" fill="{p["folder_light"]}" '
        f'stroke="{p["line"]}" stroke-width="2"/>')
    s["folder-favorites"] = z.nt_folder() + z.badge(
        f'<polygon points="16,4 20,13 29,13 22,19 25,28 16,22 7,28 10,19 '
        f'3,13 12,13" fill="{p["folder_light"]}" stroke="{p["line"]}" '
        f'stroke-width="2" stroke-linejoin="round"/>')

    # The remaining folders of the sidebar.
    #
    # Dolphin requests a name of its own for every XDG user folder -
    # folder-desktop for ~/Desktop, folder-templates for ~/Templates
    # and so on. If the name is missing, the icon lookup shortens it at
    # the hyphen, finds our plain "folder" and stops looking: all user
    # folders then look the same, and because the hit comes from our own
    # set, Breeze is not even asked. The badges are therefore
    # deliberately solid areas instead of fine lines - inside the circle
    # only about six pixels remain at 16 px, and only a silhouette
    # survives in that.
    s["folder-desktop"] = z.nt_folder() + z.badge(
        f'<rect x="3" y="5" width="26" height="18" fill="{p["line"]}"/>'
        f'<rect x="6" y="8" width="20" height="12" fill="{p["glass"]}"/>'
        f'<rect x="12" y="23" width="8" height="4" fill="{p["line"]}"/>'
        f'<rect x="6" y="27" width="20" height="4" fill="{p["line"]}"/>')
    # Templates are sheets to trace from: a second, coloured sheet
    # behind the white one. The offset is what tells it apart from
    # folder-documents at 16 px - lines would not do it there.
    s["folder-templates"] = z.nt_folder() + z.badge(
        f'<rect x="2" y="2" width="18" height="24" fill="{p["accent"]}" '
        f'stroke="{p["line"]}" stroke-width="2"/>'
        f'<rect x="12" y="8" width="18" height="24" fill="{p["paper"]}" '
        f'stroke="{p["line"]}" stroke-width="2"/>')
    # Important gets an exclamation mark instead of a second star:
    # next to folder-favorites a star could no longer be told apart,
    # and the red bar is the strongest shape that fits into the badge.
    s["folder-important"] = z.nt_folder() + z.badge(
        f'<rect x="12" y="2" width="9" height="18" fill="{p["red"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>'
        f'<rect x="12" y="23" width="9" height="8" fill="{p["red"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>')
    # Angle brackets as in applications-development, but drawn as thick
    # lines: the text "</>" falls apart inside the badge.
    # The gap between the two brackets is the actual sign - if they
    # touch, they turn into a black blob at 16 px.
    s["folder-development"] = z.nt_folder() + z.badge(
        f'<polyline points="10,4 2,16 10,28" fill="none" '
        f'stroke="{p["line"]}" stroke-width="6" stroke-linecap="round" '
        f'stroke-linejoin="round"/>'
        f'<polyline points="22,4 30,16 22,28" fill="none" '
        f'stroke="{p["line"]}" stroke-width="6" stroke-linecap="round" '
        f'stroke-linejoin="round"/>')
    # Playing card instead of joystick: a knob on a base has the same
    # silhouette as the person on folder-publicshare and at 16 px can
    # only be told apart by colour. The red diamond on white has no twin
    # in the whole set - and Solitaire was the game every Windows came
    # with.
    s["folder-games"] = z.nt_folder() + z.badge(
        f'<rect x="6" y="2" width="21" height="28" fill="{p["paper"]}" '
        f'stroke="{p["line"]}" stroke-width="2.5"/>'
        f'<polygon points="16,8 23,16 16,24 9,16" fill="{p["red"]}"/>')

    # Recycle bin: in NT a wire basket, not a bin
    basket = (f'<path d="M9,10 l2,18 h10 l2,-18 z" fill="{p["metal_mid"]}" '
            f'stroke="{p["line"]}" stroke-width="1.5" '
            f'stroke-linejoin="round"/>'
            f'<ellipse cx="16" cy="10" rx="7" ry="2.5" fill="{p["metal_light"]}" '
            f'stroke="{p["line"]}" stroke-width="1.5"/>' +
            "".join(f'<line x1="{12+i*4}" y1="12" x2="{12.8+i*3.4}" y2="27" '
                    f'stroke="{p["metal_dark"]}" stroke-width="1"/>'
                    for i in range(3)))
    s["user-trash"] = basket
    s["user-trash-full"] = (
        f'<path d="M11,9 l3,-5 4,3 3,-4 2,6 z" fill="{p["paper"]}" '
        f'stroke="{p["line"]}" stroke-width="1.2"/>' + basket)

    # ── Computers and network ──────────────────────────────────────────
    s["computer"] = z.monitor()
    s["computer-laptop"] = (
        z.box(5, 6, 22, 15, p["metal_mid"]) +
        f'<rect x="8" y="9" width="16" height="9" fill="{p["glass"]}" '
        f'stroke="{p["line"]}" stroke-width="1"/>' +
        f'<path d="M2,26 h28 l-3,-5 h-22 z" fill="{p["metal_light"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5" stroke-linejoin="round"/>')
    s["video-display"] = z.monitor()
    s["network-workgroup"] = (
        z.box(2, 4, 14, 11, p["metal_mid"]) +
        f'<rect x="4" y="6" width="10" height="7" fill="{p["glass"]}"/>' +
        z.box(16, 17, 14, 11, p["metal_mid"]) +
        f'<rect x="18" y="19" width="10" height="7" fill="{p["glass"]}"/>'
        f'<path d="M9,15 v4 h14 v-2" fill="none" stroke="{p["line"]}" '
        f'stroke-width="1.5"/>')
    s["network-server"] = (
        "".join(z.device(x=6, y=4 + i * 8, b=20, h=7) for i in range(3)) +
        "".join(f'<circle cx="10" cy="{7.5 + i*8}" r="1.5" '
                f'fill="{p["green"]}"/>' for i in range(3)))
    s["network-offline"] = s["network-workgroup"] + z.cross(
        cx=24, cy=8, r=6, colour=p["red"])

    # ── Drives and devices ─────────────────────────────────────────────
    s["drive-harddisk"] = (
        z.device(y=9, h=15) +
        f'<circle cx="24" cy="20" r="2" fill="{p["green"]}"/>'
        f'<line x1="7" y1="20" x2="19" y2="20" stroke="{p["metal_dark"]}" '
        f'stroke-width="1.5"/>')
    s["drive-harddisk-solidstate"] = (
        z.device(y=9, h=15) +
        "".join(f'<rect x="{8+i*5}" y="14" width="3" height="6" '
                f'fill="{p["line"]}"/>' for i in range(4)))
    s["drive-removable-media"] = z.device(y=11, h=11) + z.box(
        7, 14, 11, 5, p["metal_dark"])
    s["drive-removable-media-usb"] = (
        z.box(4, 12, 18, 9, p["metal_mid"]) +
        z.box(22, 14, 7, 5, p["metal_dark"]) +
        f'<line x1="8" y1="16.5" x2="17" y2="16.5" stroke="{p["accent"]}" '
        f'stroke-width="2"/>')
    s["media-floppy"] = (
        z.box(4, 4, 24, 24, p["line"]) +
        z.box(9, 4, 14, 10, p["metal_mid"]) +
        f'<rect x="17" y="6" width="4" height="6" fill="{p["metal_dark"]}"/>' +
        z.box(8, 17, 16, 11, p["metal_light"]))
    s["drive-optical"] = z.device(y=11, h=11) + f'<circle cx="16" cy="16.5" ' \
        f'r="3.5" fill="none" stroke="{p["metal_dark"]}" stroke-width="1.5"/>'
    s["media-optical"] = z.disc()
    s["media-optical-audio"] = z.disc() + (
        f'<path d="M14,22 v-9 l7,-2 v9" fill="none" stroke="{p["line"]}" '
        f'stroke-width="2"/>')
    s["media-optical-dvd"] = z.disc(colour=p["accent"])
    s["media-optical-recordable"] = z.disc(colour=p["good"])
    s["media-optical-rewritable"] = z.disc(colour=p["warn"])
    s["media-flash"] = (
        z.box(8, 4, 16, 24, p["line"]) +
        "".join(f'<rect x="{10+i*4}" y="7" width="3" height="6" '
                f'fill="{p["folder_mid"]}"/>' for i in range(3)))
    s["media-flash-sd"] = (
        f'<path d="M8,4 h12 l4,4 v20 h-16 z" fill="{p["accent"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5" stroke-linejoin="round"/>' +
        "".join(f'<rect x="{10+i*4}" y="8" width="2.5" height="5" '
                f'fill="{p["metal_light"]}"/>' for i in range(3)))
    s["printer"] = (
        z.box(8, 3, 16, 9, p["paper"]) +
        z.device(x=3, y=12, b=26, h=11) +
        z.box(8, 20, 16, 9, p["paper"]))
    s["printer-network"] = s["printer"] + z.badge(
        # Globe as the network badge - the same sign as on folder-remote,
        # so that "on the network" looks the same everywhere
        f'<circle cx="16" cy="16" r="12" fill="{p["glass"]}" '
        f'stroke="{p["line"]}" stroke-width="2"/>'
        f'<ellipse cx="16" cy="16" rx="5" ry="12" fill="none" '
        f'stroke="{p["line"]}" stroke-width="2"/>'
        f'<line x1="4" y1="16" x2="28" y2="16" stroke="{p["line"]}" '
        f'stroke-width="2"/>', mx=24, my=24, r=7)
    s["printer-fax"] = s["printer"]
    s["scanner"] = (
        z.device(x=3, y=14, b=26, h=10) +
        z.box(7, 5, 18, 9, p["glass"]) +
        f'<line x1="9" y1="19" x2="23" y2="19" stroke="{p["red"]}" '
        f'stroke-width="2"/>')
    s["camera-photo"] = (
        z.device(x=3, y=9, b=26, h=16) +
        z.box(11, 5, 8, 4, p["metal_dark"]) +
        f'<circle cx="16" cy="17" r="6" fill="{p["glass"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>'
        f'<circle cx="16" cy="17" r="2.5" fill="{p["line"]}"/>')
    s["camera-video"] = (
        z.device(x=2, y=10, b=19, h=13) +
        f'<polygon points="21,16 29,11 29,22 21,19" fill="{p["metal_dark"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5" stroke-linejoin="round"/>'
        f'<circle cx="9" cy="8" r="4" fill="{p["metal_light"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>')
    s["input-mouse"] = (
        f'<path d="M16,4 a9,9 0 0 1 9,9 v9 a9,9 0 0 1 -18,0 v-9 '
        f'a9,9 0 0 1 9,-9 z" fill="{p["metal_mid"]}" stroke="{p["line"]}" '
        f'stroke-width="1.5"/>'
        f'<line x1="16" y1="5" x2="16" y2="14" stroke="{p["line"]}" '
        f'stroke-width="1.5"/>'
        f'<line x1="7" y1="14" x2="25" y2="14" stroke="{p["line"]}" '
        f'stroke-width="1.5"/>')
    s["audio-input-microphone"] = (
        f'<rect x="12" y="3" width="8" height="14" rx="4" '
        f'fill="{p["metal_mid"]}" stroke="{p["line"]}" stroke-width="1.5"/>'
        f'<path d="M8,15 a8,8 0 0 0 16,0" fill="none" stroke="{p["line"]}" '
        f'stroke-width="2"/>'
        f'<line x1="16" y1="23" x2="16" y2="28" stroke="{p["line"]}" '
        f'stroke-width="2"/>')

    # ── Volume ─────────────────────────────────────────────────────────
    #
    # These four names were missing, and their absence was worse than a
    # gap. The icon lookup shortens an unknown name at the hyphens until
    # something matches: audio-volume-high became audio-volume, then
    # audio - and ended up on our audio-x-generic. So the panel showed a
    # sheet of paper with a note instead of a speaker, and because the
    # hit came from our own set, Breeze was never asked. Reproduced with
    # kiconfinder6.
    #
    # Rule of thumb for new icons: a short name catches all longer ones
    # that start with it. Whoever ships audio-x-generic has to ship the
    # audio-volume series too.
    def _speaker(arcs, extra=""):
        # Box and cone in one stroke, so that no line runs through the
        # icon at the seam.
        body = (
            f'<path d="M4,12 h5 l7,-6 v20 l-7,-6 h-5 z" '
            f'fill="{p["metal_mid"]}" stroke="{p["line"]}" '
            f'stroke-width="1.5" stroke-linejoin="round"/>')
        # The arcs have to sit on the centre axis of the body, i.e.
        # at y=16. They sat 2 px too low, which the community reported:
        # the start point was 13-2.5i and the arc height 10+5i, giving a
        # centre at 13-2.5i+(10+5i)/2 = 18. The start point has to move
        # up by the same 2 px, then the i cancels out again and every arc
        # is centred on 16.
        waves = "".join(
            f'<path d="M{18 + i*4},{11 - i*2.5} a{5 + i*4},{5 + i*4} 0 0 1 '
            f'0,{10 + i*5}" fill="none" stroke="{p["line"]}" '
            f'stroke-width="2" stroke-linecap="round"/>'
            for i in range(arcs))
        return body + waves + extra

    # The same trap, other names: the volume menu and System Settings
    # ask for devices, and those also used to end up on
    # audio-x-generic. Found with
    # tools/check-symbolic-trap.py.
    s["audio-card"] = (
        z.box(4, 10, 24, 14, p["metal_mid"]) +
        f'<rect x="7" y="24" width="4" height="5" fill="{p["metal_dark"]}" '
        f'stroke="{p["line"]}" stroke-width="1"/>'
        f'<rect x="21" y="24" width="4" height="5" fill="{p["metal_dark"]}" '
        f'stroke="{p["line"]}" stroke-width="1"/>'
        f'<circle cx="12" cy="17" r="3.5" fill="{p["metal_dark"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>'
        f'<circle cx="22" cy="17" r="2.5" fill="{p["metal_dark"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>')
    s["audio-headphones"] = (
        f'<path d="M5,20 v-4 a11,11 0 0 1 22,0 v4" fill="none" '
        f'stroke="{p["line"]}" stroke-width="2.5"/>' +
        z.box(2, 18, 6, 10, p["metal_mid"]) +
        z.box(24, 18, 6, 10, p["metal_mid"]))
    s["audio-headset"] = (
        s["audio-headphones"] +
        f'<path d="M8,26 q-4,4 0,4 h5" fill="none" stroke="{p["line"]}" '
        f'stroke-width="2"/>')

    s["audio-volume-high"] = _speaker(3)
    s["audio-volume-medium"] = _speaker(2)
    s["audio-volume-low"] = _speaker(1)
    s["audio-volume-muted"] = _speaker(
        0,
        f'<line x1="19" y1="11" x2="29" y2="21" stroke="{p["red"]}" '
        f'stroke-width="3" stroke-linecap="round"/>'
        f'<line x1="29" y1="11" x2="19" y2="21" stroke="{p["red"]}" '
        f'stroke-width="3" stroke-linecap="round"/>')
    s["pda"] = (
        z.box(8, 2, 16, 28, p["metal_mid"]) +
        f'<rect x="11" y="5" width="10" height="16" fill="{p["glass"]}" '
        f'stroke="{p["line"]}" stroke-width="1"/>'
        f'<circle cx="16" cy="25" r="2.5" fill="{p["metal_dark"]}" '
        f'stroke="{p["line"]}" stroke-width="1"/>')
    s["phone"] = s["pda"]

    # ── Programs and settings ──────────────────────────────────────────
    # The same cog wheel as for "configure", just a touch bigger -
    # for the same reason: teeth on the rim, hub in the middle. Before,
    # the teeth stood in front of it as separate dark blocks.
    s["applications-system"] = (
        f'<circle cx="16" cy="16" r="9" fill="{p["metal_mid"]}" '
        f'stroke="{p["line"]}" stroke-width="2"/>' +
        "".join(f'<rect x="13" y="0.5" width="6" height="8" '
                f'fill="{p["metal_mid"]}" stroke="{p["line"]}" '
                f'stroke-width="1.5" stroke-linejoin="round" '
                f'transform="rotate({a},16,16)"/>'
                for a in range(0, 360, 60)) +
        f'<circle cx="16" cy="16" r="9" fill="none" '
        f'stroke="{p["line"]}" stroke-width="2"/>'
        f'<circle cx="16" cy="16" r="3.5" fill="{p["surface"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>')
    s["preferences-system"] = s["applications-system"]

    # ── The System Settings categories ─────────────────────────────────
    #
    # From the community: in the System Settings sidebar a dozen
    # categories carried the same cog wheel - session, users, power,
    # date, login screen, window management, network, drives,
    # Bluetooth. The cause is the name shortening: they are all called
    # preferences-system-<something>, none of them was drawn, and the
    # lookup fell back to our preferences-system. An icon set that only
    # provides the umbrella term turns twelve categories into the same
    # picture twelve times.
    #
    # Hence the names that Plasma's own KCMs request -
    # determined from /usr/share/applications/kcm_*.desktop, not guessed.
    s["preferences-system-time"] = (
        f'<circle cx="16" cy="16" r="12" fill="{p["paper"]}" '
        f'stroke="{p["line"]}" stroke-width="2"/>'
        f'<line x1="16" y1="16" x2="16" y2="8" stroke="{p["line"]}" '
        f'stroke-width="2.5" stroke-linecap="round"/>'
        f'<line x1="16" y1="16" x2="22" y2="19" stroke="{p["line"]}" '
        f'stroke-width="2.5" stroke-linecap="round"/>')
    s["preferences-system-users"] = (
        z.person(cx=12, cy=17, s=0.8, colour=p["metal_mid"]) +
        z.person(cx=21, cy=15, s=0.85))
    s["preferences-system-power-management"] = (
        # Battery lying down, with a lightning bolt. The plug would be a
        # blot at 16 px; the bolt stays readable as a silhouette.
        z.box(3, 10, 22, 13, p["metal_mid"]) +
        z.box(25, 14, 4, 5, p["metal_dark"]) +
        f'<polygon points="15,11 9,17 13,17 11,22 18,15 14,15" '
        f'fill="{p["warn"]}" stroke="{p["line"]}" stroke-width="1.2" '
        f'stroke-linejoin="round"/>')
    s["preferences-system-bluetooth"] = (
        f'<circle cx="16" cy="16" r="12" fill="{p["accent"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>'
        # The Bluetooth rune: centre axis with two triangles.
        f'<path d="M13,10 L20,15 L13,21 L13,10 M13,21 L20,17 L13,11" '
        f'fill="none" stroke="{p["paper"]}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<line x1="13" y1="16" x2="9" y2="13" stroke="{p["paper"]}" '
        f'stroke-width="2" stroke-linecap="round"/>'
        f'<line x1="13" y1="16" x2="9" y2="19" stroke="{p["paper"]}" '
        f'stroke-width="2" stroke-linecap="round"/>')
    s["preferences-system-network"] = (
        # Globe with meridian and parallel.
        f'<circle cx="16" cy="16" r="12" fill="{p["glass"]}" '
        f'stroke="{p["line"]}" stroke-width="2"/>'
        f'<ellipse cx="16" cy="16" rx="5" ry="12" fill="none" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>'
        f'<line x1="4" y1="16" x2="28" y2="16" stroke="{p["line"]}" '
        f'stroke-width="1.5"/>'
        f'<path d="M6.5,9.5 h19 M6.5,22.5 h19" fill="none" '
        f'stroke="{p["line"]}" stroke-width="1.2"/>')
    s["preferences-system-login"] = (
        # Login screen: monitor with a person on it.
        z.box(2, 4, 28, 20, p["metal_mid"]) +
        z.box(5, 7, 22, 14, p["accent"]) +
        z.person(cx=16, cy=15, s=0.55, colour=p["paper"]) +
        z.box(11, 25, 10, 3, p["metal_dark"]))
    s["preferences-system-windows"] = (
        # Two offset windows with title bars - window management.
        z.box(3, 6, 18, 15, p["paper"]) +
        f'<rect x="3" y="6" width="18" height="4" fill="{p["metal_dark"]}" '
        f'stroke="{p["line"]}" stroke-width="1"/>' +
        z.box(11, 13, 18, 15, p["paper"]) +
        f'<rect x="11" y="13" width="18" height="4" fill="{p["accent"]}" '
        f'stroke="{p["line"]}" stroke-width="1"/>')
    s["preferences-system-session-services"] = (
        # Services: stacked bars with a status dot.
        "".join(z.box(4, 5 + i * 8, 24, 6, p["metal_mid"]) +
                f'<circle cx="8.5" cy="{8 + i * 8}" r="1.8" '
                f'fill="{p["good"]}"/>'
                for i in range(3)))
    s["preferences-system-splash"] = (
        z.monitor() +
        f'<circle cx="16" cy="14" r="4" fill="{p["gold"]}" '
        f'stroke="{p["line"]}" stroke-width="1.2"/>')

    # Where Plasma requests longer names, a link is enough - see the
    # EXTRA_NAMES table further down. Here only those that mean the same
    # thing as an icon already drawn.
    s["preferences-system-windows-actions"] = s["preferences-system-windows"]
    s["preferences-system-tabbox"] = s["preferences-system-windows"]

    # ── The application launcher ───────────────────────────────────────
    #
    # "start-here" used to point to applications-system - the same cog
    # wheel as System Settings. So the panel had two identical icons side
    # by side, and the launcher, the most frequently clicked element of
    # all, could not be found at a glance.
    #
    # Instead a mullioned window: outer frame, cross bars, and in each of
    # the four panes a title bar of its own - four small windows in one
    # big one. That says "all programs" without resorting to someone
    # else's logo, and stays readable as a window cross down to 16 px.
    def _pane(fx, fy, fb, fh):
        # Title bar on top, pane below. Two rectangles instead of one
        # with a border: otherwise bar and border merge at 16 px.
        return (f'<rect x="{fx}" y="{fy}" width="{fb}" height="{fh}" '
                f'fill="{p["paper"]}"/>'
                f'<rect x="{fx}" y="{fy}" width="{fb}" height="3" '
                f'fill="{p["accent"]}"/>')

    s["start-here"] = (
        # Frame and surface of the big window
        z.box(3, 3, 26, 26, p["surface"]) +
        # The four panes
        _pane(6, 6, 9, 9) + _pane(17, 6, 9, 9) +
        _pane(6, 17, 9, 9) + _pane(17, 17, 9, 9) +
        # The cross bars last, so they lie on top of the panes
        f'<line x1="16" y1="4" x2="16" y2="28" stroke="{p["line"]}" '
        f'stroke-width="2"/>'
        f'<line x1="4" y1="16" x2="28" y2="16" stroke="{p["line"]}" '
        f'stroke-width="2"/>')
    s["applications-other"] = (
        z.box(3, 5, 26, 22, p["surface"]) +
        z.box(3, 5, 26, 5, p["accent"]) +
        "".join(f'<rect x="{7+i*7}" y="14" width="5" height="5" '
                f'fill="{p["accent"]}"/>' for i in range(3)))
    s["applications-internet"] = (
        f'<circle cx="16" cy="16" r="12" fill="{p["glass"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>'
        f'<ellipse cx="16" cy="16" rx="5" ry="12" fill="none" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>'
        f'<line x1="4" y1="16" x2="28" y2="16" stroke="{p["line"]}" '
        f'stroke-width="1.5"/>'
        f'<path d="M6,9 a20,20 0 0 0 20,0 M6,23 a20,20 0 0 1 20,0" '
        f'fill="none" stroke="{p["line"]}" stroke-width="1.2"/>')
    s["applications-multimedia"] = z.disc() + (
        f'<polygon points="13,11 13,21 22,16" fill="{p["line"]}"/>')
    s["applications-development"] = (
        z.box(3, 6, 26, 20, p["paper"]) +
        f'<text x="16" y="21" text-anchor="middle" font-family="monospace" '
        f'font-size="13" font-weight="bold" fill="{p["accent"]}">&lt;/&gt;</text>')
    s["system-users"] = z.person(cx=11, s=0.85, colour=p["metal_mid"]) + \
        z.person(cx=20, s=0.85)
    s["system-search"] = z.magnifier()
    s["help-browser"] = z.circle_glyph("?", p["accent"])
    s["help-contents"] = z.circle_glyph("?", p["accent"])
    s["office-calendar"] = (
        z.box(3, 6, 26, 23, p["paper"]) +
        z.box(3, 6, 26, 7, p["red"]) +
        "".join(f'<rect x="{7+col*7}" y="{17+row*6}" width="4" height="4" '
                f'fill="{p["metal_dark"]}"/>'
                for row in range(2) for col in range(3)))
    s["preferences-desktop-screensaver"] = z.monitor(glass=p["line"]) + (
        f'<circle cx="12" cy="13" r="1.5" fill="{p["folder_light"]}"/>'
        f'<circle cx="20" cy="17" r="1.5" fill="{p["folder_light"]}"/>')
    s["preferences-desktop-wallpaper"] = z.monitor(glass=p["good"]) + (
        f'<circle cx="21" cy="12" r="2.5" fill="{p["folder_light"]}"/>')
    s["preferences-desktop-theme"] = z.monitor() + (
        f'<path d="M6,21 l6,-8 5,5 4,-4 5,7 z" fill="{p["accent"]}"/>')
    s["preferences-desktop-display"] = z.monitor()
    s["preferences-desktop-font"] = (
        z.box(4, 4, 24, 24, p["paper"]) +
        f'<text x="16" y="24" text-anchor="middle" font-family="serif" '
        f'font-size="22" fill="{p["line"]}">A</text>')
    s["preferences-desktop-accessibility"] = (
        f'<circle cx="16" cy="16" r="12" fill="{p["accent"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5"/>'
        f'<circle cx="16" cy="8" r="2.5" fill="{p["paper"]}"/>'
        f'<path d="M9,13 h14 M16,13 v7 l-4,7 M16,20 l4,7" fill="none" '
        f'stroke="{p["paper"]}" stroke-width="2.2" stroke-linecap="round"/>')

    # ── File types ─────────────────────────────────────────────────────
    s["text-x-generic"] = z.sheet() + z.lines(n=4)
    s["text-x-preview"] = s["text-x-generic"]
    s["application-x-generic"] = z.sheet()
    s["application-x-executable"] = z.sheet() + z.badge(
        s["applications-system"], mx=21, my=22, r=7)
    s["application-x-archive"] = (
        z.box(4, 7, 24, 21, p["folder_mid"]) +
        z.box(4, 4, 24, 5, p["folder_dark"]) +
        z.box(13, 11, 6, 6, p["metal_light"]))
    s["audio-x-generic"] = z.sheet() + z.badge(
        f'<path d="M12,24 v-16 l12,-3 v16" fill="none" stroke="{p["line"]}" '
        f'stroke-width="4"/><circle cx="9" cy="24" r="5" '
        f'fill="{p["line"]}"/><circle cx="21" cy="21" r="5" '
        f'fill="{p["line"]}"/>', mx=21, my=22, r=7)
    s["video-x-generic"] = z.sheet() + z.badge(
        f'<polygon points="10,8 10,24 24,16" fill="{p["line"]}"/>',
        mx=21, my=22, r=7)
    s["image-x-generic"] = (
        z.box(3, 6, 26, 20, p["paper"]) +
        f'<circle cx="10" cy="13" r="3" fill="{p["folder_mid"]}"/>'
        f'<polygon points="5,25 14,14 21,25" fill="{p["green"]}"/>'
        f'<polygon points="17,25 23,17 28,25" fill="{p["accent"]}"/>')
    s["font-x-generic"] = s["preferences-desktop-font"]
    s["x-office-document"] = z.sheet() + z.lines(n=4)
    s["x-office-presentation"] = (
        z.box(4, 5, 24, 17, p["paper"]) +
        f'<polygon points="8,18 14,11 18,15 24,9 24,18" fill="{p["accent"]}"/>'
        f'<line x1="16" y1="22" x2="16" y2="27" stroke="{p["line"]}" '
        f'stroke-width="2"/>'
        f'<line x1="9" y1="28" x2="23" y2="28" stroke="{p["line"]}" '
        f'stroke-width="2"/>')

    # ── Status ─────────────────────────────────────────────────────────
    s["dialog-error"] = z.circle_glyph("!", p["red"])
    s["dialog-warning"] = (
        f'<polygon points="16,3 30,28 2,28" fill="{p["warn"]}" '
        f'stroke="{p["line"]}" stroke-width="1.5" stroke-linejoin="round"/>'
        f'<text x="16" y="26" text-anchor="middle" font-family="sans-serif" '
        f'font-size="17" font-weight="bold" fill="{p["line"]}">!</text>')
    s["dialog-information"] = z.circle_glyph("i", p["accent"])
    s["dialog-question"] = z.circle_glyph("?", p["accent"])

    return s


# Additional names that point to an existing icon.
#
# Without inode-directory PCManFM-Qt shows the Breeze icon for ordinary
# folders - right in between our own. The name is the MIME type of a
# directory and is requested more often than "folder" itself.
EXTRA_NAMES = {
    "inode-directory":        "folder",
    "folder-blue":            "folder",
    "folder-orange":          "folder",
    # Two or three names are in circulation for the same thing - Breeze
    # also maps them to one image. Drawing it once is enough, otherwise
    # you maintain the same icon three times.
    "folder-downloads":       "folder-download",
    "folder-text":            "folder-documents",
    "folder-txt":             "folder-documents",
    "folder-image":           "folder-pictures",
    "folder-images":          "folder-pictures",
    # Otherwise folder-image catches folder-image-people without serving
    # it - the folder with photos of people is a pictures folder,
    # so it gets the same image instead of half a match.
    "folder-image-people":    "folder-pictures",
    "folder-picture":         "folder-pictures",
    "folder-sound":           "folder-music",
    "folder-video":           "folder-videos",
    "folder-public":          "folder-publicshare",
    "unknown":                "application-x-generic",
    "application-octet-stream": "application-x-generic",
    "text-plain":             "text-x-generic",
    "text-x-script":          "text-x-generic",
    "text-x-python":          "text-x-generic",
    "text-x-python3":         "text-x-generic",
    "text-html":              "text-x-generic",
    "application-pdf":        "x-office-document",
    "application-zip":        "application-x-archive",
    "application-x-tar":      "application-x-archive",
    "application-x-gzip":     "application-x-archive",
    "package-x-generic":      "application-x-archive",
    "audio-mpeg":             "audio-x-generic",
    # So that the audio- class is complete and audio-x-generic no longer
    # catches anything that is not a file type - see
    # tools/check-symbolic-trap.py.
    "audio-speakers":         "audio-volume-high",
    "audio-on":               "audio-volume-high",
    "audio-ready":            "audio-volume-high",
    "audio-off":              "audio-volume-muted",
    "audio-volume-high-danger":  "audio-volume-muted",
    "audio-volume-high-warning": "audio-volume-medium",
    "video-mp4":              "video-x-generic",
    "image-png":              "image-x-generic",
    "image-jpeg":             "image-x-generic",
    "user-desktop":           "video-display",
    # The "System Settings" menu entry requests this name and used to
    # get the Breeze icon - checked with kiconfinder6.
    # Next to our cog wheel that stood out.
    "systemsettings":         "applications-system",
    # The network sub-items all mean the same image. Without these
    # links preferences-system catches them and they would get the cog
    # wheel again - exactly what was reported.
    "preferences-system-network-connection": "preferences-system-network",
    "preferences-system-network-proxy":      "preferences-system-network",
    "preferences-system-network-remote":     "preferences-system-network",
    "user-trash-symbolic":    "user-trash",
    "emblem-favorite":        "folder-favorites",
    # Kickoff and its siblings ask for the launcher icon under several
    # names - depending on Plasma version and distribution. If one of
    # them is missing, the panel shows the fallback's cog wheel again.
    "start-here-kde":         "start-here",
    "start-here-kde-plasma":  "start-here",
    "start-here-kde-symbolic": "start-here",
    "distributor-logo":       "start-here",
    "system-file-manager":    "folder-open",
    "system-run":             "application-x-executable",
    "utilities-terminal":     "applications-development",
}


# Directory name -> Context value of the index.theme.
#
# The two do NOT match throughout, and a simple capitalize() produces
# two values that violate the specification: apps becomes "Apps"
# instead of "Applications", mimetypes "Mimetypes" instead of
# "MimeTypes" - with a capital T. Checked against Breeze
# (/usr/share/icons/breeze/index.theme): there the directories are
# called apps/ and mimetypes/, but the contexts Applications and MimeTypes.
#
# According to the Icon Theme Specification only these are valid:
# Actions, Animations, Applications, Categories, Devices, Emblems,
# Emotes, International, MimeTypes, Places, Status.
CONTEXT_NAME = {
    "actions":   "Actions",
    "apps":      "Applications",
    "devices":   "Devices",
    "mimetypes": "MimeTypes",
    "places":    "Places",
    "status":    "Status",
    "emblems":   "Emblems",
    "categories": "Categories",
}


def index_theme(theme: Path, name="NT Legacy Icons"):
    """Writes the index.theme. Without it the directory is not a theme."""
    contexts = sorted(d.name for d in theme.iterdir() if d.is_dir())
    directories = [f"{k}/{g}" for k in contexts for g in SIZES
                     if (theme / k / str(g)).is_dir()]
    directories += [f"{k}/scalable" for k in contexts
                      if (theme / k / "scalable").is_dir()]
    lines = ["[Icon Theme]",
              f"Name={name}",
              "Comment=Icons in the style of Windows NT 4.0, fully generated",
              # Breeze as the fallback level: whatever is missing ends up
              # there anyway - this way it is at least stated explicitly.
              "Inherits=breeze,hicolor",
              # Without this line KIconLoader does not recolour the
              # inherited Breeze icons. For that it asks the ACTIVE theme
              # (kiconloader.cpp: q->theme()->followsColorScheme()), not
              # the one in which it found the file - Breeze itself carries
              # the flag, but that does not help here. The icons then keep
              # their fixed colour: #232629 from breeze, white from
              # breeze-dark. If the wrong set is in kdeglobals, the system
              # tray section is unreadable (issue 1: white icons on the
              # light panel). Reproduced in the VM and fixed with this
              # line. Our own icons are not affected, they carry no
              # "current-color-scheme" stylesheet.
              "FollowsColorScheme=true",
              f"Directories={','.join(directories)}", ""]
    unknown = []
    for v in directories:
        context, size = v.split("/")
        ctx = CONTEXT_NAME.get(context)
        if ctx is None:
            unknown.append(context)
            ctx = context.capitalize()
        if size == "scalable":
            lines += [f"[{v}]", f"Size={SCALABLE_FROM}", f"Context={ctx}",
                       "Type=Scalable", f"MinSize={SCALABLE_FROM}",
                       f"MaxSize={SCALABLE_TO}", ""]
        else:
            lines += [f"[{v}]", f"Size={size}", f"Context={ctx}",
                       "Type=Fixed", ""]
    (theme / "index.theme").write_text("\n".join(lines))
    if unknown:
        print(f"  WARNING: unknown context {sorted(set(unknown))} - "
              f"please add it to CONTEXT_NAME")
    return len(directories)


def extra_names(theme: Path):
    """Creates the extra names as links - in the same size and
    the same context as the source."""
    created = 0
    for target, source in EXTRA_NAMES.items():
        # The vector version too: an extra name that only exists as a
        # bitmap would be the pixelated case again above 48 px.
        for suffix in (".png", ".svg"):
            for q in theme.rglob(f"{source}{suffix}"):
                z = q.with_name(f"{target}{suffix}")
                if z.exists() or z.is_symlink():
                    continue
                z.symlink_to(q.name)
                created += 1
    return created


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path)
    ap.add_argument("--palette", default="teal", choices=sorted(PALETTES))
    ap.add_argument("--context", default="actions")
    args = ap.parse_args()

    z = Painter(PALETTES[args.palette])

    # Context per icon. Freedesktop looks up by context, and an icon in
    # the wrong directory is simply not found.
    CONTEXT = {}
    for n in icons(z):
        CONTEXT[n] = args.context
    sh = shell_icons(z)
    for n in sh:
        if n.startswith(("folder", "user-", "computer", "network")):
            CONTEXT[n] = "places"
        elif n.startswith(("drive", "media", "printer", "scanner", "camera",
                           "input-", "audio-input", "pda", "phone",
                           "video-display")):
            CONTEXT[n] = "devices"
        elif n.startswith(("text-", "application-x", "audio-x", "video-x",
                           "image-x", "font-x", "x-office")):
            CONTEXT[n] = "mimetypes"
        elif n.startswith("dialog-"):
            CONTEXT[n] = "status"
        else:
            CONTEXT[n] = "apps"
    # computer-laptop and video-display are devices, not places
    CONTEXT["computer-laptop"] = "devices"
    CONTEXT["video-display"] = "devices"
    CONTEXT["network-offline"] = "status"
    # Volume is a status, not a device - Breeze also puts it under
    # status/. In the devices context the panel would not find it.
    for _n in ("audio-volume-high", "audio-volume-medium",
               "audio-volume-low", "audio-volume-muted"):
        CONTEXT[_n] = "status"
    # The playback devices, on the other hand, are - that is where Breeze has them too.
    for _n in ("audio-card", "audio-headphones", "audio-headset"):
        CONTEXT[_n] = "devices"

    all_icons = dict(icons(z))
    all_icons.update(sh)
    written = 0

    for name, content in all_icons.items():
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="32" '
               f'height="32" viewBox="0 0 32 32">\n'
               f'  <!-- Generated by tools/gen-icons.py -->\n'
               f'  {content}\n</svg>\n')
        for g in SIZES:
            target = args.theme / CONTEXT[name] / str(g) / f"{name}.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            # If a link from an earlier run sits at the target, magick
            # writes THROUGH it - and damages the file it points to.
            # That is exactly how a newly drawn start-here overwrote the
            # cog wheel of applications-system, which it had previously
            # linked to itself. The link has to go before a real icon
            # is created here.
            if target.is_symlink():
                target.unlink()
            tmp = target.with_suffix(".svg")
            tmp.write_text(svg)
            try:
                subprocess.run(
                    ["magick", "-background", "none", "-density",
                     str(int(g * 96 / 32)), str(tmp), "-resize", f"{g}x{g}",
                     str(target)], check=True, capture_output=True)
                written += 1
            except subprocess.CalledProcessError as e:
                print(f"  {name} {g}px: {e.stderr.decode()[:80]}")
            finally:
                tmp.unlink(missing_ok=True)

        # The same source once more, unchanged, for everything above
        # 48 px. No second drawing, no second palette - what Dolphin
        # shows large is character for character the same image as the
        # 16 one, just without rasterisation.
        vector = args.theme / CONTEXT[name] / "scalable" / f"{name}.svg"
        vector.parent.mkdir(parents=True, exist_ok=True)
        if vector.is_symlink():
            vector.unlink()
        vector.write_text(svg)
        written += 1

    links = extra_names(args.theme)
    dirs = index_theme(args.theme)
    print(f"  {len(all_icons)} icons, {written} files, "
          f"{links} extra names ({args.palette}) to {args.theme}/")
    print(f"  index.theme with {dirs} directories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
