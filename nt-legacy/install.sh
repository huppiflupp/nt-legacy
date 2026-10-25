#!/usr/bin/env bash
# Installs NT Legacy.
#
#   ./install.sh                    # install only
#   ./install.sh --apply            # then apply the base version
#   ./install.sh --apply win2k      # then apply this variant
#
# Touches nothing but $HOME, never asks for sudo, and backs up the
# configuration first. That makes the installation reversible in every case -
# that is the difference between a theme you can try out
# and one you have to think about first.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"

LNF_ID="com.github.huppiflupp.nt-legacy"
STYLE_ID="nt-legacy"

# ── Apply: the default is still "install only" ───────────────────────────
#
# From the community (cubanismo, KDE 6.6.5): after install.sh the theme was
# not active, and the final message suggested
# "plasma-apply-lookandfeel --apply …". That route is incomplete -
# the application style stays on Breeze, because Qt programs
# do not read the value from ~/.config/kdedefaults (reasoning in
# apply.sh). Whoever follows it ends up in System Settings and does
# the rest by hand.
#
# Hence two changes: the final message now names ./apply.sh,
# and with --apply install.sh takes care of the second step right away.
APPLY=false
VARIANT=""
for arg in "$@"; do
    case "$arg" in
        --apply) APPLY=true ;;
        -*)      echo "Unknown option '$arg'." >&2; exit 1 ;;
        *)       VARIANT="$arg" ;;
    esac
done

# ── Backup ───────────────────────────────────────────────────────────────
BACKUP="$DATA/nt-legacy/backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
# kcminputrc belongs here - otherwise the mouse cursor stays on NT Legacy
# after restoring.
for f in plasma-org.kde.plasma.desktop-appletsrc plasmarc kdeglobals \
         kwinrc ksplashrc kcminputrc; do
    if [ -f "$HOME/.config/$f" ]; then
        cp -a "$HOME/.config/$f" "$BACKUP/"
    else
        # The file does not exist yet - the common case on a fresh
        # account. Without a note restore.sh would not know that it has to
        # disappear again afterwards, and our values would stay in it.
        echo "$f" >> "$BACKUP/.war-nicht-vorhanden"
    fi
done
cat > "$BACKUP/restore.sh" <<'EOF'
#!/usr/bin/env bash
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in "$HERE"/*; do
    n="$(basename "$f")"
    case "$n" in restore.sh|README|.war-nicht-vorhanden) continue ;; esac
    cp -a "$f" "$HOME/.config/$n"; echo "  $n"
done

# Files that did not exist before the installation have to go again -
# otherwise our values stay in them. That is exactly how the
# Plasma style and mouse cursor used to survive a restore.sh.
if [ -f "$HERE/.war-nicht-vorhanden" ]; then
    while read -r n; do
        [ -n "$n" ] && [ -f "$HOME/.config/$n" ] && {
            rm -f "$HOME/.config/$n"
            echo "  $n removed (did not exist before)"
        }
    done < "$HERE/.war-nicht-vorhanden"
fi

# Explicitly reset the window decoration. If kwinrc points to a
# deleted Aurorae theme, KWin draws NO title bar AT ALL - no
# fallback, no close button. Proven in the test VM.
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 \
    --key library org.kde.breeze 2>/dev/null || true
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 \
    --key theme Breeze 2>/dev/null || true

rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements" \
      "$HOME/.cache/icon-cache.kcache"
echo ""
echo "Restored. Log out and back in."
EOF
chmod +x "$BACKUP/restore.sh"
echo "Backup: $BACKUP"

# ── Installation ─────────────────────────────────────────────────────────
# Call kpackagetool6 and filter out a known noise.
#
# From the community (cubanismo, Arch with Plasma 6.6.5): one line
# per installed Plasma style
#
#   qt.dbus.integration: QDBusConnection: error: could not send signal to
#   service "" path "/KPackage/" interface "org.kde.plasma.kpackage"
#   member "packageInstalled": Invalid object path: /KPackage/
#
# This is NOT a bug in this theme, nor in the installation: the
# packages land correctly. KPackage announces the successful installation over
# D-Bus and builds the object path from a prefix that is empty for
# Plasma/Theme - "/KPackage/" is invalid as a path, and Qt says so loudly.
#
# Reproduced: on Fedora with KF6 6.28 stderr stays empty, with the
# older libraries of Plasma 6.6.5 ten of these lines appear. The
# reporter took them for the reason the theme did not take effect, and
# fixed things up by hand - this filter protects against exactly that.
#
# Deliberately no blanket 2>/dev/null: real errors from kpackagetool6
# must stay visible.
kpackage() {
    local errors rc=0
    errors="$(mktemp)"
    kpackagetool6 "$@" >/dev/null 2>"$errors" || rc=$?
    grep -v "^qt\.dbus\.integration:" "$errors" >&2 || true
    rm -f "$errors"
    return $rc
}

# kpackagetool6 instead of cp -r: it checks the metadata, stores under the
# right Id and can uninstall cleanly again.
install_package() {
    local type="$1" path="$2" target="$3"
    # First -u (upgrade), then -r + -i. The upgrade fails if the
    # directory exists but the package is not registered - then
    # -i fails too with "already exists". Without this route
    # every second installation fails.
    if kpackage -t "$type" -u "$path" 2>/dev/null; then
        return 0
    fi
    kpackage -t "$type" -r "$(basename "$path")" 2>/dev/null || true
    rm -rf "$target"
    kpackage -t "$type" -i "$path"
}

echo "Plasma styles …"
for d in "$HERE"/desktoptheme/*/; do
    n="$(basename "$d")"
    install_package Plasma/Theme "${d%/}" "$DATA/plasma/desktoptheme/$n"
    echo "  $n"
done

echo "Colour scheme …"
install -Dm644 "$HERE/color-schemes/"*.colors -t "$DATA/color-schemes/"

# Third-party sets fetched by fetch-icons.sh: NTLegacy (Chicago95) and
# NTLegacySE98 (SE98). Both are optional, neither is in the repo. Nothing
# is looked up by name here; whatever is there is taken - so a third
# set later costs no further change.
if [ -d "$HERE/icons" ] && [ -n "$(ls -A "$HERE/icons" 2>/dev/null)" ]; then
    mkdir -p "$DATA/icons"
    for q in "$HERE/icons"/*/; do
        [ -d "$q" ] || continue
        s="$(basename "$q")"
        echo "Icons ($s, optional) …"
        # Remove first, then copy: a "cp" on top would write through the
        # links of the previous installation - the same trap as
        # below with NTLegacyIcons, here with even more links.
        rm -rf "${DATA:?}/icons/$s"
        cp -a "${q%/}" "$DATA/icons/"
        # Without an updated cache Plasma sometimes still shows the old icons
        command -v gtk-update-icon-cache >/dev/null && \
            gtk-update-icon-cache -q -t -f "$DATA/icons/$s" 2>/dev/null || true
    done
fi

# The bundled icon set. Unlike Chicago95 it is in the repo,
# because its origin is clear: drawn entirely by ourselves in
# tools/gen-icons.py, no third-party material taken over (ATTRIBUTION.md).
# It is the default; Chicago95 remains selectable alongside it if it was
# fetched with fetch-icons.sh.
if [ -d "$HERE/icons-nt" ]; then
    echo "Icons (NTLegacyIcons) …"
    # The night version is not in the repo - it is derived and
    # otherwise created in build.py. Whoever installs directly from a clone
    # does not have it yet; without it the night variants point to an
    # icon theme that does not exist on the machine.
    #
    # tools/ sits next to nt-legacy/ in the working tree, inside it in the archive.
    if [ ! -d "$HERE/icons-nt/NTLegacyIconsNacht" ]; then
        for w in "$HERE/tools/make-night-icons.py" \
                 "$HERE/../tools/make-night-icons.py"; do
            [ -f "$w" ] || continue
            python3 "$w" "$HERE/icons-nt/NTLegacyIcons" >/dev/null 2>&1 || true
            break
        done
    fi
    mkdir -p "$DATA/icons"
    # Remove the old directory first, then copy.
    #
    # A plain "cp -r" on top follows the links of the previous
    # installation: almost half of the set consists of symlinks, and
    # cp writes THROUGH them into the target file. That is how a new
    # start-here.png overwrote the gear of applications-system -
    # after that the launcher and System Settings showed the same
    # icon again, only this time both the wrong one.
    rm -rf "$DATA/icons/NTLegacyIcons" "$DATA/icons/NTLegacyIconsNacht"
    cp -a "$HERE/icons-nt/"* "$DATA/icons/"

    # Enter the previous icon theme as a fallback.
    #
    # From feedback: on EndeavourOS the system updater showed a
    # blank page after the switch. Its icon is called
    # "endeavouros-icon" and lives only in Qogir, the
    # distribution's icon theme - our set inherits from breeze and
    # hicolor, Qogir is not among them, so Plasma finds nothing.
    #
    # This affects every distribution-specific icon and happens the same way when
    # switching to Breeze. But we can catch it here: the
    # previously active theme goes BEFORE breeze in the Inherits line. Then
    # such icons keep their image, and everything else still comes from
    # us - the order decides, and we come first.
    #
    # The price should be stated honestly: in exactly these places two
    # visual languages mix. A blank page is the worse choice.
    previous_icon_theme() {
        local candidate src d
        # First the running state, then the backup just created
        # (it holds what applied before this installation), finally the
        # defaults of the global theme.
        for src in "$HOME/.config/kdeglobals" "$BACKUP/kdeglobals" \
                      "$HOME/.config/kdedefaults/kdeglobals"; do
            [ -f "$src" ] || continue
            candidate="$(sed -n '/^\[Icons\]/,/^\[/{s/^Theme=//p}' "$src" | head -1)"
            case "$candidate" in
                ""|NTLegacy|NTLegacySE98|NTLegacyIcons|NTLegacyIconsNacht|hicolor) continue ;;
            esac
            for d in "$DATA/icons/$candidate" "/usr/share/icons/$candidate"; do
                [ -d "$d" ] && { echo "$candidate"; return 0; }
            done
        done
        return 1
    }

    if FOREIGN="$(previous_icon_theme)"; then
        for icon_set in NTLegacyIcons NTLegacyIconsNacht; do
            idx="$DATA/icons/$icon_set/index.theme"
            [ -f "$idx" ] || continue
            # Only the first Inherits line, and only if the theme is not
            # already in it anyway.
            grep -q "^Inherits=.*\b$FOREIGN\b" "$idx" && continue
            sed -i "0,/^Inherits=/s//Inherits=$FOREIGN,/" "$idx"
        done
        echo "  Fallback to '$FOREIGN' added (for the distribution's icons)"
    fi

    for icon_set in NTLegacyIcons NTLegacyIconsNacht; do
        [ -d "$DATA/icons/$icon_set" ] || continue
        command -v gtk-update-icon-cache >/dev/null && \
            gtk-update-icon-cache -q -t -f "$DATA/icons/$icon_set" 2>/dev/null || true
    done
fi

if [ -d "$HERE/cursors" ]; then
    echo "Mouse cursors …"
    mkdir -p "$DATA/icons"
    # Clear out first here too: half of a cursor theme consists of
    # links (left_ptr -> default and so on), and cp -r would write
    # through them. See the reasoning for the icons above.
    rm -rf "$DATA"/icons/NTLegacy_cursors "$DATA"/icons/NTLegacyRot_cursors
    cp -a "$HERE/cursors/"* "$DATA/icons/"
fi

if [ -d "$HERE/konsole" ]; then
    # Only put in place, do not activate. Konsole then offers the profile and
    # schemes for selection; only appearance.sh switches over -
    # Konsole is someone else's program, and whoever tries out a theme
    # does not expect their terminal to look different afterwards.
    echo "Konsole profile and colour schemes (put in place only) …"
    mkdir -p "$DATA/konsole"
    cp -r "$HERE/konsole/"* "$DATA/konsole/"
fi

# The helper script that makes Konsole follow the theme switch, together with its
# table. Both are only put in place - the service is only switched on
# by appearance.sh, for the same reason as with the profile above.
#
# Not into konsole/: that holds the files Konsole itself reads,
# and a script among the profiles shows up in the selection menu as a
# broken profile. That has not been measured - but the folder
# belongs to someone else's program, and you do not put anything there that it
# does not expect.
if [ -f "$HERE/konsole-follow.sh" ]; then
    mkdir -p "$DATA/nt-legacy/bin"
    install -m 755 "$HERE/konsole-follow.sh" "$DATA/nt-legacy/bin/"
    [ -f "$HERE/konsole-variants.tsv" ] \
        && install -m 644 "$HERE/konsole-variants.tsv" "$DATA/nt-legacy/"
fi

if [ -d "$HERE/wallpapers" ]; then
    echo "Wallpapers …"
    mkdir -p "$DATA/wallpapers"
    # Clear away our own packages first, then copy.
    #
    # cp -r only copies on top. Up to 0.2.5 every package contained a
    # 3840x2160.png plus SVG, since 0.2.6 a 3840x2160.jpg - after an
    # update all three lay side by side. Plasma looks for
    # the resolution, finds three candidates for the same one and takes one
    # of them; which one depends on the order in the directory. On
    # a test machine it was the old gradient surface - the new image
    # was installed and stayed invisible.
    #
    # Only ntlegacy*: whatever else the user has under wallpapers/
    # is none of our business.
    rm -rf "$DATA"/wallpapers/ntlegacy*
    cp -r "$HERE/wallpapers/"* "$DATA/wallpapers/"
fi

if [ -d "$HERE/aurorae" ]; then
    echo "Window decoration …"
    mkdir -p "$DATA/aurorae/themes"
    cp -r "$HERE/aurorae/"* "$DATA/aurorae/themes/"
fi

echo "Global themes …"
for d in "$HERE"/look-and-feel/*/; do
    n="$(basename "$d")"
    install_package Plasma/LookAndFeel "${d%/}" "$DATA/plasma/look-and-feel/$n"
    echo "  $n"
done

# The icon theme has to be set hard. Plasma picks up the other
# defaults from contents/defaults at runtime (Plasma style, colour scheme,
# application style take effect that way), but not the icon theme - measured: with
# the fallback the Breeze icons stayed, only kwriteconfig6 brought in the
# icon set. The old values are in the backup above.
#
# Whoever already runs a night version keeps its set. Otherwise a
# plain update would throw it back to the light one - and the panel would then
# show dark grey on dark grey again, without anyone having changed anything.
CURRENT=$(kreadconfig6 --file kdeglobals --group Icons --key Theme 2>/dev/null)
case "$CURRENT" in
    NTLegacyIconsNacht) SET=NTLegacyIconsNacht ;;
    *)                  SET=NTLegacyIcons ;;
esac
kwriteconfig6 --file kdeglobals --group Icons --key Theme "$SET"

# The render cache carries the theme version in its name. Without deleting it
# you see the old theme after an update and look for the bug elsewhere.
#
# icon-cache.kcache belongs here and was missing up to 0.2.12 - while
# our own check script has always named it. It remembers which
# icon was found under which name; after a theme switch
# it says the icon was NOT found, and the application keeps
# showing a blank page. Reported exactly like that from the community
# (EndeavourOS, system updater).
rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements" \
      "$HOME/.cache/icon-cache.kcache"

echo ""
echo "Installed."

# ── Apply ────────────────────────────────────────────────────────────────
if $APPLY; then
    echo ""
    exec "$HERE/apply.sh" ${VARIANT:+"$VARIANT"}
fi

cat <<EOF

  Apply:        ./apply.sh              # base version (petrol)
                ./apply.sh win2k        # one of the variants
                ./apply.sh --help       # all variants and switches

                Or both at once:  ./install.sh --apply win2k

  Use apply.sh for this and not plasma-apply-lookandfeel: the
  application style (Windows instead of Breeze) can only be set via
  ~/.config/kdeglobals, and that is exactly what apply.sh does. Via
  System Settings > Colors & Themes > Global Theme it is missing.

The theme only takes full effect after logging out and back in.

  To undo:      $BACKUP/restore.sh
EOF
