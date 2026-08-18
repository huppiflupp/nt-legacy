# Installing NT Legacy

A Plasma 6 theme in the style of Windows NT — five palettes, each in a day
and a night version.

**The installation only ever touches `$HOME`.** It never asks for `sudo`,
and it backs up every configuration file it writes to before writing.
The way back is at the bottom of this file.

---

## Requirements

- **Plasma 6** (developed and tested on 6.7, Fedora 44)
- `kpackagetool6` and `kwriteconfig6` — part of any Plasma 6 installation
- **No extra package** for the application style: NT Legacy uses
  *MS Windows 9x*, which ships with Qt itself

Optional but recommended:

- **PCManFM-Qt** as the file manager. Dolphin draws its free-space
  indicator past the widget style — a silver capsule in the middle of the
  NT grey. Everything works without PCManFM-Qt; that one bar just looks
  out of place. See `./anmutung.sh` below.

## Option 1 — full package (recommended)

The archive `nt-legacy-full-manual-install-<version>.tar.xz` contains all
six layers of the theme at once.

```bash
tar -xf nt-legacy-full-manual-install-0.2.10.tar.xz
cd nt-legacy
./install.sh --anwenden win2k     # install, then apply that version
```

`install.sh` creates a backup first and prints its path. It then installs
Plasma styles, colour schemes, window decorations, icons, cursors and
wallpapers. Without `--anwenden` it only installs and leaves your desktop
untouched; you pick a version afterwards:

```bash
./apply.sh                        # Petrol, the base version
./apply.sh win98-nacht            # Windows 98, night version
./apply.sh win98-nacht --panel    # …and the NT panel (replaces yours)
./apply.sh --help                 # all ten versions and switches
```

**Use `apply.sh`, not `plasma-apply-lookandfeel`.** The widget style
(Windows instead of Breeze) can only be set in `~/.config/kdeglobals`,
and that is what `apply.sh` does — see *If something does not take
effect*. Applying the global theme alone, from the command line or from
System Settings, leaves that one layer on Breeze.

**Add `--panel` if you want it to look like the screenshots.** Without it
your existing panel stays — and on most distributions that panel *floats*,
which no version of NT ever did. See *The panel* below; `apply.sh` keeps a
copy of your old one either way.

**Then log out and back in once.** KWin loads Aurorae themes only at
session start — until then every window still wears the old titlebar.
Everything else takes effect immediately.

## Option 2 — *Get New …* in System Settings

If you only want a single layer, use the matching individual archive.
Every layer in System Settings has a *Get New …* button for this — or you
can unpack the archive by hand:

| Archive | Destination |
|---|---|
| `…-global-theme-<palette>-…` | `~/.local/share/plasma/look-and-feel/` |
| `…-plasma-style-<palette>-…` | `~/.local/share/plasma/desktoptheme/` |
| `…-window-decorations-…` | `~/.local/share/aurorae/themes/` |
| `…-icons-…` | `~/.local/share/icons/` |
| `…-cursors-…` | `~/.local/share/icons/` |
| `…-color-schemes-…` | `~/.local/share/color-schemes/` |

This route does not give you `apply.sh`. You can select the global theme
under *System Settings → Colors & Themes → Global Theme*, but you may have
to set the individual layers by hand — see *If something does not take
effect*.

## The ten versions

| Command | Display name | Palette |
|---|---|---|
| `./apply.sh` or `teal` | NT Legacy | petrol and warm grey — the base version |
| `./apply.sh lilac` | NT Legacy Flieder | lilac instead of petrol, after NT's *Lilac* |
| `./apply.sh desert` | NT Legacy Wüste | sand and terracotta, after NT's *Desert* |
| `./apply.sh win2k` | NT Legacy 2000 | softer grey, blue gradient |
| `./apply.sh win98` | NT Legacy 98 | system grey and navy blue |

Each of these also comes as a night version — dark surfaces, same accents:

```bash
./apply.sh teal-nacht     ./apply.sh lilac-nacht    ./apply.sh desert-nacht
./apply.sh win2k-nacht    ./apply.sh win98-nacht
```

Three extras:

```bash
./apply.sh win2k --panel      # also install the NT panel (replaces yours)
./apply.sh win2k --rot        # red cursor instead of white
./apply.sh win2k --schrift    # bold titlebar font, as in the original
```

`--panel` is what makes the desktop look like the screenshots — see below.

`--schrift` is deliberately not applied automatically: otherwise your
setting under *Fonts → Window Title* would be overwritten on every run.

## Automatic day/night switching

Plasma 6 can switch between a light and a dark global theme by time of day
(*System Settings → Colors & Themes → Global Theme → Day/Night switching*).
It uses two keys, `DefaultLightLookAndFeel` and `DefaultDarkLookAndFeel`.

`apply.sh` fills both with the pair belonging to the palette you picked —
`./apply.sh desert` registers *Wüste* as the light and *Wüste Nacht* as the
dark version. So if you turn the automatic switch on, you stay in the same
palette and only day and night change. Mixing two palettes is otherwise easy
to end up with, and the machine then changes colour scheme entirely at dusk.

`apply.sh` does not turn the automatic switch on — that stays your decision.

## The panel — and why it matters more than it sounds

By default `apply.sh` leaves your panel alone. That is the safe choice, but
it has a visible consequence: most distributions ship a *floating* panel,
and Plasma draws floating panels with the rounded, translucent variants of
the theme. NT Legacy looks dark and out of place in them — nothing about it
recalls NT.

To get the panel you see in the screenshots — at the screen edge, 30 pixels
high, not floating:

```bash
./apply.sh win98 --panel
```

This **replaces your panel**. `apply.sh` writes a copy first, every time,
and prints the way back:

```bash
cp ~/.local/share/nt-legacy/panel/appletsrc-<timestamp> \
   ~/.config/plasma-org.kde.plasma.desktop-appletsrc
systemctl --user restart plasma-plasmashell.service
```

The last ten copies are kept. Note that switching global themes in System
Settings can also replace the panel — whenever you tick the workspace
layout there — which is why the copy is written even without `--panel`.

## The look — separate and optional

`anmutung.sh` changes settings of **other programs**: a full-width status
bar in Dolphin, PCManFM-Qt as the file manager, its icon theme, and
Konsole's default profile.

This is deliberately not part of `install.sh`. Someone trying out a theme
does not expect their Dolphin configuration to be different afterwards.

```bash
./anmutung.sh --zeigen    # what would be set, and why
./anmutung.sh             # apply
./anmutung.sh --zurueck   # full revert
```

### Konsole

`install.sh` only *places* a Konsole profile and five colour schemes in
`~/.local/share/konsole/` — one scheme per palette, built from the same
colour values as everything else. Nothing is switched over until you run
`anmutung.sh`; your own profiles stay and remain selectable in the menu.

The profile uses **Liberation Mono**, which is metrically Courier
compatible and present on practically every Linux. A theme should not
depend on a font it does not ship: if it is missing, Qt substitutes one
silently and the terminal simply does not look like NT.

`apply.sh` keeps the profile's colour scheme in step with the palette you
pick. There are five schemes rather than ten because the accent colours
are identical between the day and night version of a palette — the
terminal is dark either way, as it was under NT.

## Boot screens — GRUB and Plymouth

The theme also covers what you see before the desktop appears: the GRUB
boot menu and the Plymouth boot splash, both in the same NT dialog shape
as the Plasma splash screen.

**These two are not part of `install.sh`.** They write to `/boot` and
`/usr` and therefore need `sudo` — every other part of NT Legacy stays
inside `$HOME`. They are separate scripts so that the decision is yours:

```bash
./install-grub.sh win2k          # boot menu
./install-plymouth.sh win2k      # boot splash
./install-grub.sh --zurueck      # remove, restore what was there before
./install-plymouth.sh --zurueck
```

Both back up what they change before changing it, and `--zurueck`
restores it byte for byte — verified in a VM by comparing checksums of
`/etc/default/grub` before and after.

What can go wrong is limited: if GRUB cannot find its theme it draws its
plain text menu, and if Plymouth cannot find its theme you simply see the
usual boot messages. The machine boots either way.

Three things worth knowing:

- **Plymouth needs its script module.** On Fedora and Nobara it is a
  separate package: `sudo dnf install plymouth-plugin-script`. Debian and
  Arch ship it inside `plymouth`. Without it, Plymouth silently falls back
  to the text theme — the most common reason a boot splash "just doesn't
  show up". `install-plymouth.sh` checks for it and stops.
- **`GRUB_TERMINAL=console` beats everything.** If that line is in
  `/etc/default/grub`, the menu stays in text mode and the theme is
  installed but invisible. The script warns you if it finds it.
- **With an encrypted disk, test the passphrase prompt** before you
  reboot. It is the one thing that can leave you staring at a screen that
  waits for input without showing what for:

  ```bash
  sudo plymouth ask-for-password --prompt "Test"
  ```

  The theme draws prompt and one box per typed character; both were
  verified in a VM.

## Chicago95 icons — optional, not included

NT Legacy ships its own icon set (*NTLegacyIcons*, plus a night version),
so you do not need anything else. If you would rather have the Chicago95
icons, fetch them yourself:

```bash
./fetch-icons.sh    # clones Chicago95 and adapts it for Plasma 6
./build.py          # only needed if you build from source
```

They are **not** part of any archive here: Chicago95 has no LICENSE file
and the provenance of its bitmaps is unclear, so shipping them would be
irresponsible. `fetch-icons.sh` uses the `tools/` directory that comes
with the full package.

## Verifying

```bash
./pruefe.sh            # are all parts present?
./pruefe.sh --system   # also check against the installed system
```

## If something does not take effect

**The titlebar still looks the way it did.** Log out and back in. KWin
loads Aurorae themes only at session start; a `reconfigure` is not enough.

**After an update everything looks unchanged.** The render cache carries
the theme's name and version:

```bash
rm -f ~/.cache/plasma_theme_*.kcache ~/.cache/ksvg-elements
```

Then log out and back in.

**Everything looks like Breeze except the titlebar.** The application style
is the one layer a global theme cannot set on its own. Plasma stores a
theme's settings as *defaults* under `~/.config/kdedefaults/`, and Qt
applications do not read the application style from there — measured in a
clean VM: `widgetStyle=Windows` was set correctly and every application
still started with Breeze.

`apply.sh` works around this by writing the value into `~/.config/kdeglobals`
itself. If you installed via *Get New …* and have no `apply.sh`, set it by
hand under *System Settings → Colors & Themes → Application Style →
MS Windows 9x*.

**`qt.dbus.integration` messages while installing.** On Plasma 6.6 and
older you may see one line per Plasma style:

```
qt.dbus.integration: QDBusConnection: error: could not send signal to
service "" path "/KPackage/" … Invalid object path: /KPackage/
```

Harmless, and not a failed installation: KPackage announces each
installed package over D-Bus and builds the object path from a prefix
that is empty for Plasma styles. The packages themselves are installed
correctly. Since 0.2.10 `install.sh` filters these lines out — real
errors from `kpackagetool6` still get through. Newer KDE Frameworks
(6.28 measured) no longer produce them.

**No panel after switching several times.** `plasma-plasmashell` allows
three starts per minute. `apply.sh` therefore does not restart the shell
but switches at runtime. If it happens anyway:

```bash
systemctl --user reset-failed plasma-plasmashell.service
systemctl --user start plasma-plasmashell.service
```

## Going back

Three levels, depending on how far back you want:

```bash
~/.local/share/nt-legacy/backup-*/restore.sh   # configuration from before the install
./anmutung.sh --zurueck                        # settings of other programs
./uninstall.sh                                 # remove the theme completely
```

`uninstall.sh` resets the configuration to Breeze **first** and deletes
the files **afterwards**. That order matters: if `kwinrc` points at a
deleted Aurorae theme, KWin draws no titlebar at all — no frame, no close
button.

The backups under `~/.local/share/nt-legacy/` are left in place.

## Licence and provenance

GPL-2.0-or-later. The theme contains **no third-party material**: icons,
SVGs, window decoration and cursors are all generated from colour values.
The photographic wallpapers are rendered locally with FLUX.1-schnell
(Apache-2.0). Details in `ATTRIBUTION.md`.
