#!/usr/bin/env python3
"""Generates an Aurorae window decoration from parameters.

Aurorae is KWin's SVG-based decoration engine. A decoration
consists of:

    decoration.svg   9-patch for active, inactive and maximized
    close/maximize/minimize/restore.svg   five states each
    <Name>rc         geometry: border widths, title height, buttons
    metadata.desktop registration with KWin

The element IDs are the contract with KWin - if one is missing, KWin
draws nothing in that spot, without an error message.

    ./gen-aurorae.py --name NTLegacy -o nt-legacy/aurorae/
"""

import argparse
from pathlib import Path

# Aurorae knows exactly these state sets in the decoration.
# maximized-* is drawn when the window is maximized -
# there the border is dropped, only the title bar remains.
DECORATION_SETS = ["decoration", "decoration-inactive"]
BUTTON_STATES = ["active", "inactive", "hover", "pressed", "deactivated"]
BUTTONS = ["close", "maximize", "minimize", "restore", "alldesktops",
           "keepabove", "keepbelow", "shade", "help", "menu"]


class Aurorae:
    def __init__(self, palette, title_height=22, border=4, outer=1,
                 bevel=1, button_size=14):
        self.p = palette
        self.th = title_height
        self.border = border
        self.outer = outer
        self.bevel = bevel
        self.bg = button_size

    def f(self, *keys):
        for k in keys:
            if k in self.p:
                return self.p[k]
        return "#000000"

    # ------------------------------------------------------------------
    def _patch(self, prefix, ox, oy, width, height, title, surface):
        """A 9-patch for the decoration.

        At the top sits the title bar in solid colour, on the other
        sides only the border. The top corners belong to the title bar,
        the bottom ones to the border - otherwise the title bar visually
        breaks off at the sides.
        """
        r, a, b = self.border, self.outer, self.bevel
        outer_colour = self.f("border")
        light, dark = self.f("light"), self.f("dark")
        t = []

        def rect(x, y, w, h, colour):
            if w > 0 and h > 0:
                t.append(f'    <rect x="{x:g}" y="{y:g}" width="{w:g}" '
                         f'height="{h:g}" fill="{colour}"/>')

        def field(name, x, y, w, h, ground, edges):
            t.append(f'  <g id="{prefix}-{name}">')
            rect(x, y, w, h, ground)
            # Outer border
            if "t" in edges: rect(x, y, w, a, outer_colour)
            if "b" in edges: rect(x, y + h - a, w, a, outer_colour)
            if "l" in edges: rect(x, y, a, h, outer_colour)
            if "r" in edges: rect(x + w - a, y, a, h, outer_colour)
            # 3D edge inside it
            if "t" in edges: rect(x + (a if "l" in edges else 0), y + a,
                                  w - (a if "l" in edges else 0) - (a if "r" in edges else 0), b, light)
            if "l" in edges: rect(x + a, y + (a if "t" in edges else 0), b,
                                  h - (a if "t" in edges else 0) - (a if "b" in edges else 0), light)
            if "b" in edges: rect(x + (a if "l" in edges else 0), y + h - a - b,
                                  w - (a if "l" in edges else 0) - (a if "r" in edges else 0), b, dark)
            if "r" in edges: rect(x + w - a - b, y + (a if "t" in edges else 0), b,
                                  h - (a if "t" in edges else 0) - (a if "b" in edges else 0), dark)
            t.append('  </g>')

        th = self.th
        middle_h = height - th - r
        # Title row
        field("topleft",     ox,              oy,      r,            th, title, "tl")
        field("top",         ox + r,          oy,      width - 2*r,  th, title, "t")
        field("topright",    ox + width - r,  oy,      r,            th, title, "tr")
        # Window content. The centre carries the border colour, even though
        # the window normally covers it completely.
        #
        # Reason: if the user turns the border size up (System Settings >
        # Window Decorations > Border size), KWin reports a wider border
        # than our graphic draws - Large is a factor of 1.5, 4 px become 6.
        # The left/right/bottom elements keep their natural width; the
        # difference falls into the center field. The Aurorae docs say so
        # explicitly: "the borders may extend into the center element if
        # the border size is changed". When center was transparent, the
        # desktop showed through there - a gap between border and window
        # content.
        #
        # Price: with a window that is itself translucent, you see this
        # area behind it instead of the desktop. For an opaque NT theme
        # that is the right trade.
        field("left",        ox,              oy + th, r,            middle_h, surface, "l")
        t.append(f'  <g id="{prefix}-center">')
        t.append(f'    <rect x="{ox + r:g}" y="{oy + th:g}" '
                 f'width="{width - 2*r:g}" height="{middle_h:g}" fill="{surface}"/>')
        t.append('  </g>')
        field("right",       ox + width - r,  oy + th, r,            middle_h, surface, "r")
        # Bottom edge
        field("bottomleft",  ox,              oy + height - r, r,           r, surface, "bl")
        field("bottom",      ox + r,          oy + height - r, width - 2*r, r, surface, "b")
        field("bottomright", ox + width - r,  oy + height - r, r,           r, surface, "br")
        return t

    def decoration(self):
        b, h = 200, 120
        gap = 20
        parts = []
        # active
        parts += self._patch("decoration", gap, gap, b, h,
                             self.f("title_active"), self.f("surface"))
        # inactive
        parts += self._patch("decoration-inactive", gap, gap + h + gap, b, h,
                             self.f("title_inactive"), self.f("surface"))

        # Maximized: only the title bar, no border around it.
        for name, colour, oy in [
            ("decoration-maximized-center", self.f("title_active"), gap + 2*(h+gap)),
            ("decoration-maximized-inactive-center", self.f("title_inactive"),
             gap + 2*(h+gap) + self.th + gap),
        ]:
            parts.append(f'  <g id="{name}">')
            parts.append(f'    <rect x="{gap}" y="{oy}" width="{b}" '
                         f'height="{self.th}" fill="{colour}"/>')
            parts.append(f'    <rect x="{gap}" y="{oy + self.th - self.outer}" '
                         f'width="{b}" height="{self.outer}" fill="{self.f("border")}"/>')
            parts.append('  </g>')

        gh = gap + 2*(h+gap) + 2*(self.th + gap)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{b + 2*gap}" '
                f'height="{gh}" viewBox="0 0 {b + 2*gap} {gh}">\n'
                '  <!-- Generated by tools/gen-aurorae.py.\n'
                '       The IDs are the contract with KWin - do not rename. -->\n'
                + "\n".join(parts) + '\n</svg>\n')

    def button(self, kind):
        """One button per state - exclusively as a "center" element.

        The Aurorae documentation is unambiguous here:
        "Each button has to provide the center element. Borders are not
        supported." (develop.kde.org/docs/plasma/aurorae/)

        Trying a full 9-patch would have been the obvious move, because
        AuroraeButton.qml uses a KSvg.FrameSvgItem - technically it might
        have worked, but it is not documented. And the symbol has to sit
        IN the center anyway: FrameSvgItem only draws the grid fields, a
        separate symbol element would never have been drawn.

        Consequence: KWin stretches the graphic to the configured button
        size (window decoration KCM, cog wheel). With sizes that differ a
        lot, the 1px edges turn soft. That is a quirk of Aurorae, not a
        bug in this theme - which is why the buttons here are drawn
        generously, so enough substance remains when scaled down.
        """
        g, a, b = self.bg, self.outer, self.bevel
        gap = 6
        parts = []

        for i, state in enumerate(BUTTON_STATES):
            ox = gap + i * (g + gap)
            oy = gap
            pressed = state == "pressed"
            ground = self.f("hover") if state == "hover" else self.f("surface")
            if state == "deactivated":
                ground = self.f("dark")
            light = self.f("dark" if pressed else "light")
            dark = self.f("light" if pressed else "dark")
            border = self.f("border")
            stroke = self.f("text")

            parts.append(f'  <g id="{state}-center">')
            parts.append(f'    <rect x="{ox}" y="{oy}" width="{g}" height="{g}" '
                         f'fill="{ground}"/>')
            # Outer border
            for x, y, w, h in [(ox, oy, g, a), (ox, oy + g - a, g, a),
                               (ox, oy, a, g), (ox + g - a, oy, a, g)]:
                parts.append(f'    <rect x="{x:g}" y="{y:g}" width="{w:g}" '
                             f'height="{h:g}" fill="{border}"/>')
            # 3D edge inside it
            parts.append(f'    <rect x="{ox+a}" y="{oy+a}" width="{g-2*a}" '
                         f'height="{b}" fill="{light}"/>')
            parts.append(f'    <rect x="{ox+a}" y="{oy+a}" width="{b}" '
                         f'height="{g-2*a}" fill="{light}"/>')
            parts.append(f'    <rect x="{ox+a}" y="{oy+g-a-b}" width="{g-2*a}" '
                         f'height="{b}" fill="{dark}"/>')
            parts.append(f'    <rect x="{ox+g-a-b}" y="{oy+a}" width="{b}" '
                         f'height="{g-2*a}" fill="{dark}"/>')

            # The symbol sits in the same element - see above.
            v = 1 if pressed else 0
            cx, cy = ox + g / 2 + v, oy + g / 2 + v
            s = (g - 2 * (a + b)) * 0.72 / 2
            sw = max(1.5, g * 0.09)
            parts.append(self._symbol(kind, cx, cy, s, sw, stroke))
            parts.append('  </g>')

        width = gap + len(BUTTON_STATES) * (g + gap)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
                f'height="{g + 2*gap}" viewBox="0 0 {width} {g + 2*gap}">\n'
                + "\n".join(parts) + '\n</svg>\n')

    def _symbol(self, kind, m, n, s, sw, colour):
        """The glyph in the button. Every function needs its own -
        six buttons with the same bar cannot be told apart."""
        if kind == "close":
            return (f'    <path d="M{m-s:g},{n-s:g} L{m+s:g},{n+s:g} '
                    f'M{m+s:g},{n-s:g} L{m-s:g},{n+s:g}" stroke="{colour}" '
                    f'stroke-width="{sw:g}"/>')
        if kind == "maximize":
            return (f'    <rect x="{m-s:g}" y="{n-s:g}" width="{2*s:g}" '
                    f'height="{2*s:g}" fill="none" stroke="{colour}" '
                    f'stroke-width="{sw:g}"/>')
        if kind == "minimize":
            return (f'    <rect x="{m-s:g}" y="{n+s-sw:g}" width="{2*s:g}" '
                    f'height="{sw:g}" fill="{colour}"/>')
        if kind == "restore":
            return (f'    <rect x="{m-s:g}" y="{n-s+sw:g}" width="{2*s-sw:g}" '
                    f'height="{2*s-sw:g}" fill="none" stroke="{colour}" '
                    f'stroke-width="{sw*0.8:g}"/>\n'
                    f'    <path d="M{m-s+sw:g},{n-s+sw:g} L{m-s+sw:g},{n-s:g} '
                    f'L{m+s:g},{n-s:g} L{m+s:g},{n+s-sw:g}" fill="none" '
                    f'stroke="{colour}" stroke-width="{sw*0.8:g}"/>')
        if kind == "shade":
            # Shade: bar at the top plus an upward arrow
            return (f'    <rect x="{m-s:g}" y="{n-s:g}" width="{2*s:g}" '
                    f'height="{sw:g}" fill="{colour}"/>\n'
                    f'    <path d="M{m:g},{n+s:g} L{m-s*0.6:g},{n:g} '
                    f'L{m+s*0.6:g},{n:g} Z" fill="{colour}"/>')
        if kind == "keepabove":
            return (f'    <path d="M{m:g},{n-s:g} L{m-s:g},{n+s*0.3:g} '
                    f'L{m+s:g},{n+s*0.3:g} Z" fill="{colour}"/>\n'
                    f'    <rect x="{m-s:g}" y="{n+s*0.6:g}" width="{2*s:g}" '
                    f'height="{sw:g}" fill="{colour}"/>')
        if kind == "keepbelow":
            return (f'    <path d="M{m:g},{n+s:g} L{m-s:g},{n-s*0.3:g} '
                    f'L{m+s:g},{n-s*0.3:g} Z" fill="{colour}"/>\n'
                    f'    <rect x="{m-s:g}" y="{n-s:g}" width="{2*s:g}" '
                    f'height="{sw:g}" fill="{colour}"/>')
        if kind == "alldesktops":
            # Four small squares = several desktops
            q = s * 0.8
            return "\n".join(
                f'    <rect x="{m + dx*q - q*0.85:g}" y="{n + dy*q - q*0.85:g}" '
                f'width="{q*0.7:g}" height="{q*0.7:g}" fill="{colour}"/>'
                for dx in (0, 1) for dy in (0, 1))
        if kind == "help":
            return (f'    <text x="{m:g}" y="{n+s*0.8:g}" font-size="{2.2*s:g}" '
                    f'font-family="sans-serif" font-weight="bold" '
                    f'text-anchor="middle" fill="{colour}">?</text>')
        if kind == "menu":
            # Three lines
            return "\n".join(
                f'    <rect x="{m-s:g}" y="{n + (k-1)*s*0.75 - sw/2:g}" '
                f'width="{2*s:g}" height="{sw:g}" fill="{colour}"/>'
                for k in range(3))
        return (f'    <rect x="{m-s:g}" y="{n-sw/2:g}" width="{2*s:g}" '
                f'height="{sw:g}" fill="{colour}"/>')

    def rc(self, name):
        def rgb(h):
            h = h.lstrip("#")
            return ",".join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))
        r = self.border
        return f"""[General]
ActiveTextColor={rgb(self.f("selection_text", "window"))}
InactiveTextColor={rgb(self.f("window"))}
TitleAlignment=Left
TitleVerticalAlignment=Center
UseTextShadow=false
Animation=0
Shadow=true

[Layout]
BorderLeft={r}
BorderRight={r}
BorderBottom={r}
TitleHeight={self.th}
TitleEdgeTop=0
TitleEdgeTopMaximized=0
TitleEdgeBottom=0
TitleEdgeBottomMaximized=0
TitleEdgeLeft={r}
TitleEdgeLeftMaximized=2
TitleEdgeRight={r}
TitleEdgeRightMaximized=2
TitleBorderLeft=4
TitleBorderRight=4
ButtonWidth={self.bg}
ButtonHeight={self.bg}
ButtonSpacing=2
ButtonMarginTop={max(0, (self.th - self.bg) // 2)}
ExplicitButtonSpacer=4
PaddingTop=0
PaddingBottom=0
PaddingLeft=0
PaddingRight=0
"""

    def config_main_xml(self):
        """KConfigXT description of the adjustable values.

        The window decoration KCM (kcm_auroraedecoration.so) loads
        contents/config/main.xml and contents/ui/config.ui if an
        Aurorae theme ships them - the strings are in the plugin, and
        it uses QUiLoader. Settings are stored in ~/.config/auroraerc.

        CAUTION: there is not a single Aurorae theme on the system with
        a configuration page, and the documentation does not describe the
        format. The structure here follows the usual KConfigXT rules
        (widget "kcfg_<Name>" is bound to the entry "<Name>").
        Whether the KCM actually shows the page is therefore not
        guaranteed - if in doubt the theme keeps its rc values,
        nothing breaks.
        """
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<kcfg xmlns="http://www.kde.org/standards/kcfg/1.0"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.kde.org/standards/kcfg/1.0
                          http://www.kde.org/standards/kcfg/1.0/kcfg.xsd">
  <kcfgfile name=""/>
  <group name="General">
    <entry name="TitleHeight" type="Int">
      <label>Title bar height</label>
      <default>{self.th}</default>
      <min>16</min>
      <max>48</max>
    </entry>
    <entry name="ButtonHeight" type="Int">
      <label>Button size</label>
      <default>{self.bg}</default>
      <min>10</min>
      <max>40</max>
    </entry>
    <entry name="BorderLeft" type="Int">
      <label>Border width</label>
      <default>{self.border}</default>
      <min>0</min>
      <max>12</max>
    </entry>
    <entry name="TitleAlignment" type="String">
      <label>Title alignment</label>
      <default>Left</default>
    </entry>
  </group>
</kcfg>
"""

    def config_ui(self):
        """The UI for it. Widget names "kcfg_<entry>" bind to the
        entries from main.xml - KConfigDialogManager does that."""
        def spin(name, label, mini, maxi, value, suffix=" px"):
            return f"""   <item row="{spin.row}" column="0">
    <widget class="QLabel" name="label_{name}">
     <property name="text"><string>{label}</string></property>
    </widget>
   </item>
   <item row="{spin.row}" column="1">
    <widget class="QSpinBox" name="kcfg_{name}">
     <property name="minimum"><number>{mini}</number></property>
     <property name="maximum"><number>{maxi}</number></property>
     <property name="value"><number>{value}</number></property>
     <property name="suffix"><string>{suffix}</string></property>
    </widget>
   </item>
"""
        spin.row = 0
        parts = []
        for name, label, mini, maxi, value in [
            ("TitleHeight", "Title bar:", 16, 48, self.th),
            ("ButtonHeight", "Buttons:", 10, 40, self.bg),
            ("BorderLeft", "Border:", 0, 12, self.border),
        ]:
            parts.append(spin(name, label, mini, maxi, value))
            spin.row += 1

        return """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>NTLegacyConfig</class>
 <widget class="QWidget" name="NTLegacyConfig">
  <layout class="QGridLayout" name="gridLayout">
""" + "".join(parts) + """   <item row="3" column="0" colspan="2">
    <spacer name="spacer">
     <property name="orientation"><enum>Qt::Vertical</enum></property>
    </spacer>
   </item>
  </layout>
 </widget>
 <resources/>
 <connections/>
</ui>
"""

    def metadata(self, name, display_name, description, author, license, version,
                 description_de=None):
        # Aurorae uses metadata.desktop - here that is not legacy but
        # the intended format. The prefix __aurorae__svg__ is mandatory
        # and must be followed by the folder name.
        comment_de = f"Comment[de]={description_de}\n" if description_de else ""
        return f"""[Desktop Entry]
Name={display_name}
Comment={description}
{comment_de}Type=Service
X-KDE-ServiceTypes=KWin/Decoration
X-KDE-Library=kwin3_aurorae
X-KDE-PluginInfo-Name=__aurorae__svg__{name}
X-KDE-PluginInfo-Author={author}
X-KDE-PluginInfo-License={license}
X-KDE-PluginInfo-Version={version}
"""


PALETTE_NT = {
    "surface": "#d8d8d0", "window": "#f0f0e8",
    "title_active": "#176b78", "title_inactive": "#60777a",
    "light": "#f4f4ee", "dark": "#8a8a82", "border": "#202628",
    "text": "#202628", "selection_text": "#ffffff", "hover": "#d6a23a",
}


def main():
    ap = argparse.ArgumentParser(description="Generates an Aurorae decoration.")
    ap.add_argument("--name", default="NTLegacy")
    ap.add_argument("--display-name", default="NT Legacy")
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--title-height", type=int, default=22)
    ap.add_argument("--border", type=int, default=4)
    ap.add_argument("--button", type=int, default=14)
    ap.add_argument("--author", default="huppiflupp")
    ap.add_argument("--license", default="GPL-2.0-or-later")
    ap.add_argument("--version", default="0.1.0")
    args = ap.parse_args()

    a = Aurorae(PALETTE_NT, title_height=args.title_height,
                border=args.border, button_size=args.button)
    target = args.output / args.name
    target.mkdir(parents=True, exist_ok=True)

    (target / "decoration.svg").write_text(a.decoration())
    print(f"  {target.name}/decoration.svg")
    for btn in BUTTONS:
        (target / f"{btn}.svg").write_text(a.button(btn))
    print(f"  {target.name}/*.svg ({len(BUTTONS)} buttons)")
    (target / "contents" / "config").mkdir(parents=True, exist_ok=True)
    (target / "contents" / "ui").mkdir(parents=True, exist_ok=True)
    (target / "contents" / "config" / "main.xml").write_text(a.config_main_xml())
    (target / "contents" / "ui" / "config.ui").write_text(a.config_ui())
    print(f"  {target.name}/contents/  (configuration page)")

    (target / f"{args.name}rc").write_text(a.rc(args.name))
    print(f"  {target.name}/{args.name}rc")
    (target / "metadata.desktop").write_text(a.metadata(
        args.name, args.display_name,
        "Windows NT 4.0 in petrol - angular frames, square buttons",
        args.author, args.license, args.version,
        description_de="Windows NT 4.0 in Petrol - eckige Rahmen, quadratische Knoepfe"))
    print(f"  {target.name}/metadata.desktop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
