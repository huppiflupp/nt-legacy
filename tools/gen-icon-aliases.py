#!/usr/bin/env python3
"""Creates missing icon names as links to existing ones.

Retro icon sets often carry GNOME names (view-grid, view-list), while
KDE programs request freedesktop or KDE-specific names
(view-list-icons, view-list-details). If a name is missing, Plasma falls
back to Breeze - flat grey strokes next to 16-colour pixel art.

The script creates, for every missing name, a link to an
existing icon with a matching meaning. In every size in which
the source exists.

    ./gen-icon-aliases.py <theme-directory> [--probe]

The mappings are handwork - which icon matches in meaning, no
script can decide.
"""

import argparse
import os
from pathlib import Path

# Target -> list of possible sources, the first one present wins.
# Derived from the names that Dolphin, Kate and System Settings
# actually request (read from the binaries with strings).
ALIASES = {
    # --- View modes: the most noticeable gap in Dolphin's toolbar
    "view-list-icons":       ["view-grid", "view-icon", "view-list"],
    "view-list-details":     ["view-list", "stock_view-details", "view-detailed"],
    "view-list-tree":        ["view-tree", "view-sidetree", "view-list"],
    "view-file-columns":     ["view-column", "view-columns", "view-split-left-right"],
    "view-preview":          ["document-preview", "view-preview-file", "image"],
    "view-sort":             ["view-sort-ascending", "sort_incr", "view-list"],
    "view-sort-ascending":   ["sort_incr", "go-up"],
    "view-sort-descending":  ["sort_decr", "go-down"],
    "view-hidden":           ["view-visible", "view-conceal", "dialog-close"],
    "view-visible":          ["view-preview", "document-preview"],
    "view-group":            ["view-list-details", "view-list", "view-grid"],
    "view-sidetree":         ["view-list-tree", "view-tree", "view-list"],
    "view-choose":           ["view-grid", "configure"],
    "view-mode":             ["view-list-icons", "view-grid", "view-list"],
    "view-properties":       ["document-properties", "configure"],
    "view-related":          ["view-list", "go-next"],
    "view-split-left-right": ["view-column", "view-columns"],
    "view-left-close":       ["dialog-close", "window-close"],
    "view-right-close":      ["dialog-close", "window-close"],
    # (view-sidetree is listed further up - a second entry with the same
    #  key would silently overwrite the first)
    "swap-panels":           ["view-refresh", "system-switch-user"],
    "view-refresh":          ["reload", "view-refresh"],
    "view-filter":           ["edit-find", "system-search"],

    # --- Toolbar and menu
    "application-menu":      ["open-menu", "show-menu", "gtk-index"],
    "show-menu":             ["open-menu", "gtk-index"],
    "configure":             ["preferences-system", "gtk-preferences", "settings"],
    "settings-configure":    ["preferences-system", "gtk-preferences"],
    "configure-shortcuts":   ["preferences-desktop-keyboard", "input-keyboard", "configure"],
    "configure-toolbars":    ["preferences-system", "gtk-preferences"],
    "tab-new":               ["document-new", "list-add"],
    "tab-close":             ["dialog-close", "window-close"],
    "tab-close-other":       ["dialog-close", "window-close"],
    "tab-detach":            ["window-new", "view-split-left-right"],

    # --- Context menu
    "edit-rename":           ["document-edit", "edit-entry", "gtk-edit"],
    "edit-copy-path":        ["edit-copy"],
    "edit-duplicate":        ["edit-copy"],
    "edit-select-invert":    ["edit-select-all"],
    "edit-select-none":      ["edit-select-all"],
    "edit-select-text":      ["edit-select-all"],
    "document-open-folder":  ["folder-open", "folder_open", "document-open"],
    "document-open-with":    ["document-open"],
    "object-locked":         ["lock", "changes-prevent", "emblem-locked"],
    "object-unlocked":       ["unlock", "changes-allow", "emblem-unlocked"],

    # --- Status bar and zoom
    "zoom-in":               ["viewmag+", "zoom-in"],
    "zoom-out":              ["viewmag-", "zoom-out"],
    "zoom-fit-best":         ["viewmag1", "zoom-original"],
    "zoom-original":         ["viewmag1"],
}


def find(directory: Path, name: str):
    """Finds an icon in all size directories of this context."""
    hits = []
    for sz in sorted(directory.iterdir()):
        if not sz.is_dir():
            continue
        for ext in (".png", ".svg", ".svgz"):
            f = sz / f"{name}{ext}"
            if f.exists():
                hits.append(f)
                break
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path)
    ap.add_argument("--probe", action="store_true", help="only report")
    args = ap.parse_args()

    if not (args.theme / "index.theme").exists():
        ap.error(f"{args.theme} is not an icon theme (index.theme missing)")

    # Which contexts do we search? actions covers almost everything,
    # places/apps for the folder and program names.
    contexts = [args.theme / k for k in ("actions", "places", "apps", "status")
                if (args.theme / k).is_dir()]

    created = 0
    without_source = []

    for target, sources in ALIASES.items():
        # Does the target already exist somewhere?
        if any(find(k, target) for k in contexts):
            continue

        found = False
        for source in sources:
            for context in contexts:
                hits = find(context, source)
                if not hits:
                    continue
                for f in hits:
                    z = f.with_name(f"{target}{f.suffix}")
                    if z.exists() or z.is_symlink():
                        continue
                    if not args.probe:
                        z.symlink_to(f.name)
                    created += 1
                found = True
                break
            if found:
                break
        if not found:
            without_source.append(target)

    what = "would be created" if args.probe else "created"
    print(f"  {created} links {what}")
    if without_source:
        print(f"  {len(without_source)} without a matching source - stay with Breeze:")
        for z in without_source:
            print(f"      {z}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
