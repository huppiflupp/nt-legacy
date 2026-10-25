#!/usr/bin/env python3
"""Finds icon names that the system requests and our set does not have.

The counterpart to check-symbolic-trap.py. That one looks for names we
serve WRONGLY; this one looks for names we do NOT serve AT ALL - and
sorts them by how often the system asks for them in the first place.

Where the demand comes from, in this order:

  1. Icon= from all installed .desktop files. These are the
     program icons - every missing one is visible in the application menu.
  2. Strings from the programs and KF6 libraries themselves.
     The same way the mappings in gen-icon-aliases.py
     came about: an icon name sits in the source code as a literal and
     survives compilation.

Both together produce a lot of noise - any string looks
like an icon name. Hence the filter: only what is also in
Breeze counts. Breeze is the set Plasma is developed against; what
has no name there, nobody requests either.

With --compare a second set can be laid alongside. The last
column then says whether it has a template:

    ./missing-icons.py nt-legacy/icons-nt/NTLegacyIcons \\
        --compare nt-legacy/icons/NTLegacySE98

The comparison set is explicitly ONLY a template. Third-party material does
not move into our own set - why is in nt-legacy/ATTRIBUTION.md.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

BREEZE = Path("/usr/share/icons/breeze")

# Where to look for strings. No recursive /usr/bin: that
# takes minutes and brings names from programs nobody has.
BINARIES = [
    "/usr/bin/dolphin", "/usr/bin/plasmashell", "/usr/bin/systemsettings",
    "/usr/bin/kate", "/usr/bin/konsole", "/usr/bin/ark", "/usr/bin/gwenview",
    "/usr/bin/okular", "/usr/bin/kwin_wayland", "/usr/bin/kwin_x11",
    "/usr/bin/kinfocenter", "/usr/bin/kcalc", "/usr/bin/spectacle",
    "/usr/bin/discover", "/usr/bin/kwrite", "/usr/bin/krunner",
]
LIB_PATTERNS = ["libKF6*.so*", "libplasma*.so*", "libkworkspace*.so*",
                "libPlasma*.so*"]
LIB_DIRS = ["/usr/lib64", "/usr/lib", "/usr/lib/x86_64-linux-gnu"]

DESKTOP_DIRS = ["/usr/share/applications", "/usr/local/share/applications"]

# An icon name: lower case, digits and hyphens allowed, no path.
# The length limit keeps out single letters and novels.
NAME = re.compile(rb"[a-z][a-z0-9]{1,40}(?:[-.+][a-z0-9]+){0,6}")


def strings(path: Path, minimum=4):
    """Printable ASCII sequences from a file - like strings(1).

    Done by hand instead of calling binutils: the tool should also run on
    a system on which binutils is not installed.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return
    for hit in re.finditer(rb"[\x20-\x7e]{%d,}" % minimum, raw):
        yield hit.group(0)


def breeze_inventory():
    """Icon name -> context, read from the Breeze tree.

    The context is the directory above the size
    (breeze/actions/22/foo.svg -> actions). It later tells where a
    missing icon belongs in gen-icons.py.
    """
    inventory = {}
    if not BREEZE.is_dir():
        return inventory
    for f in BREEZE.rglob("*"):
        if f.suffix not in (".svg", ".svgz", ".png"):
            continue
        parts = f.relative_to(BREEZE).parts
        if len(parts) < 2:
            continue
        # Breeze stores <context>/<size>/name.svg, sometimes also
        # <context>/<size>/<subfolder>/name.svg.
        inventory.setdefault(f.name.rsplit(".", 1)[0], parts[0])
    return inventory


def own_inventory(theme: Path):
    """All names of a theme, links included.

    A symlink counts as present: for the icon loader it is a
    hit, and that is exactly what matters here.
    """
    names = set()
    for f in theme.rglob("*"):
        if f.is_dir():
            continue
        if f.name.rsplit(".", 1)[-1] not in ("svg", "svgz", "png", "xpm"):
            continue
        names.add(f.name.rsplit(".", 1)[0])
    return names


def demand_from_desktop():
    """Icon= from the installed .desktop files."""
    counter = Counter()
    for loc in DESKTOP_DIRS:
        p = Path(loc)
        if not p.is_dir():
            continue
        for f in p.glob("*.desktop"):
            try:
                for line in f.read_text(errors="replace").splitlines():
                    if line.startswith("Icon="):
                        value = line[5:].strip()
                        # Absolute paths are not theme icons.
                        if value and "/" not in value:
                            counter[value] += 1
                        break
            except OSError:
                continue
    return counter


def demand_from_binaries(files):
    """Compound icon names from programs and libraries.

    Only compound ones, and that is the decisive filter. The
    first attempt took every string that has a name in
    Breeze - at the top were class, node, item, label, flag, user. Those
    are words from source code that Breeze happens to carry as icons
    too; none of them is ever requested.

    A real icon name in program text almost always has a
    hyphen (document-open, view-list-icons, dialog-password). The
    single-word exceptions are program names - okular, kmail, ark - and
    those are in the .desktop files anyway, where they are reliable.
    """
    counter = Counter()
    for path in files:
        seen = set()
        for s in strings(path):
            for m in NAME.finditer(s):
                name = m.group(0).decode()
                if "-" in name:
                    seen.add(name)
        # Count only once per file - otherwise what wins is what sits often
        # in the translation buffer, not what is needed often.
        counter.update(seen)
    return counter


def collect_files():
    files = [Path(b) for b in BINARIES if Path(b).is_file()]
    for loc in LIB_DIRS:
        p = Path(loc)
        if not p.is_dir():
            continue
        for pattern in LIB_PATTERNS:
            for f in p.glob(pattern):
                if f.is_file() and not f.is_symlink():
                    files.append(f)
    return files


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path, help="our own icon set")
    ap.add_argument("--compare", type=Path,
                    help="second set, only as a template hint")
    ap.add_argument("--count", type=int, default=60,
                    help="how many rows (default 60, 0 = all)")
    ap.add_argument("--only-templates", action="store_true",
                    help="only names for which --compare has something")
    args = ap.parse_args()

    if not (args.theme / "index.theme").is_file():
        ap.error(f"{args.theme} is not an icon theme (index.theme missing)")
    if not BREEZE.is_dir():
        print(f"ERROR: {BREEZE} is missing - without Breeze there is no yardstick.",
              file=sys.stderr)
        return 1

    breeze = breeze_inventory()
    own = own_inventory(args.theme)
    compare = own_inventory(args.compare) if args.compare else set()

    files = collect_files()
    counter = demand_from_binaries(files)
    # An entry in the application menu weighs more than a string
    # somewhere in the program: there the missing icon is visible at once.
    for name, n in demand_from_desktop().items():
        counter[name] += 5 * n

    # The filter without which only noise would come out.
    gaps = [(n, z) for n, z in counter.items()
            if n in breeze and n not in own]
    if args.only_templates:
        gaps = [(n, z) for n, z in gaps if n in compare]
    gaps.sort(key=lambda t: (-t[1], t[0]))

    print(f"Files checked: {len(files)} "
          f"({sum(1 for d in files if d.parent.name == 'bin')} programs, "
          f"{sum(1 for d in files if d.parent.name != 'bin')} libraries)")
    print(f"Breeze knows {len(breeze)} names, "
          f"{args.theme.name} has {len(own)}.")
    if args.compare:
        print(f"{args.compare.name} has {len(compare)}.")
    print(f"\nRequested, present in Breeze, missing here: "
          f"{len(gaps)}\n")

    header = f"{'Icon name':<40} {'Context':<12} {'Weight':>7}"
    if args.compare:
        header += "  Template"
    print(header)
    print("-" * len(header))

    for name, weight in (gaps if args.count == 0 else gaps[:args.count]):
        line = f"{name:<40} {breeze[name]:<12} {weight:>7}"
        if args.compare:
            line += "  " + ("yes" if name in compare else "-")
        print(line)

    if args.count and len(gaps) > args.count:
        print(f"\n… and {len(gaps) - args.count} more "
              f"(--count 0 shows all).")

    if args.compare:
        with_tpl = sum(1 for n, _ in gaps if n in compare)
        print(f"\n{args.compare.name} has a template for {with_tpl} of the "
              f"{len(gaps)} gaps.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
