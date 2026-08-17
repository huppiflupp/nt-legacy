#!/usr/bin/env bash
# Sagt, welcher Stand von NT Legacy tatsaechlich installiert und aktiv
# ist - Ebene fuer Ebene.
#
#     ./pruefe-installation.sh
#
# Warum es das gibt: Ein Theme besteht aus sechs Ebenen, und "Neue
# holen ..." aktualisiert JEDE EINZELN. Wer dort nur das Global Theme
# anklickt, behaelt die alten Symbole und den alten Plasma-Stil - das
# Design sieht dann aus wie vorher, obwohl die neue Fassung installiert
# scheint. Aus der Community kam genau dieser Fall zweimal.
#
# Geprueft wird deshalb nicht die Versionsnummer, sondern das Merkmal
# selbst: Liegt die Datei da, die den Fehler behebt?

set -uo pipefail

DATEN="${XDG_DATA_HOME:-$HOME/.local/share}"
ok=0
fehlt=0

titel() { printf '\n\033[1m%s\033[0m\n' "$1"; }
ja()    { printf '  \033[32mja  \033[0m %s\n' "$1"; ok=$((ok + 1)); }
nein()  { printf '  \033[31mNEIN\033[0m %s\n' "$1"; fehlt=$((fehlt + 1)); }
info()  { printf '       %s\n' "$1"; }

titel "Was gerade aktiv ist"
for paar in "Globales Design:kdeglobals:KDE:LookAndFeelPackage" \
            "Plasma-Stil:plasmarc:Theme:name" \
            "Farbschema:kdeglobals:General:ColorScheme" \
            "Symbole:kdeglobals:Icons:Theme" \
            "Widget-Stil:kdeglobals:KDE:widgetStyle"; do
    IFS=: read -r name datei gruppe schluessel <<< "$paar"
    wert="$(kreadconfig6 --file "$datei" --group "$gruppe" --key "$schluessel" 2>/dev/null)"
    printf '  %-16s %s\n' "$name" "${wert:-—}"
done

symbole="$(kreadconfig6 --file kdeglobals --group Icons --key Theme 2>/dev/null)"
stil="$(kreadconfig6 --file plasmarc --group Theme --key name 2>/dev/null)"

titel "Symbole: sind die skalierbaren Fassungen da? (0.2.6)"
if [ -z "$symbole" ]; then
    nein "kein Symbolthema eingestellt"
elif [ ! -d "$DATEN/icons/$symbole" ]; then
    info "Aktiv ist '$symbole' - das liegt nicht unter $DATEN/icons/,"
    info "kommt also aus dem System und nicht von diesem Theme."
    nein "$symbole"
else
    verz="$DATEN/icons/$symbole"
    if [ -f "$verz/places/scalable/folder.svg" ]; then
        ja "$verz/places/scalable/folder.svg"
    else
        nein "$verz/places/scalable/folder.svg fehlt"
        info "Das ist der Grund fuer pixelige Symbole ab 64 px."
        info "Abhilfe: nt-legacy-icons-0.2.6.tar.xz neu holen."
    fi
    if grep -q "Type=Scalable" "$verz/index.theme" 2>/dev/null; then
        ja "index.theme kennt Type=Scalable"
    else
        nein "index.theme ohne Type=Scalable - alter Stand"
    fi
fi

titel "Plasma-Stil: hat die Bildlaufleiste das Karo? (0.2.6)"
if [ -z "$stil" ]; then
    nein "kein Plasma-Stil eingestellt"
elif [ ! -d "$DATEN/plasma/desktoptheme/$stil" ]; then
    info "Aktiv ist '$stil' - das liegt nicht unter"
    info "$DATEN/plasma/desktoptheme/, kommt also nicht von diesem Theme."
    nein "$stil"
else
    svg="$DATEN/plasma/desktoptheme/$stil/widgets/scrollbar.svg"
    if [ ! -f "$svg" ]; then
        nein "$svg fehlt"
    elif grep -q 'stroke-dasharray' "$svg"; then
        # Die Karofarbe steht seit 0.2.6 als eigener Wert in der Palette;
        # vorher war es die 3D-Lichtkante und damit fast unsichtbar.
        if grep -q 'opacity="0.07"' "$svg"; then
            ja "$svg (Karo mit abgedunkelter Rinne)"
        else
            nein "$svg hat das Karo aus 0.2.5 - zu wenig Kontrast"
            info "Abhilfe: nt-legacy-plasma-style-<farbwelt>-0.2.6.tar.xz"
            info "neu holen. Die Farbwelt steht oben unter 'Plasma-Stil'."
        fi
    else
        nein "$svg ohne Karo - Stand vor 0.2.5"
    fi
fi

titel "Zwischenspeicher"
for muster in "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/icon-cache.kcache" \
              "$HOME/.cache/ksvg-elements"; do
    [ -e "$muster" ] && info "liegt noch: ${muster/#$HOME/~}"
done
info "Loeschen und neu anmelden, falls oben alles 'ja' ist und es"
info "trotzdem alt aussieht:"
info "  rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/icon-cache.kcache"
info "  rm -rf ~/.cache/ksvg-elements"

printf '\n%d in Ordnung, %d zu holen\n' "$ok" "$fehlt"
if [ "$fehlt" -gt 0 ]; then
    printf '\nZur Erinnerung: "Neue holen ..." aktualisiert jede Ebene\n'
    printf 'einzeln. Symbole und Plasma-Stil sind eigene Downloads -\n'
    printf 'das Global Theme bringt sie NICHT mit.\n'
fi
