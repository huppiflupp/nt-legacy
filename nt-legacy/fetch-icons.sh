#!/usr/bin/env bash
# Fetches a third-party icon set and prepares it for NT Legacy.
#
#   ./fetch-icons.sh              # Chicago95 (default, as before)
#   ./fetch-icons.sh se98         # SE98 - Win98 SE style, much larger
#   ./fetch-icons.sh both
#
# Neither of the two sets is in the repository, and neither is part of
# redistribution - reasons in ATTRIBUTION.md. In short: Chicago95 has no
# LICENSE file, SE98 has one (GPL-2.0), but calls itself in its
# own README a "manual copy-paste fork" of Chicago95 with
# material from the MicroSoft Memphis project. A GPL stamp only covers
# what the person applying it created themselves. Read that before you
# redistribute the theme.
#
# For your own machine both are harmless: the sets land in
# ~/.local/share/icons and can be selected in System Settings.

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Where are the tools from tools/?
#
# Two locations, and both are normal: in the working tree next to nt-legacy/, in
# the shipped archive as nt-legacy/tools/. Up to 0.2.7 this was hard-coded to
# "$HERE/../tools" - from inside the archive that pointed nowhere, reported
# from the community: "line 65: /nt-legacy/../tools/fix-index-theme.py:
# No such file or directory". And because that was only noticed at line 65,
# the clone of Chicago95 had already run.
if [ -d "$HERE/tools" ]; then
    TOOLS="$HERE/tools"
else
    TOOLS="$HERE/../tools"
fi
for w in fix-index-theme.py gen-symbolic-aliases.py gen-icon-aliases.py; do
    if [ ! -f "$TOOLS/$w" ]; then
        echo "ERROR: $w is missing (looked in $TOOLS)." >&2
        echo "       This script needs the tools/ directory." >&2
        echo "       It is included in the full archive and in the source code:" >&2
        echo "       https://github.com/huppiflupp/nt-legacy" >&2
        exit 1
    fi
done

WHICH="${1:-chicago95}"
case "$WHICH" in
    chicago95|se98|both) ;;
    -h|--help)
        # The header comment up to the first line that is no longer one.
        # With a fixed line range "set -euo pipefail" was included here.
        awk 'NR>1 { if ($0 !~ /^#/) exit; sub(/^# ?/, ""); print }' "$0"
        exit 0 ;;
    *)
        echo "ERROR: unknown source '$WHICH'." >&2
        echo "       Possible: chicago95, se98, both" >&2
        exit 1 ;;
esac

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Common to both sets: add sections, symbolic aliases, the
# names Dolphin asks for. Without the last step the
# view modes in the toolbar are Breeze icons in the middle of the
# pixel art.
post_process() {
    local target="$1"
    "$TOOLS/fix-index-theme.py"     "$target"
    "$TOOLS/gen-symbolic-aliases.py" "$target"
    "$TOOLS/gen-icon-aliases.py"     "$target"
}

fetch_chicago95() {
    local target="$HERE/icons/NTLegacy"

    echo "Fetching Chicago95 (only the icon folder) …"
    git clone --depth 1 --filter=blob:none --sparse \
        https://github.com/grassmunk/Chicago95.git "$TMP/c95" 2>&1 | tail -1
    git -C "$TMP/c95" sparse-checkout set Icons/Chicago95 >/dev/null

    rm -rf "$target"
    mkdir -p "$(dirname "$target")"
    cp -r "$TMP/c95/Icons/Chicago95" "$target"
    rm -f "$target/icon-theme.cache"
    find "$target" \( -name '*.html' -o -name '*.old' \) -delete

    echo "Adjusting index.theme …"
    python3 - "$target" <<'PY'
import sys, re
from pathlib import Path
p = Path(sys.argv[1]) / "index.theme"
s = p.read_text()
s = s.replace("Name=Chicago95", "Name=NT Legacy")
s = re.sub(r"^Comment=.*$", "Comment=Windows NT 4.0 icons for Plasma 6, "
           "based on Chicago95", s, count=1, flags=re.M)
# Without Inherits Plasma falls back to hicolor for every missing icon
# - and hicolor is almost empty.
if "Inherits=" not in s:
    s = s.replace("[Icon Theme]", "[Icon Theme]\nInherits=breeze,hicolor", 1)
p.write_text(s)
PY

    # In Chicago95 folder.svg, inode-directory.svg and
    # folder-symbolic.svg under places/scalable point to folder_open.svg. Since
    # scalable wins up to 256px, Dolphin shows an open folder for EVERY
    # closed folder from 64px up. Without the symlinks
    # places/48/folder.png applies, above that Breeze - less wrong.
    for f in folder.svg inode-directory.svg folder-symbolic.svg; do
        z="$target/places/scalable/$f"
        if [ -L "$z" ] && readlink "$z" | grep -q open; then rm -f "$z"; fi
    done

    # status/symbolic as Scalable 8..512 wins against all Fixed sizes
    # and delivers 16px bitmaps scaled up - especially in the system tray.
    python3 - "$target" <<'PY2'
import sys, re
from pathlib import Path
p = Path(sys.argv[1]) / "index.theme"
s = p.read_text()
m = re.search(r"\[status/symbolic\][^\[]*", s)
if m:
    p.write_text(s.replace(m.group(0),
        "[status/symbolic]\nSize=16\nContext=Status\nType=Fixed\n\n"))
PY2

    post_process "$target"
    echo "  -> $target"
}

fetch_se98() {
    local target="$HERE/icons/NTLegacySE98"

    echo "Fetching SE98 (only the icon folder) …"
    git clone --depth 1 --filter=blob:none --sparse \
        https://www.opencode.net/nestoris/Win98SE.git "$TMP/se98" 2>&1 | tail -1
    git -C "$TMP/se98" sparse-checkout set SE98 >/dev/null

    rm -rf "$target"
    mkdir -p "$(dirname "$target")"
    cp -a "$TMP/se98/SE98" "$target"
    rm -f "$target/icon-theme.cache"

    # SE98 carries its tools and preview tables in the theme tree:
    # awk scripts, icons.html per context, size lists, a template.
    # None of that is an icon. The .icon files stay - they are
    # valid freedesktop metadata.
    find "$target" \( -name '*.html' -o -name '*.md' -o -name '*.awk' \
                 -o -name '*.sh' -o -name 'sizes_brief' -o -name 'sizes_md' \
                 -o -name 'template' -o -name 'file.data' -o -name 'apps.txt' \
                 -o -name 'table_grassmunk' \) -delete

    echo "Adjusting index.theme …"
    python3 - "$target" <<'PY3'
import sys, re
from pathlib import Path
p = Path(sys.argv[1]) / "index.theme"
s = p.read_text()

s = re.sub(r"^Name=.*$", "Name=NT Legacy (SE98)", s, count=1, flags=re.M)

# The translated Comment lines (26 languages) describe a different
# theme than the one here. Out with them, one line is enough.
s = re.sub(r"^Comment\[[^\]]+\]=.*\n", "", s, flags=re.M)
s = re.sub(r"^Comment=.*$",
           "Comment=Windows 98 SE icons for Plasma 6, based on SE98 "
           "(nestoris) - not part of redistribution, see ATTRIBUTION.md",
           s, count=1, flags=re.M)

# "Breeze" capitalised does not exist as a directory. The theme is called breeze,
# lower case - on every distribution. So the fallback chain pointed nowhere:
# whatever SE98 lacks went straight to hicolor, and hicolor is almost
# empty. Order as in the rest of the theme, breeze first.
if re.search(r"^Inherits=", s, re.M):
    s = re.sub(r"^Inherits=.*$", "Inherits=breeze,Adwaita,hicolor",
               s, count=1, flags=re.M)
else:
    s = s.replace("[Icon Theme]", "[Icon Theme]\nInherits=breeze,Adwaita,hicolor", 1)

p.write_text(s)
PY3

    post_process "$target"
    echo "  -> $target"
}

case "$WHICH" in
    chicago95) fetch_chicago95 ;;
    se98)      fetch_se98 ;;
    both)      fetch_chicago95; echo; fetch_se98 ;;
esac

echo
echo "Done. Next: ./build.py && ./install.sh"
