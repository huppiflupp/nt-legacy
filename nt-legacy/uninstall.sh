#!/usr/bin/env bash
# Removes NT Legacy completely.
#
# The order matters: reset the configuration first, then
# delete the files. The other way round, kwinrc points to an Aurorae theme
# that no longer exists - and then KWin draws NO title bar
# AT ALL. No fallback, no close button, no drag area.
# Proven in the test VM: only if the "library" is invalid does KWin
# fall back to Breeze; a theme name pointing nowhere loads Aurorae and
# draws nothing.
#
# The same goes for the icon theme: if the directory is missing while
# kdeglobals points to it, launcher and systray icons disappear
# completely instead of falling back to Breeze.

set -euo pipefail

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"

echo "Resetting configuration to Breeze …"
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme   Breeze
kwriteconfig6 --file kdeglobals --group Icons   --key Theme        breeze
kwriteconfig6 --file kdeglobals --group KDE     --key widgetStyle  Breeze
kwriteconfig6 --file kdeglobals --group General --key ColorScheme   BreezeLight
kwriteconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage org.kde.breeze.desktop
kwriteconfig6 --file plasmarc   --group Theme   --key name          default
kwriteconfig6 --file kcminputrc --group Mouse   --key cursorTheme   breeze_cursors
kwriteconfig6 --file ksplashrc  --group KSplash --key Theme         org.kde.breeze.desktop

echo "Removing packages …"
for d in "$DATA"/plasma/desktoptheme/nt-legacy*; do
    [ -d "$d" ] || continue
    kpackagetool6 -t Plasma/Theme -r "$(basename "$d")" >/dev/null 2>&1 || true
    rm -rf "$d"; echo "  $(basename "$d")"
done
for d in "$DATA"/plasma/look-and-feel/com.github.huppiflupp.nt-legacy*; do
    [ -d "$d" ] || continue
    kpackagetool6 -t Plasma/LookAndFeel -r "$(basename "$d")" >/dev/null 2>&1 || true
    rm -rf "$d"; echo "  $(basename "$d")"
done

rm -rf "$DATA"/aurorae/themes/NTLegacy*      && echo "  Window decorations"

# Clean up empty shells. rmdir instead of rm -rf: it fails if there is still
# something inside - that is exactly the safeguard here. Whoever has installed
# a second theme next to NT Legacy should keep it.
for d in "$DATA"/plasma/desktoptheme "$DATA"/plasma/look-and-feel \
         "$DATA"/aurorae/themes "$DATA"/aurorae; do
    rmdir "$d" 2>/dev/null && echo "  empty directory $d removed"
done
# All four icon sets, not just one.
#
# Up to 0.2.13 this said only "$DATA/icons/NTLegacy" - that is the
# Chicago95 offshoot from fetch-icons.sh. The two bundled sets
# NTLegacyIcons and NTLegacyIconsNacht stayed behind, and with them the
# impression that the uninstall had not worked. Noticed in the Arch test VM
# when the starting state after uninstall.sh was not the old one
# again.
#
# Then there is NTLegacySE98 - the second set from fetch-icons.sh. With
# around 32,000 links it is the largest of all; if it stays behind,
# you notice it in the disk space.
rm -rf "$DATA"/icons/NTLegacy "$DATA"/icons/NTLegacySE98 \
       "$DATA"/icons/NTLegacyIcons \
       "$DATA"/icons/NTLegacyIconsNacht      && echo "  Icons"
rm -rf "$DATA"/icons/NTLegacy*_cursors         2>/dev/null || true
rm -rf "$DATA"/wallpapers/ntlegacy*           && echo "  Wallpapers"
rm -f  "$DATA"/color-schemes/NTLegacy*.colors && echo "  Colour schemes"

# Clean up the defaults file of the global theme.
#
# ~/.config/kdedefaults/ belongs to the most recently applied theme: Plasma
# stores the values there as defaults, not as user values. After
# uninstalling it still said "Theme=NTLegacyIcons" - a reference
# to an icon set we had just deleted.
#
# The backup does not cover this: install.sh copies ~/.config, not
# ~/.config/kdedefaults. Hence our own lines are removed specifically here -
# and only our own. Whoever has applied another theme in the meantime
# keeps its defaults untouched.
KDD="$HOME/.config/kdedefaults"
if [ -d "$KDD" ]; then
    cleaned=false
    for f in "$KDD"/*; do
        [ -f "$f" ] || continue
        if grep -qE "=.*(NTLegacy|nt-legacy)" "$f" 2>/dev/null; then
            sed -i -E "/=.*(NTLegacy|nt-legacy)/d" "$f"
            cleaned=true
        fi
    done
    $cleaned && echo "  Defaults in kdedefaults"
fi

# Konsole: reset konsolerc first, then delete the files.
# If DefaultProfile points to a deleted profile, Konsole does start,
# but falls back to an empty default profile - including
# a lost window size and history length.
if [ "$(kreadconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile 2>/dev/null)" = "NT Legacy.profile" ]; then
    kwriteconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile --delete
    echo "  Konsole back on its default profile"
fi
rm -f "$DATA"/konsole/NTLegacy*.colorscheme "$DATA/konsole/NT Legacy.profile" \
    && echo "  Konsole profile and colour schemes"

# The service that makes Konsole follow the theme switch.
#
# It has to be switched off BEFORE the script is deleted - an
# enabled path unit whose service points to a deleted file
# logs a failed start to the journal on every theme switch. Nothing of it
# is visible, and that is exactly why it would otherwise stay around forever.
#
# appearance.sh --revert does the same. Doing it twice is right here: whoever
# uninstalls may never have reverted the appearance.
SERVICE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
if [ -f "$SERVICE_DIR/nt-legacy-konsole.path" ]; then
    systemctl --user disable --now nt-legacy-konsole.path >/dev/null 2>&1 || true
    rm -f "$SERVICE_DIR/nt-legacy-konsole.path" \
          "$SERVICE_DIR/nt-legacy-konsole.service"
    systemctl --user daemon-reload 2>/dev/null || true
    echo "  Service nt-legacy-konsole"
fi
rm -rf "$DATA/nt-legacy/bin" "$DATA/nt-legacy/konsole-variants.tsv"

rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements"

cat <<TEXT

Removed. Log out and back in.

The backups under $DATA/nt-legacy/ stay where they are - they hold the
state from before the installation, in case you need it.
TEXT
