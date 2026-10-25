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
  out of place. See `./appearance.sh` below.

## Option 1 — full package (recommended)

The archive `nt-legacy-full-manual-install-<version>.tar.xz` contains all
six layers of the theme at once.

```bash
tar -xf nt-legacy-full-manual-install-0.3.1.tar.xz
cd nt-legacy
./install.sh --apply win2k     # install, then apply that version
```

`install.sh` creates a backup first and prints its path. It then installs
Plasma styles, colour schemes, window decorations, icons, cursors and
wallpapers. Without `--apply` it only installs and leaves your desktop
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
| `./apply.sh lilac` | NT Legacy Lilac | lilac instead of petrol, after NT's *Lilac* |
| `./apply.sh desert` | NT Legacy Desert | sand and terracotta, after NT's *Desert* |
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
./apply.sh win2k --red        # red cursor instead of white
./apply.sh win2k --font       # bold titlebar font, as in the original
```

`--panel` is what makes the desktop look like the screenshots — see below.

`--font` is deliberately not applied automatically: otherwise your
setting under *Fonts → Window Title* would be overwritten on every run.

### Why the selection colour is not the original navy

Windows 2000 selected with `#0a246a` and Windows 98 with `#000080`. Both are
in this theme — but on the **title bar**, not on the selection, and there the
white title text sits on them at 14:1.

The selection had to give way, and the reason is worth knowing because it
looks like a mistake otherwise. Dolphin paints the label of a selected item
in `QPalette::Text` — black — rather than in `HighlightedText`
(`kstandarditemlistwidget.cpp`, `normalTextColorRole()`; only while the mouse
button is down does it use the highlighted colour). Under Breeze that never
shows, because its selection is a light tint. The **Windows** widget style
this theme sets fills the whole rectangle with the selection colour, so file
names ended up black on navy: 1.5:1, unreadable, and no setting in the theme
reaches it.

One colour, two text colours, and only the colour is ours to choose. It now
sits where both contrasts are equal — luminance 0.179, which is **4.58:1
against black and against white**. Darker makes file names illegible, lighter
makes menu entries illegible; there is no gain on one side without a loss on
the other. `build.py` refuses to build a palette that falls below 4.5:1.

## Automatic day/night switching

Plasma 6 can switch between a light and a dark global theme by time of day
(*System Settings → Colors & Themes → Global Theme → Day/Night switching*).
It uses two keys, `DefaultLightLookAndFeel` and `DefaultDarkLookAndFeel`.

`apply.sh` fills both with the pair belonging to the palette you picked —
`./apply.sh desert` registers *Desert* as the light and *Desert Night* as the
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

**One panel per screen.** Plasma's own template creates a single panel and
lets Plasma decide which screen it lands on. With two monitors that is a
coin toss, and the screen that loses has no task bar at all — reported as
"switching back to NT Legacy leaves me without a task bar", and because the
choice can differ from run to run it looked like a fault in one particular
palette. The layout now loops over `screenCount`. From the second screen on
it checks that the panel really ended up there and removes it if not; the
first one is never removed, since one panel too few is exactly the bug being
fixed.

The layout no longer sets the panel's length. It used to, against a panel
that supposedly came out 34 pixels wide — but `panel.length` reports the
width of the panel's *contents*, not the width it is drawn at. Measured in
the lab VM: with no length set at all, `lengthMode` is `fill`, and the
screenshot shows the panel across the full width while `length` reports 388
of 1280. Setting `minimumLength` and `maximumLength` to the same value also
pins the panel to a fixed size, which is wrong the moment it sits on a
second screen of a different width.

The panel carries the **Application Menu** (`org.kde.plasma.kicker`), not
the Application Launcher Plasma defaults to. The launcher is a window with
a search field and a grid of tiles; the menu is the cascading one Windows
95 through 2000 had, and it is the only one of the two that fits this
shape language. Its sidebar — favourites at the top, log out, restart and
shut down at the bottom — is drawn from the Plasma style and therefore
carries the panel colour, so it reads as a strip rather than as part of
the entry list.

If the [NT Task Manager](https://github.com/huppiflupp/nt-taskmanager) is
installed, `--panel` also pins it to the task bar. That happens here and
not in the theme package: the package goes to everyone, and a pinned
launcher for a program that is not installed is a dead entry. A shell
script can check; Plasma's scripting language cannot — it has no file
access.

## The look — separate and optional

`appearance.sh` changes settings of **other programs**: a full-width status
bar in Dolphin, PCManFM-Qt as the file manager, its icon theme, and
Konsole's default profile.

This is deliberately not part of `install.sh`. Someone trying out a theme
does not expect their Dolphin configuration to be different afterwards.

```bash
./appearance.sh --show      # what would be set, and why
./appearance.sh             # apply
./appearance.sh --revert    # full revert
```

### Konsole

`install.sh` only *places* a Konsole profile and five colour schemes in
`~/.local/share/konsole/` — one scheme per palette, built from the same
colour values as everything else. Nothing is switched over until you run
`appearance.sh`; your own profiles stay and remain selectable in the menu.

The profile uses **Liberation Mono**, which is metrically Courier
compatible and present on practically every Linux. A theme should not
depend on a font it does not ship: if it is missing, Qt substitutes one
silently and the terminal simply does not look like NT.

`apply.sh` keeps the profile's colour scheme in step with the palette you
pick. There are five schemes rather than ten because the accent colours
are identical between the day and night version of a palette — the
terminal is dark either way, as it was under NT.

But `apply.sh` is not how most people switch themes. Doing it in *System
Settings → Colours and Themes → Global Theme* never calls it, and Konsole
has no "follow the system" switch of its own: a terminal's colours live in
its **profile**, and Plasma does not touch profiles.

So `appearance.sh` installs a small systemd user unit,
`nt-legacy-konsole.path`. It watches the two files Plasma writes when a
global theme is applied and runs `konsole-follow.sh`, which looks the
theme up in `konsole-variants.tsv` and rewrites that one line in the
profile. No resident process; nothing else is touched. If the new theme is
not one of ours, the profile is left exactly as it is — switching to
Breeze should not drag your terminal along.

One limit remains, and it cannot be worked around: **an already open
Konsole window keeps its colours.** Konsole reads the profile when a
session is created, and there is no way from outside to make it read the
file again. The next new window or tab is correct.

```bash
./konsole-follow.sh --show   # what it would do, without doing it
systemctl --user status nt-legacy-konsole.path
```

### Kate, and an editor closer to Notepad

`appearance.sh` switches off Kate's **mini map**. What looks like a very wide
scroll bar on the right edge is not one: it is a shrunken rendering of the
whole document that KTextEditor draws *instead of* the scroll bar, 60
pixels wide against the widget style's 16. It comes from Kate, not from the
theme, and no colour scheme or widget style makes it narrower.

Kate is a development environment — project bar, LSP client, sessions, a
terminal. For writing down a note none of that helps. If **FeatherPad** is
installed, `appearance.sh` also makes it the default for plain text: a Qt
program with a real menu bar and nothing else, which is as close to Notepad
as this desktop gets, and which the Windows widget style draws completely.
The GTK candidates (Mousepad, L3afpad, gedit) draw themselves and stay
foreign bodies.

```bash
sudo dnf install featherpad     # or: sudo pacman -S featherpad
./appearance.sh
```

Nothing is installed for you, and if FeatherPad is absent the entry is
simply left out — a default application that does not exist produces an
error message instead of an editor.

Both programs read their settings at start up and write them back when they
exit, so close them before running `appearance.sh`.

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
./install-grub.sh --revert       # remove, restore what was there before
./install-plymouth.sh --revert
```

Both back up what they change before changing it, and `--revert`
restores it byte for byte — verified in a VM by comparing checksums of
`/etc/default/grub` before and after.

What can go wrong is limited: if GRUB cannot find its theme it draws its
plain text menu, and if Plymouth cannot find its theme you simply see the
usual boot messages. The machine boots either way.

Tested on two distributions — Fedora and EndeavourOS — because the
scripts take different paths on each: `/boot/grub2` vs `/boot/grub`,
`grub2-mkconfig` vs `grub-mkconfig`, `dracut` vs `dracut-rebuild`.

Four things worth knowing:

- **Plymouth needs its script module.** On Fedora and Nobara it is a
  separate package: `sudo dnf install plymouth-plugin-script`. Debian and
  Arch ship it inside `plymouth`. Without it, Plymouth silently falls back
  to the text theme — the most common reason a boot splash "just doesn't
  show up". `install-plymouth.sh` checks for it and stops.
- **`GRUB_TERMINAL=console` beats everything.** If that line is in
  `/etc/default/grub`, the menu stays in text mode and the theme is
  installed but invisible. The script warns you if it finds it.
- **Arch and EndeavourOS need `splash` on the kernel command line.**
  Fedora sets `rhgb quiet` out of the box, Arch sets neither — and
  without it Plymouth shows nothing at all, however well the theme is
  installed. `install-plymouth.sh` checks and tells you exactly what to
  add where.
- **With an encrypted disk, test the passphrase prompt** before you
  reboot. It is the one thing that can leave you staring at a screen that
  waits for input without showing what for:

  ```bash
  sudo plymouth ask-for-password --prompt "Test"
  ```

  The theme draws prompt and one box per typed character; both were
  verified in a VM.

## Icons after switching themes

`install.sh` writes the icon theme you had before into the `Inherits`
line of the NT Legacy icon set. Distribution-specific icons — a
distribution logo in an updater, for instance — then keep their picture
instead of turning into a blank page, while everything else still comes
from NT Legacy, which sits first in that line. The trade-off is honest:
at those few spots two visual languages meet. A blank page is worse.

If an icon does turn blank anyway, it is usually the icon cache rather
than the theme: it remembers that a name could *not* be resolved.
`install.sh` and `apply.sh` clear it since 0.2.13, but if you switched
by hand:

```bash
rm -f ~/.cache/icon-cache.kcache
```

Then log out and back in.

## Other icon sets — optional, not included

NT Legacy ships its own icon set (*NTLegacyIcons*, plus a night version),
so you do not need anything else. Two well-known retro sets can be
fetched on top of it, each installed as a separate theme you can pick in
System Settings:

```bash
./fetch-icons.sh            # Chicago95      -> "NT Legacy"      (default)
./fetch-icons.sh se98       # SE98           -> "NT Legacy (SE98)"
./fetch-icons.sh both       # both
./build.py                  # only needed if you build from source
```

**Chicago95** is the Windows 95 set the first version of this theme was
built on. **SE98** aims at Windows 98 SE / ME / 2000 — a little newer
than NT 4.0, but far larger: roughly 6,400 names against our 229. If a
program shows a Breeze icon somewhere, SE98 most likely has one for it.
It needs about 15 MB of image data, but around 164 MB on disk, because
it is built from some 32,000 symlinks.

Both are adapted while they are fetched: missing `Directories=` entries
are filled in, non-standard contexts (`Stock`, `Tools`) are replaced,
`-symbolic` aliases are generated so Plasma stops mixing flat grey
strokes into the pixel art, and the names Dolphin asks for are wired to
the icons that exist. For SE98 the inherit chain is repaired as well: it
shipped `Inherits=…,Breeze`, and no distribution has a directory by that
name — it is `breeze`, lower case — so the fallback went nowhere.

Neither set is **part of any archive here**, and neither may be
redistributed with the theme. Chicago95 has no LICENSE file and the
provenance of its bitmaps is unclear. SE98 does carry a GPL-2.0 file,
but its own README calls the project a *"manual copy-paste fork"* of
Chicago95 containing icons from Faenza and from the *"MicroSoft Memphis
project"* — a licence notice only covers what the person applying it
actually made. Details in `ATTRIBUTION.md`. Installing either one on
your own machine is unproblematic; shipping them would not be.

`fetch-icons.sh` uses the `tools/` directory that comes with the full
package.

## Verifying

```bash
./check.sh            # are all parts present?
./check.sh --system   # also check against the installed system
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
./appearance.sh --revert                       # settings of other programs
./uninstall.sh                                 # remove the theme completely
```

`uninstall.sh` removes both icon sets, the wallpapers, the colour
schemes and the theme's entries in `~/.config/kdedefaults/` — that last
directory is where Plasma keeps the defaults of the global theme you
applied, and leaving NT Legacy's values there would point at files that
are gone.

It resets the configuration to Breeze **first** and deletes the files
**afterwards**. That order matters: if `kwinrc` points at a
deleted Aurorae theme, KWin draws no titlebar at all — no frame, no close
button.

The backups under `~/.local/share/nt-legacy/` are left in place.

## Licence and provenance

GPL-2.0-or-later. The theme contains **no third-party material**: icons,
SVGs, window decoration and cursors are all generated from colour values.
The photographic wallpapers are rendered locally with FLUX.1-schnell
(Apache-2.0). Details in `ATTRIBUTION.md`.
