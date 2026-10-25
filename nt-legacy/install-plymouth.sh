#!/usr/bin/env bash
# Installs the NT Legacy boot splash screen (Plymouth).
#
#   ./install-plymouth.sh              # base version (petrol)
#   ./install-plymouth.sh win2k        # one of the variants
#   ./install-plymouth.sh --revert     # back to the previous theme
#
# CAUTION - this is NOT install.sh.
#
# The theme lives under /usr/share/plymouth/themes and has to be built into the
# initramfs; both need sudo. Rebuilding the
# initramfs takes half a minute to two minutes depending on the machine.
#
# What happens in the worst case: Plymouth does not find the theme and
# shows no splash screen at all - the machine still boots, you
# then see the text messages. Whoever has an encrypted disk
# should still do the test below before rebooting.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEMES="/usr/share/plymouth/themes"
BACKUP="/var/backups/nt-legacy-plymouth"

# Names the install command of the running distribution.
#
# Both messages below used to say "dnf install …" - on the
# Arch test system, that is, a command that does not even exist there. Whoever writes an
# error message should make sure its advice can actually be followed.
package_command() {
    if command -v pacman >/dev/null;   then echo "sudo pacman -S --needed $1"
    elif command -v dnf >/dev/null;    then echo "sudo dnf install $1"
    elif command -v apt >/dev/null;    then echo "sudo apt install $1"
    elif command -v zypper >/dev/null; then echo "sudo zypper install $1"
    else echo "install the package '$1'"
    fi
}

if ! command -v plymouth-set-default-theme >/dev/null; then
    echo "ERROR: plymouth-set-default-theme is missing." >&2
    echo "       Does this system use Plymouth? Otherwise:" >&2
    echo "       $(package_command plymouth)" >&2
    exit 1
fi

# The script module is shipped as a package of its own and is often missing.
# Without it Plymouth does not load the theme and silently falls back to 'text'
# - the most common reason why a self-built theme
# "just does not show up".
if [ ! -f /usr/lib64/plymouth/script.so ] && \
   [ ! -f /usr/lib/plymouth/script.so ] && \
   [ ! -f /usr/lib/x86_64-linux-gnu/plymouth/script.so ]; then
    echo "ERROR: the Plymouth module 'script' is missing." >&2
    echo "       On Fedora and Nobara it is a separate package:" >&2
    echo "       $(package_command plymouth-plugin-script)" >&2
    echo "       Elsewhere it is part of 'plymouth' itself." >&2
    exit 1
fi

rebuild_initramfs() {
    # The order is not arbitrary.
    #
    # dracut-rebuild comes first, because EndeavourOS ships it for exactly
    # this purpose: there a plain "dracut --force" fails with
    #
    #   dracut[F]: Can't write to /boot/efi/<machine-id>/<kernel>:
    #   Directory does not exist or is not accessible.
    #
    # The reason is the kernel-install layout - dracut alone looks for a
    # directory that nobody created there. Noticed in the Arch test VM
    # on the way back; the initramfs stayed unchanged without
    # the script noticing.
    if command -v dracut-rebuild >/dev/null; then
        echo "  rebuilding initramfs (dracut-rebuild) - this takes a moment …"
        sudo dracut-rebuild
    elif command -v dracut >/dev/null; then
        echo "  rebuilding initramfs (dracut) - this takes a moment …"
        sudo dracut --force
    elif command -v update-initramfs >/dev/null; then
        echo "  rebuilding initramfs (update-initramfs) …"
        sudo update-initramfs -u
    elif command -v mkinitcpio >/dev/null; then
        echo "  rebuilding initramfs (mkinitcpio) …"
        sudo mkinitcpio -P
    else
        echo "WARNING: no initramfs tool found." >&2
        echo "         The theme only takes effect once the initramfs has been" >&2
        echo "         rebuilt." >&2
        return 1
    fi
}

# The call above must not fail silently: an initramfs that was not
# renewed keeps showing the old theme on the next boot,
# and nobody would think of looking there.
rebuild_initramfs_reported() {
    if ! rebuild_initramfs; then
        echo "" >&2
        echo "WARNING: rebuilding the initramfs failed." >&2
        echo "         The theme is in the right place, but only appears on the next" >&2
        echo "         boot once the rebuild has been done." >&2
        return 1
    fi
}

# ── Way back ─────────────────────────────────────────────────────────────
if [ "${1:-}" = "--revert" ]; then
    if [ -f "$BACKUP/theme" ]; then
        previous="$(cat "$BACKUP/theme")"
        echo "Resetting to '$previous' …"
        sudo plymouth-set-default-theme "$previous"
    else
        echo "No backup found - setting 'bgrt' (Fedora default) …"
        sudo plymouth-set-default-theme bgrt 2>/dev/null || \
            sudo plymouth-set-default-theme details
    fi
    sudo sh -c "rm -rf '$THEMES'/nt-legacy-*"
    rebuild_initramfs_reported || true
    echo "Reset."
    exit 0
fi

VARIANT="${1:-teal}"

NAME=$(cd "$HERE" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
v = sys.argv[1]
if v not in m.VARIANTS:
    print('UNKNOWN ' + ' '.join(sorted(m.VARIANTS)))
else:
    print(m.ids(v)['lnf'].split('.')[-1])
" "$VARIANT")

if [ "${NAME%% *}" = "UNKNOWN" ]; then
    echo "Unknown variant '$VARIANT'." >&2
    echo "Possible: ${NAME#UNKNOWN }" >&2
    exit 1
fi

SOURCE="$HERE/plymouth/$NAME"
if [ ! -d "$SOURCE" ]; then
    echo "ERROR: $SOURCE is missing." >&2
    echo "       Run  ./build.py  first." >&2
    exit 1
fi

echo "Plymouth theme: $NAME"
echo "This script needs sudo - it writes to $THEMES."
echo ""

# ── Backup ───────────────────────────────────────────────────────────────
# Here too only the first time: on the second run the
# "previous" theme would be our own, and --revert would go round in circles.
sudo mkdir -p "$BACKUP"
if sudo test ! -f "$BACKUP/theme"; then
    previous="$(plymouth-set-default-theme 2>/dev/null || echo bgrt)"
    echo "$previous" | sudo tee "$BACKUP/theme" >/dev/null
    echo "Previous theme: $previous  (remembered in $BACKUP/theme)"
else
    echo "Previous theme already recorded: $(sudo cat "$BACKUP/theme")"
fi

# ── Installation ─────────────────────────────────────────────────────────
sudo rm -rf "${THEMES:?}/$NAME"
sudo cp -a "$SOURCE" "$THEMES/$NAME"
echo "  $THEMES/$NAME"

sudo plymouth-set-default-theme "$NAME"
echo "  set as default"

rebuild_initramfs_reported || true

# Without "splash" on the kernel command line Plymouth shows nothing.
#
# Fedora and Nobara set "rhgb quiet" out of the box, Arch and EndeavourOS
# do not - there the theme sits there cleanly installed and still never
# appears at boot. Reproduced in the Arch test VM; plymouthd says
# so itself, but only in the debug log:
#
#   no default splash because kernel command line lacks "splash" or "rhgb"
#
# Deliberately only a note: this script does not change kernel parameters
# on its own.
if ! grep -qE "(^| )(splash|rhgb)( |$)" /proc/cmdline; then
    # Name the right command for this distribution instead of one
    # that is right elsewhere. A first draft suggested a sed here
    # that matched double quotes - but EndeavourOS writes
    # the line in single ones. The advice would have fizzled out without effect,
    # and the user would have looked for the bug in the theme.
    if [ -d /boot/grub2 ]; then
        mkcfg="sudo grub2-mkconfig -o /boot/grub2/grub.cfg"
    else
        mkcfg="sudo grub-mkconfig -o /boot/grub/grub.cfg"
    fi
    cat >&2 <<NOTE

NOTE: "splash" is missing from the kernel command line.

      Without this word Plymouth shows nothing at all at boot - the
      theme is then installed and invisible. On Arch and
      EndeavourOS that is the normal case, on Fedora it says
      "rhgb quiet" there out of the box. plymouthd says so itself, but only in the
      debug log:

        no default splash because kernel command line lacks
        "splash" or "rhgb"

      This is how to add it: in /etc/default/grub add the word splash to
      the GRUB_CMDLINE_LINUX_DEFAULT line - inside the
      quotes, after the existing values - and then run

        $mkcfg

NOTE
fi

cat <<EOF

Done. The NT splash screen appears on the next boot.

  Preview it without rebooting:

    sudo plymouthd --debug --tty=/dev/tty1
    sudo plymouth --show-splash
    sleep 5; sudo plymouth --quit

  With an encrypted disk, be sure to also check the password prompt
  - it is the only thing that can really go wrong
  at boot:

    sudo plymouth ask-for-password --prompt "Test"

  To undo:  ./install-plymouth.sh --revert
EOF
