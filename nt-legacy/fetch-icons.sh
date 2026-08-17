#!/usr/bin/env bash
# Holt das Icon-Set und bereitet es fuer NT Legacy auf.
#
# Das Set ist ein Ableger von Chicago95. Es liegt nicht im Repository -
# Begruendung in ATTRIBUTION.md: Chicago95 hat keine LICENSE-Datei, und
# die Herkunft der Bitmaps ist ungeklaert. Lies das, bevor du das Theme
# weitergibst.

set -euo pipefail
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZIEL="$HIER/icons/NTLegacy"

# Wo liegen die Werkzeuge aus tools/?
#
# Zwei Lagen, und beide sind normal: im Arbeitsbaum neben nt-legacy/, im
# ausgelieferten Archiv als nt-legacy/tools/. Bis 0.2.7 stand hier fest
# "$HIER/../tools" - aus dem Archiv heraus lief das ins Leere, gemeldet
# aus der Community: "line 65: /nt-legacy/../tools/fix-index-theme.py:
# No such file or directory". Und weil das erst in Zeile 65 auffiel, war
# der Klon von Chicago95 schon gelaufen.
if [ -d "$HIER/tools" ]; then
    WERKZEUGE="$HIER/tools"
else
    WERKZEUGE="$HIER/../tools"
fi
for w in fix-index-theme.py gen-symbolic-aliase.py gen-icon-aliase.py; do
    if [ ! -f "$WERKZEUGE/$w" ]; then
        echo "FEHLER: $w fehlt (gesucht in $WERKZEUGE)." >&2
        echo "        Dieses Skript braucht das Verzeichnis tools/." >&2
        echo "        Es steckt im Gesamtarchiv und im Quelltext:" >&2
        echo "        https://github.com/huppiflupp/nt-legacy" >&2
        exit 1
    fi
done
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Hole Chicago95 (nur den Icon-Ordner) …"
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/grassmunk/Chicago95.git "$TMP/c95" 2>&1 | tail -1
git -C "$TMP/c95" sparse-checkout set Icons/Chicago95 >/dev/null

rm -rf "$ZIEL"
mkdir -p "$(dirname "$ZIEL")"
cp -r "$TMP/c95/Icons/Chicago95" "$ZIEL"
rm -f "$ZIEL/icon-theme.cache"
find "$ZIEL" \( -name '*.html' -o -name '*.old' \) -delete

echo "Passe index.theme an …"
python3 - "$ZIEL" <<'PY'
import sys, re
from pathlib import Path
p = Path(sys.argv[1]) / "index.theme"
s = p.read_text()
s = s.replace("Name=Chicago95", "Name=NT Legacy")
s = re.sub(r"^Comment=.*$", "Comment=Windows-NT-4.0-Icons fuer Plasma 6, "
           "auf Basis von Chicago95", s, count=1, flags=re.M)
# Ohne Inherits faellt Plasma fuer jedes fehlende Icon auf hicolor
# zurueck - und hicolor ist fast leer.
if "Inherits=" not in s:
    s = s.replace("[Icon Theme]", "[Icon Theme]\nInherits=breeze,hicolor", 1)
p.write_text(s)
PY

# In Chicago95 zeigen folder.svg, inode-directory.svg und
# folder-symbolic.svg unter places/scalable auf folder_open.svg. Da
# scalable bis 256px gewinnt, zeigt Dolphin ab 64px fuer JEDEN
# geschlossenen Ordner einen offenen. Ohne die Symlinks greift
# places/48/folder.png, darueber Breeze - weniger falsch.
for f in folder.svg inode-directory.svg folder-symbolic.svg; do
    z="$ZIEL/places/scalable/$f"
    if [ -L "$z" ] && readlink "$z" | grep -q open; then rm -f "$z"; fi
done

# status/symbolic als Scalable 8..512 gewinnt gegen alle Fixed-Groessen
# und liefert 16px-Bitmaps hochskaliert - besonders im Systemabschnitt.
python3 - "$ZIEL" <<'PY2'
import sys, re
from pathlib import Path
p = Path(sys.argv[1]) / "index.theme"
s = p.read_text()
m = re.search(r"\[status/symbolic\][^\[]*", s)
if m:
    p.write_text(s.replace(m.group(0),
        "[status/symbolic]\nSize=16\nContext=Status\nType=Fixed\n\n"))
PY2

"$WERKZEUGE/fix-index-theme.py" "$ZIEL"
"$WERKZEUGE/gen-symbolic-aliase.py" "$ZIEL"

# Chicago95 traegt GNOME-Namen (view-grid, view-list), Dolphin fordert
# aber view-list-icons, view-list-details, view-file-columns an. Ohne
# diese Verweise sind die Ansichtsmodi in der Werkzeugleiste Breeze-
# Symbole mitten in der Pixelart.
"$WERKZEUGE/gen-icon-aliase.py" "$ZIEL"

echo
echo "Fertig. Danach: ./build.py && ./install.sh"
