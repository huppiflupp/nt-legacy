#!/usr/bin/env bash
# Installiert das GRUB-Theme von NT Legacy.
#
#   ./install-grub.sh              # Grundfassung (Petrol)
#   ./install-grub.sh win2k        # eine der Varianten
#   ./install-grub.sh --zurueck    # Theme entfernen, Vorgabe wiederherstellen
#
# ACHTUNG - das hier ist NICHT install.sh.
#
# install.sh fasst ausschliesslich $HOME an. Dieses Skript schreibt nach
# /boot und /etc/default/grub und braucht deshalb sudo. Es sichert
# vorher, und der Rueckweg steht am Ende - aber wer seinen Bootloader
# nicht anfassen will, laesst es einfach: das Theme funktioniert ohne.
#
# Was im schlimmsten Fall passiert: GRUB findet das Theme nicht und
# zeichnet sein schlichtes Textmenue. Der Rechner startet trotzdem.
# Kaputtgehen kann der Start nur, wenn grub.cfg selbst beschaedigt wird -
# deshalb wird sie vorher kopiert und danach neu erzeugt, nicht editiert.

set -euo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Wohin gehoert das Theme, und wie heisst die Konfiguration? ───────────
#
# Fedora und Verwandte nennen alles "grub2", Debian und Arch "grub".
# Beides kommt vor, und der falsche Pfad faellt erst beim naechsten
# Start auf - da ist es zu spaet zum Nachsehen.
if [ -d /boot/grub2 ]; then
    GRUB_DIR="/boot/grub2"
elif [ -d /boot/grub ]; then
    GRUB_DIR="/boot/grub"
else
    echo "FEHLER: Weder /boot/grub2 noch /boot/grub gefunden." >&2
    echo "        Nutzt dieses System ueberhaupt GRUB?" >&2
    exit 1
fi
THEMES="$GRUB_DIR/themes"
DEFAULT="/etc/default/grub"
SICHERUNG="/var/backups/nt-legacy-grub"

mkgrubcfg() {
    # Die Konfiguration neu erzeugen. Auf UEFI-Fedora liegt sie unter
    # /boot/efi/EFI/<distro>/grub.cfg, auf BIOS unter /boot/grub2 - der
    # Aufruf ohne -o trifft beides, weil grub2-mkconfig die richtige
    # Datei selbst kennt. Nur wo das Werkzeug anders heisst, muessen wir
    # suchen.
    if command -v grub2-mkconfig >/dev/null; then
        sudo grub2-mkconfig -o "$GRUB_DIR/grub.cfg"
    elif command -v grub-mkconfig >/dev/null; then
        sudo grub-mkconfig -o "$GRUB_DIR/grub.cfg"
    elif command -v update-grub >/dev/null; then
        sudo update-grub
    else
        echo "WARNUNG: grub2-mkconfig nicht gefunden - grub.cfg unveraendert." >&2
        return 1
    fi
}

# ── Rueckweg ─────────────────────────────────────────────────────────────
if [ "${1:-}" = "--zurueck" ]; then
    echo "Setze GRUB auf den Stand vor der Installation zurueck …"
    if [ -f "$SICHERUNG/grub" ]; then
        sudo cp -a "$SICHERUNG/grub" "$DEFAULT"
        echo "  $DEFAULT wiederhergestellt"
    else
        # Keine Sicherung? Dann wenigstens die Zeile entfernen, die wir
        # gesetzt haben - ein Verweis auf ein geloeschtes Theme laesst
        # GRUB im Textmodus starten, was zwar funktioniert, aber
        # unnoetig haesslich ist.
        sudo sed -i '/^GRUB_THEME=.*NTLegacy/d' "$DEFAULT"
        echo "  GRUB_THEME-Zeile entfernt (keine Sicherung gefunden)"
    fi
    # Das Sternchen muss ROOT ausklappen, nicht die Shell des Nutzers.
    #
    # /boot/grub2 ist nur fuer root lesbar. Als tester findet die Shell
    # keinen Treffer und reicht das Muster woertlich weiter - rm loescht
    # dann eine Datei namens "NTLegacy*", die es nicht gibt, und meldet
    # Erfolg. In der Test-VM stand das Theme nach --zurueck noch da.
    sudo sh -c "rm -rf '$THEMES'/NTLegacy*"
    echo "  Themes entfernt"
    mkgrubcfg && echo "  grub.cfg neu erzeugt"
    exit 0
fi

VARIANTE="${1:-teal}"

# Die Kennung kommt aus build.py - eine Wahrheit, wie in apply.sh.
NAME=$(cd "$HIER" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
v = sys.argv[1]
if v not in m.VARIANTEN:
    print('UNBEKANNT ' + ' '.join(sorted(m.VARIANTEN)))
else:
    print(m.ids(v)['aurorae'])
" "$VARIANTE")

if [ "${NAME%% *}" = "UNBEKANNT" ]; then
    echo "Unbekannte Variante '$VARIANTE'." >&2
    echo "Moeglich: ${NAME#UNBEKANNT }" >&2
    exit 1
fi

QUELLE="$HIER/grub/$NAME"
if [ ! -d "$QUELLE" ]; then
    echo "FEHLER: $QUELLE fehlt." >&2
    echo "        Erst  ./build.py  ausfuehren." >&2
    exit 1
fi

echo "GRUB-Theme: $NAME"
echo "Dieses Skript braucht sudo - es schreibt nach $GRUB_DIR und $DEFAULT."
echo ""

# ── Sicherung ────────────────────────────────────────────────────────────
#
# Nur beim ERSTEN Mal. Beim zweiten Lauf stuende in /etc/default/grub
# bereits unsere GRUB_THEME-Zeile - eine Sicherung davon fuehrt nicht
# mehr zurueck, sondern stellt den veraenderten Zustand wieder her.
# Genau so ist der erste Rueckweg-Test in der VM ausgegangen.
sudo mkdir -p "$SICHERUNG"
if sudo test ! -f "$SICHERUNG/grub"; then
    [ -f "$DEFAULT" ] && sudo cp -a "$DEFAULT" "$SICHERUNG/grub"
    [ -f "$GRUB_DIR/grub.cfg" ] && sudo cp -a "$GRUB_DIR/grub.cfg" "$SICHERUNG/grub.cfg"
    echo "Sicherung: $SICHERUNG"
else
    echo "Sicherung liegt schon vor: $SICHERUNG  (vom ersten Lauf, bleibt)"
fi

# ── Installation ─────────────────────────────────────────────────────────
sudo mkdir -p "$THEMES"
sudo rm -rf "$THEMES/$NAME"
sudo cp -a "$QUELLE" "$THEMES/$NAME"
echo "  $THEMES/$NAME"

# GRUB_THEME setzen - vorhandene Zeile ersetzen, sonst anhaengen.
if sudo grep -q "^GRUB_THEME=" "$DEFAULT" 2>/dev/null; then
    sudo sed -i "s|^GRUB_THEME=.*|GRUB_THEME=\"$THEMES/$NAME/theme.txt\"|" "$DEFAULT"
else
    echo "GRUB_THEME=\"$THEMES/$NAME/theme.txt\"" | sudo tee -a "$DEFAULT" >/dev/null
fi

# Ohne Grafikmodus zeigt GRUB das Theme nicht an, sondern sein
# Textmenue - das Theme waere installiert und unsichtbar. 'auto' laesst
# GRUB die beste Aufloesung selbst waehlen.
if sudo grep -q "^GRUB_GFXMODE=" "$DEFAULT" 2>/dev/null; then
    :
else
    echo 'GRUB_GFXMODE=auto' | sudo tee -a "$DEFAULT" >/dev/null
fi
# GRUB_TERMINAL=console schaltet die Grafik ausdruecklich ab. Wenn die
# Zeile gesetzt ist, gewinnt sie gegen alles andere.
if sudo grep -qE "^GRUB_TERMINAL(_OUTPUT)?=.*console" "$DEFAULT" 2>/dev/null; then
    echo ""
    echo "HINWEIS: In $DEFAULT steht GRUB_TERMINAL=console."
    echo "         Solange die Zeile dort steht, bleibt das Menue im"
    echo "         Textmodus und das Theme unsichtbar. Auskommentieren"
    echo "         und dieses Skript erneut laufen lassen."
fi

echo ""
mkgrubcfg && echo "  grub.cfg neu erzeugt"

cat <<EOF

Fertig. Beim naechsten Start zeigt GRUB das NT-Menue.

  Sieht man es nicht? Dann steht das Menue vermutlich auf versteckt:
    GRUB_TIMEOUT_STYLE=menu  und  GRUB_TIMEOUT=5  in $DEFAULT

  Zurueck:  ./install-grub.sh --zurueck
EOF
