#!/usr/bin/env python3
"""Checks Plasma Style SVGs for missing element IDs.

Why this is needed: Plasma checks whether a state prefix exists by
looking only at whether "<prefix>-center" is present. If an edge
element is missing, there is neither a crash nor a warning - the element
is silently not drawn. This script catches exactly that class of bug.

    ./lint-plasma-svg.py <theme-directory> [...]
    ./lint-plasma-svg.py --compare <reference> <theme>

Exit code: 0 = no errors, 1 = errors found.
Warnings alone do not change the exit code.
"""

import argparse
import gzip
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# The eight edge elements of a 9-patch. "center" is handled separately,
# because its existence decides whether Plasma considers the prefix
# present at all.
EDGES = ["top", "bottom", "left", "right",
         "topleft", "topright", "bottomleft", "bottomright"]

# IDs that are not 9-patch parts and therefore never count as a prefix.
NOT_PREFIXES = re.compile(
    r"^(hint-|mask-hint-|defs|grid|namedview|path|rect|circle|ellipse|g\d|"
    r"linearGradient|radialGradient|stop|filter|clipPath|use|text|tspan|"
    r"feGaussianBlur|feFlood|feComposite|feColorMatrix|feOffset|feBlend|"
    r"current-color-scheme|layer)"
)

# The colour scheme classes KSvg replaces at runtime.
# Extracted in full from the Breeze source tree, not guessed.
COLOUR_CLASSES = {
    "ColorScheme-Text", "ColorScheme-Background", "ColorScheme-Highlight",
    "ColorScheme-Frame",
    "ColorScheme-ViewText", "ColorScheme-ViewBackground", "ColorScheme-ViewHover",
    "ColorScheme-ViewFocus",
    "ColorScheme-ButtonText", "ColorScheme-ButtonBackground",
    "ColorScheme-ButtonHover", "ColorScheme-ButtonFocus",
    "ColorScheme-NegativeText", "ColorScheme-NeutralText", "ColorScheme-PositiveText",
}


class Findings:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, file, text):
        self.errors.append((file, text))

    def warning(self, file, text):
        self.warnings.append((file, text))


def read_svg(path: Path) -> str:
    """Reads .svg and .svgz."""
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "replace")


def collect_ids(text: str):
    """All id attributes. Deliberately by regex rather than a parser -
    broken XML should be reported separately, not prevent collecting."""
    return set(re.findall(r'\bid="([^"]+)"', text))


def derive_prefixes(ids):
    """Derives the present states from '<prefix>-center'.

    A bare 'center' means the empty prefix (default state).
    """
    prefixes = set()
    for i in ids:
        if i == "center":
            prefixes.add("")
        elif i.endswith("-center") and not NOT_PREFIXES.match(i):
            prefixes.add(i[: -len("-center")])
    return prefixes


def check_file(path: Path, findings: Findings, strict: bool, root: Path = None):
    # Relative path instead of the bare file name: a Plasma Style contains
    # panel-background.svg up to four times (widgets, opaque, solid,
    # translucent). Without the path a message cannot be traced back.
    short = path.relative_to(root).as_posix() if root else path.name
    try:
        text = read_svg(path)
    except Exception as e:
        findings.error(short, f"not readable: {e}")
        return

    # 1. Well-formed XML
    try:
        ET.fromstring(text)
    except ET.ParseError as e:
        findings.error(short, f"not valid XML: {e}")
        return

    ids = collect_ids(text)

    # 2. Completeness of the 9-patch sets
    prefixes = derive_prefixes(ids)
    if not prefixes:
        # Not every SVG is a frame (arrows.svg, checkmarks.svg ...).
        # Not an error, but worth mentioning if there are no IDs at all.
        if not ids:
            findings.warning(short, "contains no named elements")
        return

    for p in sorted(prefixes):
        def has(part):
            return (f"{p}-{part}" if p else part) in ids

        present = {r for r in EDGES if has(r)}
        name = p or "(default state)"

        # Besides the full 9-patch, Plasma also knows narrower forms.
        # Breeze uses all four - switch.svg is horizontal, dragger.svg
        # vertical. Only something matching none of these forms has a hole.
        FULL       = set(EDGES)
        HORIZONTAL = {"left", "right"}
        VERTICAL   = {"top", "bottom"}

        if present in (FULL, HORIZONTAL, VERTICAL, set()):
            continue

        if present < FULL and present > (HORIZONTAL | VERTICAL):
            missing = sorted(FULL - present)
            findings.error(
                short, f"'{name}': incomplete 9-patch, missing "
                       f"{', '.join(missing)}")
        elif present and not (present <= HORIZONTAL or present <= VERTICAL):
            # Mixed form, e.g. topleft without top and left
            findings.error(
                short, f"'{name}': inconsistent edge set - only present are "
                       f"{', '.join(sorted(present))}")

    # 3. Colour scheme support
    has_stylesheet = "current-color-scheme" in ids
    used_classes = set(re.findall(r'class="([^"]*ColorScheme-[^"]*)"', text))
    single_classes = {k for group in used_classes for k in group.split()}

    if has_stylesheet:
        # currentColor is mandatory - without it the fixed colour stays
        if single_classes and "currentColor" not in text:
            findings.error(
                short, "has ColorScheme classes but no fill/stroke="
                       '"currentColor" - the colours are not replaced')
        unknown = {k for k in single_classes
                   if k.startswith("ColorScheme-") and k not in COLOUR_CLASSES}
        for k in sorted(unknown):
            findings.warning(short, f"unknown colour class '{k}'")
    elif strict and single_classes:
        findings.error(
            short, "uses ColorScheme classes, but the "
                   "<style id=\"current-color-scheme\"> element is missing")

    # 4. Insets - new in Plasma 6, needed for floating panels
    if path.name.startswith("panel-background"):
        if not any(i.endswith("-inset") for i in ids):
            findings.warning(
                short, "no hint-*-inset elements - on a floating "
                       "panel the geometry will then be wrong")


def check_theme(directory: Path, strict: bool):
    findings = Findings()

    if not directory.is_dir():
        print(f"ERROR: {directory} is not a directory", file=sys.stderr)
        return None, None

    # metadata.json
    meta = directory / "metadata.json"
    # Source trees often contain only a template from which the build
    # generates the real metadata.json (Breeze: metadata.json.cmake). That
    # is not an error - the content just cannot be checked here.
    templates = [directory / n for n in ("metadata.json.cmake", "metadata.json.in")]
    if not meta.exists():
        if any(v.exists() for v in templates):
            findings.warning(
                "metadata.json",
                "exists only as a template - content not checkable here, "
                "check the build output instead")
        elif (directory / "metadata.desktop").exists():
            findings.warning("metadata.desktop",
                             "outdated format - Plasma 6 expects metadata.json")
        else:
            findings.error("metadata.json", "missing - the theme will not be found")
    else:
        import json
        try:
            d = json.loads(meta.read_text())
        except json.JSONDecodeError as e:
            findings.error("metadata.json", f"not valid JSON: {e}")
            d = None
        if d is not None:
            kp = d.get("KPlugin", {})
            for field in ("Id", "Name", "Version"):
                if not kp.get(field):
                    findings.error("metadata.json", f"KPlugin.{field} is missing or empty")
            for field in ("Description", "License", "Website"):
                if not kp.get(field):
                    findings.warning("metadata.json", f"KPlugin.{field} is empty")
            for a in kp.get("Authors", []):
                if not a.get("Name"):
                    findings.warning("metadata.json", "author without a name")
            if kp.get("Id") and kp["Id"] != directory.name:
                findings.warning(
                    "metadata.json",
                    f"KPlugin.Id '{kp['Id']}' differs from the folder name "
                    f"'{directory.name}' (works, but confuses)")

    files = sorted(list(directory.rglob("*.svg")) + list(directory.rglob("*.svgz")))
    for f in files:
        check_file(f, findings, strict, directory)

    return findings, files


# By visibility in everyday use. Anyone starting from zero works through
# this list from top to bottom - after that a theme is perceived as its
# own and no longer as "Breeze with a different panel".
PRIORITY = {
    1: ["widgets/panel-background", "dialogs/background", "widgets/background"],
    2: ["widgets/tooltip", "widgets/listitem", "widgets/viewitem",
        "widgets/button", "widgets/lineedit", "widgets/checkmarks",
        "widgets/radiobutton", "widgets/switch", "widgets/scrollbar",
        "widgets/slider", "widgets/frame", "widgets/toolbar"],
}


def compare(reference: Path, theme: Path):
    """Shows which SVGs are missing compared with a reference - sorted
    by urgency instead of as one long list."""
    def file_set(v):
        return {p.relative_to(v).with_suffix("").as_posix()
                for p in list(v.rglob("*.svg")) + list(v.rglob("*.svgz"))}

    r, t = file_set(reference), file_set(theme)
    missing = r - t
    extra = sorted(t - r)

    # icons/ is deprecated in Plasma 6 - tray icons come from the
    # icon theme. Counting them makes the gap look bigger than it is.
    deprecated = {f for f in missing if f.startswith("icons/")}
    missing -= deprecated

    print(f"\nComparison against {reference.name}")
    print(f"  Reference: {len(r)} files · this theme: {len(t)}")
    if deprecated:
        print(f"  ({len(deprecated)} missing icons/*.svg ignored - "
              f"deprecated in Plasma 6)")

    if not missing:
        print("  All relevant files present.")
    else:
        print(f"\n  {len(missing)} relevant files are missing - "
              f"Plasma shows Breeze there:")
        reported = set()
        for level in (1, 2):
            hits = [f for f in PRIORITY[level] if f in missing]
            if hits:
                title = {1: "first - without these it is not a look of its own",
                         2: "next - visible in plasmoids and popups"}[level]
                print(f"\n    Priority {level} ({title}):")
                for f in hits:
                    print(f"      {f}.svg")
                reported |= set(hits)
        rest = sorted(missing - reported)
        if rest:
            print(f"\n    Priority 3 (polish, {len(rest)} files):")
            by_folder = defaultdict(list)
            for f in rest:
                parts = f.split("/")
                by_folder["/".join(parts[:-1]) or "."].append(parts[-1])
            for folder in sorted(by_folder):
                print(f"      {folder}/: {', '.join(sorted(by_folder[folder]))}")

    if extra:
        print(f"\n  Not in the reference ({len(extra)}): {', '.join(extra)}")


def main():
    p = argparse.ArgumentParser(
        description="Checks Plasma Style SVGs for missing element IDs.")
    p.add_argument("directory", nargs="+", type=Path,
                   help="theme directory (the one with the metadata.json)")
    p.add_argument("--compare", type=Path, metavar="REFERENCE",
                   help="additionally compare against a reference theme")
    p.add_argument("--strict", action="store_true",
                   help="also treat a missing current-color-scheme as an error")
    args = p.parse_args()

    total_errors = 0
    for v in args.directory:
        print(f"\n=== {v} ===")
        findings, files = check_theme(v, args.strict)
        if findings is None:
            total_errors += 1
            continue

        for file, text in findings.errors:
            print(f"  ERROR    {file}: {text}")
        for file, text in findings.warnings:
            print(f"  Note     {file}: {text}")

        n_svg = len(files) if files else 0
        if not findings.errors and not findings.warnings:
            print(f"  OK ({n_svg} SVG files checked).")
        else:
            print(f"  {len(findings.errors)} errors, {len(findings.warnings)} notes "
                  f"({n_svg} SVG files checked).")
        total_errors += len(findings.errors)

        if args.compare:
            compare(args.compare, v)

    print()
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
