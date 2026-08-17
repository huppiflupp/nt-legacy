#!/usr/bin/env python3
"""Findet Symbolnamen, die unser Satz abfaengt, ohne sie zu bedienen.

Warum es das gibt: In 0.2.2 zeigte der Lautstaerkeregler im Panel ein
Blatt Papier mit einer Note. Der Grund war nicht, dass ein Symbol fehlte -
der Grund war, dass eines zu viel da war.

Ein unvollstaendiger Satz ist schlechter als gar keiner: Er ueberschreibt
den Rueckfall auf Breeze, ohne Ersatz zu liefern. Zwei Wege fuehren
dahin, beide in der Test-VM mit kiconfinder6 nachgemessen:

  1. Die Suche kuerzt einen unbekannten Namen an den Bindestrichen:
     go-previous-skip -> go-previous. Meist harmlos, weil das kuerzere
     Symbol dasselbe meint.

  2. Sie faellt auf das Klassensymbol <klasse>-x-generic zurueck:

         audio-volume-high  ->  audio-x-generic
         audio-card         ->  audio-x-generic
         image-rotate-left  ->  image-x-generic

     Das ist der gefaehrliche Fall. Ein Blatt Papier mit Note ist die
     richtige Antwort auf eine MP3-Datei und die falsche auf einen
     Lautstaerkeregler - und weil der Treffer aus dem eigenen Satz kommt,
     wird Breeze nie gefragt.

    ./pruefe-symbolfalle.py nt-legacy/icons-nt/NTLegacyIcons
    ./pruefe-symbolfalle.py <verz> --alle    # auch Fall 1 auflisten
"""

import argparse
import sys
from pathlib import Path

BREEZE = Path("/usr/share/icons/breeze")


def namen(verzeichnis: Path) -> set:
    """Alle Symbolnamen eines Themes, ohne Groesse und Endung."""
    return set(mit_kontext(verzeichnis))


def mit_kontext(verzeichnis: Path) -> dict:
    """Symbolname -> Kontext (mimetypes, actions, apps, status, devices).

    Der Kontext trennt die echten Treffer von den harmlosen. Ein Name aus
    mimetypes/ ist ein Dateityp - dass text-css unser text-x-generic
    bekommt, ist genau richtig. Ein Name aus actions/ oder status/ ist
    kein Dateityp: application-exit ist der Menuepunkt "Beenden", und ein
    Blatt Papier ist dort schlicht falsch.
    """
    # Verweise zaehlen mit. Ein Alias ist ein geliefertes Symbol - wer
    # sie ueberspringt, meldet Namen als gekapert, die laengst bedient
    # werden. Genau das ist hier einmal passiert.
    raus = {}
    for p in verzeichnis.rglob("*"):
        if p.suffix.lower() in (".png", ".svg", ".svgz"):
            # .../<kontext>/<groesse>/<name>.png
            teile = p.relative_to(verzeichnis).parts
            raus[p.stem] = teile[0] if len(teile) > 1 else "?"
    return raus


def zeige(titel, treffer, grenze=6):
    print(f"{titel}\n")
    for kurz in sorted(treffer, key=lambda k: -len(treffer[k])):
        lang = sorted(treffer[kurz])
        rest = f"  (+{len(lang) - grenze})" if len(lang) > grenze else ""
        print(f"  {kurz:<24} faengt  {', '.join(lang[:grenze])}{rest}")
    print()


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path)
    ap.add_argument("--alle", action="store_true",
                    help="auch die Kuerzung an Bindestrichen auflisten")
    ap.add_argument("--vergleich", type=Path, default=BREEZE,
                    help=f"Rueckfall-Theme (Vorgabe: {BREEZE})")
    args = ap.parse_args()

    if not args.theme.is_dir():
        sys.exit(f"Kein Verzeichnis: {args.theme}")
    if not args.vergleich.is_dir():
        sys.exit(f"Rueckfall-Theme nicht gefunden: {args.vergleich}")

    unsere = namen(args.theme)
    # Symbolische Doppel interessieren nicht - sie zeigen auf dasselbe
    # Bild wie der Name ohne Zusatz.
    kontexte = {n: k for n, k in mit_kontext(args.vergleich).items()
                if not n.endswith(("-symbolic", "-rtl", "-symbolic-rtl"))}
    fremde = set(kontexte)

    # Fall 2: das Klassensymbol faengt seine ganze Klasse. Dateitypen
    # zaehlen nicht - fuer die ist das Klassensymbol gerade gedacht.
    klassen = {}
    for n in unsere:
        if n.endswith("-x-generic"):
            k = n[:-len("-x-generic")]
            offen = sorted(f for f in fremde
                           if f.startswith(k + "-")
                           and f not in unsere
                           and not f.startswith(k + "-x-")
                           and kontexte[f] != "mimetypes")
            if offen:
                klassen[n] = offen

    # Fall 1: Kuerzung an Bindestrichen.
    kurz_lang = {}
    for kurz in unsere:
        if kurz.endswith("-x-generic"):
            continue
        offen = [f for f in fremde
                 if f.startswith(kurz + "-") and f not in unsere]
        if offen:
            kurz_lang[kurz] = offen

    if klassen:
        zeige(f"{len(klassen)} Klassensymbole fangen Namen ab, die etwas "
              f"anderes bedeuten\n(diese Namen zeigen im Betrieb ein "
              f"falsches Bild):", klassen)

    if args.alle and kurz_lang:
        zeige(f"{len(kurz_lang)} Symbole fangen laengere Namen ab "
              f"(meist eine sinnvolle Verallgemeinerung):", kurz_lang)
    elif kurz_lang:
        print(f"Dazu {len(kurz_lang)} Faelle der Bindestrich-Kuerzung - "
              f"mit --alle auflisten.\n")

    if not klassen:
        print("Keine Klassensymbole fangen fremde Namen ab.")
        return 0

    print("Entweder die fehlenden Namen mitzeichnen oder das "
          "Klassensymbol weglassen,\ndamit der Rueckfall auf Breeze "
          "wieder greift.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
