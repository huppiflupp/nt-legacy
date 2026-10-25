#!/usr/bin/env bash
# Installs the NT Legacy GRUB theme.
#
#   ./install-grub.sh              # base version (petrol)
#   ./install-grub.sh win2k        # one of the variants
#   ./install-grub.sh --revert     # remove the theme, restore the default
#
# CAUTION - this is NOT install.sh.
#
# install.sh touches nothing but $HOME. This script writes to
# /boot and /etc/default/grub and therefore needs sudo. It makes a backup
# first, and the way back is given at the end - but whoever does not want to touch
# their bootloader simply leaves it alone: the theme works without it.
#
# What happens in the worst case: GRUB does not find the theme and
# draws its plain text menu. The machine still boots.
# Booting can only break if grub.cfg itself gets damaged -
# that is why it is copied first and regenerated afterwards, not edited.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Where does the theme belong, and what is the configuration called? ───
#
# Fedora and relatives call everything "grub2", Debian and Arch "grub".
# Both occur, and the wrong path is only noticed at the next
# boot - by then it is too late to look.
if [ -d /boot/grub2 ]; then
    GRUB_DIR="/boot/grub2"
elif [ -d /boot/grub ]; then
    GRUB_DIR="/boot/grub"
else
    echo "ERROR: neither /boot/grub2 nor /boot/grub found." >&2
    echo "       Does this system use GRUB at all?" >&2
    exit 1
fi
THEMES="$GRUB_DIR/themes"
DEFAULT="/etc/default/grub"
BACKUP="/var/backups/nt-legacy-grub"

mkgrubcfg() {
    # Regenerate the configuration. On UEFI Fedora it lives under
    # /boot/efi/EFI/<distro>/grub.cfg, on BIOS under /boot/grub2 - the
    # call without -o hits both, because grub2-mkconfig knows the right
    # file itself. Only where the tool has a different name do we have to
    # search.
    if command -v grub2-mkconfig >/dev/null; then
        sudo grub2-mkconfig -o "$GRUB_DIR/grub.cfg"
    elif command -v grub-mkconfig >/dev/null; then
        sudo grub-mkconfig -o "$GRUB_DIR/grub.cfg"
    elif command -v update-grub >/dev/null; then
        sudo update-grub
    else
        echo "WARNING: grub2-mkconfig not found - grub.cfg unchanged." >&2
        return 1
    fi
}

# ── Way back ─────────────────────────────────────────────────────────────
if [ "${1:-}" = "--revert" ]; then
    echo "Resetting GRUB to the state before the installation …"
    if [ -f "$BACKUP/grub" ]; then
        sudo cp -a "$BACKUP/grub" "$DEFAULT"
        echo "  $DEFAULT restored"
    else
        # No backup? Then at least remove the line we
        # set - a reference to a deleted theme makes
        # GRUB start in text mode, which works but is
        # needlessly ugly.
        sudo sed -i '/^GRUB_THEME=.*NTLegacy/d' "$DEFAULT"
        echo "  GRUB_THEME line removed (no backup found)"
    fi
    # The asterisk has to be expanded by ROOT, not by the user's shell.
    #
    # /boot/grub2 is readable only by root. As tester the shell finds
    # no match and passes the pattern on literally - rm then deletes
    # a file called "NTLegacy*" that does not exist, and reports
    # success. In the test VM the theme was still there after --revert.
    sudo sh -c "rm -rf '$THEMES'/NTLegacy*"
    echo "  Themes removed"
    mkgrubcfg && echo "  grub.cfg regenerated"
    exit 0
fi

VARIANT="${1:-teal}"

# The ID comes from build.py - one source of truth, as in apply.sh.
NAME=$(cd "$HERE" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
v = sys.argv[1]
if v not in m.VARIANTS:
    print('UNKNOWN ' + ' '.join(sorted(m.VARIANTS)))
else:
    print(m.ids(v)['aurorae'])
" "$VARIANT")

if [ "${NAME%% *}" = "UNKNOWN" ]; then
    echo "Unknown variant '$VARIANT'." >&2
    echo "Possible: ${NAME#UNKNOWN }" >&2
    exit 1
fi

SOURCE="$HERE/grub/$NAME"
if [ ! -d "$SOURCE" ]; then
    echo "ERROR: $SOURCE is missing." >&2
    echo "       Run  ./build.py  first." >&2
    exit 1
fi

echo "GRUB theme: $NAME"
echo "This script needs sudo - it writes to $GRUB_DIR and $DEFAULT."
echo ""

# ── Backup ───────────────────────────────────────────────────────────────
#
# Only the FIRST time. On the second run /etc/default/grub would
# already contain our GRUB_THEME line - a backup of that no longer leads
# back, but restores the modified state.
# That is exactly how the first way-back test in the VM turned out.
sudo mkdir -p "$BACKUP"
if sudo test ! -f "$BACKUP/grub"; then
    [ -f "$DEFAULT" ] && sudo cp -a "$DEFAULT" "$BACKUP/grub"
    [ -f "$GRUB_DIR/grub.cfg" ] && sudo cp -a "$GRUB_DIR/grub.cfg" "$BACKUP/grub.cfg"
    echo "Backup: $BACKUP"
else
    echo "Backup already exists: $BACKUP  (from the first run, kept)"
fi

# ── Installation ─────────────────────────────────────────────────────────
sudo mkdir -p "$THEMES"
sudo rm -rf "$THEMES/$NAME"
sudo cp -a "$SOURCE" "$THEMES/$NAME"
echo "  $THEMES/$NAME"

# Set GRUB_THEME - replace an existing line, otherwise append.
if sudo grep -q "^GRUB_THEME=" "$DEFAULT" 2>/dev/null; then
    sudo sed -i "s|^GRUB_THEME=.*|GRUB_THEME=\"$THEMES/$NAME/theme.txt\"|" "$DEFAULT"
else
    echo "GRUB_THEME=\"$THEMES/$NAME/theme.txt\"" | sudo tee -a "$DEFAULT" >/dev/null
fi

# Without graphics mode GRUB does not show the theme but its
# text menu - the theme would be installed and invisible. 'auto' lets
# GRUB pick the best resolution itself.
if sudo grep -q "^GRUB_GFXMODE=" "$DEFAULT" 2>/dev/null; then
    :
else
    echo 'GRUB_GFXMODE=auto' | sudo tee -a "$DEFAULT" >/dev/null
fi
# GRUB_TERMINAL=console explicitly switches graphics off. If the
# line is set, it wins over everything else.
if sudo grep -qE "^GRUB_TERMINAL(_OUTPUT)?=.*console" "$DEFAULT" 2>/dev/null; then
    echo ""
    echo "NOTE: $DEFAULT contains GRUB_TERMINAL=console."
    echo "      As long as that line is there, the menu stays in"
    echo "      text mode and the theme invisible. Comment it out"
    echo "      and run this script again."
fi

echo ""
mkgrubcfg && echo "  grub.cfg regenerated"

cat <<EOF

Done. On the next boot GRUB shows the NT menu.

  You do not see it? Then the menu is probably set to hidden:
    GRUB_TIMEOUT_STYLE=menu  and  GRUB_TIMEOUT=5  in $DEFAULT

  To undo:  ./install-grub.sh --revert
EOF
