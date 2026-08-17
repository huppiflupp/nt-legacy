#!/usr/bin/env python3
"""Prueft Plasma-Style-SVGs auf fehlende Element-IDs.

Warum es das braucht: Plasma prueft die Existenz eines Zustands-Praefixes,
indem es ausschliesslich nachsieht, ob "<praefix>-center" vorhanden ist.
Fehlt ein Randelement, gibt es weder Absturz noch Warnung - das Element
wird still nicht gezeichnet. Genau diese Fehlerklasse faengt dieses Skript.

    ./lint-plasma-svg.py <theme-verzeichnis> [...]
    ./lint-plasma-svg.py --vergleich <referenz> <theme>

Rueckgabe: 0 = keine Fehler, 1 = Fehler gefunden.
Warnungen allein aendern den Rueckgabewert nicht.
"""

import argparse
import gzip
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# Die acht Randelemente eines 9-Patch. "center" wird getrennt behandelt,
# weil seine Existenz darueber entscheidet, ob Plasma den Praefix ueberhaupt
# als vorhanden ansieht.
RAENDER = ["top", "bottom", "left", "right",
           "topleft", "topright", "bottomleft", "bottomright"]

# IDs, die keine 9-Patch-Teile sind und deshalb nie als Praefix zaehlen.
KEINE_PRAEFIXE = re.compile(
    r"^(hint-|mask-hint-|defs|grid|namedview|path|rect|circle|ellipse|g\d|"
    r"linearGradient|radialGradient|stop|filter|clipPath|use|text|tspan|"
    r"feGaussianBlur|feFlood|feComposite|feColorMatrix|feOffset|feBlend|"
    r"current-color-scheme|layer)"
)

# Die Farbschema-Klassen, die KSvg zur Laufzeit ersetzt.
# Vollstaendig aus dem Breeze-Quellbaum extrahiert, nicht geraten.
FARBKLASSEN = {
    "ColorScheme-Text", "ColorScheme-Background", "ColorScheme-Highlight",
    "ColorScheme-Frame",
    "ColorScheme-ViewText", "ColorScheme-ViewBackground", "ColorScheme-ViewHover",
    "ColorScheme-ViewFocus",
    "ColorScheme-ButtonText", "ColorScheme-ButtonBackground",
    "ColorScheme-ButtonHover", "ColorScheme-ButtonFocus",
    "ColorScheme-NegativeText", "ColorScheme-NeutralText", "ColorScheme-PositiveText",
}


class Befund:
    def __init__(self):
        self.fehler = []
        self.warnungen = []

    def fehler_(self, datei, text):
        self.fehler.append((datei, text))

    def warnung(self, datei, text):
        self.warnungen.append((datei, text))


def svg_lesen(pfad: Path) -> str:
    """Liest .svg und .svgz."""
    roh = pfad.read_bytes()
    if roh[:2] == b"\x1f\x8b":
        roh = gzip.decompress(roh)
    return roh.decode("utf-8", "replace")


def ids_sammeln(text: str):
    """Alle id-Attribute. Bewusst per Regex statt per Parser - kaputtes
    XML soll separat gemeldet werden, nicht das Sammeln verhindern."""
    return set(re.findall(r'\bid="([^"]+)"', text))


def praefixe_ableiten(ids):
    """Leitet aus '<praefix>-center' die vorhandenen Zustaende ab.

    Ein nacktes 'center' bedeutet den leeren Praefix (Standardzustand).
    """
    praefixe = set()
    for i in ids:
        if i == "center":
            praefixe.add("")
        elif i.endswith("-center") and not KEINE_PRAEFIXE.match(i):
            praefixe.add(i[: -len("-center")])
    return praefixe


def datei_pruefen(pfad: Path, befund: Befund, streng: bool, wurzel: Path = None):
    # Relativer Pfad statt blossem Dateinamen: ein Plasma Style enthaelt
    # panel-background.svg bis zu viermal (widgets, opaque, solid,
    # translucent). Ohne Pfad ist eine Meldung nicht zuzuordnen.
    kurz = pfad.relative_to(wurzel).as_posix() if wurzel else pfad.name
    try:
        text = svg_lesen(pfad)
    except Exception as e:
        befund.fehler_(kurz, f"nicht lesbar: {e}")
        return

    # 1. Wohlgeformtes XML
    try:
        ET.fromstring(text)
    except ET.ParseError as e:
        befund.fehler_(kurz, f"kein gueltiges XML: {e}")
        return

    ids = ids_sammeln(text)

    # 2. Vollstaendigkeit der 9-Patch-Saetze
    praefixe = praefixe_ableiten(ids)
    if not praefixe:
        # Nicht jede SVG ist ein Rahmen (arrows.svg, checkmarks.svg ...).
        # Kein Fehler, aber erwaehnenswert wenn ueberhaupt keine IDs da sind.
        if not ids:
            befund.warnung(kurz, "enthaelt keine benannten Elemente")
        return

    for p in sorted(praefixe):
        def da(teil):
            return (f"{p}-{teil}" if p else teil) in ids

        vorhanden = {r for r in RAENDER if da(r)}
        name = p or "(Standardzustand)"

        # Plasma kennt neben dem vollen 9-Patch auch schmalere Formen.
        # Breeze nutzt alle vier - switch.svg ist horizontal, dragger.svg
        # vertikal. Nur wer keiner dieser Formen entspricht, hat ein Loch.
        VOLL       = set(RAENDER)
        HORIZONTAL = {"left", "right"}
        VERTIKAL   = {"top", "bottom"}

        if vorhanden in (VOLL, HORIZONTAL, VERTIKAL, set()):
            continue

        if vorhanden < VOLL and vorhanden > (HORIZONTAL | VERTIKAL):
            fehlend = sorted(VOLL - vorhanden)
            befund.fehler_(
                kurz, f"'{name}': unvollstaendiger 9-Patch, es fehlen "
                      f"{', '.join(fehlend)}")
        elif vorhanden and not (vorhanden <= HORIZONTAL or vorhanden <= VERTIKAL):
            # Mischform, z.B. topleft ohne top und left
            befund.fehler_(
                kurz, f"'{name}': unstimmiger Randsatz - vorhanden sind nur "
                      f"{', '.join(sorted(vorhanden))}")

    # 3. Farbschema-Unterstuetzung
    hat_stylesheet = "current-color-scheme" in ids
    benutzte_klassen = set(re.findall(r'class="([^"]*ColorScheme-[^"]*)"', text))
    einzelklassen = {k for gruppe in benutzte_klassen for k in gruppe.split()}

    if hat_stylesheet:
        # currentColor ist Pflicht - ohne bleibt die feste Farbe stehen
        if einzelklassen and "currentColor" not in text:
            befund.fehler_(
                kurz, "hat ColorScheme-Klassen, aber kein fill/stroke="
                      '"currentColor" - die Farben werden nicht ersetzt')
        unbekannt = {k for k in einzelklassen
                     if k.startswith("ColorScheme-") and k not in FARBKLASSEN}
        for k in sorted(unbekannt):
            befund.warnung(kurz, f"unbekannte Farbklasse '{k}'")
    elif streng and einzelklassen:
        befund.fehler_(
            kurz, "benutzt ColorScheme-Klassen, aber es fehlt das "
                  "<style id=\"current-color-scheme\">-Element")

    # 4. Insets - Plasma-6-Neuzugang, fuer schwebende Panels noetig
    if pfad.name.startswith("panel-background"):
        if not any(i.endswith("-inset") for i in ids):
            befund.warnung(
                kurz, "keine hint-*-inset-Elemente - auf einem schwebenden "
                      "Panel stimmt die Geometrie dann nicht")


def theme_pruefen(verzeichnis: Path, streng: bool):
    befund = Befund()

    if not verzeichnis.is_dir():
        print(f"FEHLER: {verzeichnis} ist kein Verzeichnis", file=sys.stderr)
        return None, None

    # metadata.json
    meta = verzeichnis / "metadata.json"
    # Quellbaeume enthalten oft nur eine Vorlage, aus der der Build die
    # echte metadata.json erzeugt (Breeze: metadata.json.cmake). Das ist
    # kein Fehler - dann laesst sich der Inhalt hier nur nicht pruefen.
    vorlagen = [verzeichnis / n for n in ("metadata.json.cmake", "metadata.json.in")]
    if not meta.exists():
        if any(v.exists() for v in vorlagen):
            befund.warnung(
                "metadata.json",
                "liegt nur als Vorlage vor - Inhalt hier nicht pruefbar, "
                "stattdessen das Bauergebnis pruefen")
        elif (verzeichnis / "metadata.desktop").exists():
            befund.warnung("metadata.desktop",
                           "veraltetes Format - Plasma 6 erwartet metadata.json")
        else:
            befund.fehler_("metadata.json", "fehlt - das Theme wird nicht gefunden")
    else:
        import json
        try:
            d = json.loads(meta.read_text())
        except json.JSONDecodeError as e:
            befund.fehler_("metadata.json", f"kein gueltiges JSON: {e}")
            d = None
        if d is not None:
            kp = d.get("KPlugin", {})
            for feld in ("Id", "Name", "Version"):
                if not kp.get(feld):
                    befund.fehler_("metadata.json", f"KPlugin.{feld} fehlt oder ist leer")
            for feld in ("Description", "License", "Website"):
                if not kp.get(feld):
                    befund.warnung("metadata.json", f"KPlugin.{feld} ist leer")
            for a in kp.get("Authors", []):
                if not a.get("Name"):
                    befund.warnung("metadata.json", "Autor ohne Namen")
            if kp.get("Id") and kp["Id"] != verzeichnis.name:
                befund.warnung(
                    "metadata.json",
                    f"KPlugin.Id '{kp['Id']}' weicht vom Ordnernamen "
                    f"'{verzeichnis.name}' ab (funktioniert, verwirrt aber)")

    dateien = sorted(list(verzeichnis.rglob("*.svg")) + list(verzeichnis.rglob("*.svgz")))
    for f in dateien:
        datei_pruefen(f, befund, streng, verzeichnis)

    return befund, dateien


# Nach Sichtbarkeit im Alltag. Wer bei Null anfaengt, arbeitet diese
# Liste von oben nach unten ab - danach wird ein Theme als eigenstaendig
# wahrgenommen und nicht mehr als "Breeze mit anderem Panel".
PRIORITAET = {
    1: ["widgets/panel-background", "dialogs/background", "widgets/background"],
    2: ["widgets/tooltip", "widgets/listitem", "widgets/viewitem",
        "widgets/button", "widgets/lineedit", "widgets/checkmarks",
        "widgets/radiobutton", "widgets/switch", "widgets/scrollbar",
        "widgets/slider", "widgets/frame", "widgets/toolbar"],
}


def vergleichen(referenz: Path, theme: Path):
    """Zeigt, welche SVGs gegenueber einer Referenz fehlen - nach
    Dringlichkeit sortiert statt als eine lange Liste."""
    def satz(v):
        return {p.relative_to(v).with_suffix("").as_posix()
                for p in list(v.rglob("*.svg")) + list(v.rglob("*.svgz"))}

    r, t = satz(referenz), satz(theme)
    fehlen = r - t
    extra = sorted(t - r)

    # icons/ ist in Plasma 6 abgekuendigt - Tray-Symbole kommen aus dem
    # Icon-Theme. Sie mitzuzaehlen laesst die Luecke groesser aussehen
    # als sie ist.
    veraltet = {f for f in fehlen if f.startswith("icons/")}
    fehlen -= veraltet

    print(f"\nAbgleich gegen {referenz.name}")
    print(f"  Referenz: {len(r)} Dateien · dieses Theme: {len(t)}")
    if veraltet:
        print(f"  ({len(veraltet)} fehlende icons/*.svg ignoriert - "
              f"in Plasma 6 abgekuendigt)")

    if not fehlen:
        print("  Alle relevanten Dateien vorhanden.")
    else:
        print(f"\n  Es fehlen {len(fehlen)} relevante Dateien - "
              f"dort zeigt Plasma Breeze:")
        gemeldet = set()
        for stufe in (1, 2):
            treffer = [f for f in PRIORITAET[stufe] if f in fehlen]
            if treffer:
                titel = {1: "zuerst - ohne diese ist es kein eigener Look",
                         2: "danach - sichtbar in Plasmoids und Popups"}[stufe]
                print(f"\n    Prioritaet {stufe} ({titel}):")
                for f in treffer:
                    print(f"      {f}.svg")
                gemeldet |= set(treffer)
        rest = sorted(fehlen - gemeldet)
        if rest:
            print(f"\n    Prioritaet 3 (Feinschliff, {len(rest)} Dateien):")
            nach_ordner = defaultdict(list)
            for f in rest:
                teile = f.split("/")
                nach_ordner["/".join(teile[:-1]) or "."].append(teile[-1])
            for ordner in sorted(nach_ordner):
                print(f"      {ordner}/: {', '.join(sorted(nach_ordner[ordner]))}")

    if extra:
        print(f"\n  Nicht in der Referenz ({len(extra)}): {', '.join(extra)}")


def main():
    p = argparse.ArgumentParser(
        description="Prueft Plasma-Style-SVGs auf fehlende Element-IDs.")
    p.add_argument("verzeichnis", nargs="+", type=Path,
                   help="Theme-Verzeichnis (das mit der metadata.json)")
    p.add_argument("--vergleich", type=Path, metavar="REFERENZ",
                   help="zusaetzlich gegen ein Referenz-Theme abgleichen")
    p.add_argument("--streng", action="store_true",
                   help="auch fehlendes current-color-scheme als Fehler werten")
    args = p.parse_args()

    gesamt_fehler = 0
    for v in args.verzeichnis:
        print(f"\n=== {v} ===")
        befund, dateien = theme_pruefen(v, args.streng)
        if befund is None:
            gesamt_fehler += 1
            continue

        for datei, text in befund.fehler:
            print(f"  FEHLER   {datei}: {text}")
        for datei, text in befund.warnungen:
            print(f"  Hinweis  {datei}: {text}")

        n_svg = len(dateien) if dateien else 0
        if not befund.fehler and not befund.warnungen:
            print(f"  In Ordnung ({n_svg} SVG-Dateien geprueft).")
        else:
            print(f"  {len(befund.fehler)} Fehler, {len(befund.warnungen)} Hinweise "
                  f"({n_svg} SVG-Dateien geprueft).")
        gesamt_fehler += len(befund.fehler)

        if args.vergleich:
            vergleichen(args.vergleich, v)

    print()
    return 1 if gesamt_fehler else 0


if __name__ == "__main__":
    sys.exit(main())
