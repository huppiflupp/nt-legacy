#!/usr/bin/env bash
# Bundles the archives for the KDE Store (store.kde.org / kde-look.org).
#
#   ./make-package.sh            # all archives into dist/
#   ./make-package.sh --check    # only show what would go in
#
# Two kinds are produced:
#
#   1. A full archive with install.sh. That is the route almost all
#      larger themes take, because a theme consists of several layers
#      (Plasma style, colour scheme, decoration, icons, cursors) and
#      the store knows only one category per entry.
#
#   2. Single archives per layer. Only with these does "Get New"
#      work directly in System Settings: KNewStuff unpacks the archive
#      into the right place and expects exactly one layer there.
#
# Format tar.xz: smaller than zip, unpackable everywhere on Linux, and
# it keeps the symbolic links. The icon set consists of almost
# half links - a zip would turn them into copies and bloat the
# archive needlessly.

set -euo pipefail

LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEME="$LAB/nt-legacy"
DIST="$LAB/dist"

VERSION="$(python3 -c "
import json
d = json.load(open('$THEME/look-and-feel/com.github.huppiflupp.nt-legacy/metadata.json'))
print(d['KPlugin']['Version'])
")"

CHECK=false
[ "${1:-}" = "--check" ] && CHECK=true

# What belongs in NO archive.
#
# icons/ is Chicago95 - third-party material with an unclear licence, it is in
# .gitignore and must under no circumstances be shipped.
# That is why it is listed here explicitly once more, instead of relying on
# .gitignore: whoever accidentally builds an archive from a
# working directory in which fetch-icons.sh has run should
# still not pack it in.
EXCLUDES=(
    --exclude="icons"
    --exclude="__pycache__"
    --exclude="*.pyc"
    --exclude=".directory"
)

if $CHECK; then
    echo "Version: $VERSION"
    echo
    echo "The full archive would contain:"
    tar -cf /dev/null "${EXCLUDES[@]}" -C "$LAB" nt-legacy -v 2>/dev/null \
        | sed 's|^nt-legacy/||' | awk -F/ 'NF<=2' | sort -u | head -30
    echo
    echo "Excluded:"
    printf '  %s\n' "${EXCLUDES[@]}"
    exit 0
fi

# Safeguard: never build an archive with Chicago95
if tar -cf /dev/null "${EXCLUDES[@]}" -C "$LAB" nt-legacy -v 2>/dev/null \
        | grep -q "nt-legacy/icons/"; then
    echo "ABORT: Chicago95 icons would have ended up in the archive." >&2
    exit 1
fi

rm -rf "$DIST"
mkdir -p "$DIST"

# ── 1. Full archive ──────────────────────────────────────────────────────
# The purpose is in the file name, and that is not a cosmetic flaw.
#
# The same report came from the community twice: "Get New" creates
# Breeze duplicates. The second time it was no longer the archives -
# the user had clicked the FULL package in the store. That is a
# snapshot of the working directory with install.sh, not a kpackage package;
# kpackagetool6 turns it into the same nameless folder as it used to with
# the bundle.
#
# In the downloader every file has a button next to it, and the
# category view does not say which one is meant. "full-manual-
# install" in the name is the only thing left that warns at that point.
# It only becomes safe when this file is not in the store entry
# at all - see UPLOAD.md.
#
# Without tiles and large images. With them this file would be 72 MB instead of
# 10 - for 61 MB of image material that has nothing to do with the theme and
# that nobody wants to download unasked. The ten landscapes stay
# in: contents/defaults of every variant points to them, without them
# you would install a theme whose wallpaper is missing.
#
# tools/ goes in as nt-legacy/tools/.
#
# From the community (cubanismo): "./fetch-icons.sh: line 65:
# /nt-legacy/../tools/fix-index-theme.py: No such file or directory".
# fetch-icons.sh and build.py call six scripts from tools/, and the
# archive used to contain only nt-legacy/. Whoever rebuilt from it or added
# Chicago95 ran into nothing - after cloning Chicago95, i.e. at the
# most expensive point.
#
# As a subdirectory and not next to it: the archive should still unpack exactly
# one folder. Both scripts look in nt-legacy/tools/ first
# and then next to it, so that working tree and archive work the same.
FULL="$DIST/nt-legacy-full-manual-install-$VERSION.tar.xz"
TMPTOOLS="$THEME/tools"
if [ -e "$TMPTOOLS" ]; then
    echo "ABORT: $TMPTOOLS already exists - leftovers of an aborted run?" >&2
    exit 1
fi
cp -a "$LAB/tools" "$TMPTOOLS"
trap 'rm -rf "$TMPTOOLS"' EXIT
tar -caf "$FULL" "${EXCLUDES[@]}" \
    --exclude="wallpapers/ntlegacy-kachel-*" \
    --exclude="wallpapers/ntlegacy-gross-*" \
    -C "$LAB" nt-legacy
rm -rf "$TMPTOOLS"
trap - EXIT
echo "  $(basename "$FULL")  $(du -h "$FULL" | cut -f1)   (full package with install.sh, without tiles)"

# ── 2. Single archives per layer ─────────────────────────────────────────
#
# Structure per archive: the folder KNewStuff expects sits directly at
# the root. So nt-legacy/ and not desktoptheme/nt-legacy/.
single() {
    local name="$1" source="$2" dest="$DIST/$3"
    [ -d "$source" ] || return 0
    tar -caf "$dest" "${EXCLUDES[@]}" -C "$(dirname "$source")" "$(basename "$source")"
    printf '  %-42s %6s   (%s)\n' "$(basename "$dest")" \
        "$(du -h "$dest" | cut -f1)" "$name"
}

# ── One package per archive, where KNewStuff demands it ──────────────────
#
# From the community: whoever installs the Global Theme via "Get New"
# gets five to six nameless entries and not a single NT theme.
# Reproduced and confirmed.
#
# The reason is in Plasma's knsrc files. Two kinds:
#
#   Uncompress=archive   unpacks bluntly into the target directory. Ten
#                        folders side by side are right here -
#                        Aurorae, icons, cursors, colour schemes.
#   Uncompress=kpackage  hands the archive to kpackagetool, and
#                        that expects EXACTLY ONE package whose
#                        metadata.json sits at the archive root.
#                        Global Themes and Plasma styles work this way.
#
# Our bundle archive had ten package folders at the root and no
# metadata.json next to them. kpackagetool then takes the archive itself as
# the package, names it after the file and appends a number:
#
#   $ kpackagetool6 -t Plasma/LookAndFeel -i nt-legacy-global-themes.tar.xz
#   Successfully installed: .../look-and-feel/nt-legacy-global-themes-0/
#
# A folder without metadata.json - the theme is missing, the entry stays
# nameless, and every new attempt puts the next one beside it. With the
# Plasma styles the installation itself already fails ("the package is
# considered invalid").
#
# Hence one archive per variant. In the store that becomes ten
# files on one entry, of which the user picks one -
# that is the usual form there for themes with several versions.
# The file name carries the palette, not the full package ID. In the
# store the user faces a list of twenty files; there
# "desert-nacht" helps and "com.github.huppiflupp.nt-legacy-desert-nacht" does not.
short_name() {
    local b="$1"
    b="${b#com.github.huppiflupp.}"
    b="${b#nt-legacy}"
    b="${b#-}"
    echo "${b:-teal}"
}

package_per_variant() {
    local name="$1" source="$2" prefix="$3"
    local n=0
    for d in "$source"/*/; do
        [ -d "$d" ] || continue
        local b; b="$(basename "$d")"
        tar -caf "$DIST/$prefix-$(short_name "$b")-$VERSION.tar.xz" \
            "${EXCLUDES[@]}" -C "$source" "$b"
        n=$((n + 1))
    done
    printf '  %-42s %6s   (%s)\n' "$prefix-*-$VERSION.tar.xz" "$n pcs" "$name"
}

package_per_variant "Plasma Style, one archive per variant" \
    "$THEME/desktoptheme" "nt-legacy-plasma-style"
package_per_variant "Global Theme, one archive per variant" \
    "$THEME/look-and-feel" "nt-legacy-global-theme"

# Aurorae goes through Uncompress=archive - a bundle is right here.
tar -caf "$DIST/nt-legacy-window-decorations-$VERSION.tar.xz" "${EXCLUDES[@]}" \
    -C "$THEME/aurorae" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-window-decorations-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-window-decorations-$VERSION.tar.xz" | cut -f1)" "Aurorae, 10 variants"

# Both icon sets in one archive. The icon downloader goes through
# Uncompress=true, so it unpacks bluntly into ~/.local/share/icons/ - two
# folders side by side are right there. And whoever pulls only the light one
# is back to the dark system tray with every night version.
tar -caf "$DIST/nt-legacy-icons-$VERSION.tar.xz" "${EXCLUDES[@]}" \
    -C "$THEME/icons-nt" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-icons-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-icons-$VERSION.tar.xz" | cut -f1)" \
    "icons, light and night version"

tar -caf "$DIST/nt-legacy-cursors-$VERSION.tar.xz" "${EXCLUDES[@]}" \
    -C "$THEME/cursors" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-cursors-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-cursors-$VERSION.tar.xz" | cut -f1)" "cursors, light and red"

# Colour schemes are single files - the store takes them that way too,
# but bundled it is less work for the user.
tar -caf "$DIST/nt-legacy-color-schemes-$VERSION.tar.xz" \
    -C "$THEME/color-schemes" .
printf '  %-42s %6s   (%s)\n' "nt-legacy-color-schemes-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-color-schemes-$VERSION.tar.xz" | cut -f1)" "colour schemes, 10 variants"

# ── Wallpapers ───────────────────────────────────────────────────────────
#
# One archive per package, and that is not a matter of taste here.
# wallpaper.knsrc says Uncompress=subdir-archive: KNewStuff expects exactly
# ONE directory in the archive and puts it into ~/.local/share/wallpapers.
# If several sit side by side, it packs them into a folder named after
# the archive - the metadata.json then sits one level too deep
# and Plasma finds not a single image. That is the same bug that produced
# the nameless entries in 0.2.2, just one level further down.
#
# The gradient surfaces (*-flaeche) get no archive of their own. They are
# the fallback for whoever builds from source, and are in the
# full archive - in the store they would be 20 more files for 95 KB of image.
wp_n=0
for d in "$THEME"/wallpapers/*/; do
    b="$(basename "$d")"
    case "$b" in *-flaeche) continue;; esac
    # "ntlegacy" is the base variant - in the file name it is called "teal",
    # as everywhere else. Without this case the archive would be called
    # nt-legacy-wallpaper-ntlegacy-*.
    short="${b#ntlegacy-}"
    [ "$short" = "ntlegacy" ] && short="teal"
    tar -caf "$DIST/nt-legacy-wallpaper-$short-$VERSION.tar.xz" \
        "${EXCLUDES[@]}" -C "$THEME/wallpapers" "$b"
    wp_n=$((wp_n + 1))
done
printf '  %-42s %6s   (%s)\n' "nt-legacy-wallpaper-*-$VERSION.tar.xz" \
    "$wp_n pcs" "wallpapers, one archive per package"

# Plus a collective archive for the manual route: unpack into
# ~/.local/share/wallpapers, done. It must NOT go through "Get New"
# - see above. The name says so, as with the full archive.
tar -caf "$DIST/nt-legacy-wallpapers-manual-install-$VERSION.tar.xz" \
    "${EXCLUDES[@]}" -C "$THEME/wallpapers" .
printf '  %-42s %6s   (%s)\n' \
    "nt-legacy-wallpapers-manual-install-$VERSION.tar.xz" \
    "$(du -h "$DIST/nt-legacy-wallpapers-manual-install-$VERSION.tar.xz" | cut -f1)" \
    "all wallpapers, to unpack by hand"

# ── Screenshots for the store gallery ────────────────────────────────────
#
# They are generated here and not copied in by hand. Reason: the
# script clears dist/ at the start. Whoever puts the images in on the side
# loses them on the next run - exactly that happened once.
mkdir -p "$DIST/screenshots"
count=0
for d in "$THEME"/look-and-feel/*/; do
    n="$(basename "$d" | sed 's/com.github.huppiflupp.//')"
    full="$d/contents/previews/fullscreenpreview.jpg"
    [ -f "$full" ] || continue
    cp "$full" "$DIST/screenshots/$n.jpg"
    count=$((count + 1))
done

# ── Day/night in one image ───────────────────────────────────────────────
#
# Every palette comes in a day and a night version. Side by side
# in the gallery that says little: two nearly identical images, and whoever
# does not look closely takes the second for a repeat. Hence one
# image per palette, split diagonally from top right to bottom left -
# day at the top left, night at the bottom right. In the store that is the usual
# presentation for themes with two versions.
#
# This only works because gen-preview.sh puts the windows for every
# variant in the same place: same programs, same
# order, same resolution. The window edges run straight across the
# cut, and you see the same screen tinted twice
# instead of two different shots.
diagonal() {
    local day="$1" night="$2" dest="$3"
    local b h
    # The \n is mandatory: without a line end read returns an error status,
    # and set -e ends the script silently in the middle of the run.
    read -r b h < <(magick identify -format '%w %h\n' "$day")

    # The detour via CopyOpacity instead of a mask as a third image with
    # -composite: the latter does not evaluate the mask reliably, the
    # result was the day image in one piece. This way the mask is explicitly
    # the alpha channel of the day image, and there is nothing to guess.
    magick "$day" \
        \( -size "${b}x${h}" xc:black -fill white \
           -draw "polygon 0,0 ${b},0 0,${h}" \) \
        -alpha off -compose CopyOpacity -composite "$tmp/top.png"

    # The light line on the cut edge is not decoration: without it
    # the transition looks like an image defect in the darker palettes,
    # because day and night surfaces are similarly bright there.
    magick "$night" "$tmp/top.png" -compose Over -composite \
        -stroke "#e8e8e8" -strokewidth 3 -draw "line ${b},0 0,${h}" \
        -quality 88 "$dest"
}

# Which night belongs to which day image? The base version is called
# nt-legacy.jpg, but its night version nt-legacy-teal-nacht.jpg - the
# name carries the palette, which the base version leaves out of its name.
night_image_for() {
    local day="$1"
    case "$(basename "$day")" in
        nt-legacy.jpg) echo "$(dirname "$day")/nt-legacy-teal-nacht.jpg" ;;
        *)             echo "${day%.jpg}-nacht.jpg" ;;
    esac
}

if command -v magick >/dev/null && [ "$count" -gt 0 ]; then
    tmp="$(mktemp -d)"
    pairs=0
    tiles=()

    # Base version first, the rest alphabetically - the same order
    # as later in the gallery.
    day_images=("$DIST/screenshots/nt-legacy.jpg")
    for b in "$DIST"/screenshots/nt-legacy-*.jpg; do
        case "$b" in *-nacht.jpg) continue ;; esac
        day_images+=("$b")
    done

    for day in "${day_images[@]}"; do
        [ -f "$day" ] || continue
        night="$(night_image_for "$day")"
        [ -f "$night" ] || continue
        pairs=$((pairs + 1))
        name="$(basename "${day%.jpg}" | sed 's/^nt-legacy-*//')"
        [ -z "$name" ] && name="teal"

        diagonal "$day" "$night" \
            "$(printf '%s/screenshots/%02d-day-night-%s.jpg' "$DIST" "$pairs" "$name")"
        count=$((count + 1))

        # For the overview tile the finished full image is not
        # scaled down; it is cropped first and then split. Otherwise
        # the cut edge runs askew through the tile instead of from corner
        # to corner, and the effect is lost.
        #
        # The same crop as for preview.png in gen-preview.sh:
        # top left corner, the two left windows. A centred
        # crop used to fit when the windows were stacked
        # - since they stand side by side, it hits the editor and
        # the terminal, and nothing is left of the folder icons.
        for side in day night; do
            [ "$side" = day ] && q="$day" || q="$night"
            magick "$q" -gravity northwest -crop 69%x69%+8+24 +repage \
                   -resize 640x360! "$tmp/tile-$side.png" 2>/dev/null
        done
        diagonal "$tmp/tile-day.png" "$tmp/tile-night.png" \
                 "$tmp/tile-$pairs.jpg"
        tiles+=("$tmp/tile-$pairs.jpg")
    done

    # Plus an overview image: all palettes on one tile. That is
    # usually the first thing someone looks at in a gallery - a row of
    # nearly identical full images says less than one image that shows
    # the range.
    #
    # Five split tiles instead of ten whole ones: each is twice as
    # large, and the ten versions are all on it anyway.
    #
    # Grid 3x2, not 5x1: side by side that would give a strip 2860 pixels
    # wide and 430 high - in the gallery overview nothing of it
    # can be made out. The sixth slot is left over and
    # gets a caption, otherwise the gap looks like a mistake.
    if [ ${#tiles[@]} -gt 0 ]; then
        magick -size 640x360 xc:"#3a4446" -gravity center \
            -fill "#dfe6e6" -pointsize 46 -annotate +0-30 "NT Legacy" \
            -fill "#9fb0b0" -pointsize 24 -annotate +0+30 "five palettes, day and night" \
            "$tmp/tile-text.jpg" 2>/dev/null \
            && tiles+=("$tmp/tile-text.jpg")

        magick montage "${tiles[@]}" -tile 3x2 -geometry +6+6 \
            -background "#3a4446" "$DIST/screenshots/00-overview.jpg" 2>/dev/null \
            && count=$((count + 1))
    fi
    rm -rf "$tmp"
fi
echo "  screenshots/                               $(du -sh "$DIST/screenshots" | cut -f1)   ($count images)"

# ── Checksums ────────────────────────────────────────────────────────────
(cd "$DIST" && sha256sum *.tar.xz > SHA256SUMS)

echo
echo "Done: $DIST"
echo "Checksums in dist/SHA256SUMS"
