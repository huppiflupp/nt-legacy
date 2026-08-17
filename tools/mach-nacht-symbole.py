#!/usr/bin/env python3
"""Erzeugt aus dem Symbolsatz eine Zweitfassung fuer die Nachtvarianten.

Die Bilder sind in beiden Saetzen dieselben. Es unterscheidet sich genau
eine Zeile: die Rueckfallkette in der index.theme.

Warum das noetig ist: Unser Satz deckt rund 150 Namen ab. Alles andere im
Panel kommt aus dem geerbten Theme - Aktualisierung, Zwischenablage,
Helligkeit, Netzwerk, Akku. Breeze zeichnet diese Symbole in #232629. Auf
dem hellen NT-Panel ist das genau richtig; auf dem dunklen Panel der
Nachtfassungen stand damit Dunkelgrau auf Dunkelgrau. In der Test-VM
gemessen: Symbolfarbe #2C3233 auf Panelgrund #151A1B, ein Kontrast von
1,3:1. Der halbe Systemabschnitt war schlicht nicht zu sehen.

Warum ein zweites Theme und kein zweites Inherits: Ein Icon-Theme hat
genau eine Rueckfallkette; es kann sie nicht je nach Farbschema wechseln.
Und ein Nacht-Theme mit `Inherits=NTLegacyIcons,breeze-dark` hilft nicht -
die Suche geht die Kette tiefenorientiert ab, laeuft also ueber
NTLegacyIcons in dessen eigenes `Inherits=breeze` und findet das helle
Breeze, bevor breeze-dark je an die Reihe kommt.

Warum Kopien und keine Verweise: `install.sh` kopiert mit `cp -r`, und das
schreibt durch Verweise hindurch. Genau daran ist in diesem Projekt schon
einmal ein Symbol zerstoert worden (siehe den Kommentar zu den Verweisen
in gen-icons.py). Der Satz ist 184 KB gross - die doppelte Ablage ist
billiger als die Fehlersuche.

    ./mach-nacht-symbole.py nt-legacy/icons-nt/NTLegacyIcons
    ./mach-nacht-symbole.py <quelle> --ziel <verz>   # sonst <quelle>Nacht
"""

import argparse
import shutil
import sys
from pathlib import Path

# Was in der index.theme ersetzt wird. Die helle Breeze-Fassung fliegt
# raus, breeze-dark kommt davor - breeze bleibt als zweite Ebene stehen,
# weil breeze-dark nicht jeden Namen kennt.
KETTE_HELL = "Inherits=breeze,hicolor"
KETTE_DUNKEL = "Inherits=breeze-dark,breeze,hicolor"

NAME_HELL = "Name=NT Legacy Icons"
NAME_DUNKEL = "Name=NT Legacy Icons Nacht"

KOMMENTAR = (
    "Comment=Symbole im Stil von Windows NT 4.0, vollstaendig erzeugt - "
    "Fassung fuer die dunklen Varianten")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("quelle", type=Path, help="der fertige helle Symbolsatz")
    ap.add_argument("--ziel", type=Path, default=None)
    args = ap.parse_args()

    quelle = args.quelle
    ziel = args.ziel or quelle.with_name(quelle.name + "Nacht")

    if not (quelle / "index.theme").is_file():
        sys.exit(f"Kein Symbolsatz: {quelle} (index.theme fehlt)")
    if ziel.resolve() == quelle.resolve():
        sys.exit("Quelle und Ziel sind dasselbe Verzeichnis.")

    # Vollstaendig neu, damit ein geloeschtes Symbol nicht in der
    # Nachtfassung weiterlebt.
    if ziel.exists():
        shutil.rmtree(ziel)
    # symlinks=True: die Zusatznamen sind Verweise und sollen Verweise
    # bleiben - sonst wuerde aus jedem Alias eine echte Kopie und der Satz
    # doppelt so gross.
    shutil.copytree(quelle, ziel, symlinks=True)

    idx = ziel / "index.theme"
    text = idx.read_text()
    if KETTE_HELL not in text:
        sys.exit(f"Unerwartete index.theme: '{KETTE_HELL}' steht nicht darin. "
                 f"Hat sich gen-icons.py geaendert?")
    text = text.replace(KETTE_HELL, KETTE_DUNKEL)
    text = text.replace(NAME_HELL, NAME_DUNKEL)
    # Den Kommentar ersetzen, nicht anhaengen - sonst stuenden zwei
    # Comment-Zeilen da und KConfig nimmt die erste.
    zeilen = [KOMMENTAR if z.startswith("Comment=") else z
              for z in text.splitlines()]
    idx.write_text("\n".join(zeilen) + "\n")

    dateien = sum(1 for p in ziel.rglob("*") if p.is_file() or p.is_symlink())
    print(f"  {ziel.name}/  ({dateien} Dateien, {KETTE_DUNKEL})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
