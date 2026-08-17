#!/usr/bin/env python3
"""Repariert die index.theme eines Icon-Themes.

Nach freedesktop-Spezifikation durchsucht der Icon-Loader ausschliesslich
die Verzeichnisse, die in Directories= stehen. Was dort fehlt, wird nie
gefunden - die Dateien liegen da, sind aber unsichtbar und fallen still
auf das geerbte Theme zurueck.

Das Skript nimmt jedes Verzeichnis auf, das Icons enthaelt, legt fehlende
Sektionen an und ersetzt nicht-standardisierte Contexts.

    ./fix-index-theme.py <theme-verzeichnis> [--probe]
"""
import argparse
import re
from pathlib import Path

# Die Spezifikation kennt genau diese Contexts. "Stock" und "Tools"
# stammen aus GTK-Zeiten; KIconTheme ist tolerant, aber konform ist es
# nicht - und Plasma findet unter dem falschen Context nichts.
CONTEXT_ERSATZ = {"Stock": "Actions", "Tools": "Applications"}

def context_fuer(kontext):
    return {
        "actions": "Actions", "animations": "Animations", "apps": "Applications",
        "categories": "Categories", "devices": "Devices", "emblems": "Emblems",
        "emotes": "Emotes", "mimes": "MimeTypes", "mimetypes": "MimeTypes",
        "places": "Places", "status": "Status", "panel": "Status",
        "notifications": "Status", "stock": "Actions", "tools": "Applications",
    }.get(kontext, "Applications")

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path)
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()

    idx = args.theme / "index.theme"
    text = idx.read_text()

    # Vorhandene Sektionen einlesen
    sektionen = set(re.findall(r"^\[([^\]]+)\]", text, re.M))
    m = re.search(r"^Directories=(.*)$", text, re.M)
    gelistet = [d.strip() for d in m.group(1).split(",") if d.strip()] if m else []

    # Alle Verzeichnisse mit Icons finden
    mit_icons = []
    for d in sorted(args.theme.rglob("*")):
        if not d.is_dir():
            continue
        rel = d.relative_to(args.theme).as_posix()
        if "/" not in rel:          # nur <kontext>/<groesse>
            continue
        if any(f.suffix.lower() in (".png", ".svg", ".svgz")
               for f in d.iterdir() if f.is_file() or f.is_symlink()):
            mit_icons.append(rel)

    fehlend = [d for d in mit_icons if d not in gelistet]
    leer = [d for d in gelistet if d not in mit_icons]

    print(f"  {len(gelistet)} gelistet, {len(mit_icons)} mit Icons")
    print(f"  {len(fehlend)} fehlen in Directories=, {len(leer)} gelistet aber leer")
    for d in fehlend:
        n = len([f for f in (args.theme / d).iterdir()
                 if f.suffix.lower() in (".png", ".svg", ".svgz")])
        print(f"    + {d:<24} ({n} Icons)")

    if args.probe:
        return 0

    # Directories= neu setzen, leere Eintraege entfernen
    neu_liste = sorted(set(gelistet) - set(leer) | set(fehlend))
    text = re.sub(r"^Directories=.*$", "Directories=" + ",".join(neu_liste),
                  text, count=1, flags=re.M)

    # Fehlende Sektionen anhaengen, auskommentierte reaktivieren
    for d in fehlend:
        if d in sektionen:
            continue
        # Auskommentierte Sektion suchen und wiederbeleben
        aus = re.search(rf"^#\s*\[{re.escape(d)}\](.*?)(?=^\s*#?\s*\[|\Z)",
                        text, re.M | re.S)
        if aus:
            block = "[" + d + "]" + re.sub(r"^#\s?", "", aus.group(1), flags=re.M)
            text = text[:aus.start()] + block + text[aus.end():]
            continue
        groesse = d.split("/")[-1]
        typ = "Scalable" if not groesse.isdigit() else "Fixed"
        gr = groesse if groesse.isdigit() else "48"
        text += (f"\n[{d}]\nSize={gr}\nContext={context_fuer(d.split('/')[0])}\n"
                 f"Type={typ}\n")

    # Nicht-standardisierte Contexts ersetzen
    for alt, neu in CONTEXT_ERSATZ.items():
        text = re.sub(rf"^Context={alt}$", f"Context={neu}", text, flags=re.M)

    idx.write_text(text)
    print(f"  index.theme aktualisiert ({len(neu_liste)} Verzeichnisse)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
