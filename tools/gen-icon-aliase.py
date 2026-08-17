#!/usr/bin/env python3
"""Legt fehlende Icon-Namen als Verweise auf vorhandene an.

Retro-Icon-Saetze tragen oft GNOME-Namen (view-grid, view-list), waehrend
KDE-Programme freedesktop- oder KDE-eigene Namen anfordern
(view-list-icons, view-list-details). Fehlt ein Name, faellt Plasma auf
Breeze zurueck - flache graue Striche neben 16-Farben-Pixelart.

Das Skript legt fuer jeden fehlenden Namen einen Verweis auf ein
vorhandenes, inhaltlich passendes Icon an. In allen Groessen, in denen
die Quelle existiert.

    ./gen-icon-aliase.py <theme-verzeichnis> [--probe]

Die Zuordnungen sind Handarbeit - welches Icon inhaltlich passt, kann
kein Skript entscheiden.
"""

import argparse
import os
from pathlib import Path

# Ziel -> Liste moeglicher Quellen, erste vorhandene gewinnt.
# Ermittelt aus den Namen, die Dolphin, Kate und die Systemeinstellungen
# tatsaechlich anfordern (per strings aus den Binaerdateien gelesen).
ALIASE = {
    # --- Ansichtsmodi: die auffaelligste Luecke in Dolphins Werkzeugleiste
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
    # (view-sidetree steht weiter oben - ein zweiter Eintrag mit gleichem
    #  Schluessel wuerde den ersten still ueberschreiben)
    "swap-panels":           ["view-refresh", "system-switch-user"],
    "view-refresh":          ["reload", "view-refresh"],
    "view-filter":           ["edit-find", "system-search"],

    # --- Werkzeugleiste und Menue
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

    # --- Kontextmenue
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

    # --- Statusleiste und Zoom
    "zoom-in":               ["viewmag+", "zoom-in"],
    "zoom-out":              ["viewmag-", "zoom-out"],
    "zoom-fit-best":         ["viewmag1", "zoom-original"],
    "zoom-original":         ["viewmag1"],
}


def hat(verz: Path, name: str):
    """Findet ein Icon in allen Groessenverzeichnissen dieses Kontexts."""
    treffer = []
    for gr in sorted(verz.iterdir()):
        if not gr.is_dir():
            continue
        for endung in (".png", ".svg", ".svgz"):
            f = gr / f"{name}{endung}"
            if f.exists():
                treffer.append(f)
                break
    return treffer


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path)
    ap.add_argument("--probe", action="store_true", help="nur berichten")
    args = ap.parse_args()

    if not (args.theme / "index.theme").exists():
        ap.error(f"{args.theme} ist kein Icon-Theme (index.theme fehlt)")

    # In welchen Kontexten suchen wir? actions deckt fast alles ab,
    # places/apps fuer die Ordner- und Programmnamen.
    kontexte = [args.theme / k for k in ("actions", "places", "apps", "status")
                if (args.theme / k).is_dir()]

    angelegt = 0
    ohne_quelle = []

    for ziel, quellen in ALIASE.items():
        # Gibt es das Ziel schon irgendwo?
        if any(hat(k, ziel) for k in kontexte):
            continue

        gefunden = False
        for quelle in quellen:
            for kontext in kontexte:
                treffer = hat(kontext, quelle)
                if not treffer:
                    continue
                for f in treffer:
                    z = f.with_name(f"{ziel}{f.suffix}")
                    if z.exists() or z.is_symlink():
                        continue
                    if not args.probe:
                        z.symlink_to(f.name)
                    angelegt += 1
                gefunden = True
                break
            if gefunden:
                break
        if not gefunden:
            ohne_quelle.append(ziel)

    was = "waeren anzulegen" if args.probe else "angelegt"
    print(f"  {angelegt} Verweise {was}")
    if ohne_quelle:
        print(f"  {len(ohne_quelle)} ohne passende Quelle - bleiben bei Breeze:")
        for z in ohne_quelle:
            print(f"      {z}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
