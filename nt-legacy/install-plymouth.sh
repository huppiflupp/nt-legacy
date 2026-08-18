#!/usr/bin/env bash
# Installiert den Boot-Startbildschirm (Plymouth) von NT Legacy.
#
#   ./install-plymouth.sh              # Grundfassung (Petrol)
#   ./install-plymouth.sh win2k        # eine der Varianten
#   ./install-plymouth.sh --zurueck    # zurueck auf das vorherige Theme
#
# ACHTUNG - das hier ist NICHT install.sh.
#
# Das Theme liegt unter /usr/share/plymouth/themes und muss in die
# initramfs eingebaut werden; beides braucht sudo. Der Neubau der
# initramfs dauert je nach Rechner eine halbe bis zwei Minuten.
#
# Was im schlimmsten Fall passiert: Plymouth findet das Theme nicht und
# zeigt gar keinen Startbildschirm - der Rechner startet trotzdem, man
# sieht dann die Textmeldungen. Wer eine verschluesselte Platte hat,
# sollte trotzdem den Test unten machen, bevor er neu startet.

set -euo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEMES="/usr/share/plymouth/themes"
SICHERUNG="/var/backups/nt-legacy-plymouth"

if ! command -v plymouth-set-default-theme >/dev/null; then
    echo "FEHLER: plymouth-set-default-theme fehlt." >&2
    echo "        Nutzt dieses System Plymouth? (dnf install plymouth)" >&2
    exit 1
fi

# Das Skript-Modul ist eine eigene Paketauslieferung und fehlt oft.
# Ohne es laedt Plymouth das Theme nicht und faellt still auf 'text'
# zurueck - der haeufigste Grund, warum ein selbstgebautes Theme
# "einfach nicht erscheint".
if [ ! -f /usr/lib64/plymouth/script.so ] && \
   [ ! -f /usr/lib/plymouth/script.so ] && \
   [ ! -f /usr/lib/x86_64-linux-gnu/plymouth/script.so ]; then
    echo "FEHLER: Das Plymouth-Modul 'script' fehlt." >&2
    echo "        Fedora/Nobara:  sudo dnf install plymouth-plugin-script" >&2
    echo "        Debian/Ubuntu:  ist in plymouth enthalten" >&2
    echo "        Arch:           ist in plymouth enthalten" >&2
    exit 1
fi

initramfs_neu() {
    if command -v dracut >/dev/null; then
        echo "  initramfs neu bauen (dracut) - das dauert einen Moment …"
        sudo dracut --force
    elif command -v update-initramfs >/dev/null; then
        echo "  initramfs neu bauen (update-initramfs) …"
        sudo update-initramfs -u
    elif command -v mkinitcpio >/dev/null; then
        echo "  initramfs neu bauen (mkinitcpio) …"
        sudo mkinitcpio -P
    else
        echo "WARNUNG: Kein initramfs-Werkzeug gefunden." >&2
        echo "         Das Theme greift erst, wenn die initramfs neu" >&2
        echo "         gebaut wurde." >&2
        return 1
    fi
}

# ── Rueckweg ─────────────────────────────────────────────────────────────
if [ "${1:-}" = "--zurueck" ]; then
    if [ -f "$SICHERUNG/theme" ]; then
        vorher="$(cat "$SICHERUNG/theme")"
        echo "Setze zurueck auf '$vorher' …"
        sudo plymouth-set-default-theme "$vorher"
    else
        echo "Keine Sicherung gefunden - setze auf 'bgrt' (Fedora-Vorgabe) …"
        sudo plymouth-set-default-theme bgrt 2>/dev/null || \
            sudo plymouth-set-default-theme details
    fi
    sudo sh -c "rm -rf '$THEMES'/nt-legacy-*"
    initramfs_neu || true
    echo "Zurueckgesetzt."
    exit 0
fi

VARIANTE="${1:-teal}"

NAME=$(cd "$HIER" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
v = sys.argv[1]
if v not in m.VARIANTEN:
    print('UNBEKANNT ' + ' '.join(sorted(m.VARIANTEN)))
else:
    print(m.ids(v)['lnf'].split('.')[-1])
" "$VARIANTE")

if [ "${NAME%% *}" = "UNBEKANNT" ]; then
    echo "Unbekannte Variante '$VARIANTE'." >&2
    echo "Moeglich: ${NAME#UNBEKANNT }" >&2
    exit 1
fi

QUELLE="$HIER/plymouth/$NAME"
if [ ! -d "$QUELLE" ]; then
    echo "FEHLER: $QUELLE fehlt." >&2
    echo "        Erst  ./build.py  ausfuehren." >&2
    exit 1
fi

echo "Plymouth-Theme: $NAME"
echo "Dieses Skript braucht sudo - es schreibt nach $THEMES."
echo ""

# ── Sicherung ────────────────────────────────────────────────────────────
# Auch hier nur beim ersten Mal: beim zweiten Lauf waere das
# "vorherige" Theme unser eigenes, und --zurueck fuehrte im Kreis.
sudo mkdir -p "$SICHERUNG"
if sudo test ! -f "$SICHERUNG/theme"; then
    vorher="$(plymouth-set-default-theme 2>/dev/null || echo bgrt)"
    echo "$vorher" | sudo tee "$SICHERUNG/theme" >/dev/null
    echo "Vorheriges Theme: $vorher  (gemerkt in $SICHERUNG/theme)"
else
    echo "Vorheriges Theme steht schon fest: $(sudo cat "$SICHERUNG/theme")"
fi

# ── Installation ─────────────────────────────────────────────────────────
sudo rm -rf "${THEMES:?}/$NAME"
sudo cp -a "$QUELLE" "$THEMES/$NAME"
echo "  $THEMES/$NAME"

sudo plymouth-set-default-theme "$NAME"
echo "  als Vorgabe gesetzt"

initramfs_neu || true

cat <<EOF

Fertig. Beim naechsten Start erscheint der NT-Startbildschirm.

  Vorher ansehen, ohne neu zu starten:

    sudo plymouthd --debug --tty=/dev/tty1
    sudo plymouth --show-splash
    sleep 5; sudo plymouth --quit

  Mit verschluesselter Platte unbedingt zusaetzlich die Passwortabfrage
  pruefen - sie ist das einzige, was beim Start wirklich schiefgehen
  kann:

    sudo plymouth ask-for-password --prompt "Test"

  Zurueck:  ./install-plymouth.sh --zurueck
EOF
