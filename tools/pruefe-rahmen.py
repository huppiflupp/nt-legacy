#!/usr/bin/env python3
"""Prueft, ob der Fensterrahmen bei jeder Rahmengroesse dicht ist.

Hintergrund: Stellt der Nutzer in den Systemeinstellungen eine groessere
Rahmengroesse ein, meldet KWin einen breiteren Rand, als die Elemente
left/right/bottom der decoration.svg zeichnen. Die Differenz faellt in
das center-Feld. Ist das transparent, sieht man dort den Desktop - eine
Luecke zwischen Rahmen und Fensterinhalt.

Das Skript nimmt einen Bildschirmfoto-Pfad und die Desktopfarbe und
meldet, ob diese Farbe innerhalb des Fensterrechtecks noch vorkommt.

    ./pruefe-rahmen.py bild.png --zeile 400
"""

import argparse
import subprocess
from pathlib import Path


def zeile_lesen(bild: Path, y: int, breite: int):
    """Liest eine Bildzeile als Liste von (r,g,b)."""
    roh = subprocess.run(
        ["magick", str(bild), "-crop", f"{breite}x1+0+{y}", "+repage",
         "-depth", "8", "txt:-"],
        capture_output=True, text=True, check=True).stdout
    punkte = []
    for z in roh.splitlines()[1:]:
        # Format: "0,0: (192,192,192)  #C0C0C0  srgb(192,192,192)"
        teil = z.split("(", 1)
        if len(teil) < 2:
            continue
        werte = teil[1].split(")", 1)[0].split(",")
        punkte.append(tuple(int(w.strip()) for w in werte[:3]))
    return punkte


def laeufe(punkte, toleranz=6):
    """Fasst gleiche Farben zu Laeufen zusammen: [(farbe, von, bis)]."""
    if not punkte:
        return []
    aus = []
    start, aktuell = 0, punkte[0]
    for i, p in enumerate(punkte[1:], 1):
        if max(abs(a - b) for a, b in zip(p, aktuell)) > toleranz:
            aus.append((aktuell, start, i - 1))
            start, aktuell = i, p
    aus.append((aktuell, start, len(punkte) - 1))
    return aus


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bild", type=Path)
    ap.add_argument("--zeile", type=int, required=True,
                    help="Bildzeile durch die Fenstermitte")
    ap.add_argument("--breite", type=int, default=1920)
    ap.add_argument("--toleranz", type=int, default=6)
    args = ap.parse_args()

    punkte = zeile_lesen(args.bild, args.zeile, args.breite)
    if not punkte:
        print("Zeile nicht lesbar"); return 2
    lf = laeufe(punkte, args.toleranz)

    # Die Desktopfarbe ist die des ersten Laufs - links vom Fenster ist
    # immer Schreibtisch. Robuster als eine fest eingetragene Farbe, denn
    # jede Variante hat einen anderen Hintergrund.
    desktop = lf[0][0]

    # Fenster: vom Ende des ersten bis zum Anfang des letzten
    # Desktop-Laufs.
    desktop_laeufe = [l for l in lf
                      if max(abs(a - b) for a, b in zip(l[0], desktop)) <= args.toleranz]
    if len(desktop_laeufe) < 2:
        print("Kein Fenster auf dieser Zeile erkannt"); return 2
    links, rechts = desktop_laeufe[0][2], desktop_laeufe[-1][1]

    # Nur die Laeufe ZWISCHEN dem ersten und dem letzten sind Luecken.
    # Der erste liegt links vom Fenster, der letzte rechts davon - beide
    # sind normaler Schreibtisch und keine Fehler.
    luecken = desktop_laeufe[1:-1]
    luecken_start = {l[1] for l in luecken}

    print(f"Desktopfarbe {desktop}, Fenster von x={links+1} bis x={rechts-1}")
    print("Farbfolge:")
    for farbe, von, bis in lf:
        if bis < links or von > rechts:
            continue
        n = bis - von + 1
        marke = "   <-- LUECKE: Desktop scheint durch" if von in luecken_start else ""
        print(f"  x={von:4d}..{bis:<4d} {n:3d}px  rgb{farbe}{marke}")
    print()
    if luecken:
        print(f"FEHLER: {len(luecken)} Luecke(n) im Rahmen.")
        return 1
    print("Rahmen dicht.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
