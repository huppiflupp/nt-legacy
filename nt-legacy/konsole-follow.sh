#!/usr/bin/env bash
# Makes the Konsole colour scheme follow the global theme.
#
#   ./konsole-follow.sh            # update once
#   ./konsole-follow.sh --show     # only say what it would do
#
# Why this is needed:
#
# Konsole does not follow the system colour scheme. That is not a gap
# in this theme but a property of the program: the colour scheme
# of a terminal lives in the PROFILE, and a profile is a file that
# Konsole alone manages. Plasma does not touch it when switching themes,
# and Konsole has no "follow the system" switch.
#
# apply.sh therefore switches the line itself. But: whoever switches the theme via
# System Settings > Theme never calls apply.sh - and
# that is exactly the usual route. The terminal then stayed in the old
# colour world while everything else switched.
#
# This script closes the gap. It does not run all the time,
# but is kicked off by a systemd path unit when Plasma writes its
# defaults files (see appearance.sh).
#
# A limit that remains: an ALREADY OPEN Konsole window keeps its
# colours. Konsole reads the profile when a session is created; there is no way
# to tell it from outside to re-read it
# (neither via D-Bus nor via a signal). The next new window
# or tab comes out right.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"

SHOW=false
[ "${1:-}" = "--show" ] && SHOW=true

PROFILE="$DATA/konsole/NT Legacy.profile"

# The mapping comes from build.py, not from a second list here.
# In the working tree it sits next to this script, installed under
# nt-legacy/. If it is missing, that is not the user's fault but an
# incomplete package - hence a message and not a silent exit.
TABLE=""
for candidate in "$HERE/konsole-variants.tsv" \
                 "$DATA/nt-legacy/konsole-variants.tsv"; do
    [ -f "$candidate" ] && { TABLE="$candidate"; break; }
done
if [ -z "$TABLE" ]; then
    echo "konsole-follow: konsole-variants.tsv not found." >&2
    exit 1
fi

# Which global theme is currently active?
#
# ~/.config/kdedefaults/package is the more reliable source: Plasma
# writes it when applying, and it contains exactly one line with the
# ID. kdeglobals is read as a fallback - the value is only there
# if someone has set it explicitly (such as apply.sh).
THEME=""
if [ -f "$CONFIG/kdedefaults/package" ]; then
    THEME="$(tr -d '\r\n' < "$CONFIG/kdedefaults/package")"
fi
if [ -z "$THEME" ] && command -v kreadconfig6 >/dev/null; then
    THEME="$(kreadconfig6 --file kdeglobals --group KDE \
                          --key LookAndFeelPackage 2>/dev/null || true)"
fi
if [ -z "$THEME" ]; then
    $SHOW && echo "No global theme could be determined - nothing to do."
    exit 0
fi

SCHEME="$(awk -F'\t' -v d="$THEME" '$1 == d { print $2; exit }' "$TABLE")"

# A different theme is the normal case, not an error: whoever switches from NT Legacy
# to Breeze should keep their terminal. It would be intrusive
# to write an NT scheme into it then - and just as wrong to force
# the Breeze scheme on them, which they may never have wanted.
if [ -z "$SCHEME" ]; then
    $SHOW && echo "'$THEME' does not belong to NT Legacy - profile stays."
    exit 0
fi

if [ ! -f "$PROFILE" ]; then
    $SHOW && echo "Profile '$PROFILE' is missing - run ./install.sh first."
    exit 0
fi

OLD="$(kreadconfig6 --file "$PROFILE" --group Appearance \
                    --key ColorScheme 2>/dev/null || true)"

if [ "$OLD" = "$SCHEME" ]; then
    $SHOW && echo "Already correct: $THEME -> $SCHEME"
    exit 0
fi

if $SHOW; then
    echo "Would set: $THEME -> $SCHEME (currently '${OLD:-nothing}')"
    exit 0
fi

kwriteconfig6 --file "$PROFILE" --group Appearance --key ColorScheme "$SCHEME"
echo "konsole-follow: $THEME -> $SCHEME"
