#!/usr/bin/env bash
# Entfernt NT Legacy vollstaendig.
#
# Wichtig ist die Reihenfolge: erst die Konfiguration zuruecksetzen, dann
# die Dateien loeschen. Andersherum zeigt kwinrc auf ein nicht mehr
# vorhandenes Aurorae-Thema - und dann zeichnet KWin GAR KEINE
# Titelleiste. Kein Fallback, kein Schliessknopf, kein Ziehbereich.
# In der Test-VM belegt: nur wenn die "library" ungueltig ist, faellt KWin
# auf Breeze zurueck; ein ins Leere zeigender Themename laedt Aurorae und
# zeichnet nichts.
#
# Dasselbe gilt fuer das Icon-Theme: fehlt das Verzeichnis, waehrend
# kdeglobals darauf zeigt, verschwinden Starter- und Systray-Symbole
# ganz, statt auf Breeze zurueckzufallen.

set -euo pipefail

DATEN="${XDG_DATA_HOME:-$HOME/.local/share}"

echo "Setze Konfiguration auf Breeze zurueck …"
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme   Breeze
kwriteconfig6 --file kdeglobals --group Icons   --key Theme        breeze
kwriteconfig6 --file kdeglobals --group KDE     --key widgetStyle  Breeze
kwriteconfig6 --file kdeglobals --group General --key ColorScheme   BreezeLight
kwriteconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage org.kde.breeze.desktop
kwriteconfig6 --file plasmarc   --group Theme   --key name          default
kwriteconfig6 --file kcminputrc --group Mouse   --key cursorTheme   breeze_cursors
kwriteconfig6 --file ksplashrc  --group KSplash --key Theme         org.kde.breeze.desktop

echo "Entferne Pakete …"
for d in "$DATEN"/plasma/desktoptheme/nt-legacy*; do
    [ -d "$d" ] || continue
    kpackagetool6 -t Plasma/Theme -r "$(basename "$d")" >/dev/null 2>&1 || true
    rm -rf "$d"; echo "  $(basename "$d")"
done
for d in "$DATEN"/plasma/look-and-feel/com.github.huppiflupp.nt-legacy*; do
    [ -d "$d" ] || continue
    kpackagetool6 -t Plasma/LookAndFeel -r "$(basename "$d")" >/dev/null 2>&1 || true
    rm -rf "$d"; echo "  $(basename "$d")"
done

rm -rf "$DATEN"/aurorae/themes/NTLegacy*      && echo "  Fensterdekorationen"

# Leere Huellen aufraeumen. rmdir statt rm -rf: schlaegt fehl, wenn noch
# etwas drin ist - genau das ist hier die Sicherung. Wer neben NT Legacy
# ein zweites Theme installiert hat, soll es behalten.
for d in "$DATEN"/plasma/desktoptheme "$DATEN"/plasma/look-and-feel \
         "$DATEN"/aurorae/themes "$DATEN"/aurorae; do
    rmdir "$d" 2>/dev/null && echo "  leeres Verzeichnis $d entfernt"
done
# Alle drei Symbolsaetze, nicht nur einer.
#
# Hier stand bis 0.2.13 allein "$DATEN/icons/NTLegacy" - das ist der
# Chicago95-Ableger aus fetch-icons.sh. Die beiden mitgelieferten Saetze
# NTLegacyIcons und NTLegacyIconsNacht blieben liegen, und mit ihnen der
# Eindruck, die Deinstallation habe nicht gewirkt. In der Arch-Test-VM
# aufgefallen, als der Ausgangszustand nach uninstall.sh nicht wieder
# der alte war.
rm -rf "$DATEN"/icons/NTLegacy "$DATEN"/icons/NTLegacyIcons \
       "$DATEN"/icons/NTLegacyIconsNacht      && echo "  Symbole"
rm -rf "$DATEN"/icons/NTLegacy*_cursors         2>/dev/null || true
rm -rf "$DATEN"/wallpapers/ntlegacy*           && echo "  Hintergrundbilder"
rm -f  "$DATEN"/color-schemes/NTLegacy*.colors && echo "  Farbschemata"

# Die Vorgabedatei des Globalen Designs aufraeumen.
#
# ~/.config/kdedefaults/ gehoert dem zuletzt angewendeten Design: Plasma
# legt die Werte dort als Vorgaben ab, nicht als Nutzerwerte. Nach der
# Deinstallation stand dort weiter "Theme=NTLegacyIcons" - ein Verweis
# auf einen Symbolsatz, den wir gerade geloescht haben.
#
# Die Sicherung deckt das nicht ab: install.sh kopiert ~/.config, nicht
# ~/.config/kdedefaults. Deshalb hier gezielt die eigenen Zeilen weg -
# und nur die eigenen. Wer inzwischen ein anderes Design angewendet hat,
# behaelt dessen Vorgaben unangetastet.
KDD="$HOME/.config/kdedefaults"
if [ -d "$KDD" ]; then
    geraeumt=false
    for f in "$KDD"/*; do
        [ -f "$f" ] || continue
        if grep -qE "=.*(NTLegacy|nt-legacy)" "$f" 2>/dev/null; then
            sed -i -E "/=.*(NTLegacy|nt-legacy)/d" "$f"
            geraeumt=true
        fi
    done
    $geraeumt && echo "  Vorgaben in kdedefaults"
fi

# Konsole: erst konsolerc zuruecksetzen, dann die Dateien loeschen.
# Zeigt DefaultProfile auf ein geloeschtes Profil, startet Konsole zwar,
# faellt aber auf ein leeres Standardprofil zurueck - inklusive
# verlorener Fenstergroesse und Verlaufslaenge.
if [ "$(kreadconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile 2>/dev/null)" = "NT Legacy.profile" ]; then
    kwriteconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile --delete
    echo "  Konsole zurueck auf ihr Standardprofil"
fi
rm -f "$DATEN"/konsole/NTLegacy*.colorscheme "$DATEN/konsole/NT Legacy.profile" \
    && echo "  Konsole-Profil und -Farbschemata"

rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements"

cat <<TEXT

Entfernt. Ab- und wieder anmelden.

Die Sicherungen unter $DATEN/nt-legacy/ bleiben liegen - dort steht der
Zustand von vor der Installation, falls du ihn brauchst.
TEXT
