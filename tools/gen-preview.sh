#!/usr/bin/env bash
# Replaces the schematic preview images with real screenshots.
#
# For every variant: apply it in the test VM, restart the session,
# open a few windows, take a screenshot, crop it.
#
#   ./gen-preview.sh              # all variants
#   ./gen-preview.sh teal lilac   # only these
#
# The session restart per variant cannot be optimised away: KWin loads
# Aurorae themes only at startup. Without a restart every image carries
# the title bar of the previous variant - and that is exactly the
# most noticeable feature.
#
# Duration: about two minutes per variant.

set -uo pipefail

LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VMCTL="$LAB/vm/vmctl.sh"
THEME="$LAB/nt-legacy"
WIDTH=1920
HEIGHT=1080

variants=("$@")
if [ ${#variants[@]} -eq 0 ]; then
    mapfile -t variants < <(cd "$THEME" && python3 -c "
import importlib.util
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print('\n'.join(m.VARIANTEN))
")
fi

lnf_for() {
    (cd "$THEME" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(m.ids(sys.argv[1])['lnf'])
" "$1")
}

wait_for_vm() {
    for _ in $(seq 1 30); do
        "$VMCTL" ssh 'test -f /etc/plasma-lab-ready' >/dev/null 2>&1 && return 0
        sleep 10
    done
    return 1
}

echo "Transferring current state …"
"$VMCTL" push "$THEME/" /home/tester/nt-legacy/ >/dev/null 2>&1
"$VMCTL" ssh 'cd nt-legacy && ./install.sh >/dev/null 2>&1' || {
    echo "ERROR: installation in the VM failed" >&2; exit 1; }

for v in "${variants[@]}"; do
    lnf="$(lnf_for "$v")"
    dest="$THEME/look-and-feel/$lnf/contents/previews"
    echo
    echo "=== $v ==="

    "$VMCTL" ssh "cd nt-legacy && ./apply.sh $v >/dev/null 2>&1" || {
        echo "  skipped (apply.sh failed)"; continue; }

    # Set the variant's wallpaper explicitly.
    #
    # The Global Theme names it in contents/defaults, but that only takes
    # effect in a fresh session - an existing one keeps its image.
    # Since 0.2.6 it is a landscape and no longer a gradient;
    # without this line the previews kept showing the old
    # background.
    wp="$(cd "$THEME" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(m.ids(sys.argv[1])['wallpaper'])
" "$v")"
    "$VMCTL" ssh "plasma-apply-wallpaperimage \
        ~/.local/share/wallpapers/$wp >/dev/null 2>&1" || true

    # Log in again so the window decoration takes effect
    "$VMCTL" ssh 'sudo systemctl reboot' >/dev/null 2>&1
    sleep 45
    wait_for_vm || { echo "  VM did not come back"; continue; }
    sleep 30

    "$VMCTL" ssh "
        kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
        # 16:9, so the tile in the selection dialog is not cropped
        kscreen-doctor output.1.mode.${WIDTH}x${HEIGHT}@60 >/dev/null 2>&1
        sleep 4

        # Three windows side by side instead of stacked.
        #
        # Stacking was meant to show one active and several
        # inactive title bars in one image. The price was high: of the
        # lower windows only a strip each was left, and the file manager
        # in particular - the showcase for the icon set - was
        # half covered. Side by side every window can be seen in
        # full. The two windows that do not have focus still show
        # the inactive title bar.
        #
        # Dolphin gets the largest share and sits in the home
        # folder: Pictures, Documents, Downloads, Music, Videos - each with
        # its own folder emblem. That shows more of the icon set
        # at a glance than any toolbar.
        #
        # Positioning is done via KWin window rules, not via
        # xdotool: under Wayland no foreign process can move
        # windows. The rules live in the throwaway VM, not on the
        # user's machine.
        # The windows keep a distance from the edge and leave a strip
        # free at the bottom. Since 0.2.6 the wallpaper is a separate
# landscape per variant - fully covered it would not be visible
# in the preview, and it is one of the reasons to make new images at all.
cat > ~/.config/kwinrulesrc <<'RULES'
[General]
count=4
rules=preview-files,preview-editor,preview-taskmanager,preview-terminal

[preview-files]
Description=Preview: file manager left
wmclass=dolphin
wmclassmatch=2
position=40,40
positionrule=3
size=660,790
sizerule=3

[preview-editor]
Description=Preview: editor middle
wmclass=kwrite
wmclassmatch=2
position=716,40
positionrule=3
size=500,790
sizerule=3

[preview-taskmanager]
Description=Preview: task manager top right
wmclass=nt-taskmanager
wmclassmatch=2
position=1232,40
positionrule=3
size=648,420
sizerule=3

[preview-terminal]
Description=Preview: terminal bottom right
wmclass=konsole
wmclassmatch=2
position=1232,476
positionrule=3
size=648,354
sizerule=3
RULES
        qdbus-qt6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1
        sleep 2

        # Dolphin in icon view with large icons. The detail list
        # shows 16 px icons - the folder emblems are no longer
        # recognisable there.
        kwriteconfig6 --file dolphinrc --group General --key ViewMode 0
        kwriteconfig6 --file dolphinrc --group IconsMode --key PreviewSize 64
        kwriteconfig6 --file dolphinrc --group IconsMode --key IconSize 64
        kwriteconfig6 --file dolphinrc --group General --key ShowFullPath false

        # Whatever else lies around here does not belong in the image. The
        # theme's working directory cannot be cleared away - it is
        # needed -, but .hidden takes it out of the view: KIO
        # hides every name listed there.
        mkdir -p ~/.preview-aside
        mv ~/*.sh ~/*.py ~/.preview-aside/ 2>/dev/null
        printf 'nt-legacy\n' > ~/.hidden

        # The user folders get English names. Without this the image shows
        # an English sidebar next to German folder names -
        # \"Home, Documents, Pictures\" on the left, \"Bilder, Dokumente,
        # Schreibtisch\" on the right. But these very folders are the
        # subject here, because they carry the new folder emblems.
        #
        # xdg-user-dirs-update is no good: it creates the English folders
        # anew instead of renaming the existing ones, and afterwards
        # both are there.
        cd ~
        while IFS=: read -r old new key; do
            [ -d \"\$old\" ] && [ ! -e \"\$new\" ] && mv \"\$old\" \"\$new\"
            printf 'XDG_%s_DIR=\"\$HOME/%s\"\n' \"\$key\" \"\$new\"
        done <<'FOLDERS' > ~/.config/user-dirs.dirs
Schreibtisch:Desktop:DESKTOP
Dokumente:Documents:DOCUMENTS
Downloads:Downloads:DOWNLOAD
Musik:Music:MUSIC
Bilder:Pictures:PICTURES
Videos:Videos:VIDEOS
Öffentlich:Public:PUBLICSHARE
Vorlagen:Templates:TEMPLATES
FOLDERS

        # Order: the window opened last has focus and
        # shows the active title bar. That should be the file manager.
        #
        # Konsole gets a command to run. A bare
        # prompt shows only the terminal background - but the eight
        # ANSI colours were specifically tuned to measured contrast
        # (4.5:1 normal, 7:1 intense), and a coloured ls is the
        # only place where you can see that.
        # English UI, although the VM runs in German. The
        # images go to store.kde.org, and the listing is in English -
        # German menu items shut out most of the readers.
        # Only the programs are switched, not the session:
        # panel and clock stay German, which does not stand out in the image, and
        # switching the language of the whole session would need another
        # restart.
        export LANGUAGE=en_US LANG=en_US.UTF-8 LC_ALL=
        (setsid konsole -e bash -c 'ls --color=always -l /usr/share | head -22; exec bash' >/dev/null 2>&1 &); sleep 9
        (setsid kwrite ~/nt-legacy/INSTALL.md >/dev/null 2>&1 &); sleep 10
        # The task manager on the tab with the graphs: the process list and
        # services are tables like the file manager next to it, the bars
        # and graphs are the only thing not found anywhere else in the
        # image. --on-top would be wrong here - the rule puts it
        # in its place anyway, and on top it would cover part of the next
        # window.
        (setsid nt-taskmanager --tab 2 >/dev/null 2>&1 &); sleep 8
        (setsid dolphin ~ >/dev/null 2>&1 &); sleep 12
    " >/dev/null 2>&1

    virsh -c qemu:///system send-key plasma-lab KEY_LEFTSHIFT >/dev/null 2>&1
    sleep 3

    raw="$(mktemp --suffix=.png)"
    "$VMCTL" shot "$raw" >/dev/null 2>&1
    if [ ! -s "$raw" ]; then
        echo "  no screenshot"; rm -f "$raw"; continue
    fi

    mkdir -p "$dest"

    # Full image for the large view - there is enough room there.
    magick "$raw" -resize "${WIDTH}x${HEIGHT}!" -quality 88 \
        "$dest/fullscreenpreview.jpg"

    # The tile shows only the two left windows, not all four.
    #
    # Four windows side by side make a subject with a 3:1 ratio.
    # The tile however is 16:9 - forcing it in gives either
    # two empty bars or a crop in which nothing is left of the
    # outer windows. Both were worse than the simple solution:
    # Dolphin and the editor, at full height.
    # Those are the two that show something anyway - folder icons and
    # a coloured text view. The terminal is in the full image.
    # 64 instead of 69 percent: at 69 the crop ended in the middle of the
    # task manager, since it was added as the fourth window. 64
    # cuts in the gap between editor and task manager - no
    # partly cut window at the edge. The ratio stays 16:9.
    magick "$raw" -gravity northwest -crop 64%x64%+8+24 +repage \
        -resize 600x337! "$dest/preview.png"
    cp "$dest/preview.png" "$dest/lockscreen.png"
    cp "$dest/preview.png" "$dest/splash.png"
    rm -f "$raw"

    echo "  $(basename "$dest")/preview.png  (from a real screenshot)"
    "$VMCTL" ssh 'pkill dolphin; pkill kwrite; pkill konsole' >/dev/null 2>&1
done

echo
echo "Done. The images are in nt-legacy/look-and-feel/*/contents/previews/."
