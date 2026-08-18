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

# Nennt den Installationsbefehl der laufenden Distribution.
#
# Vorher stand in beiden Meldungen unten "dnf install …" - auf dem
# Arch-Testsystem also ein Befehl, den es dort gar nicht gibt. Wer eine
# Fehlermeldung schreibt, sollte den Rat darin auch ausfuehren koennen.
paketbefehl() {
    if command -v pacman >/dev/null;   then echo "sudo pacman -S --needed $1"
    elif command -v dnf >/dev/null;    then echo "sudo dnf install $1"
    elif command -v apt >/dev/null;    then echo "sudo apt install $1"
    elif command -v zypper >/dev/null; then echo "sudo zypper install $1"
    else echo "das Paket '$1' nachinstallieren"
    fi
}

if ! command -v plymouth-set-default-theme >/dev/null; then
    echo "FEHLER: plymouth-set-default-theme fehlt." >&2
    echo "        Nutzt dieses System Plymouth? Sonst:" >&2
    echo "        $(paketbefehl plymouth)" >&2
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
    echo "        Auf Fedora und Nobara ist es ein eigenes Paket:" >&2
    echo "        $(paketbefehl plymouth-plugin-script)" >&2
    echo "        Anderswo steckt es in 'plymouth' selbst." >&2
    exit 1
fi

initramfs_neu() {
    # Die Reihenfolge ist nicht beliebig.
    #
    # dracut-rebuild kommt zuerst, weil EndeavourOS es genau dafuer
    # mitbringt: dort scheitert ein blosses "dracut --force" mit
    #
    #   dracut[F]: Can't write to /boot/efi/<machine-id>/<kernel>:
    #   Directory does not exist or is not accessible.
    #
    # Grund ist das kernel-install-Layout - dracut allein sucht ein
    # Verzeichnis, das dort niemand angelegt hat. In der Arch-Test-VM
    # beim Rueckweg aufgefallen; die initramfs blieb unveraendert, ohne
    # dass das Skript es gemerkt haette.
    if command -v dracut-rebuild >/dev/null; then
        echo "  initramfs neu bauen (dracut-rebuild) - das dauert einen Moment …"
        sudo dracut-rebuild
    elif command -v dracut >/dev/null; then
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

# Der Aufruf oben darf nicht stillschweigend scheitern: eine nicht
# erneuerte initramfs zeigt beim naechsten Start weiter das alte Theme,
# und niemand kaeme auf die Idee, dort zu suchen.
initramfs_neu_gemeldet() {
    if ! initramfs_neu; then
        echo "" >&2
        echo "WARNUNG: Der Neubau der initramfs ist fehlgeschlagen." >&2
        echo "         Das Theme liegt richtig, erscheint beim naechsten" >&2
        echo "         Start aber erst, wenn er nachgeholt wird." >&2
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
    initramfs_neu_gemeldet || true
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

initramfs_neu_gemeldet || true

# Ohne "splash" auf der Kernel-Kommandozeile zeigt Plymouth nichts.
#
# Fedora und Nobara setzen "rhgb quiet" ab Werk, Arch und EndeavourOS
# nicht - dort steht das Theme sauber installiert da und erscheint beim
# Start trotzdem nie. In der Arch-Test-VM nachgestellt; plymouthd sagt
# es selbst, aber nur im Debug-Protokoll:
#
#   no default splash because kernel command line lacks "splash" or "rhgb"
#
# Bewusst nur ein Hinweis: Kernel-Parameter aendert dieses Skript nicht
# von sich aus.
if ! grep -qE "(^| )(splash|rhgb)( |$)" /proc/cmdline; then
    # Den passenden Befehl fuer diese Distribution nennen statt einen,
    # der anderswo stimmt. Ein erster Entwurf schlug hier ein sed vor,
    # das auf doppelte Anfuehrungszeichen passte - EndeavourOS schreibt
    # die Zeile aber in einfachen. Der Rat waere wirkungslos verpufft,
    # und der Nutzer haette den Fehler beim Theme gesucht.
    if [ -d /boot/grub2 ]; then
        mkcfg="sudo grub2-mkconfig -o /boot/grub2/grub.cfg"
    else
        mkcfg="sudo grub-mkconfig -o /boot/grub/grub.cfg"
    fi
    cat >&2 <<HINWEIS

HINWEIS: Auf der Kernel-Kommandozeile fehlt "splash".

         Ohne dieses Wort zeigt Plymouth beim Start gar nichts - das
         Theme ist dann installiert und unsichtbar. Auf Arch und
         EndeavourOS ist das der Normalfall, auf Fedora steht dort ab
         Werk "rhgb quiet". plymouthd sagt es selbst, aber nur im
         Debug-Protokoll:

           no default splash because kernel command line lacks
           "splash" or "rhgb"

         So kommt es hinein: in /etc/default/grub das Wort splash in
         die Zeile GRUB_CMDLINE_LINUX_DEFAULT aufnehmen - innerhalb der
         Anfuehrungszeichen, hinter die vorhandenen Werte - und danach

           $mkcfg

HINWEIS
fi

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
