#!/usr/bin/env bash
# Wendet eine NT-Legacy-Variante an.
#
#   ./apply.sh              # Grundfassung (Petrol)
#   ./apply.sh lilac        # Flieder
#   ./apply.sh desert       # Wueste
#   ./apply.sh teal-nacht   # Nachtfassung (auch lilac-nacht, desert-nacht)
#   ./apply.sh teal --rot   # mit rotem Mauszeiger
#   ./apply.sh teal --panel # dazu das NT-Panel (ersetzt das vorhandene)
#
# Warum es dieses Skript gibt:
#
# Hier stand lange, Plasma ziehe die Vorgaben aus contents/defaults nicht
# zuverlaessig - "gemessen in der Test-VM, alle Schluessel blieben leer".
# Das war ein MESSFEHLER, nachgeprueft am 9.8.2026:
#
# Plasma stellt der Konfigurationskaskade beim Sitzungsstart
# ~/.config/kdedefaults voran (XDG_CONFIG_DIRS). Beim Anwenden eines
# Globalen Designs landen die Werte genau dort - als Vorgaben, nicht als
# Nutzerwerte (libklookandfeel/klookandfeelmanager.cpp, writeNewDefaults:
# Vorgabe schreiben, dann revertToDefault auf den Nutzerwert).
#
# Wer per SSH misst, hat dieses Verzeichnis NICHT in der Kaskade. Dann
# liefert kreadconfig6 leere Werte, obwohl alles korrekt gesetzt ist.
# Genau so ist die falsche Diagnose entstanden.
#
# Mit richtiger Kaskade gemessen setzt "plasma-apply-lookandfeel --apply"
# allein jede Ebene: ColorScheme, widgetStyle, plasmarc/Theme, Icons,
# Mauszeiger, Fensterdekoration, Startbildschirm - und die Farbwerte
# landen in kdeglobals.
#
# Zweite Folgerung daraus: Die kwriteconfig6-Aufrufe unten schreiben
# NICHTS, solange der Wert der Vorgabe entspricht - KConfig speichert
# keinen Eintrag, der dem kaskadierten Default gleicht. In der Test-VM
# nachgewiesen: nach 'kwriteconfig6 ... widgetStyle Windows' stand der
# Schluessel weiterhin nur in kdedefaults, nicht in kdeglobals.
#
# Sie bleiben trotzdem stehen, weil sie greifen, wenn die Vorgabe fehlt
# oder abweicht - etwa nach einer Installation ueber "Neue holen …",
# bei der es gar kein Globales Design gibt. Schaden koennen sie nicht:
# was gleich ist, wird nicht geschrieben.

set -euo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARIANTE="${1:-teal}"
ROT=false
SCHRIFT=false
PANEL=false
for arg in "$@"; do
    [[ "$arg" == "--rot" ]] && ROT=true
    [[ "$arg" == "--schrift" ]] && SCHRIFT=true
    [[ "$arg" == "--panel" ]] && PANEL=true
    if [[ "$arg" == "--help" || "$arg" == "-h" ]]; then
        # Die Liste kommt aus build.py, nicht aus einer zweiten hier -
        # aus demselben Grund wie unten bei den Kennungen.
        sed -n '3,9p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
        echo "Varianten:"
        (cd "$HIER" && python3 -c "
import importlib.util
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
for v in sorted(m.VARIANTEN):
    print('  %-14s %s' % (v, m.VARIANTEN[v]['beschreibung_en']))
")
        exit 0
    fi
done
[[ "$VARIANTE" == --* ]] && VARIANTE="teal"

# Die Kennungen kommen aus build.py, nicht aus einer zweiten Liste hier.
# Frueher standen sie doppelt - beim Hinzufuegen von win98/win2k wurde nur
# build.py gepflegt, und die neuen Varianten waren ueber apply.sh gar
# nicht erreichbar. Eine Wahrheit, kein Abgleich noetig.
#
# Mitgeliefert wird auch das Tag/Nacht-Gegenstueck derselben Farbwelt.
# Plasma hat seit 6 einen eingebauten Umschalter (kded-Modul
# lookandfeelautoswitcher), der nach Sonnenauf- und -untergang zwischen
# DefaultLightLookAndFeel und DefaultDarkLookAndFeel wechselt. Traegt man
# dort ein gemischtes Paar ein, springt der Rechner abends von einer
# Farbwelt in eine andere - auf dem Entwicklungsrechner stand so
# 'desert' als helle und 'teal-nacht' als dunkle Fassung.
KENNUNG=$(cd "$HIER" && python3 -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('b', 'build.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
v = sys.argv[1]
if v not in m.VARIANTEN:
    print('UNBEKANNT ' + ' '.join(sorted(m.VARIANTEN)))
else:
    i = m.ids(v)
    # Das Paar: Grundlage ist die Farbwelt ohne '-nacht'.
    basis = v[:-len('-nacht')] if v.endswith('-nacht') else v
    hell = m.ids(basis)['lnf'] if basis in m.VARIANTEN else ''
    dunkel = m.ids(basis + '-nacht')['lnf'] if basis + '-nacht' in m.VARIANTEN else ''
    # Das Konsole-Farbschema gibt es je Farbwelt, nicht je Fassung -
    # deshalb der Kurzname der hellen Fassung, auch fuer die Nacht.
    konsole = m.ids(basis)['schema'] if basis in m.VARIANTEN else ''
    print(i['schema'], i['style'], i['lnf'], hell or '-', dunkel or '-',
          konsole or '-', i['icons'])
" "$VARIANTE")

if [ "${KENNUNG%% *}" = "UNBEKANNT" ]; then
    echo "Unbekannte Variante '$VARIANTE'." >&2
    echo "Moeglich: ${KENNUNG#UNBEKANNT }" >&2
    exit 1
fi
read -r KURZ STYLE LNF LNF_HELL LNF_DUNKEL KONSOLE SYMBOLE <<< "$KENNUNG"

# Alle Kennungen muessen belegt sein. Faellt eine leer aus, schreibt das
# Skript sonst leere Werte in die Konfiguration und ruft die
# plasma-apply-Werkzeuge mit leerem Namen auf - das ergibt Meldungen wie
# "Could not find theme """, die niemand einem Theme zuordnen kann.
for feld in KURZ STYLE LNF KONSOLE SYMBOLE; do
    if [ -z "${!feld}" ]; then
        echo "FEHLER: Kennung '$feld' ist leer (Variante '$VARIANTE')." >&2
        echo "        Das ist ein Fehler im Theme, nicht auf deinem Rechner." >&2
        echo "        Bitte melden: $(sed -n 's/^WEBSITE = "\(.*\)"/\1/p' "$HIER/build.py" | head -1)" >&2
        exit 1
    fi
done

# Trockenlauf: nur pruefen, ob die Variante existiert, nichts anwenden.
# Wird von pruefe.sh genutzt.
for arg in "$@"; do [[ "$arg" == "--nur-pruefen" ]] && exit 0; done

# Die Zeiger gibt es nur einmal fuer alle Varianten - sie unterscheiden
# sich in weiss und rot, nicht nach Farbwelt. Frueher stand hier
# "${KURZ}_cursors", was fuer fuenf von sechs Varianten ins Leere lief.
ZEIGER="NTLegacy_cursors"
$ROT && ZEIGER="NTLegacyRot_cursors"

# Ist das Theme ueberhaupt installiert? Ohne diese Pruefung meldet das
# Skript Erfolg, schreibt alle Schluessel auf nicht vorhandene Themes und
# verweist auf eine Sicherung, die es nie gab.
DATEN="${XDG_DATA_HOME:-$HOME/.local/share}"
if [ ! -d "$DATEN/plasma/look-and-feel/$LNF" ]; then
    echo "FEHLER: '$LNF' ist nicht installiert." >&2
    echo "        Erst  ./install.sh  ausfuehren." >&2
    exit 1
fi
if [ ! -d "$DATEN/icons/$ZEIGER" ]; then
    echo "Hinweis: Mauszeiger '$ZEIGER' fehlt - der Systemzeiger bleibt." >&2
    ZEIGER=""
fi

if $ROT; then echo "Wende an: $KURZ (roter Zeiger)"; else echo "Wende an: $KURZ"; fi

# ── Panel sichern ────────────────────────────────────────────────────────
#
# Jedes Look-and-Feel-Paket bringt ein Panel-Layout mit
# (contents/layouts/org.kde.plasma.desktop-layout.js), das ALLE
# bestehenden Panels entfernt und das NT-Panel neu aufbaut.
#
# Angewendet wird es in zwei Faellen: mit --panel hier, und wenn jemand
# in den Systemeinstellungen beim Designwechsel das Arbeitsflaechen-Layout
# mit auswaehlt. Der zweite Fall ist der haeufigere, und er trifft den
# Nutzer ohne Vorwarnung - deshalb wird hier immer gesichert, auch ohne
# --panel. Eine Kopie kostet nichts, ein verlorenes Panel schon.
#
# install.sh sichert appletsrc nur einmal, vor der Installation. Das hilft
# beim zehnten Variantenwechsel nicht mehr.
APPLETSRC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
PANELKOPIE=""
if [ -f "$APPLETSRC" ]; then
    mkdir -p "$DATEN/nt-legacy/panel"
    PANELKOPIE="$DATEN/nt-legacy/panel/appletsrc-$(date +%Y%m%d-%H%M%S)"
    cp -a "$APPLETSRC" "$PANELKOPIE"
    # Nur die letzten zehn behalten. Ohne das waechst das Verzeichnis bei
    # jedem Wechsel um eine weitere Kopie - und wer Varianten vergleicht,
    # wechselt oft.
    ls -1t "$DATEN/nt-legacy/panel"/appletsrc-* 2>/dev/null \
        | tail -n +11 | xargs -r rm -f || true
fi

# Globales Design zuerst - es setzt den Rahmen, den Rest praezisieren wir.
#
# Ohne --resetLayout bleiben Panel und Hintergrundbild des Nutzers stehen.
# Das ist die Vorgabe, weil ein Theme das Panel nicht ungefragt abraeumen
# soll - aber es hat eine Nebenwirkung, die lange niemand bemerkt hat:
#
# Fedoras Standardpanel schwebt (floating). Ein schwebendes Panel zeichnet
# Plasma mit den abgerundeten Varianten aus translucent/, und NT Legacy
# sieht darin dunkel und fremd aus - nichts davon erinnert an NT. Erst
# mit dem eigenen Layout (Panel am Rand, 30 Pixel, nicht schwebend) sieht
# es aus wie auf den Bildschirmfotos.
#
# In der Test-VM auf 'clean' nachgewiesen: derselbe Plasma-Stil, einmal
# ohne und einmal mit --resetLayout - erst mit Layout stimmt das Bild.
#
# Die Ausgabe wird aufgehoben und nur bei einem Fehlschlag gezeigt.
#
# Vorher stand hier ">/dev/null 2>&1 || true": jede Meldung fiel weg,
# auch "Unable to find the theme named …". Aus der Community kam genau so
# ein Fall zurueck - Fehler beim Anwenden, Design nicht aktiv, und
# niemand konnte hinterher sagen, welche Meldung es war. Umgekehrt soll
# ein geglueckter Lauf still bleiben: plasma-apply-lookandfeel schreibt
# auch dann Zeilen, die niemand braucht (etwa xrdb-Warnungen unter
# Wayland).
LNF_LOG="$(mktemp)"
trap 'rm -f "$LNF_LOG"' EXIT
if $PANEL; then
    echo "  Panel wird durch das NT-Layout ersetzt (Sicherung siehe unten)."
    plasma-apply-lookandfeel --apply "$LNF" --resetLayout >"$LNF_LOG" 2>&1 || true
else
    plasma-apply-lookandfeel --apply "$LNF" >"$LNF_LOG" 2>&1 || true
fi
if grep -qi "unable to find\|could not find\|error" "$LNF_LOG"; then
    echo "  Warnung: plasma-apply-lookandfeel meldet:" >&2
    sed 's/^/    /' "$LNF_LOG" >&2
    echo "  Die Ebenen werden trotzdem einzeln gesetzt." >&2
fi

kwriteconfig6 --file plasmarc   --group Theme   --key name          "$STYLE"
kwriteconfig6 --file kdeglobals --group General --key ColorScheme   "$KURZ"
kwriteconfig6 --file kdeglobals --group KDE     --key widgetStyle   Windows

# Der Anwendungsstil braucht eine Sonderbehandlung.
#
# Als Vorgabe in ~/.config/kdedefaults/kdeglobals wird er von
# Qt-Anwendungen NICHT gelesen - in der Test-VM belegt: nach dem Anmelden
# stand dort 'Windows', und trotzdem startete jede Anwendung mit Breeze.
# Erst ein Eintrag in der Nutzerdatei wirkt.
#
# Genau den kann kwriteconfig6 aber nicht schreiben: KConfig speichert
# keinen Wert, der dem kaskadierten Vorgabewert gleicht - die Zeile
# darueber ist also wirkungslos, sobald ein Globales Design dasselbe
# vorgibt. Deshalb hier ausdruecklich an KConfig vorbei.
python3 - <<'PY' || true
import re, pathlib
p = pathlib.Path.home() / ".config" / "kdeglobals"
if p.exists():
    t = p.read_text()
    if re.search(r"^widgetStyle=", t, re.M):
        t = re.sub(r"^widgetStyle=.*$", "widgetStyle=Windows", t, flags=re.M)
    elif re.search(r"^\[KDE\]$", t, re.M):
        t = re.sub(r"^\[KDE\]$", "[KDE]\nwidgetStyle=Windows", t, count=1, flags=re.M)
    else:
        t = t.rstrip("\n") + "\n\n[KDE]\nwidgetStyle=Windows\n"
    p.write_text(t)
PY
# Der Symbolsatz haengt an der Fassung, nicht an der Farbwelt: die
# Nachtvarianten bekommen NTLegacyIconsNacht. Dieselben Bilder, aber
# breeze-dark als Rueckfall - sonst zeichnet Breeze die Symbole, die wir
# nicht selbst liefern, in Dunkelgrau auf das dunkle Panel.
kwriteconfig6 --file kdeglobals --group Icons   --key Theme         "$SYMBOLE"
kwriteconfig6 --file kdeglobals --group KDE     --key LookAndFeelPackage "$LNF"

# Konsole: das Farbschema der Farbwelt im mitgelieferten Profil
# nachziehen. Das ist KEIN Eingriff in fremde Konfiguration - die Datei
# gehoert zum Theme. Ob Konsole sie ueberhaupt benutzt, entscheidet
# allein konsolerc, und das setzt nur anmutung.sh.
PROFIL="$DATEN/konsole/NT Legacy.profile"
if [ "$KONSOLE" != "-" ] && [ -f "$PROFIL" ]; then
    kwriteconfig6 --file "$PROFIL" --group Appearance --key ColorScheme "$KONSOLE"
fi

# Das Tag/Nacht-Paar derselben Farbwelt hinterlegen. Wer den
# automatischen Wechsel in den Systemeinstellungen einschaltet, bleibt
# damit in der gewaehlten Farbwelt und wechselt nur zwischen hell und
# dunkel. Der Umschalter selbst wird NICHT eingeschaltet - das ist die
# Entscheidung des Nutzers, nicht die des Designs.
if [ "$LNF_HELL" != "-" ] && [ "$LNF_DUNKEL" != "-" ]; then
    kwriteconfig6 --file kdeglobals --group KDE --key DefaultLightLookAndFeel "$LNF_HELL"
    kwriteconfig6 --file kdeglobals --group KDE --key DefaultDarkLookAndFeel  "$LNF_DUNKEL"
fi
[ -n "$ZEIGER" ] && kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "$ZEIGER"
# Den eigenen Startbildschirm aktivieren. Weder plasma-apply-lookandfeel
# noch die defaults setzen ihn - ohne diese Zeile laeuft Splash.qml nie.
kwriteconfig6 --file ksplashrc  --group KSplash --key Theme  "$LNF"
kwriteconfig6 --file ksplashrc  --group KSplash --key Engine KSplashQML
# Bewusst die v1-Bibliothek, nicht org.kde.kwin.aurorae.v2:
#
# Das Plugin v2 gibt es erst ab Plasma 6.6. Auf 6.0 bis 6.5 schlaegt das
# Laden fehl und KWin faellt still auf Breeze zurueck - der Nutzer sieht
# Breeze-Fensterrahmen und keine Fehlermeldung.
#
# Umgekehrt kostet v1 auf neuen Systemen nichts: KWin schreibt die Zeile
# beim Sitzungsstart selbst auf .v2 hoch (migrateAuroraeTheme in
# decorations/decorationbridge.cpp). In der Test-VM mit Plasma 6.7
# nachgeprueft - nach einem Neustart stand dort .v2.
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme "__aurorae__svg__$KURZ"

# Die Titelschrift wird hier bewusst NICHT geschrieben.
#
# Sie steht als Vorgabe in contents/defaults - dort wirkt sie einmal beim
# Anwenden des Globalen Designs, und danach behaelt der Nutzer seine
# Wahl in Systemeinstellungen > Schriftarten > Fensterueberschrift.
# Wuerde apply.sh sie bei jedem Aufruf setzen, waere diese Einstellung
# wirkungslos. Breeze setzt aus demselben Grund gar keine Schrift.
#
# Wer die fette NT-Titelschrift ausdruecklich will:
#   ./apply.sh <variante> --schrift

if $SCHRIFT; then
    # Das fuenfte Feld einer Qt-Schriftangabe ist das Gewicht: 50 normal,
    # 75 fett. Aurorae kennt dafuer keine eigene Option.
    kwriteconfig6 --file kdeglobals --group WM --key activeFont \
        "Noto Sans,10,-1,5,75,0,0,0,0,0"
    echo "  Titelschrift auf fett gesetzt."
fi

# Der Render-Cache traegt Themename und -version. Ohne Loeschen sieht man
# nach einem Update das alte Bild und sucht den Fehler an der falschen Stelle.
rm -f "$HOME/.cache/plasma_theme_"*.kcache "$HOME/.cache/ksvg-elements" \
      "$HOME/.cache/icon-cache.kcache"

# --- Uebernehmen, ohne die Shell abzuschiessen ---------------------------
#
# Frueher stand hier ein bedingungsloses
#   systemctl --user restart plasma-plasmashell.service
# Das ist die gefaehrlichste Zeile, die dieses Skript je hatte:
# plasma-plasmashell.service erlaubt drei Starts in 60 Sekunden
# (StartLimitBurst=3, StartLimitIntervalSec=60s), und der Sitzungsstart
# zaehlt als erster. Beim DRITTEN apply.sh innerhalb einer Minute gibt
# systemd auf - kein Panel, kein Desktop, kein Anwendungsstarter. Und es
# erholt sich nicht von selbst; in der Test-VM war der Bildschirm auch
# nach 100 Sekunden noch schwarz.
#
# Genau so klickt aber, wer Designs ausprobiert: drei Varianten
# hintereinander.
#
# Deshalb jetzt drei Stufen:
#   1. plasma-apply-* schalten zur Laufzeit um - so macht es auch die
#      Systemsteuerung, ganz ohne Neustart.
#   2. KWin bekommt ein reconfigure statt eines Neustarts.
#   3. Nur wenn plasmashell danach wirklich nicht laeuft, wird gestartet -
#      mit vorherigem reset-failed, damit der Zaehler nicht im Weg steht.

# Auch hier: still bei Erfolg, sichtbar bei Fehlschlag. "Could not find
# theme" mit leerem Namen war die Meldung, die aus der Community gemeldet
# wurde, ohne dass sich hinterher sagen liess, woher sie kam.
zur_laufzeit() {
    local werkzeug="$1" name="$2"
    if [ -z "$name" ]; then
        echo "  Warnung: leerer Name fuer $werkzeug - uebersprungen." >&2
        return
    fi
    # Der Ausgang allein reicht nicht: plasma-apply-desktoptheme meldet
    # "Could not find theme" und beendet sich trotzdem mit 0.
    if "$werkzeug" "$name" >"$LNF_LOG" 2>&1 \
       && ! grep -qi "could not find\|unable to find" "$LNF_LOG"; then
        return
    fi
    echo "  Warnung: $werkzeug '$name' fehlgeschlagen:" >&2
    sed 's/^/    /' "$LNF_LOG" >&2
}
zur_laufzeit plasma-apply-desktoptheme "$STYLE"
zur_laufzeit plasma-apply-colorscheme  "$KURZ"

# KWin die Dekoration neu einlesen lassen. Das Aurorae-THEMA selbst laedt
# KWin allerdings nur beim Sitzungsstart - deshalb der Hinweis unten.
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 \
    || qdbus org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true

if command -v systemctl >/dev/null; then
    if ! systemctl --user is-active --quiet plasma-plasmashell.service; then
        echo "  plasmashell laeuft nicht - starte neu."
        # Ohne reset-failed greift die Startbegrenzung und der Start
        # wird verweigert.
        systemctl --user reset-failed plasma-plasmashell.service 2>/dev/null || true
        systemctl --user start plasma-plasmashell.service 2>/dev/null || true
    fi
fi

# ── Panelbreite nachziehen ───────────────────────────────────────────────
#
# Das Layout-Skript im Design setzt die Laenge des Panels, und Plasma
# ueberschreibt sie beim Anwenden wieder mit der Breite der Symbole:
# gemessen 456 statt 1024 Pixel (EndeavourOS) und 388 statt 1280
# (Fedora). Auf dem Bildschirm sieht das nicht nach "Panel etwas kurz"
# aus, sondern nach "Panel fehlt" - ein Stummel in der linken Ecke.
#
# Deshalb hier noch einmal ueber die Skriptkonsole - und zwar in einer
# Schleife mit Nachkontrolle. Ein einzelner Versuch reicht nicht: Plasma
# baut das Layout asynchron auf und schrumpft das Panel unter Umstaenden
# NACH unserem Aufruf wieder. Wie lange das dauert, ist von System zu
# System verschieden - drei Sekunden genuegten auf EndeavourOS und auf
# Fedora nicht.
#
# Nur mit --panel: an einem selbstgebauten Panel des Nutzers hat dieses
# Skript nichts zu drehen.
if $PANEL; then
    PANEL_JS='var ps = panels();
var alles_gut = true;
for (var i = 0; i < ps.length; i++) {
    var nr = ps[i].screen; if (nr === undefined || nr < 0) { nr = 0; }
    var g = screenGeometry(nr);
    var b = (g && g.width > 0) ? g.width : 99999;
    ps[i].length = b; ps[i].maximumLength = b; ps[i].minimumLength = b;
    if (ps[i].length != b) { alles_gut = false; }
}
print(alles_gut ? "PANEL-OK" : "PANEL-KURZ");'

    plasma_skript() {
        if command -v qdbus6 >/dev/null; then
            qdbus6 org.kde.plasmashell /PlasmaShell evaluateScript "$1" 2>/dev/null
        elif command -v qdbus >/dev/null; then
            qdbus org.kde.plasmashell /PlasmaShell evaluateScript "$1" 2>/dev/null
        else
            dbus-send --session --print-reply --dest=org.kde.plasmashell \
                /PlasmaShell org.kde.PlasmaShell.evaluateScript \
                "string:$1" 2>/dev/null
        fi
    }

    panel_sitzt=false
    for _versuch in 1 2 3 4 5 6; do
        sleep 2
        if plasma_skript "$PANEL_JS" | grep -q "PANEL-OK"; then
            # Noch einmal hinsehen: der Wert muss auch zwei Sekunden
            # spaeter noch stehen, sonst hat Plasma nur noch nicht
            # zurueckgeschrieben.
            sleep 2
            if plasma_skript "$PANEL_JS" | grep -q "PANEL-OK"; then
                panel_sitzt=true
                break
            fi
        fi
    done
    if ! $panel_sitzt; then
        echo "  Warnung: Das Panel konnte nicht auf volle Breite gezogen" >&2
        echo "           werden. Rechtsklick darauf > Anzeigen einrichten" >&2
        echo "           > Breite, oder einmal ab- und wieder anmelden." >&2
    fi
fi

cat <<EOF

Angewendet.

  Damit die Fensterdekoration greift, einmal ab- und wieder anmelden.
  KWin laedt Aurorae-Themes ausschliesslich beim Sitzungsstart.

  Zurueck:   ~/.local/share/nt-legacy/backup-*/restore.sh
EOF

if ! $PANEL; then
    cat <<EOF
  Dein Panel bleibt unveraendert. Fedoras Standardpanel schwebt und sieht
  im NT-Stil dunkel und fremd aus - wie auf den Bildschirmfotos wird es
  erst mit dem eigenen Panel:

    ./apply.sh $VARIANTE --panel

EOF
fi

# Der Hinweis steht bewusst hier und nicht im Heredoc oben: er gilt nur,
# wenn wirklich eine Kopie entstanden ist.
if [ -n "$PANELKOPIE" ]; then
    cat <<EOF
  Panel war vorher anders? Das Design hat es ersetzt. Zurueck mit:

    cp "$PANELKOPIE" "$APPLETSRC"
    systemctl --user restart plasma-plasmashell.service

EOF
fi
