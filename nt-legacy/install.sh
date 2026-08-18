#!/usr/bin/env bash
# Installiert NT Legacy.
#
#   ./install.sh                    # nur installieren
#   ./install.sh --anwenden         # danach die Grundfassung anwenden
#   ./install.sh --anwenden win2k   # danach diese Variante anwenden
#
# Fasst ausschliesslich $HOME an, fragt nie nach sudo, und sichert vorher
# die Konfiguration. Damit ist die Installation in jedem Fall umkehrbar -
# das ist der Unterschied zwischen einem Theme, das man ausprobieren
# kann, und einem, bei dem man vorher ueberlegt.

set -euo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATEN="${XDG_DATA_HOME:-$HOME/.local/share}"

LNF_ID="com.github.huppiflupp.nt-legacy"
STYLE_ID="nt-legacy"

# ── Anwenden: Vorgabe ist weiterhin "nur installieren" ───────────────────
#
# Aus der Community (cubanismo, KDE 6.6.5): nach install.sh war das Design
# nicht aktiv, und die Schlussmeldung riet zu
# "plasma-apply-lookandfeel --apply …". Dieser Weg ist unvollstaendig -
# der Anwendungsstil bleibt dabei auf Breeze stehen, weil Qt-Programme
# den Wert aus ~/.config/kdedefaults nicht lesen (Begruendung in
# apply.sh). Wer ihm folgt, landet in den Systemeinstellungen und macht
# den Rest von Hand.
#
# Deshalb zwei Aenderungen: die Schlussmeldung nennt jetzt ./apply.sh,
# und mit --anwenden erledigt install.sh den zweiten Schritt gleich mit.
ANWENDEN=false
VARIANTE=""
for arg in "$@"; do
    case "$arg" in
        --anwenden) ANWENDEN=true ;;
        -*)         echo "Unbekannte Option '$arg'." >&2; exit 1 ;;
        *)          VARIANTE="$arg" ;;
    esac
done

# ── Sicherung ────────────────────────────────────────────────────────────
BACKUP="$DATEN/nt-legacy/backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
# kcminputrc gehoert dazu - sonst bleibt der Mauszeiger nach dem
# Zuruecksetzen auf NT Legacy stehen.
for f in plasma-org.kde.plasma.desktop-appletsrc plasmarc kdeglobals \
         kwinrc ksplashrc kcminputrc; do
    if [ -f "$HOME/.config/$f" ]; then
        cp -a "$HOME/.config/$f" "$BACKUP/"
    else
        # Datei gibt es noch nicht - der haeufige Fall auf einem frischen
        # Konto. Ohne Vermerk wuesste restore.sh nicht, dass sie hinterher
        # wieder verschwinden muss, und unsere Werte blieben darin stehen.
        echo "$f" >> "$BACKUP/.war-nicht-vorhanden"
    fi
done
cat > "$BACKUP/restore.sh" <<'EOF'
#!/usr/bin/env bash
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in "$HERE"/*; do
    n="$(basename "$f")"
    case "$n" in restore.sh|README|.war-nicht-vorhanden) continue ;; esac
    cp -a "$f" "$HOME/.config/$n"; echo "  $n"
done

# Dateien, die es vor der Installation nicht gab, muessen wieder weg -
# sonst bleiben unsere Werte darin stehen. Genau so ueberlebten frueher
# Plasma-Stil und Mauszeiger ein restore.sh.
if [ -f "$HERE/.war-nicht-vorhanden" ]; then
    while read -r n; do
        [ -n "$n" ] && [ -f "$HOME/.config/$n" ] && {
            rm -f "$HOME/.config/$n"
            echo "  $n entfernt (gab es vorher nicht)"
        }
    done < "$HERE/.war-nicht-vorhanden"
fi

# Fensterdekoration ausdruecklich zuruecksetzen. Zeigt kwinrc auf ein
# geloeschtes Aurorae-Thema, zeichnet KWin GAR KEINE Titelleiste - kein
# Fallback, kein Schliessknopf. In der Test-VM belegt.
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 \
    --key library org.kde.breeze 2>/dev/null || true
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 \
    --key theme Breeze 2>/dev/null || true

rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements" \
      "$HOME/.cache/icon-cache.kcache"
echo ""
echo "Wiederhergestellt. Ab- und wieder anmelden."
EOF
chmod +x "$BACKUP/restore.sh"
echo "Sicherung: $BACKUP"

# ── Installation ─────────────────────────────────────────────────────────
# kpackagetool6 aufrufen und dabei ein bekanntes Rauschen aussieben.
#
# Aus der Community (cubanismo, Arch mit Plasma 6.6.5): je installiertem
# Plasma-Stil eine Zeile
#
#   qt.dbus.integration: QDBusConnection: error: could not send signal to
#   service "" path "/KPackage/" interface "org.kde.plasma.kpackage"
#   member "packageInstalled": Invalid object path: /KPackage/
#
# Das ist KEIN Fehler dieses Themes und auch keiner der Installation: die
# Pakete landen korrekt. KPackage meldet die geglueckte Installation per
# D-Bus und baut den Objektpfad aus einem Praefix, das bei Plasma/Theme
# leer ist - "/KPackage/" ist als Pfad ungueltig, Qt sagt das laut.
#
# Nachgestellt: Auf Fedora mit KF6 6.28 bleibt stderr leer, mit den
# aelteren Bibliotheken von Plasma 6.6.5 kommen zehn dieser Zeilen. Der
# Melder hielt sie fuer den Grund, warum das Design nicht griff, und hat
# von Hand nachgearbeitet - genau davor schuetzt dieser Filter.
#
# Bewusst kein pauschales 2>/dev/null: echte Fehler von kpackagetool6
# muessen sichtbar bleiben.
kpaket() {
    local fehler rc=0
    fehler="$(mktemp)"
    kpackagetool6 "$@" >/dev/null 2>"$fehler" || rc=$?
    grep -v "^qt\.dbus\.integration:" "$fehler" >&2 || true
    rm -f "$fehler"
    return $rc
}

# kpackagetool6 statt cp -r: es prueft die Metadaten, legt unter der
# richtigen Id ab und kann sauber wieder deinstallieren.
installiere() {
    local typ="$1" pfad="$2" ziel="$3"
    # Erst -u (Upgrade), dann -r + -i. Das Upgrade scheitert, wenn das
    # Verzeichnis zwar da, das Paket aber nicht registriert ist - dann
    # scheitert auch -i mit "existiert bereits". Ohne diesen Weg schlaegt
    # jede zweite Installation fehl.
    if kpaket -t "$typ" -u "$pfad" 2>/dev/null; then
        return 0
    fi
    kpaket -t "$typ" -r "$(basename "$pfad")" 2>/dev/null || true
    rm -rf "$ziel"
    kpaket -t "$typ" -i "$pfad"
}

echo "Plasma Styles …"
for d in "$HIER"/desktoptheme/*/; do
    n="$(basename "$d")"
    installiere Plasma/Theme "${d%/}" "$DATEN/plasma/desktoptheme/$n"
    echo "  $n"
done

echo "Farbschema …"
install -Dm644 "$HIER/color-schemes/"*.colors -t "$DATEN/color-schemes/"

if [ -d "$HIER/icons" ]; then
    echo "Symbole (Chicago95, optional) …"
    mkdir -p "$DATEN/icons"
    rm -rf "$DATEN/icons/NTLegacy"
    cp -a "$HIER/icons/"* "$DATEN/icons/"
    # Ohne aktualisierten Cache zeigt Plasma teils noch die alten Symbole
    command -v gtk-update-icon-cache >/dev/null && \
        gtk-update-icon-cache -q -t -f "$DATEN/icons/NTLegacy" 2>/dev/null || true
fi

# Das mitgelieferte Symbolset. Anders als Chicago95 liegt es im Repo,
# weil seine Herkunft geklaert ist: vollstaendig selbst gezeichnet in
# tools/gen-icons.py, kein uebernommenes Fremdmaterial (ATTRIBUTION.md).
# Es ist die Vorgabe; Chicago95 bleibt daneben waehlbar, wenn es ueber
# fetch-icons.sh geholt wurde.
if [ -d "$HIER/icons-nt" ]; then
    echo "Symbole (NTLegacyIcons) …"
    # Die Nachtfassung steht nicht im Repo - sie ist eine Ableitung und
    # entsteht sonst in build.py. Wer direkt aus einem Klon installiert,
    # hat sie noch nicht; ohne sie zeigen die Nachtvarianten auf ein
    # Symbolthema, das es auf dem Rechner nicht gibt.
    #
    # tools/ liegt im Arbeitsbaum neben nt-legacy/, im Archiv darin.
    if [ ! -d "$HIER/icons-nt/NTLegacyIconsNacht" ]; then
        for w in "$HIER/tools/mach-nacht-symbole.py" \
                 "$HIER/../tools/mach-nacht-symbole.py"; do
            [ -f "$w" ] || continue
            python3 "$w" "$HIER/icons-nt/NTLegacyIcons" >/dev/null 2>&1 || true
            break
        done
    fi
    mkdir -p "$DATEN/icons"
    # Erst das alte Verzeichnis weg, dann kopieren.
    #
    # Ein blosses "cp -r" darueber folgt den Verweisen der vorherigen
    # Installation: Fast die Haelfte des Satzes besteht aus Symlinks, und
    # cp schreibt DURCH sie hindurch in die Zieldatei. So hat ein neues
    # start-here.png das Zahnrad von applications-system ueberschrieben -
    # danach zeigten Starter und Systemeinstellungen wieder dasselbe
    # Symbol, nur diesmal beide das falsche.
    rm -rf "$DATEN/icons/NTLegacyIcons" "$DATEN/icons/NTLegacyIconsNacht"
    cp -a "$HIER/icons-nt/"* "$DATEN/icons/"

    # Das bisherige Symbolthema als Rueckfall eintragen.
    #
    # Aus der Rueckmeldung: Auf EndeavourOS zeigte der Systemaktualisierer
    # nach dem Wechsel ein weisses Blatt. Sein Symbol heisst
    # "endeavouros-icon" und liegt ausschliesslich in Qogir, dem
    # Symbolthema der Distribution - unser Satz erbt von breeze und
    # hicolor, Qogir ist nicht darunter, also findet Plasma nichts.
    #
    # Das trifft jedes distributionseigene Symbol und passiert beim
    # Wechsel auf Breeze genauso. Wir koennen es hier aber abfangen: das
    # zuvor aktive Thema kommt VOR breeze in die Inherits-Zeile. Dann
    # behalten solche Symbole ihr Bild, und alles andere kommt weiter von
    # uns - die Reihenfolge entscheidet, und wir stehen an erster Stelle.
    #
    # Der Preis ist ehrlich zu nennen: an genau diesen Stellen mischen
    # sich zwei Bildsprachen. Ein weisses Blatt ist die schlechtere Wahl.
    vorheriges_symbolthema() {
        local kandidat quelle d
        # Erst der laufende Zustand, dann die eben angelegte Sicherung
        # (dort steht, was vor dieser Installation galt), zuletzt die
        # Vorgaben des Globalen Designs.
        for quelle in "$HOME/.config/kdeglobals" "$BACKUP/kdeglobals" \
                      "$HOME/.config/kdedefaults/kdeglobals"; do
            [ -f "$quelle" ] || continue
            kandidat="$(sed -n '/^\[Icons\]/,/^\[/{s/^Theme=//p}' "$quelle" | head -1)"
            case "$kandidat" in
                ""|NTLegacy|NTLegacyIcons|NTLegacyIconsNacht|hicolor) continue ;;
            esac
            for d in "$DATEN/icons/$kandidat" "/usr/share/icons/$kandidat"; do
                [ -d "$d" ] && { echo "$kandidat"; return 0; }
            done
        done
        return 1
    }

    if FREMD="$(vorheriges_symbolthema)"; then
        for satz in NTLegacyIcons NTLegacyIconsNacht; do
            idx="$DATEN/icons/$satz/index.theme"
            [ -f "$idx" ] || continue
            # Nur die erste Inherits-Zeile, und nur wenn das Thema nicht
            # ohnehin schon darin steht.
            grep -q "^Inherits=.*\b$FREMD\b" "$idx" && continue
            sed -i "0,/^Inherits=/s//Inherits=$FREMD,/" "$idx"
        done
        echo "  Rueckfall auf '$FREMD' eingetragen (fuer Symbole der Distribution)"
    fi

    for satz in NTLegacyIcons NTLegacyIconsNacht; do
        [ -d "$DATEN/icons/$satz" ] || continue
        command -v gtk-update-icon-cache >/dev/null && \
            gtk-update-icon-cache -q -t -f "$DATEN/icons/$satz" 2>/dev/null || true
    done
fi

if [ -d "$HIER/cursors" ]; then
    echo "Mauszeiger …"
    mkdir -p "$DATEN/icons"
    # Auch hier erst raeumen: Ein Zeigerthema besteht zur Haelfte aus
    # Verweisen (left_ptr -> default und so weiter), und cp -r schriebe
    # durch sie hindurch. Siehe die Begruendung bei den Symbolen oben.
    rm -rf "$DATEN"/icons/NTLegacy_cursors "$DATEN"/icons/NTLegacyRot_cursors
    cp -a "$HIER/cursors/"* "$DATEN/icons/"
fi

if [ -d "$HIER/konsole" ]; then
    # Nur ablegen, nicht aktivieren. Konsole zeigt Profil und Schemata
    # danach zur Auswahl an; umgestellt wird erst durch anmutung.sh -
    # Konsole ist ein fremdes Programm, und wer ein Design ausprobiert,
    # rechnet nicht damit, dass hinterher sein Terminal anders aussieht.
    echo "Konsole-Profil und -Farbschemata (nur ablegen) …"
    mkdir -p "$DATEN/konsole"
    cp -r "$HIER/konsole/"* "$DATEN/konsole/"
fi

if [ -d "$HIER/wallpapers" ]; then
    echo "Hintergrundbilder …"
    mkdir -p "$DATEN/wallpapers"
    # Erst die eigenen Pakete wegraeumen, dann kopieren.
    #
    # cp -r legt nur darueber. Bis 0.2.5 lag in jedem Paket eine
    # 3840x2160.png samt SVG, seit 0.2.6 eine 3840x2160.jpg - nach einer
    # Aktualisierung lagen alle drei nebeneinander. Plasma sucht nach
    # Aufloesung, findet drei Kandidaten fuer dieselbe und nimmt einen
    # davon; welchen, haengt an der Reihenfolge im Verzeichnis. Auf
    # einem Testrechner war es die alte Verlaufsflaeche - das neue Bild
    # war installiert und blieb unsichtbar.
    #
    # Nur ntlegacy*: was der Nutzer sonst unter wallpapers/ liegen hat,
    # geht uns nichts an.
    rm -rf "$DATEN"/wallpapers/ntlegacy*
    cp -r "$HIER/wallpapers/"* "$DATEN/wallpapers/"
fi

if [ -d "$HIER/aurorae" ]; then
    echo "Fensterdekoration …"
    mkdir -p "$DATEN/aurorae/themes"
    cp -r "$HIER/aurorae/"* "$DATEN/aurorae/themes/"
fi

echo "Globale Designs …"
for d in "$HIER"/look-and-feel/*/; do
    n="$(basename "$d")"
    installiere Plasma/LookAndFeel "${d%/}" "$DATEN/plasma/look-and-feel/$n"
    echo "  $n"
done

# Das Icon-Theme muss hart gesetzt werden. Plasma zieht die uebrigen
# Vorgaben aus contents/defaults zur Laufzeit (Plasma Style, Farbschema,
# Anwendungsstil greifen so), beim Icon-Theme aber nicht - gemessen: mit
# Fallback blieben Breeze-Icons stehen, erst kwriteconfig6 brachte die
# Symbolset. Die alten Werte liegen in der Sicherung oben.
#
# Wer schon eine Nachtfassung faehrt, behaelt ihren Satz. Sonst wuerfe ein
# blosses Update ihn auf den hellen zurueck - und im Panel staende danach
# wieder Dunkelgrau auf Dunkelgrau, ohne dass jemand etwas geaendert haette.
AKTUELL=$(kreadconfig6 --file kdeglobals --group Icons --key Theme 2>/dev/null)
case "$AKTUELL" in
    NTLegacyIconsNacht) SATZ=NTLegacyIconsNacht ;;
    *)                  SATZ=NTLegacyIcons ;;
esac
kwriteconfig6 --file kdeglobals --group Icons --key Theme "$SATZ"

# Der Render-Cache traegt die Themeversion im Namen. Ohne Loeschen sieht
# man nach einem Update das alte Theme und sucht den Fehler woanders.
#
# icon-cache.kcache gehoert dazu und fehlte hier bis 0.2.12 - waehrend
# das eigene Pruefskript ihn seit jeher nennt. Er merkt sich, welches
# Symbol unter welchem Namen gefunden wurde; nach einem Themenwechsel
# steht darin, dass es NICHT gefunden wurde, und die Anwendung zeigt
# weiter ein weisses Blatt. Genau so aus der Community gemeldet
# (EndeavourOS, Systemaktualisierer).
rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements" \
      "$HOME/.cache/icon-cache.kcache"

echo ""
echo "Installiert."

# ── Anwenden ─────────────────────────────────────────────────────────────
if $ANWENDEN; then
    echo ""
    exec "$HIER/apply.sh" ${VARIANTE:+"$VARIANTE"}
fi

cat <<EOF

  Anwenden:     ./apply.sh              # Grundfassung (Petrol)
                ./apply.sh win2k        # eine der Varianten
                ./apply.sh --help       # alle Varianten und Schalter

                Oder gleich beides:  ./install.sh --anwenden win2k

  Nimm dafuer apply.sh und nicht plasma-apply-lookandfeel: der
  Anwendungsstil (Windows statt Breeze) laesst sich nur ueber
  ~/.config/kdeglobals setzen, und genau das macht apply.sh. Ueber
  Systemeinstellungen > Farben & Design > Globales Design fehlt er.

Das Design wirkt erst nach einem Ab- und Wiederanmelden vollstaendig.

  Rueckweg:     $BACKUP/restore.sh
EOF
