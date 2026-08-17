#!/usr/bin/env bash
# Stellt Programmeinstellungen auf die NT-Anmutung um - ausdruecklich
# getrennt vom Theme.
#
#   ./anmutung.sh            # anwenden
#   ./anmutung.sh --zurueck  # auf die vorherigen Werte zuruecksetzen
#   ./anmutung.sh --zeigen   # nur anzeigen, was gesetzt wuerde
#
# Warum das nicht in apply.sh steht:
#
# Ein Plasma-Theme darf Aussehen setzen - Farben, Rahmen, Dekoration. Es
# darf nicht die Einstellungen fremder Programme ueberschreiben. Wer ein
# Design ausprobiert, rechnet nicht damit, dass hinterher seine
# Dolphin-Konfiguration eine andere ist. Genau solche stillen
# Nebenwirkungen sind der Grund, warum ein Theme ein System unbrauchbar
# machen kann.
#
# Deshalb: eigenes Skript, ausdruecklicher Aufruf, vollstaendiger Rueckweg.

set -euo pipefail

DATEN="${XDG_DATA_HOME:-$HOME/.local/share}"
SICHERUNG="$DATEN/nt-legacy/anmutung-vorher.conf"

# Datei : Gruppe : Schluessel : NT-Wert : Begruendung
#
# Bewusst kurz gehalten. Jeder Eintrag hier ist ein Eingriff in ein
# fremdes Programm und muss sich rechtfertigen lassen.
EINSTELLUNGEN=(
  "dolphinrc:General:ShowStatusBar:FullWidth:durchgehende Statusleiste statt schwebendem Kaestchen"
  # PCManFM-Qt als Dateimanager. Gruende, gemessen in der Test-VM:
  #   - Qt6, also greift der Widget-Stil vollstaendig
  #   - echte Menueleiste statt Hamburger-Knopf
  #   - freier Speicherplatz als Text ueber die volle Breite; Dolphin
  #     zeichnet dort eine KCapacityBar, die sich selbst zeichnet und
  #     weder Palette noch Widget-Stil folgt (silberne Kapsel)
  "mimeapps.list:Default Applications:inode/directory:pcmanfm-qt.desktop:PCManFM-Qt als Dateimanager"
  # Ohne diesen Eintrag findet pcmanfm-qt das Icon-Thema nicht und faellt
  # auf oxygen zurueck - mitten im NT-Theme.
  "pcmanfm-qt/default/settings.conf:System:FallbackIconThemeName:NTLegacy:Icon-Thema fuer PCManFM-Qt"
  # Konsole auf das mitgelieferte Profil: Liberation Mono und ein
  # Farbschema aus den Farben der jeweiligen Fassung. install.sh legt
  # beides nur ab, aktiviert wird es erst hier. Das eigene Profil des
  # Nutzers bleibt bestehen und ist im Menue weiter waehlbar.
  "konsolerc:Desktop Entry:DefaultProfile:NT Legacy.profile:Konsole nutzt das NT-Profil"
)

zeigen() {
    printf '%-12s %-10s %-16s %s\n' "Datei" "Gruppe" "Schluessel" "Wert"
    for e in "${EINSTELLUNGEN[@]}"; do
        IFS=: read -r datei gruppe schluessel wert grund <<< "$e"
        printf '%-12s %-10s %-16s %s\n' "$datei" "$gruppe" "$schluessel" "$wert"
        printf '%-40s %s\n' "" "$grund"
    done
}

zurueck() {
    if [ ! -f "$SICHERUNG" ]; then
        echo "Keine Sicherung unter $SICHERUNG - nichts zurueckzusetzen." >&2
        exit 1
    fi
    while IFS=: read -r datei gruppe schluessel wert; do
        [ -z "${datei:-}" ] && continue
        if [ -z "$wert" ]; then
            # Der Schluessel war vorher gar nicht gesetzt. Loeschen, nicht
            # auf einen erratenen Vorgabewert setzen - sonst steht dort
            # hinterher etwas, das der Nutzer nie gewaehlt hat.
            kwriteconfig6 --file "$datei" --group "$gruppe" --key "$schluessel" --delete
            echo "  $datei/$gruppe/$schluessel  entfernt (war nicht gesetzt)"
        else
            kwriteconfig6 --file "$datei" --group "$gruppe" --key "$schluessel" "$wert"
            echo "  $datei/$gruppe/$schluessel  -> $wert"
        fi
    done < "$SICHERUNG"
    rm -f "$SICHERUNG"
    echo
    echo "Zurueckgesetzt. Offene Programme einmal neu starten."
}

case "${1:-}" in
    --zeigen)  zeigen; exit 0 ;;
    --zurueck) zurueck; exit 0 ;;
    "")        ;;
    *)         echo "Unbekannte Option '$1'. Moeglich: --zeigen, --zurueck" >&2; exit 1 ;;
esac

# --- Anwenden ------------------------------------------------------------

if [ -f "$SICHERUNG" ]; then
    echo "Hinweis: Es gibt bereits eine Sicherung - die alten Werte bleiben"
    echo "         erhalten, damit --zurueck weiterhin den Urzustand trifft."
else
    mkdir -p "$(dirname "$SICHERUNG")"
    : > "$SICHERUNG"
    for e in "${EINSTELLUNGEN[@]}"; do
        IFS=: read -r datei gruppe schluessel _wert _grund <<< "$e"
        # Leerer Wert heisst: war nicht gesetzt. Den Unterschied zwischen
        # "nicht gesetzt" und "auf den Vorgabewert gesetzt" muss die
        # Sicherung festhalten, sonst ist der Rueckweg ungenau.
        alt=$(kreadconfig6 --file "$datei" --group "$gruppe" --key "$schluessel" 2>/dev/null || true)
        echo "$datei:$gruppe:$schluessel:$alt" >> "$SICHERUNG"
    done
fi

for e in "${EINSTELLUNGEN[@]}"; do
    IFS=: read -r datei gruppe schluessel wert grund <<< "$e"
    kwriteconfig6 --file "$datei" --group "$gruppe" --key "$schluessel" "$wert"
    echo "  $datei: $schluessel = $wert"
    echo "      $grund"
done

cat <<EOF

Angewendet. Betroffene Programme einmal neu starten.

  Zurueck:  ./anmutung.sh --zurueck
  Gesichert: $SICHERUNG
EOF
