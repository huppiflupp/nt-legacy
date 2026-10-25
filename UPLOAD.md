# Publishing on store.kde.org (kde-look.org)

The archives are created with

```bash
./tools/make-package.sh
```

and end up in `dist/`. They are **not** in the repository — they
can be reproduced at any time, and binary files only bloat the
history.

```
dist/
├── nt-legacy-full-manual-install-0.2.14.tar.xz    14 MB   full package
├── nt-legacy-global-theme-<colourway>-0.2.14.tar.xz      10 of them
├── nt-legacy-plasma-style-<colourway>-0.2.14.tar.xz      10 of them
├── nt-legacy-icons-0.2.14.tar.xz                1.4 MB   (light and night version)
├── nt-legacy-window-decorations-0.2.14.tar.xz    12 KB
├── nt-legacy-cursors-0.2.14.tar.xz               12 KB
├── nt-legacy-color-schemes-0.2.14.tar.xz        4.0 KB
├── nt-legacy-wallpaper-<name>-0.2.14.tar.xz              26 of them
├── nt-legacy-wallpapers-manual-install-0.2.14.tar.xz  69 MB
├── screenshots/                                 16 images (10 + 5 day/night + overview)
└── SHA256SUMS
```

## The backgrounds

Since 0.2.7, 26 wallpaper packages are included: ten landscapes (a day
and a night version for each colourway), twelve seamless tiles and
four large images at 4096×4096.

The landscapes are in the full package — every variant's
`contents/defaults` points to them, and without them the theme would have no
background. The tiles and large images are not: they are 61 of the 69 MB, and
with them the full package would be 72 instead of 14 MB.

**One archive per package, here too** — for two reasons, and the first
is the real one.

*A wallpaper package is one image.* That is how the format is defined: a
directory, a `metadata.json`, and in it `contents/images/<width>x<height>`
— several files mean several **resolutions of the same image**, not
several images. You can verify this on any of the roughly sixty packages under
`/usr/share/wallpapers/`. So 26 images in one package would not exist;
the picker would show one tile with one name, and Plasma would display
one of them.

*And several packages in one archive does not work either.* `wallpaper.knsrc`
says `Uncompress=subdir-archive` — KNewStuff expects a single directory in
the archive. What it does with several has not been
reproduced here; after the experience with 0.2.2, where `kpackage` took the
archive itself for the package when there were ten folders at the root, the
risk is not worth testing.

For the store this means: attach the 26 individual archives to the entry.
`nt-legacy-wallpapers-manual-install` belongs in the GitHub release, not in
the store — it is meant to be unpacked into `~/.local/share/wallpapers/`
and is just as wrong under *Get New…* as the full package.

## Why several archives?

The store knows exactly **one** category per entry. A theme like this one,
however, consists of six layers. That is why there are both:

- **The full package** with `install.sh` — for people who want everything
  at once. It belongs in the GitHub release, **not** in the store: it is a
  snapshot of the working directory, and the downloader cannot do anything
  with it. Why that matters is explained further down.
- **Individual archives per layer** — only these make *Get New…*
  work directly in System Settings.

## Why Global Themes and Plasma Styles are one archive per variant

Up to 0.2.2, all ten versions were in one archive. Via *Get New…*
the result was: five to six nameless entries that look like
Breeze, and not a single NT theme. Reported by the community and reproduced with
`kpackagetool6`.

The reason is in Plasma's `knsrc` files. There are two kinds:

| `Uncompress=` | Behaviour | Bundles allowed? |
|---|---|---|
| `archive`, `true` | unpacks bluntly into the target directory | yes |
| `kpackage` | hands over to `kpackagetool6` | **no** |

`kpackagetool6` expects **exactly one** package whose `metadata.json` sits at
the archive root. When there were ten folders there, it took the archive itself
for the package and named it after the file:

```
$ kpackagetool6 -t Plasma/LookAndFeel -i nt-legacy-global-themes-0.2.2.tar.xz
Successfully installed: …/plasma/look-and-feel/nt-legacy-global-themes-0/
```

A folder without `metadata.json` — no theme, a nameless entry, and
the next attempt puts `-1` next to it. With the Plasma Styles even the
installation fails ("Package is not considered valid").

Global Themes and Plasma Themes both go through `kpackage`. Aurorae,
icons, cursors and colour schemes go through `archive` — the bundles
stay there.

**When uploading:** **delete** the old bundle archives in the store, don't
just put the new ones next to them. Anyone who downloads the old file keeps getting
the broken entries.

## The full package does not belong in the Global Themes entry

After 0.2.3 the same report came in a second time — this time without
our doing: the user had clicked `nt-legacy-0.2.3.tar.xz` in the downloader,
that is, the **full package**. That is a snapshot of the
working directory with `install.sh`, not a kpackage package:

```
$ kpackagetool6 -t Plasma/LookAndFeel -i nt-legacy-0.2.4.tar.xz
Successfully installed: …/plasma/look-and-feel/nt-legacy-0/
```

The same nameless folder as with the old bundle. The archives are
fine — the store entry is not.

The downloader puts a button next to **every** file of an entry and
does not say which one matches the category. As long as the full package sits in the
Global Themes entry, someone will click it.

**So:**

1. The entry under *Global Themes* contains **only** the ten
   `nt-legacy-global-theme-<colourway>-…tar.xz`.
2. The full package goes into a **GitHub release** (the tag is set)
   and is linked in the description text — not as a store file.

The file name `nt-legacy-full-manual-install-…` adds a warning in case it
does end up there. You should not rely on that.

### One broken package spoils the whole list

Reproduced in the test VM, and this is what really explains the report.
Starting point: a user directory with exactly two packages — one
valid NT theme and the folder without `metadata.json` that the
full package leaves behind.

| State | What *Global Theme* shows |
|---|---|
| with the broken folder | **nine** tiles, all "Breeze", all with the same preview image |
| without it | Breeze, Breeze Twilight, Fedora, Fedora Dark, Fedora Light, **NT Legacy 2000** — each with its name and its own preview |

So a single package without `metadata.json` is enough for the module to
show **all** entries as "Breeze" — including the ones shipped by Fedora and KDE,
which have nothing to do with it. Anyone who sees that inevitably
thinks the installation created copies of Breeze. In fact
they are the existing themes, just labelled wrongly.

In practice: the folder has to go, then the list is immediately
fine again. For affected users:

```bash
rm -rf ~/.local/share/plasma/look-and-feel/nt-legacy-*
```

(The real packages are called `com.github.huppiflupp.nt-legacy-…` and
stay.)

The format is `tar.xz`: smaller than ZIP, unpackable everywhere on Linux, and
it preserves symbolic links. The icon set consists almost half of
links — a ZIP would turn them into copies.

## What goes in which category?

| File | Store category | System Settings |
|---|---|---|
| `nt-legacy-full-manual-install-…` | **not in the store** | GitHub release, manually with `install.sh` |
| `nt-legacy-global-theme-<colourway>-…` (10×) | Global Themes | Appearance → Global Theme |
| `nt-legacy-plasma-style-<colourway>-…` (10×) | Plasma Themes | Appearance → Plasma Style |
| `nt-legacy-window-decorations-…` | Window Decorations | Appearance → Window Decorations |
| `nt-legacy-icons-…` | Icon Sets | Appearance → Icons |
| `nt-legacy-cursors-…` | Cursors | Appearance → Cursors |
| `nt-legacy-color-schemes-…` | Color Schemes | Appearance → Colors |

**Recommendation:** one entry under *Global Themes* with the ten
individual archives, and the full package in the GitHub release alongside. This
document used to say the opposite — full package in the store, individual archives later —
and that is exactly where the second bug report came from: the downloader
fetches whatever is clicked, and the full package is not a
kpackage package.

## Details for the entry

**Licence:** GPL-2.0-or-later — select *GPL 2.0* in the form.

**Description text:** `nt-legacy/INSTALL.md` is in the full package and is
written in English — requirements, both installation methods, the
ten versions, troubleshooting, way back. For the description field in the store
the sections *Requirements*, *Option 1* and *The ten versions* are enough;
the rest is in the archive alongside anyway.

**This sentence belongs in it**, directly below the installation lines — otherwise
the screenshots promise more than an installation without
`--panel` delivers:

> The screenshots show the theme with its own panel — run
> `./apply.sh <variant> --panel` to get it; without that flag your
> existing panel is left untouched.

**Important:** the theme contains **no third-party material**. Icons, SVGs,
window decoration, cursors and backgrounds are entirely generated
(`tools/gen-icons.py`, `gen-plasma-svg.py`, `gen-aurorae.py`,
`gen-cursor.py`). Details in `nt-legacy/ATTRIBUTION.md`. Chicago95 is
explicitly **not** included — its licensing situation is unclear.

**Screenshots:** are in `dist/screenshots/` and are generated by
`make-package.sh` along the way:

| File | Size | Purpose |
|---|---|---|
| `00-overview.jpg` | 1956×744 | all five colourways, each day and night |
| `01-day-night-*.jpg` … `05-…` | 1920×1080 | one colourway, split diagonally |
| `nt-legacy.jpg` | 1920×1080 | Petrol — the base version |
| `nt-legacy-*.jpg` | 1920×1080 | one single version each |

Each full-size image shows three applications **side by side**, with an English
interface and English folder names:

| Window | What it shows |
|---|---|
| Dolphin | the home folder in icon view — eight folders, each with its own emblem |
| KWrite | `INSTALL.md`, i.e. a syntax-highlighted text view |
| Konsole | a coloured `ls`, so that the ANSI colours calibrated for contrast are visible |

Before, four windows were stacked on top of each other, offset. The idea was to show
an active and several inactive title bars in one
image — the price was that only a strip of each lower window was left and
the file manager of all things was half covered. Side by side,
every window is fully visible; Dolphin opens last and therefore still
carries the active title bar, the other two the inactive one.

`gen-preview.sh` sets up the English interface only for these three
applications (`LANGUAGE=en_US`), not for the whole session — the panel and
clock stay German, which is not noticeable in the image. The user folders are
renamed along with it, otherwise an English sidebar would sit next to
German folder names.

**The split images** put the day and night version of the same colourway into
one image: cut diagonally from top right to bottom left, top left
day, bottom right night. In the store this is the usual presentation for
themes with two versions — two nearly identical full-size images side by side,
on the other hand, are easily read as a repetition.

This only works because `gen-preview.sh` opens the same applications
in the same order at the same resolution for every variant. As a result,
the window edges run straight across the cut. Anyone who creates the
shots differently gets two offset images instead of one
split surface.

**Order in the gallery:** `00-overview.jpg` first — it shows the
range at a glance, and that decides whether someone
clicks on. Then the five split images, then the individual versions for
everyone who wants to see a particular variant in full. The file names are
sorted so that a plain `ls` already gives the right order.

**Dependencies** that belong in the description:

- Plasma 6 (tested on 6.7, Fedora 44)
- The application style is set to *MS Windows 9x* — it is built into Qt,
  nothing needs to be installed
- PCManFM-Qt is **optional**. `appearance.sh` sets it as the file manager
  because Dolphin's storage indicator draws past the widget style. Without
  PCManFM-Qt everything works, only this one bar looks out of place

## Check before uploading

```bash
./tools/make-package.sh --check   # what would go in?
sha256sum -c dist/SHA256SUMS      # archives intact?
```

The package script aborts if Chicago95 icons would end up in the archive
— even if `fetch-icons.sh` installed them locally
beforehand.

## After uploading

The store does not pick up the version number automatically. For a new
version:

1. Bump `KPlugin.Version` in all `metadata.json` files (`build.py` does this)
2. Run `./tools/make-package.sh` again
3. Add the new files to the existing entry, do not delete the old ones —
   otherwise links from forums and collections break

**One exception:** `nt-legacy-global-themes-0.2.2.tar.xz` and
`nt-legacy-plasma-styles-0.2.2.tar.xz` (both plural) should be deleted.
They cannot be installed via *Get New…* and leave
broken entries behind — see above. A dead link is better than a
file that clutters up the user's machine.

The version number is also part of the render cache's name
(`~/.cache/plasma_theme_<name>_v<version>.kcache`). If you don't bump it,
you ship an update that does not become visible on the user's machine.
