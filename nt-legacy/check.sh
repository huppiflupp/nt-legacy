#!/usr/bin/env bash
# Checks whether build.py and apply.sh mean the same thing.
#
# Why this exists: when the mouse cursors were rebuilt into two global sets,
# build.py was adjusted, apply.sh was not. Five of six variants
# then pointed to a cursor theme that is no longer built at all -
# it was only noticed in the stability test, from a log line.
#
# For every variant this script compares whether all the components
# apply.sh refers to were actually generated.
#
#   ./check.sh          # against the build directory
#   ./check.sh --system # additionally against the installed system

set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
SYSTEM=false
[ "${1:-}" = "--system" ] && SYSTEM=true

errors=0
report() { echo "  MISSING  $*"; errors=$((errors + 1)); }

# The variant list comes from build.py, not from a second copy -
# otherwise there would be two sources of truth again.
variants=$(python3 -c "
import importlib.util
s = importlib.util.spec_from_file_location('b', '$HERE/build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
for k in m.VARIANTS:
    i = m.ids(k)
    print(k, i['style'], i['schema'], i['aurorae'], i['lnf'], i['wallpaper'])
")

printf '%-14s %s\n' "Variant" "Components"
while read -r name style schema aurorae lnf wallpaper; do
    [ -z "$name" ] && continue
    before=$errors
    [ -d "$HERE/desktoptheme/$style" ]        || report "$name: desktoptheme/$style"
    [ -f "$HERE/color-schemes/$schema.colors" ] || report "$name: color-schemes/$schema.colors"
    [ -d "$HERE/aurorae/$aurorae" ]           || report "$name: aurorae/$aurorae"
    [ -d "$HERE/look-and-feel/$lnf" ]         || report "$name: look-and-feel/$lnf"
    [ -d "$HERE/wallpapers/$wallpaper" ]      || report "$name: wallpapers/$wallpaper"
    [ -f "$HERE/look-and-feel/$lnf/contents/previews/preview.png" ] \
        || report "$name: preview image"

    # The Aurorae theme must carry the prefix that contents/defaults sets
    d="$HERE/look-and-feel/$lnf/contents/defaults"
    if [ -f "$d" ]; then
        expected=$(grep -oP '(?<=^theme=__aurorae__svg__).*' "$d" || true)
        [ "$expected" = "$aurorae" ] || report "$name: defaults points to '$expected', built is '$aurorae'"
        # Does defaults point to a cursor theme that exists?
        z=$(grep -oP '(?<=^cursorTheme=).*' "$d" || true)
        [ -z "$z" ] || [ -d "$HERE/cursors/$z" ] || report "$name: cursor theme '$z'"
    fi

    # Can apply.sh handle this variant at all? It now reads them
    # from build.py, so the dry run is enough.
    "$HERE/apply.sh" "$name" --check-only >/dev/null 2>&1 \
        || report "$name: apply.sh does not know it"

    [ "$errors" -eq "$before" ] && printf '%-14s ok\n' "$name"
done <<< "$variants"

if $SYSTEM; then
    echo
    echo "Installed:"
    while read -r name style schema aurorae lnf wallpaper; do
        [ -z "$name" ] && continue
        [ -d "$DATA/plasma/desktoptheme/$style" ] || report "installed: $style"
        [ -d "$DATA/plasma/look-and-feel/$lnf" ]  || report "installed: $lnf"
        [ -d "$DATA/aurorae/themes/$aurorae" ]    || report "installed: aurorae/$aurorae"
    done <<< "$variants"
    for z in NTLegacy_cursors NTLegacyRot_cursors; do
        [ -d "$DATA/icons/$z" ] || report "installed: $z"
    done
    # Both icon sets. The night set carries the same images but inherits
    # from breeze-dark - if it is missing, every night version falls back to the light
    # set and half of the system tray becomes invisible.
    for icon_set in NTLegacyIcons NTLegacyIconsNacht; do
        [ -d "$DATA/icons/$icon_set" ] || report "installed: icon theme $icon_set"
    done
    if [ -f "$DATA/icons/NTLegacyIconsNacht/index.theme" ] && \
       ! grep -q '^Inherits=breeze-dark' "$DATA/icons/NTLegacyIconsNacht/index.theme"; then
        report "NTLegacyIconsNacht does not inherit from breeze-dark"
    fi
    # Without FollowsColorScheme KDE does not recolour the inherited Breeze icons
    # - their colour then depends solely on the set entered (issue 1).
    for icon_set in NTLegacyIcons NTLegacyIconsNacht; do
        idx="$DATA/icons/$icon_set/index.theme"
        [ -f "$idx" ] || continue
        grep -q '^FollowsColorScheme=true' "$idx" || \
            report "$icon_set: FollowsColorScheme=true missing (icons do not follow the colour scheme)"
    done

    # Is the icon theme really in kdeglobals?
    #
    # It is not enough for it to be in contents/defaults. KDE programs
    # get the right icons through the defaults cascade even
    # when the key is missing in kdeglobals - but pure Qt programs
    # (pcmanfm-qt, many third-party applications) only read the file and
    # otherwise end up with Breeze. So of all places, you do not see the bug in
    # Dolphin.
    #
    # Happens regularly: a theme switch via System Settings >
    # Global Theme rewrites the group and leaves it empty.
    if [ -z "$(kreadconfig6 --file kdeglobals --group Icons --key Theme 2>/dev/null)" ]; then
        report "kdeglobals [Icons] Theme is empty - pure Qt programs show Breeze icons"
        echo "         Fix:  kwriteconfig6 --file kdeglobals --group Icons --key Theme NTLegacy"
    fi
fi

echo
if [ "$errors" -eq 0 ]; then
    echo "All consistent."
else
    echo "$errors inconsistencies."
fi
exit $((errors > 0))
