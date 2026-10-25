#!/usr/bin/env python3
"""Builds the "NT Legacy" theme family from color definitions.

Windows NT 4.0 color world for Plasma 6, without black surfaces: only
text, borders and the active title bar are dark. That keeps the theme
pleasant for long working sessions and still gives it more character
than Breeze.

NT shipped with named color schemes ("Appearance Schemes"). Three of
them are recreated here: Teal, Lilac and Desert. They share the same
design language and differ only in their colors - exactly what a
parametric setup makes cheap.

    ./build.py              # all variants
    ./build.py --only teal  # a single one
    ./build.py --check      # lint as well

Anyone who wants to change something changes a value in BASE or VARIANTS
and runs the script again - not 25 files by hand.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent


def tool(name):
    """Path to a script from tools/.

    Two locations, and both are normal: in the working tree tools/ sits
    next to nt-legacy/, in the shipped archive it is nt-legacy/tools/. Up
    to 0.2.7 build.py only knew the first - in the archive it therefore
    ran into nothing, just like fetch-icons.sh (reported by the community:
    "line 65: /nt-legacy/../tools/fix-index-theme.py: No such file or
    directory").

    If the tool is missing in both locations, the path into the working
    tree is the more honest error message - that is where it belongs.
    """
    for candidate in (HERE / "tools" / name, LAB / "tools" / name):
        if candidate.exists():
            return str(candidate)
    return str(LAB / "tools" / name)


AUTHOR = "huppiflupp"
EMAIL = "huppiflupp@users.noreply.github.com"
# The theme's own repository, not the workshop and not NiceOS9.
#
# Up to 0.2.8 this said NiceOS9-theme - a different theme by the same
# author. The address goes into every metadata.json and with it into the
# store entry: anyone who clicked the website link there ended up at the
# wrong design.
WEBSITE = "https://github.com/huppiflupp/nt-legacy"
LICENSE = "GPL-2.0-or-later"
FONT = "Noto Sans"
VERSION = "0.3.1"

# --------------------------------------------------------------------------
# Colors. The only place where they are defined.
# --------------------------------------------------------------------------

BASE = {
    # Main surface, light neutral grey.
    #
    # An attempt to darken it has been reverted. The idea was to make the
    # checker pattern of the scroll bar visible - that pattern is drawn by
    # the Qt style from this color and a lighter one, not by our SVG. In
    # a Qt measurement without KDE it looked like 18 -> 28 percent. Measured
    # in the test machine it was 18 -> 20: KDE does not derive the light
    # color towards white, but at a fixed distance above the surface (200
    # gives 240). So the change would have darkened all light variants and
    # gained nothing. contrast=10 and a white window color do not change
    # that either - both measured again.
    "surface":        "#d8d8d0",
    "window":         "#f0f0e8",   # window content, almost cream white
    "panel":          "#b8c4c4",   # muted petrol grey
    "title_active":   "#176b78",   # active window title, dark petrol
    "title_inactive": "#60777a",   # desaturated petrol
    "text":           "#202628",   # very dark blue grey
    "text2":          "#526166",   # secondary text
    # Selection color. It has to be readable in BOTH directions - with
    # white and with black text.
    #
    # The reason is Dolphin. It draws the text of a selected item not in
    # QPalette::HighlightedText but in QPalette::Text - that is, in the
    # normal text color, black (kstandarditemlistwidget.cpp,
    # normalTextColorRole(): HighlightedText only comes out while
    # clicking). Under Breeze this goes unnoticed because its selection
    # bar is light. The "Windows" widget style that this theme sets, on
    # the other hand, fills the bar completely with the selection color.
    #
    # Result in the Win2k version: black file names on #0a246a, the real
    # selection blue of Windows 2000 - 1.47:1, reported as "you can't make
    # out anything any more", and measured again on the screenshot. The
    # same in Win98 with #000080 (1.31:1).
    #
    # The only thing that can be changed is the color. So it now sits at
    # the point where both contrasts are equal: luminance 0.179 gives
    # 4.58:1 against black AND against white. Darker means unreadable file
    # names, lighter means unreadable menu entries - there is no more on
    # one side without less on the other. check_selection() below makes
    # the build fail if a variant slips below 4.5:1.
    #
    # The price is accepted: the navy blue of Windows is now a muted steel
    # blue. It was only authentic as long as you didn't have to read
    # anything.
    "selection":      "#29818e",   # petrol
    "selection_text": "#ffffff",
    "hover":          "#d6a23a",   # NT-style gold
    "warning":        "#c87922",
    "error":          "#a83232",
    "positive":       "#39734a",
    "desktop":        "#899a9a",
    "light":          "#f4f4ee",   # 3D edge top/left
    "dark":           "#8a8a82",   # 3D edge bottom/right
    "border":         "#202628",   # outer border
    # The light dot in the checker pattern of the scroll bar trough.
    # Deliberately not "light": the highlight edge is muted, the checker
    # needs contrast. And deliberately not #ffffff - the colors are
    # replaced via their hex value, so a value that selection_text also
    # carries would recolor both at once.
    "checker":        "#fcfcfa",
}

VARIANTS = {
    "teal": {
        "short": "NTLegacy",
        "display": "NT Legacy",
        "display_de": "NT Legacy",
        "description_de": "Petrol und warmes Grau - die Grundfassung",
        "description": "Petrol and warm grey - the base version",
        "colors": {},
    },
    "lilac": {
        "short": "NTLegacyLilac",
        "display": "NT Legacy Lilac",
        "display_de": "NT Legacy Flieder",
        "description_de": "Flieder statt Petrol, nach NTs Schema Lilac",
        "description": "Lilac instead of petrol, after NT's Lilac scheme",
        "colors": {
            "panel":          "#c4bcc8",
            "title_active":   "#5c4a78",
            "title_inactive": "#7a7088",
            "selection":      "#8369ae",
            "hover":          "#c8a83a",
            "desktop":        "#9a91a6",
            "text2":          "#5a5266",
        },
    },
    "desert": {
        "short": "NTLegacyDesert",
        "display": "NT Legacy Desert",
        "display_de": "NT Legacy Wueste",
        "description_de": "Sand und Terrakotta, nach NTs Schema Desert",
        "description": "Sand and terracotta, after NT's Desert scheme",
        "colors": {
            "surface":        "#d8d0c0",
            "window":         "#f0ece0",
            "panel":          "#c8bca4",
            "title_active":   "#7a5c2e",
            "title_inactive": "#8a7c64",
            "selection":      "#946f39",
            "hover":          "#c87922",
            "desktop":        "#a89878",
            "text2":          "#6a5c46",
            "light":          "#f4f0e6",
            "checker":        "#fcfaf2",
            "dark":           "#8a8272",
        },
    },
    # Windows 98: the classic system grey #C0C0C0 with the navy blue
    # title bar. The 16-color VGA palette of the time - hence no
    # in-between shades, but the pure values.
    "win98": {
        "short": "NTLegacyWin98",
        "display": "NT Legacy 98",
        "display_de": "NT Legacy 98",
        "description_de": "Systemgrau und Marineblau - Windows 98",
        "description": "System grey and navy blue - Windows 98",
        "colors": {
            "surface":        "#c0c0c0",
            "window":         "#ffffff",
            "panel":          "#c0c0c0",
            "title_active":   "#000080",   # the navy blue
            "title_inactive": "#808080",
            "text":           "#000000",
            "text2":          "#404040",
            "selection":      "#6f6fb1",
            "hover":          "#dcdcdc",
            "warning":        "#808000",
            "error":          "#800000",
            "positive":       "#008000",
            "desktop":        "#008080",   # the teal of the default desktop
            "light":          "#ffffff",
            "checker":        "#ffffff",
            "dark":           "#808080",
            "border":         "#000000",
        },
    },
    # Windows 2000: the same design language, but softer shades and the
    # characteristic gradient in the title bar. We cannot recreate the
    # gradient with solid fills - instead the middle shade, which comes
    # closest to the overall impression.
    "win2k": {
        "short": "NTLegacyWin2k",
        "display": "NT Legacy 2000",
        "display_de": "NT Legacy 2000",
        "description_de": "Weicheres Grau, Blauverlauf - Windows 2000",
        "description": "Softer grey, blue gradient - Windows 2000",
        "colors": {
            "surface":        "#d4d0c8",
            "window":         "#ffffff",
            "panel":          "#d4d0c8",
            "title_active":   "#0a246a",
            "title_inactive": "#808080",
            "text":           "#000000",
            "text2":          "#4a4a4a",
            "selection":      "#6174aa",
            "hover":          "#316ac5",
            "warning":        "#c87922",
            "error":          "#a83232",
            "positive":       "#39734a",
            "desktop":        "#3a6ea5",
            "light":          "#ffffff",
            "checker":        "#ffffff",
            "dark":           "#808080",
            "border":         "#000000",
        },
    },
}

# --------------------------------------------------------------------------
# Night versions
#
# The rule for the light variants was: no black surfaces, only text,
# borders and the active title bar are dark. For the night this is
# reversed - but the idea behind it stays: no black here either, but dark
# blue grey. Pure black next to light text creates hard edges that are
# tiring over long use.
#
# The 3D bevel turns with it: top/left becomes a lightened grey,
# bottom/right almost black. Without that the frames would look lit from
# the wrong side and the surfaces would appear pressed in instead of
# raised.
#
# The accents - petrol, lilac, sand and the NT gold - stay unchanged.
# They carry the character, not the surfaces.
NIGHT_BASE = {
    "surface":        "#2a3234",
    "window":         "#1e2628",
    "panel":          "#232b2d",
    "title_inactive": "#3c4648",
    "text":           "#dae0e0",
    "text2":          "#94a2a4",
    "selection_text": "#ffffff",
    "desktop":        "#1a2224",
    "light":          "#4a5456",   # 3D edge top/left, lightened
    "dark":           "#0e1416",   # bottom/right, almost black
    "border":         "#0a1012",
    # In the dark the checker was already easy to see - this value is the
    # same one the night versions used to get via "light".
    "checker":        "#4a5456",
}

for _k, _v in [("teal", {}), ("win98", {}), ("win2k", {}),
               ("lilac", {"panel": "#2b2833", "title_inactive": "#443e52",
                          "desktop": "#1e1a26", "text2": "#9a92a6"}),
               ("desert", {"surface": "#32302a", "window": "#26241e",
                           "panel": "#2b2822", "title_inactive": "#4a4438",
                           "desktop": "#221f1a", "text2": "#a49a86",
                           "light": "#544e42", "checker": "#544e42",
                           "dark": "#16130e"})]:
    VARIANTS[f"{_k}-nacht"] = {
        "short": VARIANTS[_k]["short"] + "Nacht",
        "display": VARIANTS[_k]["display"] + " Night",
        "display_de": VARIANTS[_k]["display_de"] + " Nacht",
        "description_de": VARIANTS[_k]["description_de"].split(" - ")[0].split(", nach")[0]
                          + " als Nachtfassung - dunkle Flaechen, gleiche Akzente",
        "description": VARIANTS[_k]["description"].split(" - ")[0]
                       .split(", after")[0]
                       + " as a night version - dark surfaces, same accents",
        # Take over the accent colors of the light version, replace the surfaces
        "colors": {**VARIANTS[_k]["colors"], **NIGHT_BASE, **_v},
    }


def palette(variant):
    return {**BASE, **VARIANTS[variant]["colors"]}


def ids(variant):
    """The identifiers of a variant.

    The color scheme name is the FILE NAME without extension, not the
    Name= field - a color scheme "NT Legacy" in contents/defaults would
    lead nowhere.

    The identifier is stored in VARIANTS and not derived from the key:
    otherwise "teal-nacht" would become "NTLegacyTeal-nacht".
    """
    short = VARIANTS[variant]["short"]
    suffix = "" if variant == "teal" else f"-{variant}"
    return {
        "style":     "nt-legacy" + suffix,
        "schema":    short,
        "aurorae":   short,
        "lnf":       "com.github.huppiflupp.nt-legacy" + suffix,
        "wallpaper": "ntlegacy" + suffix.replace("-", "-"),
        # Suffix _cursors as with breeze_cursors. Without it the icon and
        # cursor themes both end up under ~/.local/share/icons/NTLegacy
        # and their index.theme files overwrite each other - after that
        # Plasma no longer finds any icons.
        "cursor":    short + "_cursors",
        # Two icon sets with the same images but a different fallback
        # chain.
        #
        # Our set covers 146 names; everything else in the panel comes
        # from the inherited theme - updates, clipboard, brightness,
        # network, battery. Breeze draws those in #232629. On the light NT
        # panel that is correct; on the dark panel of the night versions it
        # meant dark grey on dark grey: measured #2C3233 on #151A1B, i.e.
        # 1.3:1. In the test VM half of the system tray was simply
        # invisible.
        #
        # The night versions therefore inherit from breeze-dark. The images
        # are the same in both sets - only the chain behind them differs. A
        # second theme instead of a changed Inherits, because an icon theme
        # cannot switch its chain depending on the color scheme.
        "icons":     "NTLegacyIcons" + ("Nacht" if variant.endswith("-nacht") else ""),
    }


def rgb(hex_value):
    h = hex_value.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def write_file(path: Path, content: str, quiet=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if not quiet:
        print(f"  {path.relative_to(HERE)}")


# --------------------------------------------------------------------------

def color_scheme(p, display, display_de):
    """The .colors file - affects Qt apps AND the shell.

    This is where the actual character comes from. The Plasma style only
    colors the shell; everything else comes from here.
    """
    groups = {
        "Colors:Window":        (p["surface"], p["text"]),
        "Colors:Button":        (p["surface"], p["text"]),
        "Colors:View":          (p["window"], p["text"]),
        "Colors:Selection":     (p["selection"], p["selection_text"]),
        "Colors:Tooltip":       (p["window"], p["text"]),
        "Colors:Complementary": (p["panel"],   p["text"]),
        "Colors:Header":        (p["surface"], p["text"]),
    }
    lines = ["[General]", f"ColorScheme={display}", f"Name={display}",
             *([f"Name[de]={display_de}"] if display_de != display else []),
             "shadeSortColumn=true", "", "[KDE]", "contrast=4", ""]

    for group, (bg, fg) in groups.items():
        alt = p["selection"] if group == "Colors:Selection" else p["window"]
        lines += [f"[{group}]",
                  f"BackgroundNormal={rgb(bg)}",
                  f"BackgroundAlternate={rgb(alt)}",
                  f"ForegroundNormal={rgb(fg)}",
                  f"ForegroundInactive={rgb(p['text2'])}",
                  f"ForegroundActive={rgb(p['selection'])}",
                  f"ForegroundLink={rgb(p['selection'])}",
                  f"ForegroundVisited={rgb(p['title_inactive'])}",
                  f"ForegroundNegative={rgb(p['error'])}",
                  f"ForegroundNeutral={rgb(p['warning'])}",
                  f"ForegroundPositive={rgb(p['positive'])}",
                  f"DecorationFocus={rgb(p['selection'])}",
                  f"DecorationHover={rgb(p['hover'])}", ""]

    # Without this group inactive window headers look like active ones -
    # the difference disappears exactly where it is needed.
    lines += ["[Colors:Header][Inactive]",
              f"BackgroundNormal={rgb(p['surface'])}",
              f"BackgroundAlternate={rgb(p['window'])}",
              f"ForegroundNormal={rgb(p['text2'])}",
              f"ForegroundInactive={rgb(p['text2'])}",
              f"ForegroundActive={rgb(p['title_inactive'])}",
              f"ForegroundLink={rgb(p['title_inactive'])}",
              f"ForegroundVisited={rgb(p['title_inactive'])}",
              f"ForegroundNegative={rgb(p['error'])}",
              f"ForegroundNeutral={rgb(p['warning'])}",
              f"ForegroundPositive={rgb(p['positive'])}",
              f"DecorationFocus={rgb(p['title_inactive'])}",
              f"DecorationHover={rgb(p['hover'])}", ""]

    lines += ["[WM]",
              f"activeBackground={rgb(p['title_active'])}",
              f"activeForeground={rgb(p['selection_text'])}",
              f"inactiveBackground={rgb(p['title_inactive'])}",
              f"inactiveForeground={rgb(p['window'])}",
              f"activeBlend={rgb(p['selection'])}",
              f"inactiveBlend={rgb(p['title_inactive'])}", "",
              "[ColorEffects:Disabled]", "ChangeSelectionColor=true",
              f"Color={rgb(p['dark'])}", "ColorAmount=0", "ColorEffect=0",
              "ContrastAmount=0.65", "ContrastEffect=1",
              "IntensityAmount=0.1", "IntensityEffect=2", "",
              "[ColorEffects:Inactive]", "ChangeSelectionColor=true",
              f"Color={rgb(p['text2'])}", "ColorAmount=0.025", "ColorEffect=2",
              "ContrastAmount=0.1", "ContrastEffect=2", "Enable=false",
              "IntensityAmount=0", "IntensityEffect=0", ""]
    return "\n".join(lines)


def _channels(hex_value):
    h = hex_value.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def luminance(hex_value):
    """Relative luminance according to WCAG - the basis of every contrast calculation."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in _channels(hex_value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """Contrast ratio of two colors, 1:1 to 21:1."""
    la, lb = luminance(a), luminance(b)
    light, dark = max(la, lb), min(la, lb)
    return (light + 0.05) / (dark + 0.05)


def _hsl(hex_value):
    r, g, b = (c / 255 for c in _channels(hex_value))
    high, low = max(r, g, b), min(r, g, b)
    l = (high + low) / 2
    if high == low:
        return 0.0, 0.0, l
    d = high - low
    s = d / (2 - high - low) if l > 0.5 else d / (high + low)
    if high == r:
        h = ((g - b) / d) % 6
    elif high == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h / 6, s, l


def _hex(h, s, l):
    def channel(p, q, t):
        t %= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p
    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r, g, b = channel(p, q, h + 1 / 3), channel(p, q, h), channel(p, q, h - 1 / 3)
    return "#" + "".join(f"{round(c * 255):02x}" for c in (r, g, b))


def for_dark(hex_value, background, target):
    """Raises a color until it reaches the contrast target on 'background'.

    The reason this function exists: the theme's accent colors are made
    for LIGHT surfaces - dark navy blue on system grey. In the terminal
    they sit on a dark background, and there they disappear. The first
    attempt had exactly this problem: #000080 on #1e2628 is a contrast of
    1.1:1, practically invisible.

    The lightness is raised in HSL, not mixed towards white. Mixing
    desaturates: petrol would turn into grey blue. This way the hue is
    kept and the color world stays recognizable.

    4.5:1 is the WCAG threshold for body text, 7:1 the stricter one.
    Applying it here is not a formality - terminal output IS body text,
    and it is read for hours.
    """
    h, s, l = _hsl(hex_value)
    # Lower bound for the saturation: otherwise an already pale shade
    # turns into a white spot without color when lightened.
    #
    # Only for colors that have a hue at all. Otherwise the almost
    # neutral black of the theme would get a blue tint when raised, and
    # Color0 would become a blue-grey spot instead of a grey.
    if s > 0.12:
        s = max(s, 0.35)
    for step in range(101):
        candidate = _hex(h, s, min(1.0, l + step / 100))
        if contrast(candidate, background) >= target:
            return candidate
    return "#ffffff"


def konsole_scheme(p_night, p, display, display_de):
    """One Konsole color scheme per color world.

    Background and text come from the NIGHT version, also for the light
    variants: a terminal is dark, that was no different under NT. The
    eight ANSI colors come from the accents of the color world - and
    those are identical between day and night (see NIGHT_BASE above).
    That is why there are five schemes and not ten: the day and night
    versions of the same color world would produce the same file,
    character for character.

    Color0 to Color7 are the classic row: black, red, green, yellow,
    blue, magenta, cyan, white. These meanings are not negotiable - `ls`
    colors directories blue and links cyan, and anyone who puts the
    theme's accent color there turns a link into a golden spot. So a
    theme color only goes where it also fits semantically: red, green,
    yellow and blue. Magenta and cyan keep their hue.

    Each color is then raised far enough to be readable on the terminal
    background - see for_dark().
    """
    background = p_night["window"]
    row = [
        # Black stays dark but has to be distinguishable from the
        # background: some programs use it for dimmed text. At 1.1:1 it
        # would simply be gone.
        ("Color0", p_night["dark"], 2.2),
        ("Color1", p["error"], 4.5),
        ("Color2", p["positive"], 4.5),
        ("Color3", p["warning"], 4.5),
        ("Color4", p["title_active"], 4.5),
        ("Color5", "#800080", 4.5),   # VGA magenta, only raised
        ("Color6", "#008080", 4.5),   # VGA cyan
        ("Color7", p_night["text"], 4.5),
    ]
    parts = [
        f"[Background]\nColor={rgb(background)}\n",
        f"[BackgroundIntense]\nColor={rgb(p_night['surface'])}\n",
        f"[Foreground]\nColor={rgb(p_night['text'])}\n",
        f"[ForegroundIntense]\nColor={rgb(for_dark(p_night['text'], background, 10))}\n",
    ]
    for name, value, target in row:
        parts.append(f"[{name}]\nColor={rgb(for_dark(value, background, target))}\n")
        # The Intense row one step lighter. 7:1 is the stricter WCAG
        # threshold; for black it would be pointless, there it is enough
        # that the shade is recognizable as grey at all.
        parts.append(f"[{name}Intense]\n"
                     f"Color={rgb(for_dark(value, background, 4.5 if target < 4.5 else 7))}\n")
    parts.append(
        "[General]\n"
        "Blur=false\n"
        "ColorRandomization=false\n"
        f"Description={display}\n"
        + (f"Description[de]={display_de}\n" if display_de != display else "")
        + "Opacity=1\n"
        "Wallpaper=\n"
    )
    return "\n".join(parts)


def konsole_profile(scheme):
    """The Konsole profile - one for all versions.

    Ten profiles would be ten entries in the selection menu that differ in
    only one line. Instead one profile, whose ColorScheme apply.sh
    switches to the chosen color world.

    Liberation Mono, not the prettier programmer's font: it is
    metrically compatible with Courier and present on practically every
    Linux. A theme must not assume a font it does not bring along - if it
    is missing, Qt silently replaces it, and the user sees a terminal that
    does not look like NT without knowing why.
    """
    return (
        "[Appearance]\n"
        f"ColorScheme={scheme}\n"
        "Font=Liberation Mono,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1\n"
        "\n"
        "[General]\n"
        "Name=NT Legacy\n"
        "Parent=FALLBACK/\n"
        "TerminalColumns=90\n"
        "TerminalRows=28\n"
        "\n"
        "[Scrolling]\n"
        "HistoryMode=2\n"
        "ScrollBarPosition=1\n"
    )


# Description in English, translation next to it.
#
# KPlugin knows localized fields: "Description" is the default,
# "Description[de]" applies on a German system. Up to 0.2.7 "Description"
# contained German - so in System Settings every English-speaking user
# read German sentences under English names. The same cause as with the
# logout dialog, just in a different place.
#
# "Category" has been dropped without replacement: the key was there with
# an empty string. A field without a value is not the same as no field -
# KPackage registers it as an empty category instead of assuming none.
def metadata_style(k, display, display_de, description, description_de):
    return json.dumps({
        "KPlugin": {
            "Authors": [{"Name": AUTHOR, "Email": EMAIL}],
            "Description": description,
            "Description[de]": description_de,
            "EnabledByDefault": True,
            "Id": k["style"],
            "License": LICENSE,
            "Name": display,
            **({"Name[de]": display_de} if display_de != display else {}),
            "Version": VERSION,
            "Website": WEBSITE,
        },
        "X-Plasma-API": "5.0",
    }, indent=4, ensure_ascii=False) + "\n"


def metadata_lnf(k, display, display_de, description, description_de):
    return json.dumps({
        "KPackageStructure": "Plasma/LookAndFeel",
        "KPlugin": {
            "Authors": [{"Name": AUTHOR, "Email": EMAIL}],
            "Description": description,
            "Description[de]": description_de,
            "Id": k["lnf"],
            "License": LICENSE,
            "Name": display,
            **({"Name[de]": display_de} if display_de != display else {}),
            "Version": VERSION,
            "Website": WEBSITE,
        },
        "Keywords": "Desktop;Workspace;Appearance;Look and Feel;",
        "X-Plasma-APIVersion": "2",
    }, indent=4, ensure_ascii=False) + "\n"


def defaults(k):
    """contents/defaults - wires the layers together.

    The cursor is set because it is shipped. A reference to a missing
    cursor theme would be harmful - the user would get the default
    cursor and it would look like a bug.

    Caution: the icon theme does NOT take effect reliably this way -
    install.sh additionally sets it hard. Plasma style, color scheme and
    application style, on the other hand, apply as expected. Measured in
    the test VM.

    The name still has to be right. For a long time this said NTLegacy -
    that is the optional Chicago95 set, which is not shipped at all.
    What is shipped is NTLegacyIcons. Anyone who switched the design via
    System Settings instead of apply.sh therefore got an icon theme set
    that does not exist on their machine - and kept seeing the old icons.
    Confirmed on the host system.
    """
    return f"""[kdeglobals][KDE]
widgetStyle=Windows

[kdeglobals][General]
ColorScheme={k['schema']}

[kdeglobals][Icons]
Theme={k['icons']}

[kcminputrc][Mouse]
cursorTheme=NTLegacy_cursors

[Wallpaper]
Image={k['wallpaper']}

[plasmarc][Theme]
name={k['style']}

[kdeglobals][WM]
activeFont={FONT},10,-1,5,75,0,0,0,0,0

[ksplashrc][KSplash]
Theme={k['lnf']}
Engine=KSplashQML

[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae
theme=__aurorae__svg__{k['aurorae']}
"""


def layout_js(k):
    """Panel default: fixed at the bottom, narrow, not floating - like NT 4.0.

    CAUTION: replaces the user's panels when applied. install.sh therefore
    makes a backup first, and Plasma asks in addition (the checkbox is not
    ticked by default).

    One panel PER SCREEN, and that is the core of this file. The
    reasoning is in the generated script, so that it can also be read in
    the shipped package.
    """
    return f"""// {k['style']} - panel default

// One panel per screen.
//
// Up to 0.2.14 this script created exactly ONE - just like Plasma's own
// template (layout-templates/org.kde.plasma.desktop.defaultPanel). On a
// machine with one screen that is correct. On two it is not: Plasma then
// decides by itself which screen the one panel lands on, and the other
// has no taskbar. Reported as "when I switch back to NT Legacy, there is
// no taskbar any more" - and because the choice can differ from run to
// run, it looked as if it depended on the variant.
//
// Measured on a machine with two 2560 screens: screenCount=2,
// panels().length=1, panel.screen=0.
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) {{
    allPanels[i].remove();
}}

for (var s = 0; s < screenCount; s++) {{
    // Further screens only if Plasma already has a desktop there. When the
    // design is applied in a running Plasma (System Settings, "Desktop
    // layout") it does not know the second screen yet: the second panel
    // landed nowhere, was removed again below - and that took the first
    // one with it (screen -1, both screens black until plasmashell was
    // restarted). In the VM with two screens: before, in every second
    // switch; this way, clean in 8 out of 8.
    if (s > 0 && !desktopForScreen(s)) {{
        continue;
    }}
    var panel = new Panel;
    panel.screen = s;
    panel.location = "bottom";
    panel.height = 30;
    panel.floating = false;
    panel.hiding = "none";
    panel.alignment = "left";

    // The application menu, not the application launcher.
    //
    // org.kde.plasma.kickoff is Plasma's default: a window with a search
    // field, a tile grid and tabs. org.kde.plasma.kicker is the cascading
    // menu with submenus - what Windows 95 to 2000 had, and the only one
    // of the two that fits this design language. It also brings the
    // sidebar that the Plasma style colors (widgets/frame, prefix
    // "plain").
    panel.addWidget("org.kde.plasma.kicker");
    panel.addWidget("org.kde.plasma.icontasks");
    panel.addWidget("org.kde.plasma.systemtray");
    panel.addWidget("org.kde.plasma.digitalclock");

    // From the second screen on: only keep it if it really sits there.
    // setScreen goes through Corona::setScreenForContainment and can
    // fail - then all panels would lie on top of each other on the same
    // screen, and that would be worse than the state before. The first
    // one is NEVER removed: one panel too few is exactly the bug this
    // file is meant to fix.
    if (s > 0 && panel.screen !== s) {{
        panel.remove();
    }}
}}

// Up to 0.2.14 there was a block here that set the length, minimum and
// maximum length of the panel to the screen width - against a panel that
// supposedly only became 34 pixels wide.
//
// That never existed. "panel.length" does not return the drawn width but
// the width of the CONTENT; the diagnosis was based on this misreading.
// Measured in the test VM: without any length setting lengthMode is
// "fill", minimumLength and maximumLength are 1280 - and on the screenshot
// the panel is drawn across the full width, while "length" reports 388.
//
// The block was harmful on top of that: setting minimumLength and
// maximumLength to the same value pins the panel to a fixed size. On a
// second screen of a different width it no longer fits, and the fallback
// value 99999 (for the case that screenGeometry does not know anything
// yet) pins it to a width that exists nowhere.
//
// Plasma's own template does not set the length either.

var desktopList = desktops();
for (var j = 0; j < desktopList.length; j++) {{
    desktopList[j].wallpaperPlugin = "org.kde.image";
    desktopList[j].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktopList[j].writeConfig("Image", "{k['wallpaper']}");
    desktopList[j].reloadConfig();
}}
"""


def wallpaper_svg(p, width=3840, height=2160):
    """Background in NT style: a calm surface, no photorealism."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="base" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{p['title_inactive']}"/>
      <stop offset="1" stop-color="{p['desktop']}"/>
    </linearGradient>
    <pattern id="grid" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="1" height="1" fill="{p['window']}" opacity="0.045"/>
    </pattern>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#base)"/>
  <rect width="{width}" height="{height}" fill="url(#grid)"/>
</svg>
"""


def preview_svg(p, k, width=600, height=337):
    """The image that appears in the design selection.

    Without preview.png a grey rectangle is shown there - the most common
    reason why a good theme is overlooked in the store. What is shown is a
    miniature desktop: background, a window with a title bar and the
    panel. That is enough to recognize the color world.
    """
    th = 22          # title bar
    ph = 20          # panel
    fx, fy = 95, 60  # window position
    fw, fh = 380, 210
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{p['title_inactive']}"/>
      <stop offset="1" stop-color="{p['desktop']}"/>
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#g)"/>

  <!-- Window -->
  <rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="{p['border']}"/>
  <rect x="{fx+1}" y="{fy+1}" width="{fw-2}" height="{fh-2}" fill="{p['surface']}"/>
  <rect x="{fx+1}" y="{fy+1}" width="{fw-2}" height="{th}" fill="{p['title_active']}"/>
  <rect x="{fx+6}" y="{fy+7}" width="90" height="6" fill="{p['selection_text']}" opacity="0.9"/>
  <g fill="{p['surface']}">
    <rect x="{fx+fw-52}" y="{fy+5}" width="13" height="11"/>
    <rect x="{fx+fw-37}" y="{fy+5}" width="13" height="11"/>
    <rect x="{fx+fw-22}" y="{fy+5}" width="13" height="11"/>
  </g>
  <!-- Content area with selection bar and accent -->
  <rect x="{fx+8}" y="{fy+th+9}" width="{fw-18}" height="{fh-th-20}" fill="{p['window']}"/>
  <rect x="{fx+12}" y="{fy+th+15}" width="{fw-28}" height="12" fill="{p['selection']}"/>
  <rect x="{fx+16}" y="{fy+th+18}" width="60" height="6" fill="{p['selection_text']}"/>
  <rect x="{fx+16}" y="{fy+th+36}" width="110" height="6" fill="{p['text']}"/>
  <rect x="{fx+16}" y="{fy+th+50}" width="80" height="6" fill="{p['text2']}"/>
  <rect x="{fx+16}" y="{fy+th+64}" width="46" height="12" fill="{p['hover']}"/>

  <!-- Panel: a light line at the top, like NT -->
  <rect x="0" y="{height-ph}" width="{width}" height="{ph}" fill="{p['panel']}"/>
  <rect x="0" y="{height-ph}" width="{width}" height="1" fill="{p['light']}"/>
  <rect x="6" y="{height-ph+4}" width="34" height="9" fill="{p['surface']}"/>
  <rect x="46" y="{height-ph+4}" width="52" height="9" fill="{p['surface']}"/>
  <rect x="{width-40}" y="{height-ph+5}" width="30" height="6" fill="{p['text2']}"/>
</svg>
"""


def splash_qml(p, display):
    """Splash screen. Without it, when switching from another theme, that
    theme's splash stays - a Breeze screen in the middle of the NT look.

    Runs in a very early session state: use only QtQuick, no Plasma
    components.
    """
    return f"""import QtQuick

Rectangle {{
    id: root
    color: "{p['desktop']}"
    property int stage

    // At startup NT showed a plain box with the product name.
    Rectangle {{
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.5, 460)
        height: 150
        color: "{p['surface']}"
        border.color: "{p['border']}"
        border.width: 1

        Rectangle {{
            anchors {{ left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }}
            height: 24
            color: "{p['title_active']}"
            Text {{
                anchors {{ left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }}
                text: "{display}"
                color: "{p['selection_text']}"
                font.bold: true
                font.pixelSize: 13
            }}
        }}

        // Progress: stage runs from 1 to 6
        Rectangle {{
            anchors {{ left: parent.left; right: parent.right; bottom: parent.bottom
                       margins: 14 }}
            height: 14
            color: "{p['window']}"
            border.color: "{p['dark']}"
            border.width: 1

            Rectangle {{
                anchors {{ left: parent.left; top: parent.top; bottom: parent.bottom
                           margins: 2 }}
                width: Math.max(0, (parent.width - 4) * Math.min(root.stage, 6) / 6)
                color: "{p['selection']}"
                Behavior on width {{ NumberAnimation {{ duration: 180 }} }}
            }}
        }}
    }}
}}
"""


def logout_qml(p):
    """Logout dialog. Without it the logout screen looks Breeze-like -
    the most visible break in the overall impression.

    The labels come from Plasma's own translation catalog.

    Up to 0.2.7 there were German strings in i18n() here. But a theme does
    not bring its own catalog - i18n() then returns the msgid
    unchanged. On an English system the dialog was therefore in German,
    while everything else stayed English; reported by the community
    exactly like that (cubanismo, KDE 6.6.5).

    With i18nd on plasma_lookandfeel_org.kde.lookandfeel the translations
    that every Plasma installation brings anyway take effect: the msgids
    are the same as in Breeze's logout dialog. If the catalog is
    missing, the English msgid stays - the right fallback. The '&' in it
    marks the shortcut letter; PlasmaComponents does not evaluate it in
    this dialog, so it is dropped."""
    return f"""import QtQuick
import org.kde.plasma.components as PlasmaComponents

Item {{
    id: root
    signal logoutRequested()
    signal haltRequested()
    signal suspendRequested(int spdMethod)
    signal rebootRequested()
    signal rebootRequested2(int opt)
    signal cancelRequested()
    signal lockScreenRequested()

    property string mode
    property var currentAction

    // Translation from Plasma's catalog, without the shortcut marker.
    function nt_i18n(text) {{
        return i18nd("plasma_lookandfeel_org.kde.lookandfeel", text)
                   .replace("&", "")
    }}

    Rectangle {{
        anchors.fill: parent
        color: "{p['border']}"
        opacity: 0.55
        MouseArea {{ anchors.fill: parent; onClicked: root.cancelRequested() }}
    }}

    Rectangle {{
        anchors.centerIn: parent
        width: 340
        height: 150
        color: "{p['surface']}"
        border.color: "{p['border']}"
        border.width: 1

        Rectangle {{
            anchors {{ left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }}
            height: 22
            color: "{p['title_active']}"
            Text {{
                anchors {{ left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }}
                text: root.nt_i18n("&Shut Down")
                color: "{p['selection_text']}"
                font.bold: true
            }}
        }}

        Row {{
            anchors.centerIn: parent
            spacing: 10
            PlasmaComponents.Button {{
                text: root.nt_i18n("&Log Out"); onClicked: root.logoutRequested()
            }}
            PlasmaComponents.Button {{
                text: root.nt_i18n("&Restart"); onClicked: root.rebootRequested()
            }}
            PlasmaComponents.Button {{
                text: root.nt_i18n("&Shut Down"); onClicked: root.haltRequested()
            }}
        }}

        PlasmaComponents.Button {{
            anchors {{ bottom: parent.bottom; horizontalCenter: parent.horizontalCenter
                       bottomMargin: 10 }}
            text: root.nt_i18n("&Cancel")
            onClicked: root.cancelRequested()
        }}
    }}
}}
"""


def plasmarc():
    return """[Wallpaper]
defaultWallpaperTheme=Next
defaultFileSuffix=.png
defaultWidth=1920
defaultHeight=1080

[AdaptiveTransparency]
enabled=false
"""


# --------------------------------------------------------------------------

def build(variant, check=False):
    v = VARIANTS[variant]
    k = ids(variant)
    p = palette(variant)
    display, display_de = v["display"], v["display_de"]
    description, description_de = v["description"], v["description_de"]

    print(f"\n=== {display} ({variant}) ===")

    style = HERE / "desktoptheme" / k["style"]
    write_file(style / "metadata.json",
               metadata_style(k, display, display_de, description, description_de), quiet=True)
    write_file(style / "plasmarc", plasmarc(), quiet=True)
    # Deliberately NO colors file in the Plasma style.
    #
    # If there is one, it wins over the user's color scheme: the shell
    # then shows the theme colors, no matter what kdeglobals says.
    # Measured in the test VM on the application launcher, color scheme
    # Desert with Plasma style Teal:
    #
    #   with colors file      surface #D8D8D0  (theme color, Teal)
    #   without colors file   surface #D8D0C0  (color scheme, Desert)
    #
    # So neither a color scheme switch nor the user's accent color
    # reached the shell. Breeze ships none for the same reason.
    #
    # The colors are not lost this way - they are in the color scheme
    # color-schemes/<variant>.colors, and apply.sh puts both together.

    r = subprocess.run(
        [sys.executable, tool("gen-plasma-svg.py"),
         "--all", "-o", str(style), "--palette", "nt-legacy",
         "--outer-border", "1", "--border", "1", "--style", "bevel"],
        capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return False

    # The generator only knows the base palette. The variant colors are
    # applied here afterwards - search and replace over the generated
    # files is simpler than teaching the generator a palette format, and
    # the result is identical.
    replacements = {BASE[key]: p[key] for key in p
                    if key in BASE and BASE[key] != p[key]}
    if replacements:
        for file in style.rglob("*.svg"):
            s = file.read_text()
            for old, new in replacements.items():
                s = s.replace(old, new)
            file.write_text(s)
    print(f"  desktoptheme/{k['style']}/  ({len(list(style.rglob('*.svg')))} SVGs)")

    write_file(HERE / "color-schemes" / f"{k['schema']}.colors",
               color_scheme(p, display, display_de), quiet=True)
    print(f"  color-schemes/{k['schema']}.colors")

    # Konsole color scheme - only once per color world, with the light version.
    # See konsole_scheme(): day and night would produce the same file.
    if not variant.endswith("-nacht"):
        night = f"{variant}-nacht"
        if night in VARIANTS:
            write_file(HERE / "konsole" / f"{k['schema']}.colorscheme",
                       konsole_scheme(palette(night), p, display, display_de), quiet=True)
            print(f"  konsole/{k['schema']}.colorscheme")

    r = subprocess.run(
        [sys.executable, tool("gen-aurorae.py"),
         "--name", k["aurorae"], "--display-name", display,
         "-o", str(HERE / "aurorae"), "--author", AUTHOR,
         "--license", LICENSE, "--version", VERSION,
         "--button", "18", "--title-height", "24"],
        capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return False
    deco = HERE / "aurorae" / k["aurorae"]
    if replacements:
        for file in deco.glob("*.svg"):
            s = file.read_text()
            for old, new in replacements.items():
                s = s.replace(old, new)
            file.write_text(s)
    print(f"  aurorae/{k['aurorae']}/")

    # ── Boot screens ─────────────────────────────────────────────────────
    #
    # GRUB and Plymouth get the same design language as the splash
    # screen: an NT dialog with a title bar. That way the machine looks
    # like the same design from power-on to the desktop.
    #
    # Both generators take the finished palette, not the base colors
    # followed by search and replace as with the Plasma style: they draw
    # pixels, not SVGs, and a PNG cannot be recolored afterwards.
    #
    # This is NOT installed by install.sh - both live outside $HOME and
    # need sudo. For that there are install-grub.sh and
    # install-plymouth.sh, which the user runs deliberately.
    pal_json = json.dumps(p)
    for script, subdir, target_name in [
            ("gen-grub.py", "grub", k["aurorae"]),
            ("gen-plymouth.py", "plymouth", k["lnf"].split(".")[-1]),
    ]:
        r = subprocess.run(
            [sys.executable, tool(script), "--name", target_name,
             "--display-name", display, "--palette", pal_json,
             "-o", str(HERE / subdir)],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            return False
        print(r.stdout.rstrip())

    # ── Wallpapers ───────────────────────────────────────────────────────
    #
    # Two packages per variant, and the split has a reason.
    #
    # The main package is the one contents/defaults points to. It holds
    # the landscape - a 4K image that is not made from color values but
    # from an image model. It gets into the repository via
    # tools/make-backgrounds.py and is NOT touched here: rebuilding the
    # theme takes seconds, rebuilding the images takes hours.
    #
    # The generated gradient surface has its own package. It is 95 KB and
    # needs no image model - anyone building the theme from source thus
    # has a matching background even without the images. And anyone who
    # prefers the plain surface to the landscape still finds it in the
    # selection.
    def gradient_package(package_id, name, name_de):
        p_wp = HERE / "wallpapers" / package_id
        write_file(p_wp / "metadata.json", json.dumps({
            "KPlugin": {"Authors": [{"Name": AUTHOR}], "Id": package_id,
                        "License": LICENSE, "Name": name, "Name[de]": name_de}},
            indent=4, ensure_ascii=False) + "\n", quiet=True)
        svg = p_wp / "contents" / "images" / "3840x2160.svg"
        write_file(svg, wallpaper_svg(p), quiet=True)
        return subprocess.run(["magick", "-background", "none", str(svg),
                               str(svg.with_suffix(".png"))],
                              capture_output=True, text=True).returncode == 0

    ok = gradient_package(k["wallpaper"] + "-flaeche", display + " (Plain)",
                          display_de + " (Flaeche)")
    print(f"  wallpapers/{k['wallpaper']}-flaeche/"
          + ("" if ok else "   (PNG skipped)"))

    # If there is no landscape in the main package, the gradient surface
    # steps in - otherwise the global theme would point to an empty package.
    wp = HERE / "wallpapers" / k["wallpaper"]
    images = list((wp / "contents" / "images").glob("*.jpg")) \
        if (wp / "contents" / "images").is_dir() else []
    if images:
        print(f"  wallpapers/{k['wallpaper']}/   "
              f"(landscape, {images[0].stat().st_size // 1024} KB - kept)")
    else:
        gradient_package(k["wallpaper"], display, display_de)
        print(f"  wallpapers/{k['wallpaper']}/   "
              f"(no landscape present, gradient surface used)")

    lnf = HERE / "look-and-feel" / k["lnf"]
    write_file(lnf / "metadata.json",
               metadata_lnf(k, display, display_de, description, description_de), quiet=True)
    write_file(lnf / "contents" / "defaults", defaults(k), quiet=True)
    write_file(lnf / "contents" / "layouts" / "org.kde.plasma.desktop-layout.js",
               layout_js(k), quiet=True)

    write_file(lnf / "contents" / "splash" / "Splash.qml",
               splash_qml(p, display), quiet=True)
    write_file(lnf / "contents" / "logout" / "Logout.qml", logout_qml(p), quiet=True)

    # Preview images for the design selection.
    #
    # Only generate them if there are none yet: tools/gen-preview.sh
    # replaces them with real screenshots from the test VM, and a rebuild
    # would otherwise overwrite those with the schematic version every
    # time. Anyone who wants new ones deletes them first.
    vs = lnf / "contents" / "previews"
    if (vs / "preview.png").exists():
        print(f"  look-and-feel/{k['lnf']}/  (preview kept)")
        return True
    svg_v = vs / "preview.svg"
    write_file(svg_v, preview_svg(p, k), quiet=True)
    # 600x337 like Breeze - the tile in the selection dialog is 16:9.
    # At 400x250 (16:10) the image gets cropped.
    for file, size in [("preview.png", "600x337"),
                       ("fullscreenpreview.jpg", "1920x1080"),
                       ("lockscreen.png", "600x337"),
                       ("splash.png", "600x337")]:
        subprocess.run(["magick", "-background", "none", str(svg_v),
                        "-resize", size + "!", str(vs / file)],
                       capture_output=True)
    svg_v.unlink(missing_ok=True)
    print(f"  look-and-feel/{k['lnf']}/  (with preview)")

    if check:
        subprocess.run([sys.executable, tool("lint-plasma-svg.py"),
                        str(style)])
    return True


def check_selection():
    """The selection color has to be readable against black AND against white.

    Why both - the long version is at BASE["selection"]. In short: Qt
    views write on the selection bar in HighlightedText (white), Dolphin
    writes in Text (black). One color, two text colors, and we can only
    choose the color.

    4.5:1 is the WCAG AA threshold for normal text. Both directions can
    be reached at the same time only in a narrow band around luminance
    0.179 - there both are at 4.58:1. Anyone who changes a color here
    notices it immediately, instead of only seeing it on a user's
    screenshot.
    """
    threshold = 4.5
    failing = []
    print("\nSelection color - contrast against black and white:")
    for v in sorted(VARIANTS):
        a = palette(v)["selection"]
        b, w = contrast(a, "#000000"), contrast(a, "#ffffff")
        mark = "  " if min(b, w) >= threshold else "  TOO LOW"
        print(f"  {v:14} {a}  black {b:5.2f}  white {w:5.2f}{mark}")
        if min(b, w) < threshold:
            failing.append((v, a, b, w))
    if failing:
        print("\nERROR: selection color below %.1f:1 - see BASE[\"selection\"]."
              % threshold, file=sys.stderr)
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description="Builds the NT Legacy family.")
    ap.add_argument("--only", choices=sorted(VARIANTS), help="only one variant")
    ap.add_argument("--check", action="store_true", help="lint afterwards")
    args = ap.parse_args()

    print(f"NT Legacy {VERSION}")
    # Before building, not after: a run that writes icons for twenty
    # minutes and says at the end that the color is no good has wasted
    # twenty minutes.
    if not check_selection():
        return 1
    selected = [args.only] if args.only else list(VARIANTS)
    for v in selected:
        if not build(v, args.check):
            return 1

    # The Konsole profile, one for all. The default points to the base
    # version; apply.sh switches the line to the chosen color world as
    # soon as appearance.sh has activated the profile.
    write_file(HERE / "konsole" / "NT Legacy.profile",
               konsole_profile(VARIANTS["teal"]["short"]))

    # The mapping global theme -> Konsole color scheme, as a table.
    #
    # It lives here and nowhere else. konsole-follow.sh later runs as a
    # service of its own on the user's machine and does not have build.py
    # at hand - without this file it would have to keep the names a second
    # time, and the next time a color world is added that second list
    # would be exactly the one nobody maintains. The same reason why
    # apply.sh gets its identifiers from build.py.
    #
    # One color scheme per color world, not per version - the night
    # version shares it with the light one (see konsole_scheme).
    lines = ["# Global theme\tKonsole color scheme",
             "# Generated by build.py - do not edit by hand."]
    for v in sorted(VARIANTS):
        base = v[:-len("-nacht")] if v.endswith("-nacht") else v
        if base in VARIANTS:
            lines.append(f"{ids(v)['lnf']}\t{ids(base)['schema']}")
    write_file(HERE / "konsole-variants.tsv", "\n".join(lines) + "\n")

    # Cursors once for all variants. They only differ in white and red - a
    # separate theme per color world would be clutter in the selection
    # dialog without any visible difference.
    print("\nMouse cursors:")
    for cname, fill, disp, disp_de in [
        ("NTLegacy_cursors", "#ffffff", "NT Legacy", "NT Legacy"),
        ("NTLegacyRot_cursors", "#c03028", "NT Legacy (red pointer)", "NT Legacy (roter Zeiger)"),
    ]:
        r = subprocess.run(
            [sys.executable, tool("gen-cursor.py"),
             "-o", str(HERE / "cursors"), "--name", cname,
             "--display-name", disp, "--display-name-de", disp_de, "--fill", fill],
            capture_output=True, text=True)
        print(r.stdout.rstrip() if r.returncode == 0
              else "  skipped: " + (r.stderr.strip().splitlines() or ["?"])[0])

    # The third-party sets downloaded by fetch-icons.sh. For a long time
    # this only said "NTLegacy" - since there is a second one
    # (NTLegacySE98), whatever is there is used. fetch-icons.sh already
    # creates the aliases itself; the run here catches the case that
    # someone replaced the set by hand or used the script of an older
    # version.
    third_party = sorted(p for p in (HERE / "icons").glob("*")
                         if (p / "index.theme").is_file())
    if third_party:
        print("\nSymbolic aliases:")
        for icons in third_party:
            r = subprocess.run(
                [sys.executable, tool("gen-symbolic-aliases.py"),
                 str(icons)], capture_output=True, text=True)
            line = r.stdout.strip().splitlines()
            print(f"  {icons.name}: {line[0] if line else '—'}")

    # The night version of the icon set. Purely derived from the light
    # set - the same images, only breeze-dark as fallback. That is why it
    # is not in the repo but is created anew on every build.
    light_set = HERE / "icons-nt" / "NTLegacyIcons"
    if light_set.is_dir():
        r = subprocess.run(
            [sys.executable, tool("make-night-icons.py"),
             str(light_set)], capture_output=True, text=True)
        print("\nIcons for the night versions:")
        print(r.stdout.rstrip() if r.returncode == 0
              else "  ERROR: " + (r.stderr.strip().splitlines() or ["?"])[-1])

    print(f"\nDone ({len(selected)} variants). To install: ./install.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
