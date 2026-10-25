#!/usr/bin/env bash
# Tells which version of NT Legacy is actually installed and active
# - layer by layer.
#
#     ./check-installation.sh
#
# Why this exists: a theme consists of six layers, and "Get New
# ..." updates EACH ONE SEPARATELY. Whoever only clicks the global theme
# there keeps the old icons and the old Plasma style - the
# theme then looks like before, although the new version seems
# installed. Exactly this case came from the community twice.
#
# So what is checked is not the version number but the feature
# itself: is the file there that fixes the bug?

set -uo pipefail

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
ok=0
missing=0

title() { printf '\n\033[1m%s\033[0m\n' "$1"; }
pass()  { printf '  \033[32myes \033[0m %s\n' "$1"; ok=$((ok + 1)); }
fail()  { printf '  \033[31mNO  \033[0m %s\n' "$1"; missing=$((missing + 1)); }
info()  { printf '       %s\n' "$1"; }

title "What is active right now"
for pair in "Global theme:kdeglobals:KDE:LookAndFeelPackage" \
            "Plasma style:plasmarc:Theme:name" \
            "Colour scheme:kdeglobals:General:ColorScheme" \
            "Icons:kdeglobals:Icons:Theme" \
            "Widget style:kdeglobals:KDE:widgetStyle"; do
    IFS=: read -r name file group key <<< "$pair"
    value="$(kreadconfig6 --file "$file" --group "$group" --key "$key" 2>/dev/null)"
    printf '  %-16s %s\n' "$name" "${value:-—}"
done

icons="$(kreadconfig6 --file kdeglobals --group Icons --key Theme 2>/dev/null)"
style="$(kreadconfig6 --file plasmarc --group Theme --key name 2>/dev/null)"

title "Icons: are the scalable versions there? (0.2.6)"
if [ -z "$icons" ]; then
    fail "no icon theme set"
elif [ ! -d "$DATA/icons/$icons" ]; then
    info "'$icons' is active - it is not under $DATA/icons/,"
    info "so it comes from the system and not from this theme."
    fail "$icons"
else
    dir="$DATA/icons/$icons"
    if [ -f "$dir/places/scalable/folder.svg" ]; then
        pass "$dir/places/scalable/folder.svg"
    else
        fail "$dir/places/scalable/folder.svg is missing"
        info "That is the reason for pixelated icons from 64 px up."
        info "Fix: fetch nt-legacy-icons-0.2.6.tar.xz again."
    fi
    if grep -q "Type=Scalable" "$dir/index.theme" 2>/dev/null; then
        pass "index.theme knows Type=Scalable"
    else
        fail "index.theme without Type=Scalable - old version"
    fi
fi

title "Plasma style: does the scroll bar have the checker pattern? (0.2.6)"
if [ -z "$style" ]; then
    fail "no Plasma style set"
elif [ ! -d "$DATA/plasma/desktoptheme/$style" ]; then
    info "'$style' is active - it is not under"
    info "$DATA/plasma/desktoptheme/, so it does not come from this theme."
    fail "$style"
else
    svg="$DATA/plasma/desktoptheme/$style/widgets/scrollbar.svg"
    if [ ! -f "$svg" ]; then
        fail "$svg is missing"
    elif grep -q 'stroke-dasharray' "$svg"; then
        # Since 0.2.6 the checker colour is a value of its own in the palette;
        # before that it was the 3D highlight edge and thus almost invisible.
        if grep -q 'opacity="0.07"' "$svg"; then
            pass "$svg (checker pattern with darkened trough)"
        else
            fail "$svg has the checker pattern from 0.2.5 - too little contrast"
            info "Fix: fetch nt-legacy-plasma-style-<colour-world>-0.2.6.tar.xz"
            info "again. The colour world is shown above under 'Plasma style'."
        fi
    else
        fail "$svg without checker pattern - version before 0.2.5"
    fi
fi

title "Caches"
for pattern in "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/icon-cache.kcache" \
               "$HOME/.cache/ksvg-elements"; do
    [ -e "$pattern" ] && info "still present: ${pattern/#$HOME/~}"
done
info "Delete them and log in again if everything above says 'yes' and it"
info "still looks old:"
info "  rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/icon-cache.kcache"
info "  rm -rf ~/.cache/ksvg-elements"

printf '\n%d fine, %d to fetch\n' "$ok" "$missing"
if [ "$missing" -gt 0 ]; then
    printf '\nAs a reminder: "Get New ..." updates every layer\n'
    printf 'separately. Icons and Plasma style are separate downloads -\n'
    printf 'the global theme does NOT bring them along.\n'
fi
