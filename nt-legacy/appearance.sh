#!/usr/bin/env bash
# Switches program settings to the NT look - explicitly
# separate from the theme.
#
#   ./appearance.sh            # apply
#   ./appearance.sh --revert   # reset to the previous values
#   ./appearance.sh --show     # only show what would be set
#
# Why this is not in apply.sh:
#
# A Plasma theme may set the look - colours, frames, decoration. It
# may not overwrite the settings of other programs. Whoever tries out a
# theme does not expect their Dolphin configuration to be different
# afterwards. Exactly such silent
# side effects are the reason a theme can make a system
# unusable.
#
# Hence: a separate script, an explicit call, a complete way back.

set -euo pipefail

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
BACKUP="$DATA/nt-legacy/anmutung-vorher.conf"

# File : group : key : NT value : reason
#
# Deliberately kept short. Every entry here is an intervention in
# someone else's program and has to be justifiable.
SETTINGS=(
  "dolphinrc:General:ShowStatusBar:FullWidth:full-width status bar instead of a floating box"
  # PCManFM-Qt as the file manager. Reasons, measured in the test VM:
  #   - Qt6, so the widget style applies fully
  #   - a real menu bar instead of a hamburger button
  #   - free space as text across the full width; Dolphin
  #     draws a KCapacityBar there, which draws itself and
  #     follows neither the palette nor the widget style (silver capsule)
  "mimeapps.list:Default Applications:inode/directory:pcmanfm-qt.desktop:PCManFM-Qt as the file manager"
  # Without this entry pcmanfm-qt does not find the icon theme and falls
  # back to oxygen - in the middle of the NT theme.
  "pcmanfm-qt/default/settings.conf:System:FallbackIconThemeName:NTLegacy:icon theme for PCManFM-Qt"
  # Konsole on the bundled profile: Liberation Mono and a
  # colour scheme from the colours of the respective version. install.sh only puts
  # both in place, they are activated only here. The user's own
  # profile remains and can still be selected in the menu.
  "konsolerc:Desktop Entry:DefaultProfile:NT Legacy.profile:Konsole uses the NT profile"
  # Kate without the text preview at the right edge.
  #
  # What looks like a very wide scroll bar there is not one:
  # it is Kate's "minimap", a scaled-down view of the whole
  # document that KTextEditor draws INSTEAD of the scroll bar -
  # 60 pixels wide instead of the widget style's 16. It does not come from the
  # theme, and no colour scheme and no widget style makes it narrower.
  #
  # The key is called "Scroll Bar MiniMap" - without a space
  # between Mini and Map, unlike the three related keys
  # next to it ("Scroll Bar Mini Map All", "Scroll Bar Mini Map Width").
  # Looked up in ktexteditor/src/utils/kateconfig.cpp; a guess would have
  # got it wrong, and a wrong key is silently
  # created and never read.
  #
  # The group applies to the application, not to KTextEditor: Kate
  # reads from katerc, KWrite from kwriterc. Hence both.
  "katerc:KTextEditor View:Scroll Bar MiniMap:false:Kate: narrow scroll bar instead of text preview"
  "kwriterc:KTextEditor View:Scroll Bar MiniMap:false:KWrite: the same"
)

# FeatherPad as a simple text editor - only if present.
#
# Kate is a development environment: project bar, LSP client,
# sessions, terminal. Whoever wants to jot down a note gets
# nothing out of it. FeatherPad is the counterpart and comes closest to Notepad
# - a real menu bar, no toolbox, no sidebars.
#
# And it is a Qt application: the "Windows" widget style applies
# fully, the window looks like the rest of the theme. The
# GTK candidates (Mousepad, L3afpad, gedit) do not - they
# draw themselves and remain a foreign body.
#
# Deliberately only if it is installed. A theme must not pull in
# packages, and a default program that does not exist produces an error
# message instead of an editor when double-clicking a .txt.
if command -v featherpad >/dev/null 2>&1; then
    SETTINGS+=(
      "mimeapps.list:Default Applications:text/plain:featherpad.desktop:FeatherPad for plain text"
    )
    FEATHERPAD=true
else
    FEATHERPAD=false
fi

# ── Make Konsole follow the theme switch ─────────────────────────────────
#
# The terminal's colour scheme lives in the profile, and Plasma does not touch profiles
# when switching themes - Konsole has no "follow the system".
# apply.sh switches the line; but whoever switches the theme via
# System Settings never calls apply.sh, and the terminal
# stays in the old colour world.
#
# Hence a systemd path unit: it triggers when Plasma writes its
# defaults files and kicks off konsole-follow.sh. No
# running process, no dependency except systemd - which
# both test VMs have, Fedora as well as EndeavourOS.
#
# Exactly ONE file is watched: ~/.config/kdedefaults/package. It
# holds the ID of the global theme and is rewritten by Plasma when
# a theme is applied.
#
# At first kdeglobals was watched here too. That brought nothing and did harm:
# the mapping goes via the ID of the theme, a pure
# colour scheme switch could not be mapped at all - but
# the second file multiplied the triggers per switch and drove
# the service into the start limit (see below).
#
# The paths are written out in full in the unit, not as %h: whoever
# has moved XDG_DATA_HOME would otherwise get a unit that points
# nowhere - and systemd only reports that when it triggers, in a log
# nobody looks at.
SERVICE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_NAME="nt-legacy-konsole"

service_on() {
    local script="$DATA/nt-legacy/bin/konsole-follow.sh"
    if [ ! -x "$script" ]; then
        echo "  Note: $script is missing - run ./install.sh first." >&2
        return
    fi
    if ! command -v systemctl >/dev/null; then
        echo "  Note: no systemd - Konsole follows the theme only via" >&2
        echo "        ./apply.sh." >&2
        return
    fi
    mkdir -p "$SERVICE_DIR"
    # StartLimitIntervalSec=0 switches off the start limit, and that
    # is not a convenience here but a necessity.
    #
    # By default systemd allows a unit five starts in ten
    # seconds. But a single theme switch writes several files
    # below kdedefaults, all within the same second -
    # so the path unit triggers four to five times. By the next
    # switch the quota is used up:
    #
    #   nt-legacy-konsole.service: Start request repeated too quickly.
    #   nt-legacy-konsole.path: Failed with result unit-start-limit-hit.
    #
    # And that is not just one run lost: the PATH UNIT
    # itself goes into the failed state and watches nothing any more. Measured
    # exactly like that in the test VM - the first switch updated the profile,
    # the second no longer did, and after that none at all. On the
    # development machine it had never been noticed, because only a
    # single switch was tested there.
    #
    # The same trap as with plasma-plasmashell.service, see apply.sh.
    # There it was more dangerous, here merely silent.
    #
    # Switching it off is justifiable: the service is a script of a few
    # lines that writes one line into a file and exits.
    cat > "$SERVICE_DIR/$SERVICE_NAME.service" <<SERVICE
[Unit]
Description=NT Legacy: make the Konsole colour scheme follow the global theme
StartLimitIntervalSec=0

[Service]
Type=oneshot
ExecStart=$script
SERVICE
    cat > "$SERVICE_DIR/$SERVICE_NAME.path" <<PATHUNIT
[Unit]
Description=NT Legacy: wait for a change of the global theme

[Path]
PathChanged=${XDG_CONFIG_HOME:-$HOME/.config}/kdedefaults/package
Unit=$SERVICE_NAME.service

[Install]
WantedBy=default.target
PATHUNIT
    systemctl --user daemon-reload 2>/dev/null || true
    systemctl --user enable --now "$SERVICE_NAME.path" >/dev/null 2>&1 || true
    if systemctl --user is-active --quiet "$SERVICE_NAME.path"; then
        echo "  Konsole now follows the theme switch ($SERVICE_NAME.path)."
    else
        echo "  Note: $SERVICE_NAME.path is not running." >&2
        echo "        systemctl --user status $SERVICE_NAME.path" >&2
    fi
}

service_off() {
    command -v systemctl >/dev/null || return 0
    systemctl --user disable --now "$SERVICE_NAME.path" >/dev/null 2>&1 || true
    rm -f "$SERVICE_DIR/$SERVICE_NAME.path" "$SERVICE_DIR/$SERVICE_NAME.service"
    systemctl --user daemon-reload 2>/dev/null || true
    echo "  $SERVICE_NAME removed."
}

show() {
    printf '%-12s %-10s %-16s %s\n' "File" "Group" "Key" "Value"
    for e in "${SETTINGS[@]}"; do
        IFS=: read -r file group key value reason <<< "$e"
        printf '%-12s %-10s %-16s %s\n' "$file" "$group" "$key" "$value"
        printf '%-40s %s\n' "" "$reason"
    done
    printf '%-12s %-10s %-16s %s\n' "systemd" "user" "$SERVICE_NAME" "path+service"
    printf '%-40s %s\n' "" "Konsole follows the change of the global theme"
}

revert() {
    if [ ! -f "$BACKUP" ]; then
        echo "No backup at $BACKUP - nothing to reset." >&2
        exit 1
    fi
    while IFS=: read -r file group key value; do
        [ -z "${file:-}" ] && continue
        if [ -z "$value" ]; then
            # The key was not set at all before. Delete it, do not
            # set it to a guessed default - otherwise it would afterwards hold
            # something the user never chose.
            kwriteconfig6 --file "$file" --group "$group" --key "$key" --delete
            echo "  $file/$group/$key  removed (was not set)"
        else
            kwriteconfig6 --file "$file" --group "$group" --key "$key" "$value"
            echo "  $file/$group/$key  -> $value"
        fi
    done < "$BACKUP"
    rm -f "$BACKUP"
    service_off
    echo
    echo "Reset. Restart open programs once."
}

case "${1:-}" in
    --show)    show; exit 0 ;;
    --revert)  revert; exit 0 ;;
    "")        ;;
    *)         echo "Unknown option '$1'. Possible: --show, --revert" >&2; exit 1 ;;
esac

# --- Apply ---------------------------------------------------------------

if [ -f "$BACKUP" ]; then
    echo "Note: a backup already exists - the old values are kept,"
    echo "      so that --revert still restores the original state."
else
    mkdir -p "$(dirname "$BACKUP")"
    : > "$BACKUP"
    for e in "${SETTINGS[@]}"; do
        IFS=: read -r file group key _value _reason <<< "$e"
        # An empty value means: was not set. The backup has to record the
        # difference between "not set" and "set to the default value",
        # otherwise the way back is inaccurate.
        old=$(kreadconfig6 --file "$file" --group "$group" --key "$key" 2>/dev/null || true)
        echo "$file:$group:$key:$old" >> "$BACKUP"
    done
fi

for e in "${SETTINGS[@]}"; do
    IFS=: read -r file group key value reason <<< "$e"
    kwriteconfig6 --file "$file" --group "$group" --key "$key" "$value"
    echo "  $file: $key = $value"
    echo "      $reason"
done

service_on

if ! $FEATHERPAD; then
    cat <<EOF

  For plain text Kate remains the default. Whoever prefers a
  simple editor - a menu bar, nothing else, like
  Notepad - installs FeatherPad and runs this script once more:

      sudo dnf install featherpad     # or: sudo pacman -S featherpad
      ./appearance.sh

EOF
fi

cat <<EOF

Applied. Restart the affected programs once.

  Kate and Konsole read their settings at startup. An open
  window therefore keeps its previous look - and Kate writes
  its settings back on exit, overwriting what was
  set here. So: close them first, then run this script.

  To undo:  ./appearance.sh --revert
  Backed up: $BACKUP
EOF
