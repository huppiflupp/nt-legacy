#!/usr/bin/env python3
"""Repairs the index.theme of an icon theme.

Per the freedesktop specification, the icon loader searches only the
directories listed in Directories=. Anything missing there is never
found - the files are present but invisible, and silently fall back to
the inherited theme.

The script adds every directory that contains icons, creates missing
sections and replaces non-standard Contexts.

    ./fix-index-theme.py <theme-directory> [--probe]
"""
import argparse
import re
from pathlib import Path

# The specification knows exactly these Contexts. "Stock" and "Tools"
# date from GTK days; KIconTheme is tolerant, but it is not
# compliant - and Plasma finds nothing under the wrong Context.
CONTEXT_REPLACEMENT = {"Stock": "Actions", "Tools": "Applications"}

def context_for(context):
    return {
        "actions": "Actions", "animations": "Animations", "apps": "Applications",
        "categories": "Categories", "devices": "Devices", "emblems": "Emblems",
        "emotes": "Emotes", "mimes": "MimeTypes", "mimetypes": "MimeTypes",
        "places": "Places", "status": "Status", "panel": "Status",
        "notifications": "Status", "stock": "Actions", "tools": "Applications",
    }.get(context, "Applications")

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path)
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()

    idx = args.theme / "index.theme"
    text = idx.read_text()

    # Read existing sections
    sections = set(re.findall(r"^\[([^\]]+)\]", text, re.M))
    m = re.search(r"^Directories=(.*)$", text, re.M)
    listed = [d.strip() for d in m.group(1).split(",") if d.strip()] if m else []

    # Find all directories with icons
    with_icons = []
    for d in sorted(args.theme.rglob("*")):
        if not d.is_dir():
            continue
        rel = d.relative_to(args.theme).as_posix()
        if "/" not in rel:          # only <context>/<size>
            continue
        if any(f.suffix.lower() in (".png", ".svg", ".svgz")
               for f in d.iterdir() if f.is_file() or f.is_symlink()):
            with_icons.append(rel)

    missing = [d for d in with_icons if d not in listed]
    empty = [d for d in listed if d not in with_icons]

    print(f"  {len(listed)} listed, {len(with_icons)} with icons")
    print(f"  {len(missing)} missing from Directories=, {len(empty)} listed but empty")
    for d in missing:
        n = len([f for f in (args.theme / d).iterdir()
                 if f.suffix.lower() in (".png", ".svg", ".svgz")])
        print(f"    + {d:<24} ({n} icons)")

    if args.probe:
        return 0

    # Rewrite Directories=, drop empty entries
    new_list = sorted(set(listed) - set(empty) | set(missing))
    text = re.sub(r"^Directories=.*$", "Directories=" + ",".join(new_list),
                  text, count=1, flags=re.M)

    # Append missing sections, reactivate commented-out ones
    for d in missing:
        if d in sections:
            continue
        # Look for a commented-out section and revive it
        old = re.search(rf"^#\s*\[{re.escape(d)}\](.*?)(?=^\s*#?\s*\[|\Z)",
                        text, re.M | re.S)
        if old:
            block = "[" + d + "]" + re.sub(r"^#\s?", "", old.group(1), flags=re.M)
            text = text[:old.start()] + block + text[old.end():]
            continue
        size = d.split("/")[-1]
        kind = "Scalable" if not size.isdigit() else "Fixed"
        sz = size if size.isdigit() else "48"
        text += (f"\n[{d}]\nSize={sz}\nContext={context_for(d.split('/')[0])}\n"
                 f"Type={kind}\n")

    # Replace non-standard Contexts
    for old_ctx, new_ctx in CONTEXT_REPLACEMENT.items():
        text = re.sub(rf"^Context={old_ctx}$", f"Context={new_ctx}", text, flags=re.M)

    idx.write_text(text)
    print(f"  index.theme updated ({len(new_list)} directories)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
