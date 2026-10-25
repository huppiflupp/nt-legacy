#!/usr/bin/env python3
"""Generates Plasma style SVGs from parameters instead of by hand.

A Plasma SVG is not a drawing but an atlas: all states of a widget sit
side by side in the same coordinate space, and Plasma cuts them out by
element ID. A button quickly needs 40 precisely named objects - and
Plasma silently ignores a typo in an ID.

This script does exactly that drudgery. What is left is the design:
colours, border width, gradient, rounding - as parameters.

    ./gen-plasma-svg.py button                      # one file to stdout
    ./gen-plasma-svg.py --all -o desktoptheme/mytheme/
    ./gen-plasma-svg.py button --style flat --border 1 --radius 3
    ./gen-plasma-svg.py --list

The classic Mac OS 9 look is the default: 3D border (light at the
top/left, dark at the bottom/right), a slight gradient, hardly any rounding.
"""

import argparse
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Widget definitions
#
# Which state prefixes a widget needs and which hints go with them.
# Derived from the Breeze source tree, not guessed.
# --------------------------------------------------------------------------

# On the missing "shadow" prefix:
#
# Breeze draws a soft, semi-transparent gradient under shadow-*. If a
# generator puts the same solid surface with a 3D edge there as for the
# normal state, Plasma paints it offset under the element - and you see
# the edge twice. On the panel this was a clearly visible double line.
#
# A flat NT theme needs no shadow anyway: the taskbar, popups and
# buttons sat there without a drop shadow. If the prefix is missing,
# Plasma simply draws nothing in that spot - which is the desired result
# here, not a shortcoming.
#
# "" means: elements without a prefix (center, top, left ...)
WIDGETS = {
    "button": {
        "description": "Buttons in plasmoids",
        "prefixes": ["normal", "hover", "pressed", "focus",
                     "toolbutton-hover", "toolbutton-pressed", "toolbutton-focus"],
        "hints": ["margin", "compose-over-border"],
        "masks": ["normal"],
    },
    "background": {
        "description": "Background of plasmoids",
        "prefixes": ["",],
        "hints": ["margin", "inset"],
        "masks": [""],
    },
    "panel-background": {
        "color": "panel",
        "fixed": True,
        # No dark outer border. Measured on an NT 4.0 screenshot: the
        # taskbar has exactly ONE line at its top edge, 1px white
        # (255,255,255), with the base surface (192,192,192) directly above
        # and below it. Outer border plus 3D edge would make two lines.
        "outer_border": 0,
        "description": "Panel / taskbar",
        "prefixes": ["", "thick", "north", "south", "east", "west",],
        "hints": ["margin", "inset", "tile-center"],
        "masks": [""],
    },
    "background-dialog": {
        "description": "Background of all Plasma popups (application launcher, "
                       "notifications). If it is missing, Plasma uses the "
                       "translucent Breeze background.",
        # Plasma looks for dialogs/background.svg. If the file were named
        # after the widget key, it would never be found - and the launcher
        # would stay see-through even though the file exists.
        "file": "background",
        "folder": "dialogs",
        "prefixes": ["",],
        "hints": ["margin", "inset", "preferred-icon-size"],
        "masks": [""],
    },
    "tooltip": {
        "description": "Tooltips",
        "prefixes": ["",],
        "hints": ["margin"],
        "masks": [""],
    },
    "frame": {
        "corner": 3,
        "description": "Frames, groupings",
        "prefixes": ["", "raised", "sunken", "plain"],
        "hints": ["margin"],
        "masks": [],
        # The "plain" prefix is the SIDEBAR of the application menu.
        #
        # Not obvious, but looked up: kicker draws it as a
        # KSvg.FrameSvgItem with imagePath "widgets/frame" and prefix
        # "plain" (plasma-desktop, applets/kicker/MenuRepresentation.qml,
        # the block with id: sideBar). That makes the sidebar colourable
        # through the Plasma style - without touching the applet, which
        # has shipped compiled since Plasma 6.4 and no longer has any QML
        # files on disk.
        #
        # It gets the PANEL colour - the same as the taskbar the menu
        # opens from. Without a colour the sidebar disappears into the
        # menu surface, and the logout buttons in it look as if they
        # belonged to the list of entries.
        #
        # The title bar colour would be the more obvious choice - that is
        # where Windows 95 to 2000 had the dark bar with the vertical
        # lettering. Checked on the running desktop and rejected again:
        # the three session buttons at the bottom of the sidebar (Log Out,
        # Restart, Shut Down) are monochrome icons that Kirigami tints in
        # the TEXT colour of the colour scheme. On #176b78 they showed up
        # as dark grey on dark petrol - the sidebar was colourful and the
        # buttons in it unreadable. Nothing can be changed about that from
        # outside: the icon colour depends on the dialog's colour set, not
        # on the SVG.
        #
        # Without a colour scheme class, i.e. fixed like the panel: the
        # classes that KSvg replaces know no panel colour. With
        # ColorScheme-Highlight the sidebar would carry the selection
        # colour - a garish stripe in the night variants.
        #
        # Checked what else this affects: apart from kicker, only
        # PlasmaComponents3.Frame and .GroupBox request this prefix (per
        # strings in liborg_kde_plasmacomponents3.so). On this
        # installation not a single plasmoid uses them - measured
        # across all .so files in plasma/applets and plasma/private.
        "states": {
            "plain": ("panel", False, None),
        },
    },
    "listitem": {
        "corner": 2,
        "description": "List entries, e.g. in the application launcher",
        "prefixes": ["normal", "hover", "pressed", "selected", "selected+hover"],
        "hints": ["margin"],
        "masks": [],
    },
    "viewitem": {
        "description": "Entries in views",
        "prefixes": ["normal", "hover", "selected", "selected+hover"],
        "hints": ["margin"],
        "masks": [],
    },
    "lineedit": {
        "description": "Input fields",
        "prefixes": ["base", "focus", "hover"],
        "hints": ["margin", "focus-over-base"],
        "masks": [],
    },
    "tasks": {
        "description": "Window buttons in the taskbar",
        # Requested by org.kde.plasma.taskmanager.so (verified with
        # strings). Without this file the central part of the taskbar
        # comes from Breeze - rounded corners in the middle of the NT panel.
        # Four states per panel edge - the task manager picks by panel
        # position, as with panel-background.
        "prefixes": [s for s in ["normal", "focus", "hover", "attention",
                                 "minimized", "progress"]]
                    + [f"{e}-{s}" for e in ("north", "west", "east")
                       for s in ("normal", "focus", "hover", "attention",
                                 "minimized", "progress")],
        "hints": ["margin"],
        "masks": [],
        "margin": 4,
        # The active window button carries the title bar colour - and on
        # it the window title sits in the normal text colour, because the
        # task manager draws the text from the colour scheme, not from
        # the SVG. Measured: 1.47:1 for win2k, 1.31:1 for win98, below
        # 4.5:1 in all ten variants. The community reported exactly that
        # back ("way too dark, text unreadable").
        #
        # Hence, as in Windows itself: the active button is not a
        # coloured field but a pressed-in button in the surface colour.
        # The text then sits on the same ground as everywhere else -
        # readable in every variant and every colour scheme.
        "states": {
            "focus":       ("surface", True, "ColorScheme-Background"),
            "north-focus": ("surface", True, "ColorScheme-Background"),
            "west-focus":  ("surface", True, "ColorScheme-Background"),
            "east-focus":  ("surface", True, "ColorScheme-Background"),
        },
    },
    "toolbar": {
        "color": "panel",
        "fixed": True,
        "description": "Toolbars",
        "prefixes": ["", "north", "south", "east", "west"],
        "hints": ["margin"],
        "masks": [],
    },
    "plasmoidheading": {
        "description": "Headers in plasmoids",
        "prefixes": ["header", "footer"],
        "hints": ["margin"],
        "masks": [],
    },
    "scrollbar": {
        "description": "Scrollbars",
        # ScrollBar.qml chooses between "slider" and "mouseover-slider".
        # With slider-vertical/-horizontal it finds nothing, falls back to
        # the empty prefix - and that has no center. The result was an
        # invisible handle in every Plasma scrollbar.
        "prefixes": ["background-vertical", "background-horizontal",
                     "slider", "mouseover-slider"],
        "hints": ["scrollbar-size"],
        "masks": [],
        "corner": 3,
        # The groove gets the checkerboard pattern Windows had there: a
        # checkerboard of button grey and white, each cell one pixel.
        # The Qt style draws it in applications on its own - but in
        # Plasma surfaces such as System Settings the scrollbar comes from
        # this SVG, and there it was missing. Reported by the community.
        #
        # Only the groove, not the handle: in Windows the handle is a
        # smooth button, and the pattern is exactly what sets it apart
        # from the groove.
        "dither": ("background-vertical", "background-horizontal"),
        # Without this hint Plasma stretches the middle part, and the
        # checkerboard would turn into stripes. With it, it tiles - Breeze
        # does the same in the same file.
        "tile_center": True,
    },
    "switch": {
        "description": "Switches (system tray, notifications)",
        # Only left/right - a switch is a horizontal 3-patch.
        "prefixes": ["inactive", "active"],
        "hints": [],
        "masks": [],
        "shapes": {
            "handle":         ("circle", "surface"),
            "handle-hover":   ("circle", "hover"),
            "handle-pressed": ("circle", "dark"),
            "handle-focus":   ("circle", "active"),
        },
    },
    "tabbar": {
        "description": "Tabs",
        "prefixes": ["north-active-tab", "south-active-tab",
                     "east-active-tab", "west-active-tab"],
        "hints": ["margin"],
        "masks": [],
        # Only the border, no surface. This is not a matter of taste:
        # Plasma lays this FrameSvg OVER the content of an active panel
        # widget. An opaque surface swallows its icon - with "Peek at
        # Desktop" an empty square was left behind, which the community
        # reported as a missing texture. Narrowed down to this file by
        # bisection: take it away and the icon is back.
        #
        # Breeze solves the same problem with opacity:0.01 on all nine
        # fields, so it draws nothing there at all. We keep the 3D
        # border - it marks the pressed button as in Windows - and only
        # leave out the surface.
        "frame_only": True,
    },
    "bar_meter_horizontal": {
        "corner": 3,
        "description": "Progress and level bars",
        "prefixes": ["bar-inactive", "bar-active"],
        "hints": ["margin"],
        "masks": [],
    },
    "containment-controls": {
        "description": "Tools in panel edit mode",
        "prefixes": ["north", "south", "east", "west"],
        "hints": [],
        "masks": [],
    },
    "translucentbackground": {
        "description": "Widget in edit mode",
        "prefixes": ["",],
        "hints": ["margin"],
        "masks": [],
    },
    "slider": {
        "description": "Sliders",
        # The handle comes from actionbutton.svg - Breeze does the
        # same. Here there is only the groove plus the size hint.
        "prefixes": ["groove", "groove-highlight"],
        "hints": ["handle-size"],
        "masks": [],
        "corner": 3,
    },
}

# Widgets that are not frames but single shapes: checkmarks, arrows,
# lines. They have no 9-patch grid - Plasma cuts them out by
# individual IDs. The guide calls this the class where a generator
# reaches its limit; the shapes are therefore written out here instead
# of computed.
SHAPE_WIDGETS = {
    "line": {
        "description": "Separator lines in lists and in the application launcher",
        "shapes": {
            "horizontal-line": ("hline", "dark"),
            "vertical-line":   ("vline", "dark"),
        },
    },
    "checkmarks": {
        "description": "Checkmarks in checkboxes",
        "shapes": {
            "checkbox":    ("check", "text"),
            "radiobutton": ("dot", "text"),
        },
    },
    "radiobutton": {
        "description": "Radio buttons",
        "shapes": {
            "normal":  ("ring", "surface"),
            "hover":   ("ring", "hover"),
            "focus":   ("ring", "active"),
            "checked": ("dot", "text"),
            "shadow":  ("ring", "dark"),
        },
    },
    "arrows": {
        "description": "Arrows in drop-down menus and scrollbars",
        "shapes": {
            "up-arrow":    ("triangle-u", "text"),
            "down-arrow":  ("triangle-d", "text"),
            "left-arrow":  ("triangle-l", "text"),
            "right-arrow": ("triangle-r", "text"),
        },
    },
    "busywidget": {
        "description": "Busy indicator",
        "shapes": {
            "busywidget":       ("ring", "active"),
            "16-16-busywidget": ("ring", "active"),
            "22-22-busywidget": ("ring", "active"),
        },
    },
    "actionbutton": {
        "description": "Round buttons",
        # In addition to the sized ones, the bare names:
        # RoundButton.qml and the slider handle request "normal",
        # "hover", "pressed", "focus" without a prefix.
        "shapes": {**{f"{g}-{g}-{s}": ("circle", c)
                      for g in (16, 22, 24, 32)
                      for s, c in [("normal", "surface"), ("hover", "hover"),
                                   ("pressed", "dark"), ("focus", "active")]},
                   **{s: ("circle", c)
                      for s, c in [("normal", "surface"), ("hover", "hover"),
                                   ("pressed", "dark"), ("focus", "active")]}},
    },
    "action-overlays": {
        "description": "Overlays in the folder view",
        "shapes": {f"add-{s}": ("plus", c)
                   for s, c in [("normal", "text"), ("hover", "hover"),
                                ("pressed", "dark")]},
    },
}

# Elements of a complete 9-patch, in drawing order:
# first the surface, then the edges, so that the edges lie on top.
CORNERS = ["topleft", "topright", "bottomleft", "bottomright"]
EDGES   = ["top", "bottom", "left", "right"]

# --------------------------------------------------------------------------
# Palettes
# --------------------------------------------------------------------------

PALETTES = {
    # Mac OS 9 Platinum: warm grey, hard 3D edges, hardly any rounding
    "platinum": {
        "surface":   "#dddad2",
        "light":      "#ffffff",   # top/left
        "dark":    "#84817a",   # bottom/right
        "border":    "#000000",
        "active":     "#c8c4bc",
        "text":      "#000000",
    },
    "platinum-dark": {
        "surface":   "#2c2a28",
        "light":      "#565250",
        "dark":    "#000000",
        "border":    "#000000",
        "active":     "#3c3a38",
        "text":      "#e6e2dc",
    },
    "charcoal": {
        "surface":   "#3c3c3c",
        "light":      "#6a6a6a",
        "dark":    "#101010",
        "border":    "#000000",
        "active":     "#4c4c4c",
        "text":      "#dcdcdc",
    },
    # NT Legacy: Windows NT 4.0 colour world, petrol instead of navy blue.
    # Deliberately without black surfaces - only text, borders and the
    # active title bar go dark. That keeps the theme pleasant for long
    # sessions without losing its character.
    "nt-legacy": {
        "surface":   "#d8d8d0",   # main surface, light neutral grey
        "window":   "#f0f0e8",   # window content, almost cream white
        "panel":     "#b8c4c4",   # muted petrol grey
        "light":      "#f4f4ee",   # 3D edge top/left
        # The light dot in the scrollbar checkerboard. A value of its own,
        # not the light edge: it should be as light as possible, while the
        # edge deliberately stays muted. build.py replaces colours by
        # their hex value, so it must not coincide with any other value
        # in the palette - #fcfcfa instead of pure white.
        "checker":      "#fcfcfa",
        "dark":    "#8a8a82",   # 3D edge bottom/right
        "border":    "#202628",   # outer border, very dark blue grey
        # Must match BASE["selection"] in build.py. build.py recolours the
        # generated SVGs by replacing HEX VALUES - if a different one
        # stands here, it does not find it, and the selection bar in the
        # Plasma style stays in the base colour while the colour scheme
        # has long been showing another one.
        "active":     "#29818e",   # selection, petrol
        "aktiv_text": "#ffffff",
        "title_active":   "#176b78",
        "title_inactive": "#60777a",
        "text":      "#202628",
        "text2":     "#526166",   # secondary text
        "hover":     "#d6a23a",   # NT-like gold
        "warning":   "#c87922",
        "error":    "#a83232",
        "positive":   "#39734a",
        "desktop":   "#899a9a",
    },
}

# States that are coloured differently from the normal state.
# A button has to change visibly on hover and press - otherwise the
# theme feels "dead", even though everything is technically right.
# Per state: fallback colour, whether the 3D border is flipped, and the
# colour scheme class.
#
# The class is what matters. If every state carries the same one, they
# all look the same - then the selection bar is invisible, hover is dead
# and the progress bar shows no progress. The classes are the ones
# KSvg actually replaces (extracted from libKF6Svg); an invented name
# silently falls back to the fallback colour.
STATE_COLORS = {
    #                        fallback colour, flip bevel, colour scheme class
    "hover":                ("hover",  False, "ColorScheme-ButtonHover"),
    "toolbutton-hover":     ("hover",  False, "ColorScheme-ButtonHover"),
    "focus":                ("active",  False, "ColorScheme-ButtonFocus"),
    "toolbutton-focus":     ("active",  False, "ColorScheme-ButtonFocus"),
    "pressed":              ("dark", True,  "ColorScheme-Background"),
    "toolbutton-pressed":   ("dark", True,  "ColorScheme-Background"),
    "selected":             ("active",  False, "ColorScheme-Highlight"),
    "selected+hover":       ("active",  False, "ColorScheme-Highlight"),
    "active":               ("active",  False, "ColorScheme-Highlight"),
    "bar-active":           ("active",  False, "ColorScheme-Highlight"),
    "groove-highlight":     ("active",  False, "ColorScheme-Highlight"),
    "sunken":               ("dark", True,  "ColorScheme-Background"),
    "sunken-slider-vertical":   ("dark", True, "ColorScheme-Background"),
    "sunken-slider-horizontal": ("dark", True, "ColorScheme-Background"),
    "mouseover-slider":     ("hover",  False, "ColorScheme-ButtonHover"),
}

# Mapping colour class -> palette key, with a fallback chain.
# The first key present wins, so that simple palettes with few colours
# work just as well as detailed ones.
STYLESHEET_CLASSES = [
    ("ColorScheme-Text",             ["text"]),
    ("ColorScheme-Background",       ["surface"]),
    ("ColorScheme-Highlight",        ["active"]),
    ("ColorScheme-ViewText",         ["text"]),
    ("ColorScheme-ViewBackground",   ["window", "surface"]),
    ("ColorScheme-ViewHover",        ["hover", "active"]),
    ("ColorScheme-ViewFocus",        ["active"]),
    ("ColorScheme-ButtonText",       ["text"]),
    ("ColorScheme-ButtonBackground", ["surface"]),
    ("ColorScheme-ButtonHover",      ["hover", "active"]),
    ("ColorScheme-ButtonFocus",      ["active"]),
    ("ColorScheme-HighlightedText",  ["selection_text", "window"]),
    ("ColorScheme-ComplementaryBackground", ["panel", "surface"]),
    ("ColorScheme-NegativeText",     ["error", "text"]),
    ("ColorScheme-NeutralText",      ["warning", "text"]),
    ("ColorScheme-PositiveText",     ["positive", "text"]),
]


class Generator:
    def __init__(self, palette, border=1, radius=0, style="bevel",
                 cell=32, corner=6, gap=12, columns=4, outer_border=0):
        self.p = palette
        self.outer_border = outer_border
        self._outer_override = None
        self.border = border
        self.radius = radius
        self.style = style        # bevel | flat
        self.cell = cell          # edge length of one state set
        self.corner = corner      # size of the corner elements
        self.gap = gap            # space between the sets in the atlas
        self.columns = columns
        self.parts = []

    def color(self, *keys):
        """First colour present in the fallback chain."""
        for k in keys:
            if k in self.p:
                return self.p[k]
        return "#000000"

    # -- Building blocks ---------------------------------------------------

    def _rect(self, eid, x, y, w, h, fill, cls=None, rx=0, extra=""):
        # Leave out zero-area rects - they would only keep the linter busy
        if w <= 0 or h <= 0:
            return
        k = f' class="{cls}"' if cls else ""
        r = f' rx="{rx}" ry="{rx}"' if rx else ""
        color = 'currentColor' if cls else fill
        self.parts.append(
            f'    <rect id="{eid}" x="{x:g}" y="{y:g}" '
            f'width="{w:g}" height="{h:g}"{r}{k} fill="{color}"{extra}/>'
        )

    def _hint(self, eid, x, y, w, h, color="#ff00ff"):
        """Hints are markers, not graphics. Breeze draws them in magenta
        and makes them invisible - Plasma only reads their geometry."""
        self.parts.append(
            f'    <rect id="{eid}" x="{x:g}" y="{y:g}" '
            f'width="{w:g}" height="{h:g}" fill="{color}" opacity="0"/>'
        )

    def _nine_patch(self, prefix, ox, oy, surface_key="surface",
                    inverted=False, cls="ColorScheme-Background",
                    frame_only=False, dither=False):
        """Generates a complete 9-patch set at position (ox, oy).

        A 9-patch divides the surface completely: all nine fields are as
        wide or as tall as the corners. Borders are drawn INSIDE the
        respective field, not in place of the surface - otherwise a gap
        would open between corner and edge.

        Up to two lines lie on top of each other along each outer edge:
        outside the dark border (NT/Win95), inside it the 3D edge.

        inverted flips the 3D border - a raised button becomes a
        pressed-in one.
        """
        def n(part):
            return f"{prefix}-{part}" if prefix else part

        z, e, b = self.cell, self.corner, self.border
        # A widget can switch off the outer border - the panel does
        # that, because NT's taskbar has only a single light line.
        a = (self._outer_override if self._outer_override is not None
             else self.outer_border)
        surface = self.p[surface_key]
        light = self.p["dark" if inverted else "light"]
        dark = self.p["light" if inverted else "dark"]
        border_color = self.p.get("border", "#000000")

        if self.style == "bevel":
            edge = {"t": light, "l": light, "b": dark, "r": dark}
        else:
            edge = {s: border_color for s in "tlbr"}

        m = z - 2 * e      # length of the middle fields
        r = z - e          # start of the right/bottom edge column

        #  field          x  y  w  h   which sides are outer edges
        fields = [
            ("topleft",     0, 0, e, e, "tl"),
            ("top",         e, 0, m, e, "t"),
            ("topright",    r, 0, e, e, "tr"),
            ("left",        0, e, e, m, "l"),
            ("center",      e, e, m, m, ""),
            ("right",       r, e, e, m, "r"),
            ("bottomleft",  0, r, e, e, "bl"),
            ("bottom",      e, r, m, e, "b"),
            ("bottomright", r, r, e, e, "br"),
        ]

        for part, fx, fy, fw, fh, sides in fields:
            if fw <= 0 or fh <= 0:
                continue
            x, y = ox + fx, oy + fy
            self.parts.append(f'    <g id="{n(part)}">')

            # Surface. Only it carries the colour scheme class - the edges
            # stay fixed, otherwise the direction of the light would change
            # with every colour scheme.
            # Only fill:currentColor plus class - NO inline color:.
            #
            # This used to also put color:<colour> in the style, on the
            # grounds that Breeze does that too. That was wrong:
            # of 42 Breeze widget SVGs exactly two have a real
            # inline color:, the rest rely on the class.
            # And an inline declaration beats every class rule in the CSS
            # cascade - KSvg's replacement of the
            # <style id="current-color-scheme"> block thus came to
            # nothing. The consequences were: no user accent colour and
            # no colour variants without duplicate SVGs.
            #
            # The fallback colour is still in the stylesheet block at the
            # top, so it applies as long as KSvg replaces nothing.
            if frame_only:
                # The surface stays invisible, but the rectangle is still
                # there. An empty <g> would have a bounding box of 0x0,
                # and KSvg computes the 9-patch field sizes from exactly
                # that - the border then scaled wrongly. Hence
                # opacity:0.01 instead of nothing, as Breeze does in the
                # same element too.
                self.parts.append(
                    f'      <rect x="{x:g}" y="{y:g}" width="{fw:g}" '
                    f'height="{fh:g}" fill="{surface}" opacity="0.01"/>')
            elif cls:
                # The fallback colour is in the style block at the top,
                # per class. So that the states also differ when KSvg
                # replaces nothing, every class gets its own value - see
                # stylesheet_for().
                self.parts.append(
                    f'      <rect x="{x:g}" y="{y:g}" width="{fw:g}" '
                    f'height="{fh:g}" class="{cls}" '
                    f'style="fill:currentColor;fill-opacity:1;stroke:none"/>')
            else:
                self.parts.append(
                    f'      <rect x="{x:g}" y="{y:g}" width="{fw:g}" '
                    f'height="{fh:g}" fill="{surface}"/>')

            # The checkerboard of the groove. Drawn as dashed lines, one
            # per pixel row, not as individual rectangles: a field of
            # 26x26 would otherwise have 338 rectangles, this way it is 26 lines.
            # An SVG <pattern> would be even shorter, but QtSvg does not
            # know patterns - it drops them without replacement.
            if dither and part == "center":
                # The checkerboard was first drawn in the 3D light edge
                # ("light"). In the night variants it was clearly
                # visible that way, in the light ones not - reported by the community.
                # Worked out: #f4f4ee on #d8d8d0 is 28 steps, i.e.
                # 13 percent above the ground. At night it is 32 steps on
                # a ground of 42 - 76 percent. The same absolute delta,
                # six times the perceived difference. Windows itself
                # was at 33 percent (white on #c0c0c0).
                #
                # Two changes bring the light variant there:
                # a palette value of its own for the checkerboard colour
                # instead of the light edge, and a slight darkening of the
                # groove. The darkening lies as a semi-transparent layer
                # over the surface, not as a fixed colour - so the groove
                # stays tied to the user's colour scheme.
                self.parts.append(
                    f'      <rect x="{x:g}" y="{y:g}" width="{fw:g}" '
                    f'height="{fh:g}" fill="#000000" opacity="0.07"/>')
                light_color = self.p.get("checker", self.p.get("light", "#ffffff"))
                for row in range(int(fh)):
                    offset = row % 2
                    # Half a step in y, none in x. That is not a cosmetic
                    # flaw but the difference between a pattern and a grey
                    # haze: the stroke width measures across the line,
                    # where y+0.5 centres on exactly one pixel row. The
                    # dash, by contrast, measures along it, and a start at
                    # x+0.5 puts each dot half on two columns. Rendered
                    # (QtSvg, with antialiasing) this came out at 227
                    # instead of 252 - the checkerboard washed out into a
                    # flat surface. With whole x values: 202/252 in a clean
                    # alternation, across the whole field.
                    self.parts.append(
                        f'      <line x1="{x + offset:g}" '
                        f'y1="{y + row + 0.5:g}" x2="{x + fw:g}" '
                        f'y2="{y + row + 0.5:g}" stroke="{light_color}" '
                        f'stroke-width="1" stroke-dasharray="1 1"/>')

            def line(side, width, color, offset):
                if width <= 0:
                    return
                # Take the corners into account: on a field that has two
                # outer edges, the line has to be indented by the other one
                # so that the two do not overlap.
                in_l = offset if "l" in sides else 0
                in_r = offset if "r" in sides else 0
                in_t = offset if "t" in sides else 0
                in_b = offset if "b" in sides else 0
                if side == "t":
                    self.parts.append(
                        f'      <rect x="{x + in_l:g}" y="{y + offset:g}" '
                        f'width="{fw - in_l - in_r:g}" height="{width:g}" fill="{color}"/>')
                elif side == "b":
                    self.parts.append(
                        f'      <rect x="{x + in_l:g}" y="{y + fh - offset - width:g}" '
                        f'width="{fw - in_l - in_r:g}" height="{width:g}" fill="{color}"/>')
                elif side == "l":
                    self.parts.append(
                        f'      <rect x="{x + offset:g}" y="{y + in_t:g}" '
                        f'width="{width:g}" height="{fh - in_t - in_b:g}" fill="{color}"/>')
                elif side == "r":
                    self.parts.append(
                        f'      <rect x="{x + fw - offset - width:g}" y="{y + in_t:g}" '
                        f'width="{width:g}" height="{fh - in_t - in_b:g}" fill="{color}"/>')

            for side in sides:
                line(side, a, border_color, 0)       # outside
                line(side, b, edge[side], a)         # 3D edge beneath

            self.parts.append('    </g>')

    def _hints(self, prefix, ox, oy, kinds):
        def n(part):
            return f"{prefix}-{part}" if prefix else part

        z, e, b = self.cell, self.corner, self.border
        # Padding. Our border is itself 2px (outer border + bevel) -
        # with margin=2 the text would start exactly at the first free
        # pixel and stick to the edge. Breeze uses 4 for frames and
        # panels, 6 for lists, buttons and input fields.
        pad = self._margin

        if "margin" in kinds:
            # Padding: how much room the content keeps from the edge
            self._hint(n("hint-top-margin"),    ox + z / 2, oy,            2, pad)
            self._hint(n("hint-bottom-margin"), ox + z / 2, oy + z - pad,  2, pad)
            self._hint(n("hint-left-margin"),   ox,         oy + z / 2,    pad, 2)
            self._hint(n("hint-right-margin"),  ox + z - pad, oy + z / 2,  pad, 2)

        if "inset" in kinds:
            # Insets separate the drawn surface from the claimed space -
            # needed for shadows and floating panels (Plasma 6).
            # Inset = 0, because we draw no shadow into the surface.
            # An inset of 1 would claim one pixel as "not drawn" -
            # visible as a dead edge around the panel and popups.
            # Breeze sets 1e-8 here (practically 0); only background.svg has
            # a real 8px, because a shadow lies there.
            iw = 0.00000001
            for side, (hx, hy) in {
                "top":    (ox + z / 4, oy),
                "bottom": (ox + z / 4, oy + z),
                "left":   (ox, oy + z / 4),
                "right":  (ox + z, oy + z / 4),
            }.items():
                self._hint(n(f"hint-{side}-inset"), hx, hy, iw, iw)

        if "tile-center" in kinds:
            self._hint(n("hint-tile-center"), ox + 1, oy + 1, 1, 1, "#00ff00")
        if "compose-over-border" in kinds:
            self._hint(n("hint-compose-over-border"), ox + 3, oy + 1, 1, 1, "#00ff00")
        if "scrollbar-size" in kinds:
            # Breeze: 6x6 - the width of the scrollbar
            self._hint(n("hint-scrollbar-size"), ox + 1, oy + 3, 6, 6, "#00ff00")
        if "handle-size" in kinds:
            # Breeze: 20x20 - the size of the slider handle
            self._hint(n("hint-handle-size"), ox + 1, oy + 3, 20, 20, "#00ff00")
        if "preferred-icon-size" in kinds:
            # The width of this marker carries the desired icon size in
            # pixels. 26 instead of the Plasma default (32) is about
            # 80 percent.
            self._hint(n("hint-preferred-icon-size"), ox + 7, oy + 1, 26, 1, "#00ff00")
        if "focus-over-base" in kinds:
            self._hint(n("hint-focus-over-base"), ox + 5, oy + 1, 1, 1, "#00ff00")

    def _shape(self, eid, kind, color, ox, oy, size):
        """Draws a single shape (checkmark, arrow, circle, line).

        Unlike with the 9-patch, Plasma cuts these elements out as a
        whole - they need no grid, only a unique ID.
        """
        m = size / 2
        d = size * 0.34        # half the edge length of the inner shape
        s = max(1.5, size * 0.12)

        self.parts.append(f'    <g id="{eid}">')
        if kind == "circle":
            self.parts.append(
                f'      <circle cx="{ox+m:g}" cy="{oy+m:g}" r="{d:g}" '
                f'fill="{color}" stroke="{self.p["border"]}" stroke-width="1"/>')
        elif kind == "ring":
            self.parts.append(
                f'      <circle cx="{ox+m:g}" cy="{oy+m:g}" r="{d:g}" '
                f'fill="none" stroke="{color}" stroke-width="{s:g}"/>')
        elif kind == "dot":
            self.parts.append(
                f'      <circle cx="{ox+m:g}" cy="{oy+m:g}" r="{d*0.5:g}" '
                f'fill="{color}"/>')
        elif kind == "check":
            # The classic checkmark: short downstroke, long upstroke
            self.parts.append(
                f'      <path d="M{ox+m-d:g},{oy+m:g} L{ox+m-d*0.3:g},{oy+m+d*0.7:g} '
                f'L{ox+m+d:g},{oy+m-d*0.7:g}" fill="none" stroke="{color}" '
                f'stroke-width="{s:g}" stroke-linecap="square"/>')
        elif kind == "plus":
            self.parts.append(
                f'      <path d="M{ox+m:g},{oy+m-d:g} V{oy+m+d:g} '
                f'M{ox+m-d:g},{oy+m:g} H{ox+m+d:g}" stroke="{color}" '
                f'stroke-width="{s:g}"/>')
        elif kind == "hline":
            self.parts.append(
                f'      <rect x="{ox:g}" y="{oy+m:g}" width="{size:g}" '
                f'height="1" fill="{color}"/>')
        elif kind == "vline":
            self.parts.append(
                f'      <rect x="{ox+m:g}" y="{oy:g}" width="1" '
                f'height="{size:g}" fill="{color}"/>')
        elif kind.startswith("triangle"):
            r = kind.split("-")[1]
            pts = {
                "u": f"{ox+m:g},{oy+m-d:g} {ox+m-d:g},{oy+m+d*0.6:g} {ox+m+d:g},{oy+m+d*0.6:g}",
                "d": f"{ox+m:g},{oy+m+d:g} {ox+m-d:g},{oy+m-d*0.6:g} {ox+m+d:g},{oy+m-d*0.6:g}",
                "l": f"{ox+m-d:g},{oy+m:g} {ox+m+d*0.6:g},{oy+m-d:g} {ox+m+d*0.6:g},{oy+m+d:g}",
                "r": f"{ox+m+d:g},{oy+m:g} {ox+m-d*0.6:g},{oy+m-d:g} {ox+m-d*0.6:g},{oy+m+d:g}",
            }[r]
            self.parts.append(f'      <polygon points="{pts}" fill="{color}"/>')
        self.parts.append('    </g>')

    # -- Assembly ----------------------------------------------------------

    def generate(self, name, spec):
        self.parts = []
        self._outer_override = spec.get("outer_border")
        # Corner size per widget: a 6px corner in a 6px tall progress
        # bar leaves nothing at the top and bottom, KSvg then squashes
        # the edges and the 1px lines smear.
        self._corner_original = self.corner
        self.corner = spec.get("corner", self.corner)
        self._margin = spec.get("margin", 4)
        prefixes = spec["prefixes"]
        masks = spec.get("masks", [])
        hints = spec.get("hints", [])

        sets = [(p, False) for p in prefixes] + [(f"mask-{m}" if m else "mask", True)
                                                 for m in masks]

        shapes = list(spec.get("shapes", {}).items())
        step = self.cell + self.gap
        total = len(sets) + len(shapes)
        columns = min(self.columns, max(1, total))
        rows = (total + columns - 1) // columns
        width = columns * step + self.gap
        height = rows * step + self.gap

        head = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width:g}" height="{height:g}" '
            f'viewBox="0 0 {width:g} {height:g}">',
            f'  <!-- {name}.svg — {spec["description"]} -->',
            '  <!-- Generated by tools/gen-plasma-svg.py. The element IDs are',
            '       the interface to Plasma: please do not rename them. -->',
            '  <defs>',
            '    <style id="current-color-scheme" type="text/css">',
        ]
        for cls, keys in STYLESHEET_CLASSES:
            f = self.color(*keys)
            # Include stop-color so that gradients get recoloured too
            head.append(f'      .{cls} {{ color:{f}; stop-color:{f}; }}')
        head += ['    </style>', '  </defs>']

        for i, (prefix, is_mask) in enumerate(sets):
            ox = self.gap + (i % columns) * step
            oy = self.gap + (i // columns) * step

            base = prefix[5:] if prefix.startswith("mask-") else prefix
            default = spec.get("color", "surface")
            # A widget may colour individual states differently from the
            # general table. The taskbar needs that: there the accent
            # colour of the focus state would be meant correctly, but the
            # window title on it would no longer be readable.
            color_key, inverted, state_class = spec.get(
                "states", {}).get(base) or STATE_COLORS.get(
                base, (default, False, "ColorScheme-Background"))
            # The panel gets its colour fixed, not through the colour
            # scheme. Reason: Plasma colours shell elements from the
            # Colors:Window group, not from Complementary - a panel that
            # is meant to stand out from the plasmoid surfaces cannot be
            # controlled separately that way. Measured: with the class the
            # panel became #d8d8d0 instead of #b8c4c4.
            class_here = None if spec.get("fixed") else state_class

            self.parts.append(f'  <!-- {prefix or "(default state)"} -->')
            if is_mask:
                # Masks only define the shape, not the appearance.
                # Hence white and without a colour scheme class.
                old_style, self.style = self.style, "flat"
                old_border = self.p["border"]
                self.p = dict(self.p, border="#ffffff")
                self._nine_patch(prefix, ox, oy, "surface", cls=None)
                self.p["border"] = old_border
                self.style = old_style
            else:
                self._nine_patch(prefix, ox, oy, color_key, inverted,
                                 cls=class_here,
                                 frame_only=spec.get("frame_only", False),
                                 dither=base in spec.get("dither", ()))
                self._hints(prefix, ox, oy, hints)

        for j, (sid, (kind, color_key)) in enumerate(shapes):
            i = len(sets) + j
            ox = self.gap + (i % columns) * step
            oy = self.gap + (i // columns) * step
            self._shape(sid, kind, self.color(color_key, "text"), ox, oy, self.cell)

        # The tiling hint applies to the whole file, not per state.
        # It lies outside the visible area - KSvg only asks whether
        # the element exists, and never draws it. Breeze places it in
        # negative coordinates in the same file too.
        if spec.get("tile_center"):
            self.parts.append(
                '  <!-- Tile the center instead of stretching it -->\n'
                '    <rect id="hint-tile-center" x="0" y="-4" '
                'width="2" height="2" opacity="0"/>')

        self.corner = self._corner_original
        return "\n".join(head + self.parts + ['</svg>', ''])


# Pure shape widgets otherwise behave like the others
WIDGETS.update({n: {**s, "prefixes": [], "hints": [], "masks": []}
                for n, s in SHAPE_WIDGETS.items()})


def main():
    ap = argparse.ArgumentParser(
        description="Generates Plasma style SVGs with the correct element structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available widgets:  " + ", ".join(sorted(WIDGETS)))
    ap.add_argument("widget", nargs="?", help="name of the widget, e.g. button")
    ap.add_argument("--all", action="store_true", help="generate all widgets")
    ap.add_argument("--list", action="store_true", help="list the widgets")
    ap.add_argument("-o", "--output", type=Path,
                    help="target directory (otherwise to stdout)")
    ap.add_argument("--palette", default="platinum", choices=sorted(PALETTES))
    ap.add_argument("--style", default="bevel", choices=["bevel", "flat"],
                    help="bevel = 3D border like Mac OS 9, flat = single colour")
    ap.add_argument("--border", type=int, default=1, help="border width in px")
    ap.add_argument("--radius", type=int, default=0, help="corner radius in px")
    ap.add_argument("--outer-border", type=int, default=0,
                    help="dark border around the 3D bevel (NT/Win95 style)")
    ap.add_argument("--cell", type=int, default=32, help="size of one state set")
    ap.add_argument("--corner", type=int, default=6, help="size of the corner elements")
    args = ap.parse_args()

    if args.list:
        print(f"{'Widget':<20} {'States':>10}  Description")
        for n, s in sorted(WIDGETS.items()):
            print(f"{n:<20} {len(s['prefixes']):>10}  {s['description']}")
        return 0

    if not args.all and not args.widget:
        ap.error("give a widget name or --all (--list shows them all).")
    if args.widget and args.widget not in WIDGETS:
        ap.error(f"Unknown widget '{args.widget}'. --list shows them all.")

    g = Generator(PALETTES[args.palette], border=args.border,
                  radius=args.radius, style=args.style,
                  cell=args.cell, corner=args.corner,
                  outer_border=args.outer_border)

    names = sorted(WIDGETS) if args.all else [args.widget]
    for name in names:
        svg = g.generate(name, WIDGETS[name])
        if args.output:
            spec = WIDGETS[name]
            sub = spec.get("folder", "widgets")
            filename = spec.get("file", name)
            targets = [args.output / sub / f"{filename}.svg"]

            # Plasma picks a variant set depending on the environment:
            # solid (no blur), translucent (with blur), opaque. If the
            # matching file is missing, ONLY it falls back to Breeze -
            # the panel then turns transparent and blends with the
            # background, even though widgets/ exists. Measured:
            # panel surface #80807b instead of #b8c4c4.
            if name in ("panel-background", "background", "background-dialog",
                        "tooltip"):
                # Breeze only has solid and translucent for background -
                # opaque/widgets/background does not exist there.
                variants = ("solid", "translucent") if name == "background" \
                    else ("solid", "translucent", "opaque")
                for variant in variants:
                    targets.append(args.output / variant / sub / f"{filename}.svg")

            for target in targets:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(svg)
                print(f"  {target}")
        else:
            sys.stdout.write(svg)

    return 0


if __name__ == "__main__":
    sys.exit(main())
