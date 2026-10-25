#!/usr/bin/env bash
# Applies an NT Legacy variant.
#
#   ./apply.sh              # base version (petrol)
#   ./apply.sh lilac        # lilac
#   ./apply.sh desert       # desert
#   ./apply.sh teal-nacht   # night version (also lilac-nacht, desert-nacht)
#   ./apply.sh teal --red   # with the red mouse cursor
#   ./apply.sh teal --panel # plus the NT panel (replaces the existing one)
#
# Why this script exists:
#
# For a long time this said Plasma does not reliably pick up the defaults
# from contents/defaults - "measured in the test VM, all keys stayed empty".
# That was a MEASUREMENT ERROR, rechecked on 9.8.2026:
#
# At session start Plasma puts ~/.config/kdedefaults in front of the
# configuration cascade (XDG_CONFIG_DIRS). When a global theme is
# applied, the values land exactly there - as defaults, not as
# user values (libklookandfeel/klookandfeelmanager.cpp, writeNewDefaults:
# write the default, then revertToDefault on the user value).
#
# Whoever measures over SSH does NOT have this directory in the cascade.
# kreadconfig6 then returns empty values although everything is set correctly.
# That is exactly how the wrong diagnosis came about.
#
# Measured with the correct cascade, "plasma-apply-lookandfeel --apply"
# alone sets every layer: ColorScheme, widgetStyle, plasmarc/Theme, icons,
# mouse cursor, window decoration, splash screen - and the colour values
# land in kdeglobals.
#
# Second consequence: the kwriteconfig6 calls below write
# NOTHING as long as the value matches the default - KConfig stores
# no entry that equals the cascaded default. Proven in the test VM:
# after 'kwriteconfig6 ... widgetStyle Windows' the key was
# still only in kdedefaults, not in kdeglobals.
#
# They stay anyway, because they take effect when the default is missing
# or differs - for example after an installation via "Get New …",
# where there is no global theme at all. They cannot do any harm:
# what is equal is not written.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARIANT="${1:-teal}"
RED=false
FONT=false
PANEL=false
for arg in "$@"; do
    [[ "$arg" == "--red" ]] && RED=true
    [[ "$arg" == "--font" ]] && FONT=true
    [[ "$arg" == "--panel" ]] && PANEL=true
    if [[ "$arg" == "--help" || "$arg" == "-h" ]]; then
        # The list comes from build.py, not from a second one here -
        # for the same reason as below with the IDs.
        sed -n '3,9p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
        echo "Variants:"
        (cd "$HERE" && python3 -c "
import importlib.util
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
for v in sorted(m.VARIANTS):
    print('  %-14s %s' % (v, m.VARIANTS[v]['description']))
")
        exit 0
    fi
done
[[ "$VARIANT" == --* ]] && VARIANT="teal"

# The IDs come from build.py, not from a second list here.
# They used to be listed twice - when win98/win2k were added, only
# build.py was maintained, and the new variants could not be reached
# through apply.sh at all. One source of truth, no syncing needed.
#
# The day/night counterpart of the same colour world comes along as well.
# Since 6, Plasma has a built-in switcher (kded module
# lookandfeelautoswitcher) that changes between DefaultLightLookAndFeel
# and DefaultDarkLookAndFeel at sunrise and sunset. If you enter
# a mixed pair there, the machine jumps from one colour world into
# another in the evening - on the development machine it had
# 'desert' as the light and 'teal-nacht' as the dark version.
IDS=$(cd "$HERE" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
v = sys.argv[1]
if v not in m.VARIANTS:
    print('UNKNOWN ' + ' '.join(sorted(m.VARIANTS)))
else:
    i = m.ids(v)
    # The pair: the base is the colour world without '-nacht'.
    base = v[:-len('-nacht')] if v.endswith('-nacht') else v
    light = m.ids(base)['lnf'] if base in m.VARIANTS else ''
    dark = m.ids(base + '-nacht')['lnf'] if base + '-nacht' in m.VARIANTS else ''
    # The Konsole colour scheme exists per colour world, not per version -
    # hence the short name of the light version, also for the night one.
    konsole = m.ids(base)['schema'] if base in m.VARIANTS else ''
    print(i['schema'], i['style'], i['lnf'], light or '-', dark or '-',
          konsole or '-', i['icons'])
" "$VARIANT")

if [ "${IDS%% *}" = "UNKNOWN" ]; then
    echo "Unknown variant '$VARIANT'." >&2
    echo "Possible: ${IDS#UNKNOWN }" >&2
    exit 1
fi
read -r SHORT STYLE LNF LNF_LIGHT LNF_DARK KONSOLE ICONS <<< "$IDS"

# All IDs must be set. If one comes out empty, the script would otherwise
# write empty values into the configuration and call the
# plasma-apply tools with an empty name - which produces messages like
# "Could not find theme """ that nobody can trace back to a theme.
for field in SHORT STYLE LNF KONSOLE ICONS; do
    if [ -z "${!field}" ]; then
        echo "ERROR: ID '$field' is empty (variant '$VARIANT')." >&2
        echo "       This is a bug in the theme, not on your machine." >&2
        echo "       Please report it: $(sed -n 's/^WEBSITE = "\(.*\)"/\1/p' "$HERE/build.py" | head -1)" >&2
        exit 1
    fi
done

# Dry run: only check that the variant exists, apply nothing.
# Used by check.sh.
for arg in "$@"; do [[ "$arg" == "--check-only" ]] && exit 0; done

# There is only one set of cursors for all variants - they differ
# in white and red, not by colour world. This used to say
# "${SHORT}_cursors", which pointed nowhere for five of six variants.
CURSOR="NTLegacy_cursors"
$RED && CURSOR="NTLegacyRot_cursors"

# Is the theme installed at all? Without this check the
# script reports success, writes all keys pointing at themes that do not exist and
# refers to a backup that never existed.
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
if [ ! -d "$DATA/plasma/look-and-feel/$LNF" ]; then
    echo "ERROR: '$LNF' is not installed." >&2
    echo "       Run  ./install.sh  first." >&2
    exit 1
fi
if [ ! -d "$DATA/icons/$CURSOR" ]; then
    echo "Note: mouse cursor '$CURSOR' is missing - the system cursor stays." >&2
    CURSOR=""
fi

if $RED; then echo "Applying: $SHORT (red cursor)"; else echo "Applying: $SHORT"; fi

# ── Back up the panel ────────────────────────────────────────────────────
#
# Every look-and-feel package brings a panel layout
# (contents/layouts/org.kde.plasma.desktop-layout.js) that removes ALL
# existing panels and builds the NT panel from scratch.
#
# It is applied in two cases: with --panel here, and when someone
# also selects the desktop layout while switching themes in System Settings.
# The second case is the more common one, and it hits the
# user without warning - so a backup is always made here, even without
# --panel. A copy costs nothing, a lost panel does.
#
# install.sh backs up appletsrc only once, before the installation. That no
# longer helps on the tenth variant switch.
APPLETSRC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
PANEL_COPY=""
if [ -f "$APPLETSRC" ]; then
    mkdir -p "$DATA/nt-legacy/panel"
    PANEL_COPY="$DATA/nt-legacy/panel/appletsrc-$(date +%Y%m%d-%H%M%S)"
    cp -a "$APPLETSRC" "$PANEL_COPY"
    # Keep only the last ten. Without this the directory grows by
    # another copy on every switch - and whoever compares variants
    # switches often.
    ls -1t "$DATA/nt-legacy/panel"/appletsrc-* 2>/dev/null \
        | tail -n +11 | xargs -r rm -f || true
fi

# Global theme first - it sets the frame, we refine the rest.
#
# Without --resetLayout the user's panel and wallpaper stay as they are.
# That is the default, because a theme should not clear away the panel
# without asking - but it has a side effect that nobody noticed for a long time:
#
# Fedora's default panel floats. Plasma draws a floating panel
# with the rounded variants from translucent/, and NT Legacy
# looks dark and alien in it - nothing about it is reminiscent of NT. Only
# with its own layout (panel at the edge, 30 pixels, not floating) does
# it look like in the screenshots.
#
# Proven in the test VM on 'clean': the same Plasma style, once
# without and once with --resetLayout - only with the layout is the picture right.
#
# The output is kept and only shown on failure.
#
# This used to say ">/dev/null 2>&1 || true": every message was dropped,
# including "Unable to find the theme named …". Exactly such a case
# came back from the community - error while applying, theme not active, and
# nobody could say afterwards which message it had been. Conversely,
# a successful run should stay quiet: plasma-apply-lookandfeel writes
# lines nobody needs even then (such as xrdb warnings under
# Wayland).
LNF_LOG="$(mktemp)"
trap 'rm -f "$LNF_LOG"' EXIT
if $PANEL; then
    echo "  Panel is being replaced by the NT layout (backup see below)."
    plasma-apply-lookandfeel --apply "$LNF" --resetLayout >"$LNF_LOG" 2>&1 || true
else
    plasma-apply-lookandfeel --apply "$LNF" >"$LNF_LOG" 2>&1 || true
fi
if grep -qi "unable to find\|could not find\|error" "$LNF_LOG"; then
    echo "  Warning: plasma-apply-lookandfeel reports:" >&2
    sed 's/^/    /' "$LNF_LOG" >&2
    echo "  The layers are set individually anyway." >&2
fi

kwriteconfig6 --file plasmarc   --group Theme   --key name          "$STYLE"
kwriteconfig6 --file kdeglobals --group General --key ColorScheme   "$SHORT"
kwriteconfig6 --file kdeglobals --group KDE     --key widgetStyle   Windows

# The application style needs special treatment.
#
# As a default in ~/.config/kdedefaults/kdeglobals it is NOT read by
# Qt applications - proven in the test VM: after logging in
# it said 'Windows' there, and still every application started with Breeze.
# Only an entry in the user file takes effect.
#
# But that is exactly what kwriteconfig6 cannot write: KConfig stores
# no value that equals the cascaded default - the line
# above is therefore ineffective as soon as a global theme specifies
# the same. Hence explicitly bypassing KConfig here.
python3 - <<'PY' || true
import re, pathlib
p = pathlib.Path.home() / ".config" / "kdeglobals"
if p.exists():
    t = p.read_text()
    if re.search(r"^widgetStyle=", t, re.M):
        t = re.sub(r"^widgetStyle=.*$", "widgetStyle=Windows", t, flags=re.M)
    elif re.search(r"^\[KDE\]$", t, re.M):
        t = re.sub(r"^\[KDE\]$", "[KDE]\nwidgetStyle=Windows", t, count=1, flags=re.M)
    else:
        t = t.rstrip("\n") + "\n\n[KDE]\nwidgetStyle=Windows\n"
    p.write_text(t)
PY
# The icon set depends on the version, not on the colour world: the
# night variants get NTLegacyIconsNacht. The same images, but with
# breeze-dark as fallback - otherwise Breeze draws the icons we
# do not supply ourselves in dark grey on the dark panel.
kwriteconfig6 --file kdeglobals --group Icons   --key Theme         "$ICONS"
kwriteconfig6 --file kdeglobals --group KDE     --key LookAndFeelPackage "$LNF"

# Konsole: update the colour scheme of the colour world in the bundled
# profile. This is NOT meddling with someone else's configuration - the file
# belongs to the theme. Whether Konsole uses it at all is decided
# by konsolerc alone, and only appearance.sh sets that.
PROFILE="$DATA/konsole/NT Legacy.profile"
if [ "$KONSOLE" != "-" ] && [ -f "$PROFILE" ]; then
    kwriteconfig6 --file "$PROFILE" --group Appearance --key ColorScheme "$KONSOLE"
fi

# Store the day/night pair of the same colour world. Whoever turns on
# automatic switching in System Settings thus stays
# in the chosen colour world and only switches between light and
# dark. The switcher itself is NOT turned on - that is the
# user's decision, not the theme's.
if [ "$LNF_LIGHT" != "-" ] && [ "$LNF_DARK" != "-" ]; then
    kwriteconfig6 --file kdeglobals --group KDE --key DefaultLightLookAndFeel "$LNF_LIGHT"
    kwriteconfig6 --file kdeglobals --group KDE --key DefaultDarkLookAndFeel  "$LNF_DARK"
fi
[ -n "$CURSOR" ] && kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "$CURSOR"
# Activate our own splash screen. Neither plasma-apply-lookandfeel
# nor the defaults set it - without this line Splash.qml never runs.
kwriteconfig6 --file ksplashrc  --group KSplash --key Theme  "$LNF"
kwriteconfig6 --file ksplashrc  --group KSplash --key Engine KSplashQML
# Deliberately the v1 library, not org.kde.kwin.aurorae.v2:
#
# The v2 plugin only exists from Plasma 6.6 on. On 6.0 to 6.5
# loading fails and KWin silently falls back to Breeze - the user sees
# Breeze window frames and no error message.
#
# Conversely, v1 costs nothing on new systems: KWin upgrades the line
# to .v2 itself at session start (migrateAuroraeTheme in
# decorations/decorationbridge.cpp). Rechecked in the test VM with Plasma 6.7
# - after a restart it said .v2 there.
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme "__aurorae__svg__$SHORT"

# The title font is deliberately NOT written here.
#
# It is a default in contents/defaults - there it takes effect once when
# the global theme is applied, and after that the user keeps their
# choice in System Settings > Fonts > Window title.
# If apply.sh set it on every call, that setting would be
# ineffective. Breeze sets no font at all for the same reason.
#
# Whoever explicitly wants the bold NT title font:
#   ./apply.sh <variant> --font

if $FONT; then
    # The fifth field of a Qt font spec is the weight: 50 normal,
    # 75 bold. Aurorae has no option of its own for this.
    kwriteconfig6 --file kdeglobals --group WM --key activeFont \
        "Noto Sans,10,-1,5,75,0,0,0,0,0"
    echo "  Title font set to bold."
fi

# The render cache carries the theme name and version. Without deleting it you
# see the old image after an update and look for the bug in the wrong place.
rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements" \
      "$HOME/.cache/icon-cache.kcache"

# --- Take effect without killing the shell -------------------------------
#
# This used to contain an unconditional
#   systemctl --user restart plasma-plasmashell.service
# That is the most dangerous line this script ever had:
# plasma-plasmashell.service allows three starts in 60 seconds
# (StartLimitBurst=3, StartLimitIntervalSec=60s), and the session start
# counts as the first. On the THIRD apply.sh within a minute
# systemd gives up - no panel, no desktop, no application launcher. And it
# does not recover by itself; in the test VM the screen was still
# black after 100 seconds.
#
# But that is exactly how someone trying out themes clicks: three variants
# in a row.
#
# Hence three stages now:
#   1. plasma-apply-* switch at runtime - that is how System Settings
#      does it too, without any restart.
#   2. KWin gets a reconfigure instead of a restart.
#   3. Only if plasmashell is really not running afterwards is it started -
#      with a reset-failed first, so the counter does not get in the way.

# Here too: quiet on success, visible on failure. "Could not find
# theme" with an empty name was the message reported from the community,
# without anyone being able to tell afterwards where it came from.
at_runtime() {
    local tool="$1" name="$2"
    if [ -z "$name" ]; then
        echo "  Warning: empty name for $tool - skipped." >&2
        return
    fi
    # The exit status alone is not enough: plasma-apply-desktoptheme reports
    # "Could not find theme" and still exits with 0.
    if "$tool" "$name" >"$LNF_LOG" 2>&1 \
       && ! grep -qi "could not find\|unable to find" "$LNF_LOG"; then
        return
    fi
    echo "  Warning: $tool '$name' failed:" >&2
    sed 's/^/    /' "$LNF_LOG" >&2
}
at_runtime plasma-apply-desktoptheme "$STYLE"
at_runtime plasma-apply-colorscheme  "$SHORT"

# Let KWin re-read the decoration. KWin only loads the Aurorae THEME itself
# at session start, though - hence the note below.
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 \
    || qdbus-qt6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 \
    || qdbus org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true

if command -v systemctl >/dev/null; then
    if ! systemctl --user is-active --quiet plasma-plasmashell.service; then
        echo "  plasmashell is not running - restarting."
        # Without reset-failed the start limit kicks in and the start
        # is refused.
        systemctl --user reset-failed plasma-plasmashell.service 2>/dev/null || true
        systemctl --user start plasma-plasmashell.service 2>/dev/null || true
    fi
fi

# ── Check the panel afterwards ───────────────────────────────────────────
#
# Up to 0.2.14 there was a loop here that stretched the panel to the
# screen width six times, because "panel.length" reported 456 instead of 1024.
#
# The measurement was wrong. "length" returns the width of the CONTENT, not
# the drawn width of the panel; in the test VM a panel
# drawn across the full width reports 388 of 1280. So the loop
# fixed a bug that did not exist - and in doing so
# nailed minimumLength and maximumLength to the same value, which pins the
# panel to a fixed size. On a second screen of a
# different width that is exactly wrong.
#
# What remains is the helper function: pinning the Task Manager
# needs it.
if $PANEL; then
    plasma_script() {
        if command -v qdbus6 >/dev/null; then
            qdbus6 org.kde.plasmashell /PlasmaShell evaluateScript "$1" 2>/dev/null
        elif command -v qdbus >/dev/null; then
            qdbus org.kde.plasmashell /PlasmaShell evaluateScript "$1" 2>/dev/null
        elif command -v qdbus-qt6 >/dev/null; then
            qdbus-qt6 org.kde.plasmashell /PlasmaShell evaluateScript "$1" 2>/dev/null
        else
            dbus-send --session --print-reply --dest=org.kde.plasmashell \
                /PlasmaShell org.kde.PlasmaShell.evaluateScript \
                "string:$1" 2>/dev/null
        fi
    }

    # One panel per screen - check whether the layout managed
    # that. Report instead of repairing: whoever intervenes here may
    # end up creating a second panel on the same screen.
    sleep 3
    PANEL_STATE="$(plasma_script 'var ps = panels();
var s = "";
for (var i = 0; i < ps.length; i++) { s += (s ? "," : "") + ps[i].screen; }
print(ps.length + ":" + screenCount + ":" + s);' | tr -d '\r\n')"
    COUNT="${PANEL_STATE%%:*}"
    REST="${PANEL_STATE#*:}"
    SCREENS="${REST%%:*}"
    if [ -n "$COUNT" ] && [ -n "$SCREENS" ] && [ "$COUNT" -lt "$SCREENS" ] 2>/dev/null; then
        echo "  Note: $COUNT panel(s) on $SCREENS screens." >&2
        echo "        The others have no taskbar. Right-click" >&2
        echo "        the desktop > Add Panel, or" >&2
        echo "        log out and back in once." >&2
    fi

    # ── Pin the NT Task Manager ──────────────────────────────────────────
    #
    # Only here, not in the layout script of the theme package. The layout goes
    # to everyone who downloads the theme from the store; a pinned
    # launcher for a program that is not installed there would be
    # a dead entry for most people. Bash can check, the
    # Plasma scripting language cannot - it has no file access.
    #
    # And only with --panel: without it the panel belongs to the user, and
    # a theme pins nothing in it.
    TM_DESKTOP=""
    for dir in "$DATA/applications" /usr/local/share/applications \
               /usr/share/applications; do
        if [ -f "$dir/nt-taskmanager.desktop" ]; then
            TM_DESKTOP="nt-taskmanager.desktop"
            break
        fi
    done
    if [ -n "$TM_DESKTOP" ]; then
        # readConfig returns the list as a string with commas.
        # Pinning twice would be visible: icontasks then shows the launcher
        # twice side by side.
        TM_JS='var result = "NO-TASKMANAGER";
var ps = panels();
for (var i = 0; i < ps.length; i++) {
    var ws = ps[i].widgets("org.kde.plasma.icontasks");
    for (var j = 0; j < ws.length; j++) {
        ws[j].currentConfigGroup = ["General"];
        var l = String(ws[j].readConfig("launchers", ""));
        if (l.indexOf("nt-taskmanager.desktop") >= 0) {
            result = "ALREADY-THERE";
            continue;
        }
        ws[j].writeConfig("launchers",
            l ? l + ",applications:nt-taskmanager.desktop"
              : "applications:nt-taskmanager.desktop");
        ws[j].reloadConfig();
        result = "PINNED";
    }
}
print(result);'
        TM_RESULT="$(plasma_script "$TM_JS" | tr -d '\r\n')"
        case "$TM_RESULT" in
            *PINNED*)        echo "  NT Task Manager pinned to the taskbar." ;;
            *ALREADY-THERE*) echo "  NT Task Manager was already pinned." ;;
            *)               echo "  Note: the launcher for the NT Task Manager" >&2
                             echo "        could not be pinned." >&2 ;;
        esac
    fi
fi

cat <<EOF

Applied.

  For the window decoration to take effect, log out and back in once.
  KWin loads Aurorae themes only at session start.

  To undo:   ~/.local/share/nt-legacy/backup-*/restore.sh
EOF

if ! $PANEL; then
    cat <<EOF
  Your panel stays unchanged. Fedora's default panel floats and looks
  dark and alien in the NT style - it only looks like the screenshots
  with the theme's own panel:

    ./apply.sh $VARIANT --panel

EOF
fi

# The note is deliberately here and not in the heredoc above: it only applies
# if a copy was actually made.
if [ -n "$PANEL_COPY" ]; then
    cat <<EOF
  Was your panel different before? The theme replaced it. Undo with:

    cp "$PANEL_COPY" "$APPLETSRC"
    systemctl --user restart plasma-plasmashell.service

  (without systemd: kquitapp6 plasmashell; setsid -f plasmashell)

EOF
fi
