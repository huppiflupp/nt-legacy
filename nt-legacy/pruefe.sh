#!/usr/bin/env bash
# Prueft, ob build.py und apply.sh dasselbe meinen.
#
# Warum es das gibt: Beim Umbau der Mauszeiger auf zwei globale Saetze
# wurde build.py angepasst, apply.sh nicht. Fuenf von sechs Varianten
# verwiesen danach auf ein Zeigerthema, das gar nicht mehr gebaut wird -
# aufgefallen ist es erst im Stabilitaetstest, an einer Logzeile.
#
# Dieses Skript vergleicht fuer jede Variante, ob alle Bestandteile, auf
# die apply.sh verweist, auch wirklich erzeugt wurden.
#
#   ./pruefe.sh          # gegen das Bauverzeichnis
#   ./pruefe.sh --system # zusaetzlich gegen das installierte System

set -uo pipefail
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATEN="${XDG_DATA_HOME:-$HOME/.local/share}"
SYSTEM=false
[ "${1:-}" = "--system" ] && SYSTEM=true

fehler=0
meld() { echo "  FEHLT  $*"; fehler=$((fehler + 1)); }

# Die Variantenliste kommt aus build.py, nicht aus einer zweiten Kopie -
# sonst haette man wieder zwei Wahrheiten.
varianten=$(python3 -c "
import importlib.util
s = importlib.util.spec_from_file_location('b', '$HIER/build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
for k in m.VARIANTEN:
    i = m.ids(k)
    print(k, i['style'], i['schema'], i['aurorae'], i['lnf'], i['wallpaper'])
")

printf '%-14s %s\n' "Variante" "Bestandteile"
while read -r name style schema aurorae lnf wallpaper; do
    [ -z "$name" ] && continue
    vorher=$fehler
    [ -d "$HIER/desktoptheme/$style" ]        || meld "$name: desktoptheme/$style"
    [ -f "$HIER/color-schemes/$schema.colors" ] || meld "$name: color-schemes/$schema.colors"
    [ -d "$HIER/aurorae/$aurorae" ]           || meld "$name: aurorae/$aurorae"
    [ -d "$HIER/look-and-feel/$lnf" ]         || meld "$name: look-and-feel/$lnf"
    [ -d "$HIER/wallpapers/$wallpaper" ]      || meld "$name: wallpapers/$wallpaper"
    [ -f "$HIER/look-and-feel/$lnf/contents/previews/preview.png" ] \
        || meld "$name: Vorschaubild"

    # Das Aurorae-Thema muss den Praefix tragen, den contents/defaults setzt
    d="$HIER/look-and-feel/$lnf/contents/defaults"
    if [ -f "$d" ]; then
        soll=$(grep -oP '(?<=^theme=__aurorae__svg__).*' "$d" || true)
        [ "$soll" = "$aurorae" ] || meld "$name: defaults verweist auf '$soll', gebaut ist '$aurorae'"
        # Verweist defaults auf ein Zeigerthema, das es gibt?
        z=$(grep -oP '(?<=^cursorTheme=).*' "$d" || true)
        [ -z "$z" ] || [ -d "$HIER/cursors/$z" ] || meld "$name: Zeigerthema '$z'"
    fi

    # Kann apply.sh diese Variante ueberhaupt? Es liest sie inzwischen
    # aus build.py, also genuegt der Trockenlauf.
    "$HIER/apply.sh" "$name" --nur-pruefen >/dev/null 2>&1 \
        || meld "$name: apply.sh kennt sie nicht"

    [ "$fehler" -eq "$vorher" ] && printf '%-14s ok\n' "$name"
done <<< "$varianten"

if $SYSTEM; then
    echo
    echo "Installiert:"
    while read -r name style schema aurorae lnf wallpaper; do
        [ -z "$name" ] && continue
        [ -d "$DATEN/plasma/desktoptheme/$style" ] || meld "installiert: $style"
        [ -d "$DATEN/plasma/look-and-feel/$lnf" ]  || meld "installiert: $lnf"
        [ -d "$DATEN/aurorae/themes/$aurorae" ]    || meld "installiert: aurorae/$aurorae"
    done <<< "$varianten"
    for z in NTLegacy_cursors NTLegacyRot_cursors; do
        [ -d "$DATEN/icons/$z" ] || meld "installiert: $z"
    done
    # Beide Symbolsaetze. Der Nachtsatz traegt dieselben Bilder, erbt aber
    # von breeze-dark - fehlt er, faellt jede Nachtfassung auf den hellen
    # Satz zurueck und der halbe Systemabschnitt wird unsichtbar.
    for satz in NTLegacyIcons NTLegacyIconsNacht; do
        [ -d "$DATEN/icons/$satz" ] || meld "installiert: Icon-Theme $satz"
    done
    if [ -f "$DATEN/icons/NTLegacyIconsNacht/index.theme" ] && \
       ! grep -q '^Inherits=breeze-dark' "$DATEN/icons/NTLegacyIconsNacht/index.theme"; then
        meld "NTLegacyIconsNacht erbt nicht von breeze-dark"
    fi

    # Steht das Icon-Thema wirklich in kdeglobals?
    #
    # Es genuegt nicht, dass es in contents/defaults steht. KDE-Programme
    # kommen ueber die Vorgabenkaskade auch dann an die richtigen Icons,
    # wenn der Schluessel in kdeglobals fehlt - reine Qt-Programme
    # (pcmanfm-qt, viele Fremdanwendungen) lesen aber nur die Datei und
    # landen sonst bei Breeze. Man sieht den Fehler also ausgerechnet in
    # Dolphin nicht.
    #
    # Passiert regelmaessig: Ein Designwechsel ueber Systemeinstellungen >
    # Globales Design schreibt die Gruppe neu und laesst sie leer.
    if [ -z "$(kreadconfig6 --file kdeglobals --group Icons --key Theme 2>/dev/null)" ]; then
        meld "kdeglobals [Icons] Theme ist leer - reine Qt-Programme zeigen Breeze-Icons"
        echo "         Beheben:  kwriteconfig6 --file kdeglobals --group Icons --key Theme NTLegacy"
    fi
fi

echo
if [ "$fehler" -eq 0 ]; then
    echo "Alles stimmig."
else
    echo "$fehler Unstimmigkeiten."
fi
exit $((fehler > 0))
