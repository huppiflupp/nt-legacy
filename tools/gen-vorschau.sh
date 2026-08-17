#!/usr/bin/env bash
# Ersetzt die schematischen Vorschaubilder durch echte Screenshots.
#
# Fuer jede Variante: in der Test-VM anwenden, Sitzung neu starten,
# ein paar Fenster oeffnen, Bildschirmfoto machen, zuschneiden.
#
#   ./gen-vorschau.sh              # alle Varianten
#   ./gen-vorschau.sh teal lilac   # nur diese
#
# Der Sitzungsneustart je Variante ist nicht wegzuoptimieren: KWin laedt
# Aurorae-Themen ausschliesslich beim Start. Ohne Neustart traegt jedes
# Bild die Titelleiste der vorherigen Variante - und genau die ist das
# auffaelligste Merkmal.
#
# Dauer: rund zwei Minuten je Variante.
#
# HINWEIS: Dieses Skript braucht die Test-VM aus der Werkstatt
# (vm/vmctl.sh) und laeuft in diesem Repository deshalb nicht. Es liegt
# hier bei, weil build.py und mach-paket.sh darauf verweisen: die
# Vorschaubilder im Theme sind damit entstanden, nicht von Hand.

set -uo pipefail

LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VMCTL="$LAB/vm/vmctl.sh"
THEME="$LAB/nt-legacy"
BREITE=1920
HOEHE=1080

varianten=("$@")
if [ ${#varianten[@]} -eq 0 ]; then
    mapfile -t varianten < <(cd "$THEME" && python3 -c "
import importlib.util
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print('\n'.join(m.VARIANTEN))
")
fi

lnf_fuer() {
    (cd "$THEME" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(m.ids(sys.argv[1])['lnf'])
" "$1")
}

warte_auf_vm() {
    for _ in $(seq 1 30); do
        "$VMCTL" ssh 'test -f /etc/plasma-lab-ready' >/dev/null 2>&1 && return 0
        sleep 10
    done
    return 1
}

echo "Uebertrage aktuellen Stand …"
"$VMCTL" push "$THEME/" /home/tester/nt-legacy/ >/dev/null 2>&1
"$VMCTL" ssh 'cd nt-legacy && ./install.sh >/dev/null 2>&1' || {
    echo "FEHLER: Installation in der VM fehlgeschlagen" >&2; exit 1; }

for v in "${varianten[@]}"; do
    lnf="$(lnf_fuer "$v")"
    ziel="$THEME/look-and-feel/$lnf/contents/previews"
    echo
    echo "=== $v ==="

    "$VMCTL" ssh "cd nt-legacy && ./apply.sh $v >/dev/null 2>&1" || {
        echo "  uebersprungen (apply.sh fehlgeschlagen)"; continue; }

    # Den Hintergrund der Variante ausdruecklich setzen.
    #
    # Das Global Theme nennt ihn in contents/defaults, aber das greift
    # nur bei einer frischen Sitzung - eine bestehende behaelt ihr Bild.
    # Seit 0.2.6 ist das eine Landschaft und kein Farbverlauf mehr;
    # ohne diese Zeile zeigten die Vorschaubilder weiter den alten
    # Grund.
    wp="$(cd "$THEME" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(m.ids(sys.argv[1])['wallpaper'])
" "$v")"
    "$VMCTL" ssh "plasma-apply-wallpaperimage \
        ~/.local/share/wallpapers/$wp >/dev/null 2>&1" || true

    # Neu anmelden, damit die Fensterdekoration greift
    "$VMCTL" ssh 'sudo systemctl reboot' >/dev/null 2>&1
    sleep 45
    warte_auf_vm || { echo "  VM kam nicht zurueck"; continue; }
    sleep 30

    "$VMCTL" ssh "
        kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
        # 16:9, damit die Kachel im Auswahldialog nicht beschneidet
        kscreen-doctor output.1.mode.${BREITE}x${HOEHE}@60 >/dev/null 2>&1
        sleep 4

        # Drei Fenster nebeneinander statt gestapelt.
        #
        # Gestapelt war die Idee, auf einem Bild eine aktive und mehrere
        # inaktive Titelleisten zu zeigen. Der Preis war hoch: Von den
        # unteren Fenstern blieb je ein Streifen uebrig, und gerade der
        # Dateimanager - das Aushaengeschild fuer den Symbolsatz - war
        # zur Haelfte verdeckt. Nebeneinander ist jedes Fenster ganz zu
        # sehen. Die inaktive Titelleiste zeigen die beiden Fenster, die
        # nicht den Fokus haben, weiterhin.
        #
        # Dolphin bekommt den groessten Anteil und steht im persoenlichen
        # Ordner: Bilder, Dokumente, Downloads, Musik, Videos - jeder mit
        # seiner eigenen Ordnermarke. Das ist auf einen Blick mehr vom
        # Symbolsatz zu sehen als in jeder Werkzeugleiste.
        #
        # Positioniert wird ueber KWin-Fensterregeln, nicht ueber
        # xdotool: Unter Wayland kann kein fremder Prozess Fenster
        # verschieben. Die Regeln stehen in der Wegwerf-VM, nicht beim
        # Nutzer.
        # Die Fenster sitzen mit Abstand zum Rand und lassen unten einen
# Streifen frei. Seit 0.2.6 ist der Hintergrund je Variante eine eigene
# Landschaft - vollflaechig verdeckt waere sie im Vorschaubild nicht zu
# sehen, und sie ist einer der Gruende, ueberhaupt neue Bilder zu machen.
cat > ~/.config/kwinrulesrc <<'REGELN'
[General]
count=4
rules=vorschau-dateien,vorschau-editor,vorschau-taskmanager,vorschau-terminal

[vorschau-dateien]
Description=Vorschau: Dateimanager links
wmclass=dolphin
wmclassmatch=2
position=40,40
positionrule=3
size=660,790
sizerule=3

[vorschau-editor]
Description=Vorschau: Editor Mitte
wmclass=kwrite
wmclassmatch=2
position=716,40
positionrule=3
size=500,790
sizerule=3

[vorschau-taskmanager]
Description=Vorschau: Taskmanager rechts oben
wmclass=nt-taskmanager
wmclassmatch=2
position=1232,40
positionrule=3
size=648,420
sizerule=3

[vorschau-terminal]
Description=Vorschau: Terminal rechts unten
wmclass=konsole
wmclassmatch=2
position=1232,476
positionrule=3
size=648,354
sizerule=3
REGELN
        qdbus-qt6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1
        sleep 2

        # Dolphin auf Symbolansicht mit grossen Symbolen. Die Detailliste
        # zeigt 16-px-Symbole - da ist von den Ordnermarken nichts mehr zu
        # erkennen.
        kwriteconfig6 --file dolphinrc --group General --key ViewMode 0
        kwriteconfig6 --file dolphinrc --group IconsMode --key PreviewSize 64
        kwriteconfig6 --file dolphinrc --group IconsMode --key IconSize 64
        kwriteconfig6 --file dolphinrc --group General --key ShowFullPath false

        # Was hier sonst herumliegt, gehoert nicht ins Bild. Das
        # Arbeitsverzeichnis des Themes laesst sich nicht wegraeumen - es
        # wird gebraucht -, aber .hidden nimmt es aus der Ansicht: KIO
        # blendet jeden Namen aus, der dort steht.
        mkdir -p ~/.vorschau-beiseite
        mv ~/*.sh ~/*.py ~/.vorschau-beiseite/ 2>/dev/null
        printf 'nt-legacy\n' > ~/.hidden

        # Die Benutzerordner auf englische Namen. Ohne das steht im Bild
        # eine englische Seitenleiste neben deutschen Ordnernamen -
        # \"Home, Documents, Pictures\" links, \"Bilder, Dokumente,
        # Schreibtisch\" rechts. Genau die Ordner sind hier aber das
        # Motiv, weil sie die neuen Ordnermarken tragen.
        #
        # xdg-user-dirs-update taugt nicht: es legt die englischen Ordner
        # neu an, statt die vorhandenen umzubenennen, und danach stehen
        # beide da.
        cd ~
        while IFS=: read -r alt neu schluessel; do
            [ -d \"\$alt\" ] && [ ! -e \"\$neu\" ] && mv \"\$alt\" \"\$neu\"
            printf 'XDG_%s_DIR=\"\$HOME/%s\"\n' \"\$schluessel\" \"\$neu\"
        done <<'ORDNER' > ~/.config/user-dirs.dirs
Schreibtisch:Desktop:DESKTOP
Dokumente:Documents:DOCUMENTS
Downloads:Downloads:DOWNLOAD
Musik:Music:MUSIC
Bilder:Pictures:PICTURES
Videos:Videos:VIDEOS
Öffentlich:Public:PUBLICSHARE
Vorlagen:Templates:TEMPLATES
ORDNER

        # Reihenfolge: das zuletzt geoeffnete Fenster hat den Fokus und
        # zeigt die aktive Titelleiste. Das soll der Dateimanager sein.
        #
        # Die Konsole bekommt einen Befehl mit auf den Weg. Ein blosser
        # Prompt zeigt vom Terminal nur den Hintergrund - die acht
        # ANSI-Farben sind aber eigens auf gemessenen Kontrast gebracht
        # worden (4,5:1 normal, 7:1 intense), und ein farbiges ls ist der
        # einzige Ort, an dem man das sieht.
        # Englische Oberflaeche, obwohl die VM auf Deutsch laeuft. Die
        # Bilder gehen an store.kde.org, und der Eintrag ist englisch -
        # deutsche Menuepunkte schliessen den groessten Teil der Leser
        # aus. Nur die Programme werden umgestellt, nicht die Sitzung:
        # Panel und Uhr bleiben deutsch, was im Bild nicht auffaellt, und
        # ein Sprachwechsel der ganzen Sitzung braeuchte einen weiteren
        # Neustart.
        export LANGUAGE=en_US LANG=en_US.UTF-8 LC_ALL=
        (setsid konsole -e bash -c 'ls --color=always -l /usr/share | head -22; exec bash' >/dev/null 2>&1 &); sleep 9
        (setsid kwrite ~/nt-legacy/INSTALL.md >/dev/null 2>&1 &); sleep 10
        # Der Taskmanager auf dem Reiter mit den Balken: Prozessliste und
        # Dienste sind Tabellen wie im Dateimanager nebenan, die Balken
        # und Verlaeufe sind das Einzige, was es sonst nirgends im Bild
        # gibt. --on-top waere hier falsch - die Regel setzt ihn ohnehin
        # an seinen Platz, und obenauf verdeckte er beim naechsten
        # Fenster etwas.
        (setsid nt-taskmanager --tab 2 >/dev/null 2>&1 &); sleep 8
        (setsid dolphin ~ >/dev/null 2>&1 &); sleep 12
    " >/dev/null 2>&1

    virsh -c qemu:///system send-key plasma-lab KEY_LEFTSHIFT >/dev/null 2>&1
    sleep 3

    roh="$(mktemp --suffix=.png)"
    "$VMCTL" shot "$roh" >/dev/null 2>&1
    if [ ! -s "$roh" ]; then
        echo "  kein Bildschirmfoto"; rm -f "$roh"; continue
    fi

    mkdir -p "$ziel"

    # Vollbild fuer die Grossansicht - dort ist Platz genug.
    magick "$roh" -resize "${BREITE}x${HOEHE}!" -quality 88 \
        "$ziel/fullscreenpreview.jpg"

    # Die Kachel zeigt nur die linken zwei Fenster, nicht alle vier.
    #
    # Vier Fenster nebeneinander ergeben ein Motiv im Verhaeltnis 3:1.
    # Die Kachel ist aber 16:9 - wer das hineinzwingt, bekommt entweder
    # zwei leere Balken oder einen Bildausschnitt, in dem von den
    # aeusseren Fenstern nichts mehr uebrig ist. Beides war schlechter
    # als die einfache Loesung: Dolphin und der Editor, in ganzer Hoehe.
    # Das sind ohnehin die beiden, die etwas zeigen - Ordnersymbole und
    # eine eingefaerbte Textansicht. Das Terminal steht im Vollbild.
    # 64 statt 69 Prozent: Bei 69 endete der Ausschnitt mitten im
    # Taskmanager, seit der als viertes Fenster dazugekommen ist. 64
    # schneidet in der Luecke zwischen Editor und Taskmanager - kein
    # angeschnittenes Fenster am Rand. Das Verhaeltnis bleibt 16:9.
    magick "$roh" -gravity northwest -crop 64%x64%+8+24 +repage \
        -resize 600x337! "$ziel/preview.png"
    cp "$ziel/preview.png" "$ziel/lockscreen.png"
    cp "$ziel/preview.png" "$ziel/splash.png"
    rm -f "$roh"

    echo "  $(basename "$ziel")/preview.png  (aus echtem Bildschirmfoto)"
    "$VMCTL" ssh 'pkill dolphin; pkill kwrite; pkill konsole' >/dev/null 2>&1
done

echo
echo "Fertig. Die Bilder liegen in nt-legacy/look-and-feel/*/contents/previews/."
