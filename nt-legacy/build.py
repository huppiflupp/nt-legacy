#!/usr/bin/env python3
"""Baut die Theme-Familie "NT Legacy" aus Farbdefinitionen.

Windows-NT-4.0-Farbwelt fuer Plasma 6, ohne schwarze Flaechen: dunkel
wird nur Text, Rahmen und die aktive Titelleiste. Das haelt das Theme
fuer lange Arbeitssitzungen angenehm und gibt ihm trotzdem mehr
Charakter als Breeze.

NT brachte ab Werk benannte Farbschemata mit ("Appearance Schemes").
Drei davon sind hier nachgebaut: Teal, Lilac und Desert. Sie teilen die
Formensprache und unterscheiden sich nur in den Farben - genau das, was
ein parametrischer Aufbau billig macht.

    ./build.py              # alle Varianten
    ./build.py --nur teal   # eine einzelne
    ./build.py --pruefen    # zusaetzlich linten

Wer etwas aendern will, aendert einen Wert in BASIS oder VARIANTEN und
laesst das Skript neu laufen - nicht 25 Dateien von Hand.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
LAB = HIER.parent


def werkzeug(name):
    """Pfad zu einem Skript aus tools/.

    Zwei Lagen, und beide sind normal: im Arbeitsbaum liegt tools/ neben
    nt-legacy/, im ausgelieferten Archiv als nt-legacy/tools/. Bis 0.2.7
    kannte build.py nur die erste - im Archiv lief es damit ins Leere,
    genauso wie fetch-icons.sh (aus der Community gemeldet: "line 65:
    /nt-legacy/../tools/fix-index-theme.py: No such file or directory").

    Fehlt das Werkzeug in beiden Lagen, ist der Pfad zum Arbeitsbaum die
    ehrlichere Fehlermeldung - dort gehoert es hin.
    """
    for kandidat in (HIER / "tools" / name, LAB / "tools" / name):
        if kandidat.exists():
            return str(kandidat)
    return str(LAB / "tools" / name)


AUTOR = "huppiflupp"
EMAIL = "huppiflupp@users.noreply.github.com"
# Das eigene Repository, nicht die Werkstatt und nicht NiceOS9.
#
# Hier stand bis 0.2.8 NiceOS9-theme - ein anderes Theme desselben
# Autors. Die Adresse steckt in jeder metadata.json und damit im
# Store-Eintrag: wer dort auf die Website klickte, landete beim
# falschen Design.
WEBSITE = "https://github.com/huppiflupp/nt-legacy"
LIZENZ = "GPL-2.0-or-later"
SCHRIFT = "Noto Sans"
VERSION = "0.2.8"

# --------------------------------------------------------------------------
# Farben. Einzige Stelle, an der sie stehen.
# --------------------------------------------------------------------------

BASIS = {
    # Hauptflaeche, helles neutrales Grau.
    #
    # Ein Versuch, sie abzudunkeln, ist wieder zurueckgenommen worden.
    # Der Gedanke war, das Karo der Bildlaufleiste sichtbar zu machen -
    # das zeichnet naemlich der Qt-Stil aus dieser Farbe und einer
    # helleren, nicht unser SVG. In einer Qt-Messung ohne KDE sah das
    # nach 18 -> 28 Prozent aus. In der Testmaschine gemessen waren es
    # 18 -> 20: KDE leitet die helle Farbe nicht auf Weiss ab, sondern
    # auf einen festen Abstand ueber der Flaeche (200 ergibt 240).
    # Damit haette die Aenderung alle hellen Varianten verdunkelt und
    # nichts eingebracht. Auch contrast=10 und eine weisse Fensterfarbe
    # aendern daran nichts - beides nachgemessen.
    "flaeche":      "#d8d8d0",
    "fenster":      "#f0f0e8",   # Fensterinhalt, fast cremeweiss
    "panel":        "#b8c4c4",   # gedaempftes Petrol-Grau
    "kopf_aktiv":   "#176b78",   # Fensterkopf aktiv, dunkles Petrol
    "kopf_inaktiv": "#60777a",   # entsaettigtes Petrol
    "text":         "#202628",   # sehr dunkles Blau-Grau
    "text2":        "#526166",   # Sekundaertext
    "auswahl":      "#287f8c",   # Petrol
    "auswahl_text": "#ffffff",
    "hover":        "#d6a23a",   # NT-artiges Gold
    "warnung":      "#c87922",
    "fehler":       "#a83232",
    "positiv":      "#39734a",
    "desktop":      "#899a9a",
    "hell":         "#f4f4ee",   # 3D-Kante oben/links
    "dunkel":       "#8a8a82",   # 3D-Kante unten/rechts
    "rahmen":       "#202628",   # Aussenrahmen
    # Der helle Punkt im Karo der Bildlaufleisten-Rinne. Bewusst nicht
    # "hell": die Lichtkante ist gedaempft, das Karo braucht Kontrast.
    # Und bewusst nicht #ffffff - die Farben werden ueber ihren Hexwert
    # ersetzt, ein Wert, den auch auswahl_text traegt, wuerde beide
    # zugleich umfaerben.
    "karo":         "#fcfcfa",
}

VARIANTEN = {
    "teal": {
        "kurz": "NTLegacy",
        "anzeige": "NT Legacy",
        "beschreibung": "Petrol und warmes Grau - die Grundfassung",
        "beschreibung_en": "Petrol and warm grey - the base version",
        "farben": {},
    },
    "lilac": {
        "kurz": "NTLegacyLilac",
        "anzeige": "NT Legacy Flieder",
        "beschreibung": "Flieder statt Petrol, nach NTs Schema Lilac",
        "beschreibung_en": "Lilac instead of petrol, after NT's Lilac scheme",
        "farben": {
            "panel":        "#c4bcc8",
            "kopf_aktiv":   "#5c4a78",
            "kopf_inaktiv": "#7a7088",
            "auswahl":      "#6b5590",
            "hover":        "#c8a83a",
            "desktop":      "#9a91a6",
            "text2":        "#5a5266",
        },
    },
    "desert": {
        "kurz": "NTLegacyDesert",
        "anzeige": "NT Legacy Wueste",
        "beschreibung": "Sand und Terrakotta, nach NTs Schema Desert",
        "beschreibung_en": "Sand and terracotta, after NT's Desert scheme",
        "farben": {
            "flaeche":      "#d8d0c0",
            "fenster":      "#f0ece0",
            "panel":        "#c8bca4",
            "kopf_aktiv":   "#7a5c2e",
            "kopf_inaktiv": "#8a7c64",
            "auswahl":      "#96703a",
            "hover":        "#c87922",
            "desktop":      "#a89878",
            "text2":        "#6a5c46",
            "hell":         "#f4f0e6",
            "karo":         "#fcfaf2",
            "dunkel":       "#8a8272",
        },
    },
    # Windows 98: das klassische Systemgrau #C0C0C0 mit dem
    # marineblauen Titelbalken. Die 16-Farben-VGA-Palette von damals -
    # deshalb keine Zwischentoene, sondern die reinen Werte.
    "win98": {
        "kurz": "NTLegacyWin98",
        "anzeige": "NT Legacy 98",
        "beschreibung": "Systemgrau und Marineblau - Windows 98",
        "beschreibung_en": "System grey and navy blue - Windows 98",
        "farben": {
            "flaeche":      "#c0c0c0",
            "fenster":      "#ffffff",
            "panel":        "#c0c0c0",
            "kopf_aktiv":   "#000080",   # das Marineblau
            "kopf_inaktiv": "#808080",
            "text":         "#000000",
            "text2":        "#404040",
            "auswahl":      "#000080",
            "hover":        "#dcdcdc",
            "warnung":      "#808000",
            "fehler":       "#800000",
            "positiv":      "#008000",
            "desktop":      "#008080",   # das Teal des Standard-Desktops
            "hell":         "#ffffff",
            "karo":         "#ffffff",
            "dunkel":       "#808080",
            "rahmen":       "#000000",
        },
    },
    # Windows 2000: dieselbe Formensprache, aber weichere Toene und der
    # charakteristische Farbverlauf im Titelbalken. Den Verlauf koennen
    # wir mit Volltonflaechen nicht nachbauen - stattdessen der mittlere
    # Ton, der dem Gesamteindruck am naechsten kommt.
    "win2k": {
        "kurz": "NTLegacyWin2k",
        "anzeige": "NT Legacy 2000",
        "beschreibung": "Weicheres Grau, Blauverlauf - Windows 2000",
        "beschreibung_en": "Softer grey, blue gradient - Windows 2000",
        "farben": {
            "flaeche":      "#d4d0c8",
            "fenster":      "#ffffff",
            "panel":        "#d4d0c8",
            "kopf_aktiv":   "#0a246a",
            "kopf_inaktiv": "#808080",
            "text":         "#000000",
            "text2":        "#4a4a4a",
            "auswahl":      "#0a246a",
            "hover":        "#316ac5",
            "warnung":      "#c87922",
            "fehler":       "#a83232",
            "positiv":      "#39734a",
            "desktop":      "#3a6ea5",
            "hell":         "#ffffff",
            "karo":         "#ffffff",
            "dunkel":       "#808080",
            "rahmen":       "#000000",
        },
    },
}

# --------------------------------------------------------------------------
# Nachtfassungen
#
# Die Vorgabe fuer die hellen Varianten lautete: keine schwarzen Flaechen,
# dunkel wird nur Text, Rahmen und die aktive Titelleiste. Fuer die Nacht
# kehrt sich das um - aber der Gedanke dahinter bleibt: auch hier kein
# Schwarz, sondern dunkles Blaugrau. Reines Schwarz neben hellem Text
# erzeugt harte Kanten, die bei langer Nutzung anstrengen.
#
# Der 3D-Bevel dreht sich mit: oben/links wird ein aufgehelltes Grau,
# unten/rechts fast schwarz. Ohne das saehen die Rahmen umgekehrt
# beleuchtet aus und die Flaechen wirkten eingedrueckt statt erhaben.
#
# Die Akzente - Petrol, Flieder, Sand und das NT-Gold - bleiben
# unveraendert. Sie tragen den Charakter, nicht die Flaechen.
NACHT_BASIS = {
    "flaeche":      "#2a3234",
    "fenster":      "#1e2628",
    "panel":        "#232b2d",
    "kopf_inaktiv": "#3c4648",
    "text":         "#dae0e0",
    "text2":        "#94a2a4",
    "auswahl_text": "#ffffff",
    "desktop":      "#1a2224",
    "hell":         "#4a5456",   # 3D-Kante oben/links, aufgehellt
    "dunkel":       "#0e1416",   # unten/rechts, fast schwarz
    "rahmen":       "#0a1012",
    # Im Dunkeln war das Karo schon vorher gut zu sehen - dieser Wert
    # ist derselbe, den die Nachtfassungen bisher ueber "hell" bekamen.
    "karo":         "#4a5456",
}

for _k, _v in [("teal", {}), ("win98", {}), ("win2k", {}),
               ("lilac", {"panel": "#2b2833", "kopf_inaktiv": "#443e52",
                          "desktop": "#1e1a26", "text2": "#9a92a6"}),
               ("desert", {"flaeche": "#32302a", "fenster": "#26241e",
                           "panel": "#2b2822", "kopf_inaktiv": "#4a4438",
                           "desktop": "#221f1a", "text2": "#a49a86",
                           "hell": "#544e42", "karo": "#544e42",
                           "dunkel": "#16130e"})]:
    VARIANTEN[f"{_k}-nacht"] = {
        "kurz": VARIANTEN[_k]["kurz"] + "Nacht",
        "anzeige": VARIANTEN[_k]["anzeige"] + " Nacht",
        "beschreibung": VARIANTEN[_k]["beschreibung"].split(" - ")[0].split(", nach")[0]
                        + " als Nachtfassung - dunkle Flaechen, gleiche Akzente",
        "beschreibung_en": VARIANTEN[_k]["beschreibung_en"].split(" - ")[0]
                           .split(", after")[0]
                           + " as a night version - dark surfaces, same accents",
        # Akzentfarben der hellen Fassung uebernehmen, Flaechen ersetzen
        "farben": {**VARIANTEN[_k]["farben"], **NACHT_BASIS, **_v},
    }


def palette(variante):
    return {**BASIS, **VARIANTEN[variante]["farben"]}


def ids(variante):
    """Die Kennungen einer Variante.

    Der Farbschema-Name ist der DATEINAME ohne Endung, nicht das
    Name=-Feld - ein Farbschema "NT Legacy" liefe in contents/defaults
    ins Leere.

    Die Kennung steht in VARIANTEN und wird nicht aus dem Schluessel
    abgeleitet: aus "teal-nacht" wuerde sonst "NTLegacyTeal-nacht".
    """
    kurz = VARIANTEN[variante]["kurz"]
    endung = "" if variante == "teal" else f"-{variante}"
    return {
        "style":     "nt-legacy" + endung,
        "schema":    kurz,
        "aurorae":   kurz,
        "lnf":       "com.github.huppiflupp.nt-legacy" + endung,
        "wallpaper": "ntlegacy" + endung.replace("-", "-"),
        # Suffix _cursors wie bei breeze_cursors. Ohne ihn landen
        # Icon- und Zeigerthema beide unter ~/.local/share/icons/NTLegacy
        # und ihre index.theme-Dateien ueberschreiben sich gegenseitig -
        # danach findet Plasma keine Icons mehr.
        "cursor":    kurz + "_cursors",
        # Zwei Symbolsaetze mit denselben Bildern, aber verschiedener
        # Rueckfallkette.
        #
        # Unser Satz deckt 146 Namen ab; alles andere im Panel kommt aus
        # dem geerbten Theme - Aktualisierung, Zwischenablage,
        # Helligkeit, Netzwerk, Akku. Breeze zeichnet die in #232629.
        # Auf dem hellen NT-Panel ist das richtig, auf dem dunklen der
        # Nachtfassungen stand damit Dunkelgrau auf Dunkelgrau: gemessen
        # #2C3233 auf #151A1B, also 1,3:1. In der Test-VM war der halbe
        # Systemabschnitt schlicht nicht zu sehen.
        #
        # Die Nachtfassungen erben deshalb von breeze-dark. Die Bilder
        # sind in beiden Saetzen dieselben - nur die Kette dahinter
        # unterscheidet sich. Ein zweites Theme statt eines geaenderten
        # Inherits, weil ein Icon-Theme seine Kette nicht je nach
        # Farbschema wechseln kann.
        "icons":     "NTLegacyIcons" + ("Nacht" if variante.endswith("-nacht") else ""),
    }


def rgb(hexwert):
    h = hexwert.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def schreibe(pfad: Path, inhalt: str, still=False):
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(inhalt)
    if not still:
        print(f"  {pfad.relative_to(HIER)}")


# --------------------------------------------------------------------------

def farbschema(p, anzeige):
    """Die .colors-Datei - wirkt auf Qt-Apps UND die Shell.

    Hier entsteht der eigentliche Charakter. Der Plasma Style faerbt nur
    die Shell; alles andere kommt von hier.
    """
    gruppen = {
        "Colors:Window":        (p["flaeche"], p["text"]),
        "Colors:Button":        (p["flaeche"], p["text"]),
        "Colors:View":          (p["fenster"], p["text"]),
        "Colors:Selection":     (p["auswahl"], p["auswahl_text"]),
        "Colors:Tooltip":       (p["fenster"], p["text"]),
        "Colors:Complementary": (p["panel"],   p["text"]),
        "Colors:Header":        (p["flaeche"], p["text"]),
    }
    z = ["[General]", f"ColorScheme={anzeige}", f"Name={anzeige}",
         "shadeSortColumn=true", "", "[KDE]", "contrast=4", ""]

    for gruppe, (bg, fg) in gruppen.items():
        alt = p["auswahl"] if gruppe == "Colors:Selection" else p["fenster"]
        z += [f"[{gruppe}]",
              f"BackgroundNormal={rgb(bg)}",
              f"BackgroundAlternate={rgb(alt)}",
              f"ForegroundNormal={rgb(fg)}",
              f"ForegroundInactive={rgb(p['text2'])}",
              f"ForegroundActive={rgb(p['auswahl'])}",
              f"ForegroundLink={rgb(p['auswahl'])}",
              f"ForegroundVisited={rgb(p['kopf_inaktiv'])}",
              f"ForegroundNegative={rgb(p['fehler'])}",
              f"ForegroundNeutral={rgb(p['warnung'])}",
              f"ForegroundPositive={rgb(p['positiv'])}",
              f"DecorationFocus={rgb(p['auswahl'])}",
              f"DecorationHover={rgb(p['hover'])}", ""]

    # Ohne diese Gruppe sehen inaktive Fenster-Kopfzeilen aus wie aktive -
    # der Unterschied verschwindet genau dort, wo er gebraucht wird.
    z += ["[Colors:Header][Inactive]",
          f"BackgroundNormal={rgb(p['flaeche'])}",
          f"BackgroundAlternate={rgb(p['fenster'])}",
          f"ForegroundNormal={rgb(p['text2'])}",
          f"ForegroundInactive={rgb(p['text2'])}",
          f"ForegroundActive={rgb(p['kopf_inaktiv'])}",
          f"ForegroundLink={rgb(p['kopf_inaktiv'])}",
          f"ForegroundVisited={rgb(p['kopf_inaktiv'])}",
          f"ForegroundNegative={rgb(p['fehler'])}",
          f"ForegroundNeutral={rgb(p['warnung'])}",
          f"ForegroundPositive={rgb(p['positiv'])}",
          f"DecorationFocus={rgb(p['kopf_inaktiv'])}",
          f"DecorationHover={rgb(p['hover'])}", ""]

    z += ["[WM]",
          f"activeBackground={rgb(p['kopf_aktiv'])}",
          f"activeForeground={rgb(p['auswahl_text'])}",
          f"inactiveBackground={rgb(p['kopf_inaktiv'])}",
          f"inactiveForeground={rgb(p['fenster'])}",
          f"activeBlend={rgb(p['auswahl'])}",
          f"inactiveBlend={rgb(p['kopf_inaktiv'])}", "",
          "[ColorEffects:Disabled]", "ChangeSelectionColor=true",
          f"Color={rgb(p['dunkel'])}", "ColorAmount=0", "ColorEffect=0",
          "ContrastAmount=0.65", "ContrastEffect=1",
          "IntensityAmount=0.1", "IntensityEffect=2", "",
          "[ColorEffects:Inactive]", "ChangeSelectionColor=true",
          f"Color={rgb(p['text2'])}", "ColorAmount=0.025", "ColorEffect=2",
          "ContrastAmount=0.1", "ContrastEffect=2", "Enable=false",
          "IntensityAmount=0", "IntensityEffect=0", ""]
    return "\n".join(z)


def _kanaele(hexwert):
    h = hexwert.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def luminanz(hexwert):
    """Relative Helligkeit nach WCAG - Grundlage jeder Kontrastrechnung."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in _kanaele(hexwert))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontrast(a, b):
    """Kontrastverhaeltnis zweier Farben, 1:1 bis 21:1."""
    la, lb = luminanz(a), luminanz(b)
    hell, dunkel = max(la, lb), min(la, lb)
    return (hell + 0.05) / (dunkel + 0.05)


def _hsl(hexwert):
    r, g, b = (c / 255 for c in _kanaele(hexwert))
    hoch, tief = max(r, g, b), min(r, g, b)
    l = (hoch + tief) / 2
    if hoch == tief:
        return 0.0, 0.0, l
    d = hoch - tief
    s = d / (2 - hoch - tief) if l > 0.5 else d / (hoch + tief)
    if hoch == r:
        h = ((g - b) / d) % 6
    elif hoch == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h / 6, s, l


def _hex(h, s, l):
    def kanal(p, q, t):
        t %= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p
    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r, g, b = kanal(p, q, h + 1 / 3), kanal(p, q, h), kanal(p, q, h - 1 / 3)
    return "#" + "".join(f"{round(c * 255):02x}" for c in (r, g, b))


def fuer_dunkel(hexwert, grund, ziel):
    """Hebt eine Farbe an, bis sie auf 'grund' das Kontrastziel erreicht.

    Der Grund, warum es diese Funktion gibt: Die Akzentfarben des Themes
    sind fuer HELLE Flaechen gemacht - dunkles Marineblau auf Systemgrau.
    Im Terminal sitzen sie auf dunklem Grund, und dort verschwinden sie.
    Der erste Anlauf hatte genau dieses Problem: #000080 auf #1e2628 ist
    ein Kontrast von 1,1:1, also praktisch unsichtbar.

    Angehoben wird die Helligkeit in HSL, nicht Richtung Weiss gemischt.
    Mischen entsaettigt: aus Petrol wuerde Graublau. So bleibt der
    Farbton erhalten, und die Farbwelt bleibt erkennbar.

    4,5:1 ist die WCAG-Schwelle fuer Fliesstext, 7:1 die strengere. Sie
    hier anzuwenden ist kein Formalismus - Terminalausgabe IST Fliesstext,
    und sie wird stundenlang gelesen.
    """
    h, s, l = _hsl(hexwert)
    # Untergrenze fuer die Saettigung: sonst wird aus einem ohnehin
    # blassen Ton beim Aufhellen ein weisser Fleck ohne Farbe.
    #
    # Nur fuer Farben, die ueberhaupt einen Ton haben. Sonst bekaeme das
    # fast neutrale Schwarz des Themes beim Anheben einen Blaustich und
    # aus Color0 wuerde ein blaugrauer Fleck statt eines Graus.
    if s > 0.12:
        s = max(s, 0.35)
    for schritt in range(101):
        kandidat = _hex(h, s, min(1.0, l + schritt / 100))
        if kontrast(kandidat, grund) >= ziel:
            return kandidat
    return "#ffffff"


def konsole_schema(p_nacht, p, anzeige):
    """Ein Konsole-Farbschema je Farbwelt.

    Grund und Text kommen aus der NACHTfassung, auch fuer die hellen
    Varianten: ein Terminal ist dunkel, das war unter NT nicht anders.
    Die acht ANSI-Farben kommen aus den Akzenten der Farbwelt - und die
    sind zwischen Tag und Nacht identisch (siehe NACHT_BASIS oben).
    Deshalb gibt es fuenf Schemata und nicht zehn: Tag- und Nachtfassung
    derselben Farbwelt ergaeben Zeichen fuer Zeichen dieselbe Datei.

    Color0 bis Color7 sind die klassische Reihe: schwarz, rot, gruen,
    gelb, blau, magenta, cyan, weiss. Diese Bedeutungen sind nicht
    verhandelbar - `ls` faerbt Verzeichnisse blau und Verweise cyan, und
    wer dort die Akzentfarbe des Themes einsetzt, macht aus einem
    Verweis einen goldenen Fleck. Deshalb nur dort eine Themefarbe, wo
    sie auch semantisch passt: rot, gruen, gelb und blau. Magenta und
    Cyan behalten ihren Ton.

    Jede Farbe wird anschliessend so weit angehoben, dass sie auf dem
    Terminalgrund lesbar ist - siehe fuer_dunkel().
    """
    grund = p_nacht["fenster"]
    reihe = [
        # Schwarz bleibt dunkel, muss aber vom Grund unterscheidbar sein:
        # manche Programme setzen damit abgeblendeten Text. Bei 1,1:1
        # waere er schlicht weg.
        ("Color0", p_nacht["dunkel"], 2.2),
        ("Color1", p["fehler"], 4.5),
        ("Color2", p["positiv"], 4.5),
        ("Color3", p["warnung"], 4.5),
        ("Color4", p["kopf_aktiv"], 4.5),
        ("Color5", "#800080", 4.5),   # VGA-Magenta, nur angehoben
        ("Color6", "#008080", 4.5),   # VGA-Cyan
        ("Color7", p_nacht["text"], 4.5),
    ]
    teile = [
        f"[Background]\nColor={rgb(grund)}\n",
        f"[BackgroundIntense]\nColor={rgb(p_nacht['flaeche'])}\n",
        f"[Foreground]\nColor={rgb(p_nacht['text'])}\n",
        f"[ForegroundIntense]\nColor={rgb(fuer_dunkel(p_nacht['text'], grund, 10))}\n",
    ]
    for name, wert, ziel in reihe:
        teile.append(f"[{name}]\nColor={rgb(fuer_dunkel(wert, grund, ziel))}\n")
        # Die Intense-Reihe eine Stufe heller. 7:1 ist die strengere
        # WCAG-Schwelle; bei Schwarz waere sie sinnlos, dort reicht es,
        # dass der Ton ueberhaupt als Grau erkennbar wird.
        teile.append(f"[{name}Intense]\n"
                     f"Color={rgb(fuer_dunkel(wert, grund, 4.5 if ziel < 4.5 else 7))}\n")
    teile.append(
        "[General]\n"
        "Blur=false\n"
        "ColorRandomization=false\n"
        f"Description={anzeige}\n"
        "Opacity=1\n"
        "Wallpaper=\n"
    )
    return "\n".join(teile)


def konsole_profil(schema):
    """Das Konsole-Profil - eines fuer alle Fassungen.

    Zehn Profile waeren zehn Eintraege im Auswahlmenue, die sich nur in
    einer Zeile unterscheiden. Stattdessen ein Profil, dessen
    ColorScheme apply.sh auf die gewaehlte Farbwelt umstellt.

    Liberation Mono, nicht die huebschere Programmiererschrift: sie ist
    metrisch Courier-kompatibel und auf praktisch jedem Linux vorhanden.
    Ein Theme darf keine Schrift voraussetzen, die es nicht mitbringt -
    fehlt sie, ersetzt Qt sie stillschweigend, und der Nutzer sieht ein
    Terminal, das nicht nach NT aussieht, ohne zu wissen warum.
    """
    return (
        "[Appearance]\n"
        f"ColorScheme={schema}\n"
        "Font=Liberation Mono,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1\n"
        "\n"
        "[General]\n"
        "Name=NT Legacy\n"
        "Parent=FALLBACK/\n"
        "TerminalColumns=90\n"
        "TerminalRows=28\n"
        "\n"
        "[Scrolling]\n"
        "HistoryMode=2\n"
        "ScrollBarPosition=1\n"
    )


# Beschreibung englisch, Uebersetzung daneben.
#
# KPlugin kennt lokalisierte Felder: "Description" ist die Vorgabe,
# "Description[de]" greift auf einem deutschen System. Bis 0.2.7 stand
# in "Description" Deutsch - in den Systemeinstellungen las jeder
# englischsprachige Nutzer also deutsche Saetze unter englischen Namen.
# Dieselbe Ursache wie beim Abmeldedialog, nur an anderer Stelle.
#
# "Category" ist ersatzlos weggefallen: der Schluessel stand mit leerer
# Zeichenkette darin. Ein Feld ohne Wert ist nicht dasselbe wie kein
# Feld - KPackage traegt es als leere Kategorie ein, statt gar keine
# anzunehmen.
def metadata_style(k, anzeige, beschreibung, beschreibung_en):
    return json.dumps({
        "KPlugin": {
            "Authors": [{"Name": AUTOR, "Email": EMAIL}],
            "Description": beschreibung_en,
            "Description[de]": beschreibung,
            "EnabledByDefault": True,
            "Id": k["style"],
            "License": LIZENZ,
            "Name": anzeige,
            "Version": VERSION,
            "Website": WEBSITE,
        },
        "X-Plasma-API": "5.0",
    }, indent=4, ensure_ascii=False) + "\n"


def metadata_lnf(k, anzeige, beschreibung, beschreibung_en):
    return json.dumps({
        "KPackageStructure": "Plasma/LookAndFeel",
        "KPlugin": {
            "Authors": [{"Name": AUTOR, "Email": EMAIL}],
            "Description": beschreibung_en,
            "Description[de]": beschreibung,
            "Id": k["lnf"],
            "License": LIZENZ,
            "Name": anzeige,
            "Version": VERSION,
            "Website": WEBSITE,
        },
        "Keywords": "Desktop;Workspace;Appearance;Look and Feel;",
        "X-Plasma-APIVersion": "2",
    }, indent=4, ensure_ascii=False) + "\n"


def defaults(k):
    """contents/defaults - schaltet die Ebenen zusammen.

    Der Zeiger wird gesetzt, weil er mitgeliefert wird. Ein Verweis auf
    ein fehlendes Zeigerthema waere schaedlich - der Nutzer bekaeme den
    Standardzeiger und es saehe nach einem Fehler aus.

    Achtung: Das Icon-Theme wirkt ueber diesen Weg NICHT zuverlaessig -
    install.sh setzt es zusaetzlich hart. Plasma Style, Farbschema und
    Anwendungsstil greifen dagegen wie erwartet. Gemessen in der Test-VM.

    Der Name muss trotzdem stimmen. Hier stand lange NTLegacy - das ist
    das optionale Chicago95-Set, das gar nicht ausgeliefert wird.
    Ausgeliefert wird NTLegacyIcons. Wer das Design ueber die
    Systemeinstellungen wechselte statt ueber apply.sh, bekam damit ein
    Icon-Theme gesetzt, das es auf seinem Rechner nicht gibt - und sah
    weiter die alten Symbole. Auf dem Hostsystem belegt.
    """
    return f"""[kdeglobals][KDE]
widgetStyle=Windows

[kdeglobals][General]
ColorScheme={k['schema']}

[kdeglobals][Icons]
Theme={k['icons']}

[kcminputrc][Mouse]
cursorTheme=NTLegacy_cursors

[Wallpaper]
Image={k['wallpaper']}

[plasmarc][Theme]
name={k['style']}

[kdeglobals][WM]
activeFont={SCHRIFT},10,-1,5,75,0,0,0,0,0

[ksplashrc][KSplash]
Theme={k['lnf']}
Engine=KSplashQML

[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae
theme=__aurorae__svg__{k['aurorae']}
"""


def layout_js(k):
    """Panelvorgabe: fest unten, schmal, nicht schwebend - wie NT 4.0.

    ACHTUNG: Ersetzt beim Anwenden die Panels des Nutzers. install.sh
    sichert deshalb vorher, und Plasma fragt zusaetzlich nach (die
    Checkbox ist vorab nicht angehakt).
    """
    return f"""// {k['style']} - Panelvorgabe
var alle = panels();
for (var i = 0; i < alle.length; i++) {{
    alle[i].remove();
}}

var panel = new Panel;
panel.location = "bottom";
panel.height = 30;
panel.floating = false;
panel.hiding = "none";
panel.alignment = "left";

panel.addWidget("org.kde.plasma.kickoff");
panel.addWidget("org.kde.plasma.icontasks");
panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.kde.plasma.digitalclock");

var flaechen = desktops();
for (var j = 0; j < flaechen.length; j++) {{
    flaechen[j].wallpaperPlugin = "org.kde.image";
    flaechen[j].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    flaechen[j].writeConfig("Image", "{k['wallpaper']}");
    flaechen[j].reloadConfig();
}}
"""


def wallpaper_svg(p, breite=3840, hoehe=2160):
    """Hintergrund im NT-Stil: ruhige Flaeche, kein Fotorealismus."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{breite}" height="{hoehe}"
     viewBox="0 0 {breite} {hoehe}">
  <defs>
    <linearGradient id="grund" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{p['kopf_inaktiv']}"/>
      <stop offset="1" stop-color="{p['desktop']}"/>
    </linearGradient>
    <pattern id="raster" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="1" height="1" fill="{p['fenster']}" opacity="0.045"/>
    </pattern>
  </defs>
  <rect width="{breite}" height="{hoehe}" fill="url(#grund)"/>
  <rect width="{breite}" height="{hoehe}" fill="url(#raster)"/>
</svg>
"""


def vorschau_svg(p, k, breite=600, hoehe=337):
    """Das Bild, das in der Design-Auswahl erscheint.

    Ohne preview.png steht dort ein graues Rechteck - der haeufigste
    Grund, warum ein gutes Theme im Store uebersehen wird. Gezeigt wird
    ein Miniatur-Desktop: Hintergrund, ein Fenster mit Titelleiste und
    das Panel. Das reicht, um die Farbwelt zu erkennen.
    """
    th = 22          # Titelleiste
    ph = 20          # Panel
    fx, fy = 95, 60  # Fensterposition
    fw, fh = 380, 210
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{breite}" height="{hoehe}"
     viewBox="0 0 {breite} {hoehe}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{p['kopf_inaktiv']}"/>
      <stop offset="1" stop-color="{p['desktop']}"/>
    </linearGradient>
  </defs>
  <rect width="{breite}" height="{hoehe}" fill="url(#g)"/>

  <!-- Fenster -->
  <rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="{p['rahmen']}"/>
  <rect x="{fx+1}" y="{fy+1}" width="{fw-2}" height="{fh-2}" fill="{p['flaeche']}"/>
  <rect x="{fx+1}" y="{fy+1}" width="{fw-2}" height="{th}" fill="{p['kopf_aktiv']}"/>
  <rect x="{fx+6}" y="{fy+7}" width="90" height="6" fill="{p['auswahl_text']}" opacity="0.9"/>
  <g fill="{p['flaeche']}">
    <rect x="{fx+fw-52}" y="{fy+5}" width="13" height="11"/>
    <rect x="{fx+fw-37}" y="{fy+5}" width="13" height="11"/>
    <rect x="{fx+fw-22}" y="{fy+5}" width="13" height="11"/>
  </g>
  <!-- Inhaltsflaeche mit Auswahlbalken und Akzent -->
  <rect x="{fx+8}" y="{fy+th+9}" width="{fw-18}" height="{fh-th-20}" fill="{p['fenster']}"/>
  <rect x="{fx+12}" y="{fy+th+15}" width="{fw-28}" height="12" fill="{p['auswahl']}"/>
  <rect x="{fx+16}" y="{fy+th+18}" width="60" height="6" fill="{p['auswahl_text']}"/>
  <rect x="{fx+16}" y="{fy+th+36}" width="110" height="6" fill="{p['text']}"/>
  <rect x="{fx+16}" y="{fy+th+50}" width="80" height="6" fill="{p['text2']}"/>
  <rect x="{fx+16}" y="{fy+th+64}" width="46" height="12" fill="{p['hover']}"/>

  <!-- Panel: eine helle Linie oben, wie bei NT -->
  <rect x="0" y="{hoehe-ph}" width="{breite}" height="{ph}" fill="{p['panel']}"/>
  <rect x="0" y="{hoehe-ph}" width="{breite}" height="1" fill="{p['hell']}"/>
  <rect x="6" y="{hoehe-ph+4}" width="34" height="9" fill="{p['flaeche']}"/>
  <rect x="46" y="{hoehe-ph+4}" width="52" height="9" fill="{p['flaeche']}"/>
  <rect x="{breite-40}" y="{hoehe-ph+5}" width="30" height="6" fill="{p['text2']}"/>
</svg>
"""


def splash_qml(p, anzeige):
    """Startbildschirm. Ohne diesen bleibt beim Wechsel von einem anderen
    Theme dessen Splash stehen - mitten im NT-Look ein Breeze-Bildschirm.

    Laeuft in einem sehr fruehen Sitzungszustand: nur QtQuick verwenden,
    keine Plasma-Komponenten.
    """
    return f"""import QtQuick

Rectangle {{
    id: root
    color: "{p['desktop']}"
    property int stage

    // NT zeigte beim Start ein schlichtes Feld mit Produktnamen.
    Rectangle {{
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.5, 460)
        height: 150
        color: "{p['flaeche']}"
        border.color: "{p['rahmen']}"
        border.width: 1

        Rectangle {{
            anchors {{ left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }}
            height: 24
            color: "{p['kopf_aktiv']}"
            Text {{
                anchors {{ left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }}
                text: "{anzeige}"
                color: "{p['auswahl_text']}"
                font.bold: true
                font.pixelSize: 13
            }}
        }}

        // Fortschritt: stage laeuft von 1 bis 6
        Rectangle {{
            anchors {{ left: parent.left; right: parent.right; bottom: parent.bottom
                       margins: 14 }}
            height: 14
            color: "{p['fenster']}"
            border.color: "{p['dunkel']}"
            border.width: 1

            Rectangle {{
                anchors {{ left: parent.left; top: parent.top; bottom: parent.bottom
                           margins: 2 }}
                width: Math.max(0, (parent.width - 4) * Math.min(root.stage, 6) / 6)
                color: "{p['auswahl']}"
                Behavior on width {{ NumberAnimation {{ duration: 180 }} }}
            }}
        }}
    }}
}}
"""


def logout_qml(p):
    """Abmeldedialog. Ohne diesen sieht der Abmeldebildschirm Breeze-artig
    aus - der sichtbarste Bruch im Gesamteindruck.

    Die Beschriftungen kommen aus Plasmas eigenem Uebersetzungskatalog.

    Hier standen bis 0.2.7 deutsche Zeichenketten in i18n(). Ein Theme
    bringt aber keinen eigenen Katalog mit - i18n() gibt dann die msgid
    unveraendert zurueck. Auf einem englischen System stand der Dialog
    also deutsch da, waehrend alles andere englisch blieb; genau so aus
    der Community gemeldet (cubanismo, KDE 6.6.5).

    Mit i18nd auf plasma_lookandfeel_org.kde.lookandfeel greifen die
    Uebersetzungen, die jede Plasma-Installation ohnehin mitbringt: die
    msgids sind dieselben wie im Abmeldedialog von Breeze. Fehlt der
    Katalog, bleibt die englische msgid stehen - der richtige Rueckfall.
    Das '&' darin markiert den Tastenkuerzel-Buchstaben; PlasmaComponents
    wertet es in diesem Dialog nicht aus, deshalb faellt es weg."""
    return f"""import QtQuick
import org.kde.plasma.components as PlasmaComponents

Item {{
    id: root
    signal logoutRequested()
    signal haltRequested()
    signal suspendRequested(int spdMethod)
    signal rebootRequested()
    signal rebootRequested2(int opt)
    signal cancelRequested()
    signal lockScreenRequested()

    property string mode
    property var currentAction

    // Uebersetzung aus Plasmas Katalog, ohne den Kuerzel-Marker.
    function nt_i18n(text) {{
        return i18nd("plasma_lookandfeel_org.kde.lookandfeel", text)
                   .replace("&", "")
    }}

    Rectangle {{
        anchors.fill: parent
        color: "{p['rahmen']}"
        opacity: 0.55
        MouseArea {{ anchors.fill: parent; onClicked: root.cancelRequested() }}
    }}

    Rectangle {{
        anchors.centerIn: parent
        width: 340
        height: 150
        color: "{p['flaeche']}"
        border.color: "{p['rahmen']}"
        border.width: 1

        Rectangle {{
            anchors {{ left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }}
            height: 22
            color: "{p['kopf_aktiv']}"
            Text {{
                anchors {{ left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }}
                text: root.nt_i18n("&Shut Down")
                color: "{p['auswahl_text']}"
                font.bold: true
            }}
        }}

        Row {{
            anchors.centerIn: parent
            spacing: 10
            PlasmaComponents.Button {{
                text: root.nt_i18n("&Log Out"); onClicked: root.logoutRequested()
            }}
            PlasmaComponents.Button {{
                text: root.nt_i18n("&Restart"); onClicked: root.rebootRequested()
            }}
            PlasmaComponents.Button {{
                text: root.nt_i18n("&Shut Down"); onClicked: root.haltRequested()
            }}
        }}

        PlasmaComponents.Button {{
            anchors {{ bottom: parent.bottom; horizontalCenter: parent.horizontalCenter
                       bottomMargin: 10 }}
            text: root.nt_i18n("&Cancel")
            onClicked: root.cancelRequested()
        }}
    }}
}}
"""


def plasmarc():
    return """[Wallpaper]
defaultWallpaperTheme=Next
defaultFileSuffix=.png
defaultWidth=1920
defaultHeight=1080

[AdaptiveTransparency]
enabled=false
"""


# --------------------------------------------------------------------------

def baue(variante, pruefen=False):
    v = VARIANTEN[variante]
    k = ids(variante)
    p = palette(variante)
    anzeige, beschreibung = v["anzeige"], v["beschreibung"]
    beschreibung_en = v["beschreibung_en"]

    print(f"\n=== {anzeige} ({variante}) ===")

    style = HIER / "desktoptheme" / k["style"]
    schreibe(style / "metadata.json", metadata_style(k, anzeige, beschreibung, beschreibung_en), still=True)
    schreibe(style / "plasmarc", plasmarc(), still=True)
    # Bewusst KEINE colors-Datei im Plasma-Stil.
    #
    # Liegt dort eine, gewinnt sie gegen das Farbschema des Nutzers: Die
    # Shell zeigt dann die Theme-Farben, egal was in kdeglobals steht.
    # Gemessen in der Test-VM am Anwendungsstarter, Farbschema Desert bei
    # Plasma-Stil Teal:
    #
    #   mit colors-Datei    Flaeche #D8D8D0  (Theme-Farbe, Teal)
    #   ohne colors-Datei   Flaeche #D8D0C0  (Farbschema, Desert)
    #
    # Damit erreichten weder ein Farbschemawechsel noch die Akzentfarbe
    # des Nutzers die Shell. Breeze liefert aus demselben Grund keine.
    #
    # Die Farben gehen dadurch nicht verloren - sie stehen im Farbschema
    # color-schemes/<Variante>.colors, und apply.sh setzt beides zusammen.

    r = subprocess.run(
        [sys.executable, werkzeug("gen-plasma-svg.py"),
         "--alle", "-o", str(style), "--palette", "nt-legacy",
         "--aussenrahmen", "1", "--rahmen", "1", "--stil", "bevel"],
        capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return False

    # Der Generator kennt nur die Grundpalette. Die Variantenfarben
    # werden hier nachgezogen - Suchen und Ersetzen ueber die erzeugten
    # Dateien ist einfacher, als dem Generator ein Palettenformat
    # beizubringen, und das Ergebnis ist identisch.
    ersetzungen = {BASIS[key]: p[key] for key in p
                   if key in BASIS and BASIS[key] != p[key]}
    if ersetzungen:
        for datei in style.rglob("*.svg"):
            s = datei.read_text()
            for alt, neu in ersetzungen.items():
                s = s.replace(alt, neu)
            datei.write_text(s)
    print(f"  desktoptheme/{k['style']}/  ({len(list(style.rglob('*.svg')))} SVGs)")

    schreibe(HIER / "color-schemes" / f"{k['schema']}.colors",
             farbschema(p, anzeige), still=True)
    print(f"  color-schemes/{k['schema']}.colors")

    # Konsole-Farbschema - nur einmal je Farbwelt, an der hellen Fassung.
    # Siehe konsole_schema(): Tag und Nacht ergaeben dieselbe Datei.
    if not variante.endswith("-nacht"):
        nacht = f"{variante}-nacht"
        if nacht in VARIANTEN:
            schreibe(HIER / "konsole" / f"{k['schema']}.colorscheme",
                     konsole_schema(palette(nacht), p, anzeige), still=True)
            print(f"  konsole/{k['schema']}.colorscheme")

    r = subprocess.run(
        [sys.executable, werkzeug("gen-aurorae.py"),
         "--name", k["aurorae"], "--anzeige", anzeige,
         "-o", str(HIER / "aurorae"), "--autor", AUTOR,
         "--lizenz", LIZENZ, "--version", VERSION,
         "--button", "18", "--titelhoehe", "24"],
        capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return False
    deko = HIER / "aurorae" / k["aurorae"]
    if ersetzungen:
        for datei in deko.glob("*.svg"):
            s = datei.read_text()
            for alt, neu in ersetzungen.items():
                s = s.replace(alt, neu)
            datei.write_text(s)
    print(f"  aurorae/{k['aurorae']}/")

    # ── Hintergruende ────────────────────────────────────────────────────
    #
    # Zwei Pakete je Variante, und die Aufteilung hat einen Grund.
    #
    # Das Hauptpaket ist das, auf das contents/defaults zeigt. Dort liegt
    # die Landschaft - ein 4K-Bild, das nicht aus Farbwerten entsteht,
    # sondern aus einem Bildmodell. Es kommt ueber
    # tools/mach-hintergruende.py ins Repository und wird hier NICHT
    # angefasst: ein Neubau des Themes dauert Sekunden, ein Neubau der
    # Bilder Stunden.
    #
    # Die erzeugte Verlaufsflaeche hat ihr eigenes Paket. Sie ist 95 KB
    # gross und braucht kein Bildmodell - wer das Theme aus dem
    # Quelltext baut, hat damit auch ohne die Bilder einen passenden
    # Hintergrund. Und wer die schlichte Flaeche der Landschaft vorzieht,
    # findet sie weiterhin in der Auswahl.
    def flaechenpaket(kennung, name):
        p_wp = HIER / "wallpapers" / kennung
        schreibe(p_wp / "metadata.json", json.dumps({
            "KPlugin": {"Authors": [{"Name": AUTOR}], "Id": kennung,
                        "License": LIZENZ, "Name": name}},
            indent=4, ensure_ascii=False) + "\n", still=True)
        svg = p_wp / "contents" / "images" / "3840x2160.svg"
        schreibe(svg, wallpaper_svg(p), still=True)
        return subprocess.run(["magick", "-background", "none", str(svg),
                               str(svg.with_suffix(".png"))],
                              capture_output=True, text=True).returncode == 0

    ok = flaechenpaket(k["wallpaper"] + "-flaeche", anzeige + " (Flaeche)")
    print(f"  wallpapers/{k['wallpaper']}-flaeche/"
          + ("" if ok else "   (PNG uebersprungen)"))

    # Liegt keine Landschaft im Hauptpaket, springt die Flaeche ein -
    # sonst zeigte das Global Theme auf ein leeres Paket.
    wp = HIER / "wallpapers" / k["wallpaper"]
    bilder = list((wp / "contents" / "images").glob("*.jpg")) \
        if (wp / "contents" / "images").is_dir() else []
    if bilder:
        print(f"  wallpapers/{k['wallpaper']}/   "
              f"(Landschaft, {bilder[0].stat().st_size // 1024} KB - beibehalten)")
    else:
        flaechenpaket(k["wallpaper"], anzeige)
        print(f"  wallpapers/{k['wallpaper']}/   "
              f"(keine Landschaft vorhanden, Flaeche eingesetzt)")

    lnf = HIER / "look-and-feel" / k["lnf"]
    schreibe(lnf / "metadata.json", metadata_lnf(k, anzeige, beschreibung, beschreibung_en), still=True)
    schreibe(lnf / "contents" / "defaults", defaults(k), still=True)
    schreibe(lnf / "contents" / "layouts" / "org.kde.plasma.desktop-layout.js",
             layout_js(k), still=True)

    schreibe(lnf / "contents" / "splash" / "Splash.qml",
             splash_qml(p, anzeige), still=True)
    schreibe(lnf / "contents" / "logout" / "Logout.qml", logout_qml(p), still=True)

    # Vorschaubilder fuer die Design-Auswahl.
    #
    # Nur erzeugen, wenn noch keine da sind: tools/gen-vorschau.sh
    # ersetzt sie durch echte Bildschirmfotos aus der Test-VM, und die
    # wuerde ein Neubau sonst jedes Mal durch die schematische Fassung
    # ueberschreiben. Wer sie neu will, loescht sie vorher.
    vs = lnf / "contents" / "previews"
    if (vs / "preview.png").exists():
        print(f"  look-and-feel/{k['lnf']}/  (Vorschau beibehalten)")
        return True
    svg_v = vs / "preview.svg"
    schreibe(svg_v, vorschau_svg(p, k), still=True)
    # 600x337 wie Breeze - die Kachel im Auswahldialog ist 16:9.
    # Bei 400x250 (16:10) wird das Bild beschnitten.
    for datei, groesse in [("preview.png", "600x337"),
                           ("fullscreenpreview.jpg", "1920x1080"),
                           ("lockscreen.png", "600x337"),
                           ("splash.png", "600x337")]:
        subprocess.run(["magick", "-background", "none", str(svg_v),
                        "-resize", groesse + "!", str(vs / datei)],
                       capture_output=True)
    svg_v.unlink(missing_ok=True)
    print(f"  look-and-feel/{k['lnf']}/  (mit Vorschau)")

    if pruefen:
        subprocess.run([sys.executable, werkzeug("lint-plasma-svg.py"),
                        str(style)])
    return True


def main():
    ap = argparse.ArgumentParser(description="Baut die NT-Legacy-Familie.")
    ap.add_argument("--nur", choices=sorted(VARIANTEN), help="nur eine Variante")
    ap.add_argument("--pruefen", action="store_true", help="danach linten")
    args = ap.parse_args()

    print(f"NT Legacy {VERSION}")
    welche = [args.nur] if args.nur else list(VARIANTEN)
    for v in welche:
        if not baue(v, args.pruefen):
            return 1

    # Das Konsole-Profil, eines fuer alle. Die Vorgabe zeigt auf die
    # Grundfassung; apply.sh stellt die Zeile auf die gewaehlte Farbwelt
    # um, sobald anmutung.sh das Profil aktiviert hat.
    schreibe(HIER / "konsole" / "NT Legacy.profile",
             konsole_profil(VARIANTEN["teal"]["kurz"]))

    # Zeiger einmal fuer alle Varianten. Sie unterscheiden sich nur in
    # weiss und rot - je Farbwelt ein eigenes Thema waere Ballast im
    # Auswahldialog, ohne dass man einen Unterschied saehe.
    print("\nMauszeiger:")
    for zname, fuell, anz in [
        ("NTLegacy_cursors", "#ffffff", "NT Legacy"),
        ("NTLegacyRot_cursors", "#c03028", "NT Legacy (roter Zeiger)"),
    ]:
        r = subprocess.run(
            [sys.executable, werkzeug("gen-cursor.py"),
             "-o", str(HIER / "cursors"), "--name", zname,
             "--anzeige", anz, "--fuellung", fuell],
            capture_output=True, text=True)
        print(r.stdout.rstrip() if r.returncode == 0
              else "  uebersprungen: " + (r.stderr.strip().splitlines() or ["?"])[0])

    icons = HIER / "icons" / "NTLegacy"
    if icons.is_dir():
        r = subprocess.run(
            [sys.executable, werkzeug("gen-symbolic-aliase.py"),
             str(icons)], capture_output=True, text=True)
        zeile = r.stdout.strip().splitlines()
        print(f"\nSymbolische Aliase: {zeile[0] if zeile else '—'}")

    # Die Nachtfassung des Symbolsatzes. Reine Ableitung aus dem hellen
    # Satz - dieselben Bilder, nur breeze-dark als Rueckfall. Deshalb
    # steht sie nicht im Repo, sondern entsteht bei jedem Bau neu.
    hell = HIER / "icons-nt" / "NTLegacyIcons"
    if hell.is_dir():
        r = subprocess.run(
            [sys.executable, werkzeug("mach-nacht-symbole.py"),
             str(hell)], capture_output=True, text=True)
        print("\nSymbole fuer die Nachtfassungen:")
        print(r.stdout.rstrip() if r.returncode == 0
              else "  FEHLER: " + (r.stderr.strip().splitlines() or ["?"])[-1])

    print(f"\nFertig ({len(welche)} Varianten). Installieren: ./install.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
