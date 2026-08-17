#!/usr/bin/env python3
"""Erzeugt Plasma-Style-SVGs aus Parametern statt aus Handarbeit.

Eine Plasma-SVG ist keine Zeichnung, sondern ein Atlas: alle Zustaende
eines Widgets liegen nebeneinander im selben Koordinatenraum, und Plasma
schneidet sie ueber Element-IDs heraus. Ein Button braucht so schnell
40 exakt benannte Objekte - und ein Tippfehler in einer ID wird von
Plasma stillschweigend ignoriert.

Genau diese Fleissarbeit macht dieses Skript. Was uebrig bleibt, ist die
Gestaltung: Farben, Rahmenbreite, Verlauf, Rundung - als Parameter.

    ./gen-plasma-svg.py button                      # eine Datei nach stdout
    ./gen-plasma-svg.py --alle -o desktoptheme/meintheme/
    ./gen-plasma-svg.py button --stil flach --rahmen 1 --rundung 3
    ./gen-plasma-svg.py --liste

Der klassische Mac-OS-9-Look ist der Standard: 3D-Rahmen (oben/links
hell, unten/rechts dunkel), leichter Verlauf, kaum Rundung.
"""

import argparse
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Widget-Definitionen
#
# Welche Zustandspraefixe ein Widget braucht und welche Hints dazugehoeren.
# Abgeleitet aus dem Breeze-Quellbaum, nicht geraten.
# --------------------------------------------------------------------------

# Zum fehlenden "shadow"-Praefix:
#
# Breeze zeichnet unter shadow-* einen weichen, halbtransparenten
# Verlauf. Wenn ein Generator dort dieselbe Volltonflaeche mit 3D-Kante
# ablegt wie fuer den Normalzustand, malt Plasma sie versetzt unter das
# Element - und man sieht die Kante zweimal. Am Panel war das ein
# deutlicher Doppelstrich.
#
# Ein flaches NT-Theme braucht ohnehin keinen Schatten: Taskleiste,
# Popups und Schaltflaechen lagen dort ohne Schlagschatten auf. Fehlt
# der Praefix, zeichnet Plasma an der Stelle einfach nichts - das ist
# hier das gewuenschte Ergebnis, kein Mangel.
#
# "" bedeutet: Elemente ohne Praefix (center, top, left ...)
WIDGETS = {
    "button": {
        "beschreibung": "Schaltflaechen in Plasmoids",
        "praefixe": ["normal", "hover", "pressed", "focus",
                     "toolbutton-hover", "toolbutton-pressed", "toolbutton-focus"],
        "hints": ["margin", "compose-over-border"],
        "masken": ["normal"],
    },
    "background": {
        "beschreibung": "Hintergrund von Plasmoids",
        "praefixe": ["",],
        "hints": ["margin", "inset"],
        "masken": [""],
    },
    "panel-background": {
        "farbe": "panel",
        "fest": True,
        # Kein dunkler Aussenrahmen. Gemessen an einem NT-4.0-Screenshot:
        # die Taskleiste hat am oberen Rand genau EINE Linie, 1px weiss
        # (255,255,255), darueber und darunter direkt die Grundflaeche
        # (192,192,192). Aussenrahmen plus 3D-Kante ergaeben zwei Linien.
        "aussenrahmen": 0,
        "beschreibung": "Panel / Taskleiste",
        "praefixe": ["", "thick", "north", "south", "east", "west",],
        "hints": ["margin", "inset", "tile-center"],
        "masken": [""],
    },
    "background-dialog": {
        "beschreibung": "Hintergrund aller Plasma-Popups (Anwendungsstarter, "
                        "Benachrichtigungen). Fehlt sie, nimmt Plasma den "
                        "halbtransparenten Breeze-Hintergrund.",
        # Plasma sucht dialogs/background.svg. Hiesse die Datei nach dem
        # Widget-Schluessel, wuerde sie nie gefunden - und der Starter
        # bliebe durchscheinend, obwohl die Datei vorhanden ist.
        "datei": "background",
        "ordner": "dialogs",
        "praefixe": ["",],
        "hints": ["margin", "inset", "preferred-icon-size"],
        "masken": [""],
    },
    "tooltip": {
        "beschreibung": "Kurzinfos",
        "praefixe": ["",],
        "hints": ["margin"],
        "masken": [""],
    },
    "frame": {
        "ecke": 3,
        "beschreibung": "Rahmen, Gruppierungen",
        "praefixe": ["", "raised", "sunken", "plain"],
        "hints": ["margin"],
        "masken": [],
    },
    "listitem": {
        "ecke": 2,
        "beschreibung": "Listeneintraege, u.a. im Anwendungsstarter",
        "praefixe": ["normal", "hover", "pressed", "selected", "selected+hover"],
        "hints": ["margin"],
        "masken": [],
    },
    "viewitem": {
        "beschreibung": "Eintraege in Ansichten",
        "praefixe": ["normal", "hover", "selected", "selected+hover"],
        "hints": ["margin"],
        "masken": [],
    },
    "lineedit": {
        "beschreibung": "Eingabefelder",
        "praefixe": ["base", "focus", "hover"],
        "hints": ["margin", "focus-over-base"],
        "masken": [],
    },
    "tasks": {
        "beschreibung": "Fensterknoepfe in der Taskleiste",
        # Wird von org.kde.plasma.taskmanager.so angefordert (per strings
        # verifiziert). Ohne diese Datei kommt der zentrale Teil der
        # Taskleiste aus Breeze - runde Ecken mitten im NT-Panel.
        # Vier Zustaende je Panelkante - der Taskmanager waehlt nach
        # Panelposition, wie beim panel-background.
        "praefixe": [z for z in ["normal", "focus", "hover", "attention",
                                 "minimized", "progress"]]
                    + [f"{r}-{z}" for r in ("north", "west", "east")
                       for z in ("normal", "focus", "hover", "attention",
                                 "minimized", "progress")],
        "hints": ["margin"],
        "masken": [],
        "margin": 4,
        # Der aktive Fensterknopf traegt die Titelleistenfarbe - und
        # darauf steht der Fenstertitel in der normalen Textfarbe, denn
        # den Text zeichnet der Taskmanager aus dem Farbschema, nicht
        # aus dem SVG. Gemessen: 1,47:1 bei win2k, 1,31:1 bei win98,
        # unter 4,5:1 in allen zehn Varianten. Aus der Community kam
        # genau das zurueck ("way too dark, text unreadable").
        #
        # Deshalb wie in Windows selbst: der aktive Knopf ist kein
        # farbiges Feld, sondern ein eingedrueckter Knopf in der
        # Flaechenfarbe. Der Text steht dann auf demselben Grund wie
        # ueberall - lesbar in jeder Variante und jedem Farbschema.
        "zustaende": {
            "focus":       ("flaeche", True, "ColorScheme-Background"),
            "north-focus": ("flaeche", True, "ColorScheme-Background"),
            "west-focus":  ("flaeche", True, "ColorScheme-Background"),
            "east-focus":  ("flaeche", True, "ColorScheme-Background"),
        },
    },
    "toolbar": {
        "farbe": "panel",
        "fest": True,
        "beschreibung": "Werkzeugleisten",
        "praefixe": ["", "north", "south", "east", "west"],
        "hints": ["margin"],
        "masken": [],
    },
    "plasmoidheading": {
        "beschreibung": "Kopfzeilen in Plasmoids",
        "praefixe": ["header", "footer"],
        "hints": ["margin"],
        "masken": [],
    },
    "scrollbar": {
        "beschreibung": "Bildlaufleisten",
        # ScrollBar.qml waehlt zwischen "slider" und "mouseover-slider".
        # Mit slider-vertical/-horizontal findet es nichts, faellt auf den
        # leeren Praefix zurueck - und der hat kein center. Ergebnis war
        # ein unsichtbarer Griff in jeder Plasma-Bildlaufleiste.
        "praefixe": ["background-vertical", "background-horizontal",
                     "slider", "mouseover-slider"],
        "hints": ["scrollbar-size"],
        "masken": [],
        "ecke": 3,
        # Die Rinne bekommt das Karomuster, das Windows dort hatte: ein
        # Schachbrett aus Buttongrau und Weiss, jede Zelle ein Pixel.
        # Der Qt-Stil zeichnet es in Anwendungen von sich aus - in
        # Plasma-Oberflaechen wie den Systemeinstellungen kommt die
        # Bildlaufleiste aber aus diesem SVG, und dort fehlte es. Aus der
        # Community gemeldet.
        #
        # Nur die Rinne, nicht der Griff: In Windows ist der Griff eine
        # glatte Schaltflaeche, und das Muster ist gerade das, was ihn
        # von der Rinne unterscheidet.
        "dither": ("background-vertical", "background-horizontal"),
        # Ohne diesen Hint streckt Plasma den Mittelteil, und aus dem
        # Karo wuerden Streifen. Mit ihm kachelt es - so macht es Breeze
        # in derselben Datei auch.
        "tile_center": True,
    },
    "switch": {
        "beschreibung": "Umschalter (Systemabschnitt, Benachrichtigungen)",
        # Nur links/rechts - ein Schalter ist ein horizontaler 3-Patch.
        "praefixe": ["inactive", "active"],
        "hints": [],
        "masken": [],
        "formen": {
            "handle":         ("kreis", "flaeche"),
            "handle-hover":   ("kreis", "hover"),
            "handle-pressed": ("kreis", "dunkel"),
            "handle-focus":   ("kreis", "aktiv"),
        },
    },
    "tabbar": {
        "beschreibung": "Reiter",
        "praefixe": ["north-active-tab", "south-active-tab",
                     "east-active-tab", "west-active-tab"],
        "hints": ["margin"],
        "masken": [],
        # Nur der Rahmen, keine Flaeche. Das ist keine Geschmacksfrage:
        # Plasma legt dieses FrameSvg UEBER den Inhalt eines aktiven
        # Panel-Miniprogramms. Eine deckende Flaeche verschluckt dessen
        # Symbol - beim "Peek at Desktop" blieb ein leeres Quadrat
        # zurueck, das aus der Community als fehlende Textur gemeldet
        # wurde. Per Bisektion auf diese Datei eingegrenzt: nimmt man
        # sie weg, ist das Symbol wieder da.
        #
        # Breeze loest dasselbe Problem mit opacity:0.01 auf allen neun
        # Feldern, zeichnet dort also gar nichts. Wir behalten den
        # 3D-Rahmen - er markiert den gedrueckten Knopf wie in Windows -
        # und lassen nur die Flaeche weg.
        "nur_rahmen": True,
    },
    "bar_meter_horizontal": {
        "ecke": 3,
        "beschreibung": "Fortschritts- und Pegelbalken",
        "praefixe": ["bar-inactive", "bar-active"],
        "hints": ["margin"],
        "masken": [],
    },
    "containment-controls": {
        "beschreibung": "Werkzeuge im Panel-Bearbeitungsmodus",
        "praefixe": ["north", "south", "east", "west"],
        "hints": [],
        "masken": [],
    },
    "translucentbackground": {
        "beschreibung": "Miniprogramm im Bearbeitungsmodus",
        "praefixe": ["",],
        "hints": ["margin"],
        "masken": [],
    },
    "slider": {
        "beschreibung": "Schieberegler",
        # Der Griff kommt aus actionbutton.svg - Breeze macht das
        # genauso. Hier steht nur die Rille plus die Groessenvorgabe.
        "praefixe": ["groove", "groove-highlight"],
        "hints": ["handle-size"],
        "masken": [],
        "ecke": 3,
    },
}

# Widgets, die keine Rahmen sind, sondern Einzelformen: Haken, Pfeile,
# Linien. Sie haben kein 9-Patch-Raster - Plasma schneidet sie ueber
# einzelne IDs aus. Der Guide nennt das die Klasse, bei der ein
# Generator an seine Grenze kommt; die Formen sind hier deshalb
# ausgeschrieben statt berechnet.
FORM_WIDGETS = {
    "line": {
        "beschreibung": "Trennlinien in Listen und im Anwendungsstarter",
        "formen": {
            "horizontal-line": ("hlinie", "dunkel"),
            "vertical-line":   ("vlinie", "dunkel"),
        },
    },
    "checkmarks": {
        "beschreibung": "Haken in Ankreuzfeldern",
        "formen": {
            "checkbox":    ("haken", "text"),
            "radiobutton": ("punkt", "text"),
        },
    },
    "radiobutton": {
        "beschreibung": "Auswahlknoepfe",
        "formen": {
            "normal":  ("ring", "flaeche"),
            "hover":   ("ring", "hover"),
            "focus":   ("ring", "aktiv"),
            "checked": ("punkt", "text"),
            "shadow":  ("ring", "dunkel"),
        },
    },
    "arrows": {
        "beschreibung": "Pfeile in Aufklappmenues und Bildlaufleisten",
        "formen": {
            "up-arrow":    ("dreieck-o", "text"),
            "down-arrow":  ("dreieck-u", "text"),
            "left-arrow":  ("dreieck-l", "text"),
            "right-arrow": ("dreieck-r", "text"),
        },
    },
    "busywidget": {
        "beschreibung": "Wartekringel",
        "formen": {
            "busywidget":       ("ring", "aktiv"),
            "16-16-busywidget": ("ring", "aktiv"),
            "22-22-busywidget": ("ring", "aktiv"),
        },
    },
    "actionbutton": {
        "beschreibung": "Runde Knoepfe",
        # Zusaetzlich zu den groessenbehafteten die nackten Namen:
        # RoundButton.qml und der Schieberegler-Griff fordern "normal",
        # "hover", "pressed", "focus" ohne Praefix an.
        "formen": {**{f"{g}-{g}-{z}": ("kreis", f)
                      for g in (16, 22, 24, 32)
                      for z, f in [("normal", "flaeche"), ("hover", "hover"),
                                   ("pressed", "dunkel"), ("focus", "aktiv")]},
                   **{z: ("kreis", f)
                      for z, f in [("normal", "flaeche"), ("hover", "hover"),
                                   ("pressed", "dunkel"), ("focus", "aktiv")]}},
    },
    "action-overlays": {
        "beschreibung": "Ueberlagerungen in der Ordner-Ansicht",
        "formen": {f"add-{z}": ("plus", f)
                   for z, f in [("normal", "text"), ("hover", "hover"),
                                ("pressed", "dunkel")]},
    },
}

# Elemente eines vollstaendigen 9-Patch, in Zeichenreihenfolge:
# erst die Flaeche, dann die Raender, damit Raender obenauf liegen.
ECKEN  = ["topleft", "topright", "bottomleft", "bottomright"]
KANTEN = ["top", "bottom", "left", "right"]

# --------------------------------------------------------------------------
# Paletten
# --------------------------------------------------------------------------

PALETTEN = {
    # Mac OS 9 Platinum: warmes Grau, harte 3D-Kanten, kaum Rundung
    "platinum": {
        "flaeche":   "#dddad2",
        "hell":      "#ffffff",   # oben/links
        "dunkel":    "#84817a",   # unten/rechts
        "rahmen":    "#000000",
        "aktiv":     "#c8c4bc",
        "text":      "#000000",
    },
    "platinum-dark": {
        "flaeche":   "#2c2a28",
        "hell":      "#565250",
        "dunkel":    "#000000",
        "rahmen":    "#000000",
        "aktiv":     "#3c3a38",
        "text":      "#e6e2dc",
    },
    "charcoal": {
        "flaeche":   "#3c3c3c",
        "hell":      "#6a6a6a",
        "dunkel":    "#101010",
        "rahmen":    "#000000",
        "aktiv":     "#4c4c4c",
        "text":      "#dcdcdc",
    },
    # NT Legacy: Windows-NT-4.0-Farbwelt, Petrol statt Marineblau.
    # Bewusst ohne schwarze Flaechen - dunkel wird nur Text, Rahmen und
    # die aktive Titelleiste. Das haelt das Theme fuer lange Sitzungen
    # angenehm, ohne den Charakter zu verlieren.
    "nt-legacy": {
        "flaeche":   "#d8d8d0",   # Hauptflaeche, helles neutrales Grau
        "fenster":   "#f0f0e8",   # Fensterinhalt, fast cremeweiss
        "panel":     "#b8c4c4",   # gedaempftes Petrol-Grau
        "hell":      "#f4f4ee",   # 3D-Kante oben/links
        # Der helle Punkt im Karo der Bildlaufleiste. Eigener Wert, nicht
        # die Lichtkante: er soll so hell sein wie moeglich, waehrend die
        # Kante bewusst gedaempft bleibt. build.py ersetzt Farben ueber
        # ihren Hexwert, deshalb darf er mit keinem anderen der Palette
        # zusammenfallen - #fcfcfa statt reinem Weiss.
        "karo":      "#fcfcfa",
        "dunkel":    "#8a8a82",   # 3D-Kante unten/rechts
        "rahmen":    "#202628",   # Aussenrahmen, sehr dunkles Blau-Grau
        "aktiv":     "#287f8c",   # Auswahl, Petrol
        "aktiv_text": "#ffffff",
        "kopf_aktiv":   "#176b78",
        "kopf_inaktiv": "#60777a",
        "text":      "#202628",
        "text2":     "#526166",   # Sekundaertext
        "hover":     "#d6a23a",   # NT-artiges Gold
        "warnung":   "#c87922",
        "fehler":    "#a83232",
        "positiv":   "#39734a",
        "desktop":   "#899a9a",
    },
}

# Zustaende, die anders eingefaerbt werden als der Normalzustand.
# Ein Button muss sich beim Ueberfahren und Druecken sichtbar aendern -
# sonst wirkt das Theme "tot", obwohl technisch alles stimmt.
# Je Zustand: Ersatzfarbe, ob der 3D-Rahmen umgedreht wird, und die
# Farbschema-Klasse.
#
# Die Klasse ist das Entscheidende. Traegt jeder Zustand dieselbe, sehen
# alle gleich aus - dann ist der Auswahlbalken unsichtbar, Hover tot und
# der Fortschrittsbalken zeigt keinen Fortschritt. Die Klassen sind die,
# die KSvg tatsaechlich ersetzt (aus libKF6Svg extrahiert); ein
# erfundener Name faellt still auf die Ersatzfarbe zurueck.
ZUSTANDSFARBE = {
    #                        Ersatzfarbe, Bevel umdrehen, Farbschema-Klasse
    "hover":                ("hover",  False, "ColorScheme-ButtonHover"),
    "toolbutton-hover":     ("hover",  False, "ColorScheme-ButtonHover"),
    "focus":                ("aktiv",  False, "ColorScheme-ButtonFocus"),
    "toolbutton-focus":     ("aktiv",  False, "ColorScheme-ButtonFocus"),
    "pressed":              ("dunkel", True,  "ColorScheme-Background"),
    "toolbutton-pressed":   ("dunkel", True,  "ColorScheme-Background"),
    "selected":             ("aktiv",  False, "ColorScheme-Highlight"),
    "selected+hover":       ("aktiv",  False, "ColorScheme-Highlight"),
    "active":               ("aktiv",  False, "ColorScheme-Highlight"),
    "bar-active":           ("aktiv",  False, "ColorScheme-Highlight"),
    "groove-highlight":     ("aktiv",  False, "ColorScheme-Highlight"),
    "sunken":               ("dunkel", True,  "ColorScheme-Background"),
    "sunken-slider-vertical":   ("dunkel", True, "ColorScheme-Background"),
    "sunken-slider-horizontal": ("dunkel", True, "ColorScheme-Background"),
    "mouseover-slider":     ("hover",  False, "ColorScheme-ButtonHover"),
}

# Zuordnung Farbklasse -> Palettenschluessel, mit Ersatzkette.
# Der erste vorhandene Schluessel gewinnt, damit einfache Paletten mit
# wenigen Farben genauso funktionieren wie ausfuehrliche.
STYLESHEET_KLASSEN = [
    ("ColorScheme-Text",             ["text"]),
    ("ColorScheme-Background",       ["flaeche"]),
    ("ColorScheme-Highlight",        ["aktiv"]),
    ("ColorScheme-ViewText",         ["text"]),
    ("ColorScheme-ViewBackground",   ["fenster", "flaeche"]),
    ("ColorScheme-ViewHover",        ["hover", "aktiv"]),
    ("ColorScheme-ViewFocus",        ["aktiv"]),
    ("ColorScheme-ButtonText",       ["text"]),
    ("ColorScheme-ButtonBackground", ["flaeche"]),
    ("ColorScheme-ButtonHover",      ["hover", "aktiv"]),
    ("ColorScheme-ButtonFocus",      ["aktiv"]),
    ("ColorScheme-HighlightedText",  ["auswahl_text", "fenster"]),
    ("ColorScheme-ComplementaryBackground", ["panel", "flaeche"]),
    ("ColorScheme-NegativeText",     ["fehler", "text"]),
    ("ColorScheme-NeutralText",      ["warnung", "text"]),
    ("ColorScheme-PositiveText",     ["positiv", "text"]),
]


class Generator:
    def __init__(self, palette, rahmen=1, rundung=0, stil="bevel",
                 zelle=32, ecke=6, abstand=12, spalten=4, aussenrahmen=0):
        self.p = palette
        self.aussenrahmen = aussenrahmen
        self._aussen_override = None
        self.rahmen = rahmen
        self.rundung = rundung
        self.stil = stil          # bevel | flach
        self.zelle = zelle        # Kantenlaenge eines Zustandssatzes
        self.ecke = ecke          # Groesse der Eckelemente
        self.abstand = abstand    # Luft zwischen den Saetzen im Atlas
        self.spalten = spalten
        self.teile = []

    def farbe(self, *keys):
        """Erste vorhandene Farbe aus der Ersatzkette."""
        for k in keys:
            if k in self.p:
                return self.p[k]
        return "#000000"

    # -- Bausteine ---------------------------------------------------------

    def _rect(self, eid, x, y, w, h, fill, klasse=None, rx=0, extra=""):
        # Nullflaechen weglassen - sie wuerden nur den Linter beschaeftigen
        if w <= 0 or h <= 0:
            return
        k = f' class="{klasse}"' if klasse else ""
        r = f' rx="{rx}" ry="{rx}"' if rx else ""
        farbe = 'currentColor' if klasse else fill
        self.teile.append(
            f'    <rect id="{eid}" x="{x:g}" y="{y:g}" '
            f'width="{w:g}" height="{h:g}"{r}{k} fill="{farbe}"{extra}/>'
        )

    def _hint(self, eid, x, y, w, h, farbe="#ff00ff"):
        """Hints sind Marker, keine Grafik. Breeze zeichnet sie in Magenta
        und macht sie unsichtbar - Plasma liest nur ihre Geometrie."""
        self.teile.append(
            f'    <rect id="{eid}" x="{x:g}" y="{y:g}" '
            f'width="{w:g}" height="{h:g}" fill="{farbe}" opacity="0"/>'
        )

    def _neun_patch(self, praefix, ox, oy, flaeche_key="flaeche",
                    invertiert=False, klasse="ColorScheme-Background",
                    nur_rahmen=False, dither=False):
        """Erzeugt einen vollstaendigen 9-Patch-Satz an Position (ox, oy).

        Ein 9-Patch teilt die Flaeche restlos auf: alle neun Felder sind
        so breit bzw. hoch wie die Ecken. Rahmen werden INNEN in das
        jeweilige Feld gezeichnet, nicht anstelle der Flaeche - sonst
        klaffte zwischen Ecke und Kante eine Luecke.

        Je Aussenkante liegen bis zu zwei Linien uebereinander:
        aussen der dunkle Rahmen (NT/Win95), innen davon die 3D-Kante.

        invertiert dreht den 3D-Rahmen um - aus einer herausstehenden
        Schaltflaeche wird eine eingedrueckte.
        """
        def n(teil):
            return f"{praefix}-{teil}" if praefix else teil

        z, e, b = self.zelle, self.ecke, self.rahmen
        # Ein Widget kann den Aussenrahmen abschalten - das Panel tut
        # das, weil NTs Taskleiste nur eine einzelne helle Linie hat.
        a = (self._aussen_override if self._aussen_override is not None
             else self.aussenrahmen)
        flaeche = self.p[flaeche_key]
        hell = self.p["dunkel" if invertiert else "hell"]
        dunkel = self.p["hell" if invertiert else "dunkel"]
        rahmenfarbe = self.p.get("rahmen", "#000000")

        if self.stil == "bevel":
            kante = {"t": hell, "l": hell, "b": dunkel, "r": dunkel}
        else:
            kante = {s: rahmenfarbe for s in "tlbr"}

        m = z - 2 * e      # Laenge der mittleren Felder
        r = z - e          # Beginn der rechten/unteren Randspalte

        #  Feld          x  y  w  h   welche Seiten sind Aussenkante
        felder = [
            ("topleft",     0, 0, e, e, "tl"),
            ("top",         e, 0, m, e, "t"),
            ("topright",    r, 0, e, e, "tr"),
            ("left",        0, e, e, m, "l"),
            ("center",      e, e, m, m, ""),
            ("right",       r, e, e, m, "r"),
            ("bottomleft",  0, r, e, e, "bl"),
            ("bottom",      e, r, m, e, "b"),
            ("bottomright", r, r, e, e, "br"),
        ]

        for teil, fx, fy, fw, fh, seiten in felder:
            if fw <= 0 or fh <= 0:
                continue
            x, y = ox + fx, oy + fy
            self.teile.append(f'    <g id="{n(teil)}">')

            # Flaeche. Nur sie traegt die Farbschema-Klasse - die Kanten
            # bleiben fest, sonst wechselte der Lichteinfall mit jedem
            # Farbschema.
            # Nur fill:currentColor plus Klasse - KEIN inline color:.
            #
            # Frueher stand hier zusaetzlich color:<farbe> im style, mit
            # der Begruendung, Breeze mache das auch. Das war falsch:
            # von 42 Breeze-Widget-SVGs haben genau zwei ein echtes
            # inline color:, der Rest verlaesst sich auf die Klasse.
            # Und eine Inline-Deklaration schlaegt in der CSS-Kaskade
            # jede Klassenregel - der Austausch des
            # <style id="current-color-scheme">-Blocks durch KSvg lief
            # damit ins Leere. Folge waren: keine Akzentfarbe des
            # Nutzers und keine Farbvarianten ohne SVG-Duplikate.
            #
            # Die Ersatzfarbe steht weiterhin im Stylesheet-Block oben,
            # greift also, solange KSvg nichts ersetzt.
            if nur_rahmen:
                # Die Flaeche bleibt unsichtbar, das Rechteck aber steht
                # da. Ein leeres <g> haette eine Bounding Box von 0x0,
                # und KSvg berechnet die Feldgroessen des 9-Patch genau
                # daraus - der Rahmen skalierte dann falsch. Deshalb
                # opacity:0.01 statt nichts, wie Breeze es im selben
                # Element auch macht.
                self.teile.append(
                    f'      <rect x="{x:g}" y="{y:g}" width="{fw:g}" '
                    f'height="{fh:g}" fill="{flaeche}" opacity="0.01"/>')
            elif klasse:
                # Die Ersatzfarbe steht im style-Block oben je Klasse.
                # Damit sich die Zustaende auch dann unterscheiden, wenn
                # KSvg nichts ersetzt, bekommt jede Klasse ihren eigenen
                # Wert - siehe stylesheet_fuer().
                self.teile.append(
                    f'      <rect x="{x:g}" y="{y:g}" width="{fw:g}" '
                    f'height="{fh:g}" class="{klasse}" '
                    f'style="fill:currentColor;fill-opacity:1;stroke:none"/>')
            else:
                self.teile.append(
                    f'      <rect x="{x:g}" y="{y:g}" width="{fw:g}" '
                    f'height="{fh:g}" fill="{flaeche}"/>')

            # Das Karo der Rinne. Gezeichnet als gestrichelte Linien, eine
            # je Bildzeile, nicht als einzelne Rechtecke: Ein Feld von
            # 26x26 haette sonst 338 Rechtecke, so sind es 26 Linien.
            # Ein SVG-<pattern> waere noch kuerzer, aber QtSvg kennt
            # keine Patterns - es rendert sie ersatzlos weg.
            if dither and teil == "center":
                # Gezeichnet wurde das Karo zuerst in der 3D-Lichtkante
                # ("hell"). In den Nachtfassungen war es damit deutlich zu
                # sehen, in den hellen nicht - aus der Community gemeldet.
                # Nachgerechnet: #f4f4ee auf #d8d8d0 sind 28 Stufen, also
                # 13 Prozent ueber dem Grund. Nacht sind es 32 Stufen auf
                # einem Grund von 42 - 76 Prozent. Dasselbe absolute Delta,
                # der sechsfache wahrgenommene Unterschied. Windows selbst
                # lag bei 33 Prozent (Weiss auf #c0c0c0).
                #
                # Zwei Aenderungen bringen die helle Fassung dorthin:
                # ein eigener Palettenwert fuer die Karofarbe statt der
                # Lichtkante, und eine leichte Abdunklung der Rinne. Die
                # Abdunklung liegt als halbdurchlaessige Schicht ueber der
                # Flaeche, nicht als feste Farbe - so bleibt die Rinne an
                # das Farbschema des Nutzers gebunden.
                self.teile.append(
                    f'      <rect x="{x:g}" y="{y:g}" width="{fw:g}" '
                    f'height="{fh:g}" fill="#000000" opacity="0.07"/>')
                hell_farbe = self.p.get("karo", self.p.get("hell", "#ffffff"))
                for zeile in range(int(fh)):
                    versatz = zeile % 2
                    # In y die halbe Stufe, in x keine. Das ist kein
                    # Schoenheitsfehler, sondern der Unterschied zwischen
                    # Muster und Grauschleier: Die Strichstaerke misst
                    # quer zur Linie, dort zentriert y+0.5 auf genau eine
                    # Bildzeile. Der Strichel dagegen misst laengs, und
                    # ein Start bei x+0.5 legt jeden Punkt haelftig auf
                    # zwei Spalten. Gerendert (QtSvg, mit Kantenglaettung)
                    # kamen so 227 statt 252 heraus - das Karo verwaschen
                    # zu einer Flaeche. Mit ganzen x-Werten: 202/252 im
                    # sauberen Wechsel, ueber das ganze Feld.
                    self.teile.append(
                        f'      <line x1="{x + versatz:g}" '
                        f'y1="{y + zeile + 0.5:g}" x2="{x + fw:g}" '
                        f'y2="{y + zeile + 0.5:g}" stroke="{hell_farbe}" '
                        f'stroke-width="1" stroke-dasharray="1 1"/>')

            def linie(seite, breite, farbe, versatz):
                if breite <= 0:
                    return
                # Ecken beruecksichtigen: an einem Feld, das zwei
                # Aussenkanten hat, muss die Linie um die andere
                # eingerueckt werden, damit sich beide nicht ueberlagern.
                ein_l = versatz if "l" in seiten else 0
                ein_r = versatz if "r" in seiten else 0
                ein_t = versatz if "t" in seiten else 0
                ein_b = versatz if "b" in seiten else 0
                if seite == "t":
                    self.teile.append(
                        f'      <rect x="{x + ein_l:g}" y="{y + versatz:g}" '
                        f'width="{fw - ein_l - ein_r:g}" height="{breite:g}" fill="{farbe}"/>')
                elif seite == "b":
                    self.teile.append(
                        f'      <rect x="{x + ein_l:g}" y="{y + fh - versatz - breite:g}" '
                        f'width="{fw - ein_l - ein_r:g}" height="{breite:g}" fill="{farbe}"/>')
                elif seite == "l":
                    self.teile.append(
                        f'      <rect x="{x + versatz:g}" y="{y + ein_t:g}" '
                        f'width="{breite:g}" height="{fh - ein_t - ein_b:g}" fill="{farbe}"/>')
                elif seite == "r":
                    self.teile.append(
                        f'      <rect x="{x + fw - versatz - breite:g}" y="{y + ein_t:g}" '
                        f'width="{breite:g}" height="{fh - ein_t - ein_b:g}" fill="{farbe}"/>')

            for seite in seiten:
                linie(seite, a, rahmenfarbe, 0)       # aussen
                linie(seite, b, kante[seite], a)      # 3D-Kante darunter

            self.teile.append('    </g>')

    def _hints(self, praefix, ox, oy, arten):
        def n(teil):
            return f"{praefix}-{teil}" if praefix else teil

        z, e, b = self.zelle, self.ecke, self.rahmen
        # Innenabstand. Unser Rahmen ist selbst 2px (Aussenrahmen +
        # Bevel) - bei margin=2 begaenne der Text exakt am ersten freien
        # Pixel und klebte am Rand. Breeze nimmt 4 fuer Rahmen und
        # Panels, 6 fuer Listen, Knoepfe und Eingabefelder.
        rand = self._margin

        if "margin" in arten:
            # Innenabstand: wieviel Platz der Inhalt vom Rand haelt
            self._hint(n("hint-top-margin"),    ox + z / 2, oy,             2, rand)
            self._hint(n("hint-bottom-margin"), ox + z / 2, oy + z - rand,  2, rand)
            self._hint(n("hint-left-margin"),   ox,         oy + z / 2,     rand, 2)
            self._hint(n("hint-right-margin"),  ox + z - rand, oy + z / 2,  rand, 2)

        if "inset" in arten:
            # Insets trennen gezeichnete Flaeche von beanspruchtem Platz -
            # noetig fuer Schatten und schwebende Panels (Plasma 6).
            # Inset = 0, weil wir keinen Schatten in die Flaeche zeichnen.
            # Ein Inset von 1 wuerde einen Pixel als "nicht gezeichnet"
            # beanspruchen - sichtbar als toter Rand um Panel und Popups.
            # Breeze setzt hier 1e-8 (praktisch 0); nur background.svg hat
            # echte 8px, weil dort ein Schatten liegt.
            iw = 0.00000001
            for seite, (hx, hy) in {
                "top":    (ox + z / 4, oy),
                "bottom": (ox + z / 4, oy + z),
                "left":   (ox, oy + z / 4),
                "right":  (ox + z, oy + z / 4),
            }.items():
                self._hint(n(f"hint-{seite}-inset"), hx, hy, iw, iw)

        if "tile-center" in arten:
            self._hint(n("hint-tile-center"), ox + 1, oy + 1, 1, 1, "#00ff00")
        if "compose-over-border" in arten:
            self._hint(n("hint-compose-over-border"), ox + 3, oy + 1, 1, 1, "#00ff00")
        if "scrollbar-size" in arten:
            # Breeze: 6x6 - die Breite der Bildlaufleiste
            self._hint(n("hint-scrollbar-size"), ox + 1, oy + 3, 6, 6, "#00ff00")
        if "handle-size" in arten:
            # Breeze: 20x20 - die Groesse des Schieberegler-Griffs
            self._hint(n("hint-handle-size"), ox + 1, oy + 3, 20, 20, "#00ff00")
        if "preferred-icon-size" in arten:
            # Die Breite dieses Markers transportiert die gewuenschte
            # Symbolgroesse in Pixeln. 26 statt der Plasma-Vorgabe (32)
            # sind rund 80 Prozent.
            self._hint(n("hint-preferred-icon-size"), ox + 7, oy + 1, 26, 1, "#00ff00")
        if "focus-over-base" in arten:
            self._hint(n("hint-focus-over-base"), ox + 5, oy + 1, 1, 1, "#00ff00")

    def _form(self, eid, art, farbe, ox, oy, gr):
        """Zeichnet eine Einzelform (Haken, Pfeil, Kreis, Linie).

        Anders als beim 9-Patch schneidet Plasma diese Elemente als
        Ganzes aus - sie brauchen kein Raster, nur eine eindeutige ID.
        """
        m = gr / 2
        d = gr * 0.34          # halbe Kantenlaenge der inneren Form
        s = max(1.5, gr * 0.12)

        self.teile.append(f'    <g id="{eid}">')
        if art == "kreis":
            self.teile.append(
                f'      <circle cx="{ox+m:g}" cy="{oy+m:g}" r="{d:g}" '
                f'fill="{farbe}" stroke="{self.p["rahmen"]}" stroke-width="1"/>')
        elif art == "ring":
            self.teile.append(
                f'      <circle cx="{ox+m:g}" cy="{oy+m:g}" r="{d:g}" '
                f'fill="none" stroke="{farbe}" stroke-width="{s:g}"/>')
        elif art == "punkt":
            self.teile.append(
                f'      <circle cx="{ox+m:g}" cy="{oy+m:g}" r="{d*0.5:g}" '
                f'fill="{farbe}"/>')
        elif art == "haken":
            # Der klassische Haken: kurzer Abstrich, langer Aufstrich
            self.teile.append(
                f'      <path d="M{ox+m-d:g},{oy+m:g} L{ox+m-d*0.3:g},{oy+m+d*0.7:g} '
                f'L{ox+m+d:g},{oy+m-d*0.7:g}" fill="none" stroke="{farbe}" '
                f'stroke-width="{s:g}" stroke-linecap="square"/>')
        elif art == "plus":
            self.teile.append(
                f'      <path d="M{ox+m:g},{oy+m-d:g} V{oy+m+d:g} '
                f'M{ox+m-d:g},{oy+m:g} H{ox+m+d:g}" stroke="{farbe}" '
                f'stroke-width="{s:g}"/>')
        elif art == "hlinie":
            self.teile.append(
                f'      <rect x="{ox:g}" y="{oy+m:g}" width="{gr:g}" '
                f'height="1" fill="{farbe}"/>')
        elif art == "vlinie":
            self.teile.append(
                f'      <rect x="{ox+m:g}" y="{oy:g}" width="1" '
                f'height="{gr:g}" fill="{farbe}"/>')
        elif art.startswith("dreieck"):
            r = art.split("-")[1]
            pkt = {
                "o": f"{ox+m:g},{oy+m-d:g} {ox+m-d:g},{oy+m+d*0.6:g} {ox+m+d:g},{oy+m+d*0.6:g}",
                "u": f"{ox+m:g},{oy+m+d:g} {ox+m-d:g},{oy+m-d*0.6:g} {ox+m+d:g},{oy+m-d*0.6:g}",
                "l": f"{ox+m-d:g},{oy+m:g} {ox+m+d*0.6:g},{oy+m-d:g} {ox+m+d*0.6:g},{oy+m+d:g}",
                "r": f"{ox+m+d:g},{oy+m:g} {ox+m-d*0.6:g},{oy+m-d:g} {ox+m-d*0.6:g},{oy+m+d:g}",
            }[r]
            self.teile.append(f'      <polygon points="{pkt}" fill="{farbe}"/>')
        self.teile.append('    </g>')

    # -- Zusammenbau -------------------------------------------------------

    def erzeuge(self, name, spec):
        self.teile = []
        self._aussen_override = spec.get("aussenrahmen")
        # Eckgroesse je Widget: eine 6px-Ecke in einem 6px hohen
        # Fortschrittsbalken laesst oben und unten nichts uebrig, KSvg
        # staucht dann die Raender und die 1px-Linien verschmieren.
        self._ecke_original = self.ecke
        self.ecke = spec.get("ecke", self.ecke)
        self._margin = spec.get("margin", 4)
        praefixe = spec["praefixe"]
        masken = spec.get("masken", [])
        hints = spec.get("hints", [])

        saetze = [(p, False) for p in praefixe] + [(f"mask-{m}" if m else "mask", True)
                                                   for m in masken]

        formen = list(spec.get("formen", {}).items())
        schritt = self.zelle + self.abstand
        gesamt = len(saetze) + len(formen)
        spalten = min(self.spalten, max(1, gesamt))
        zeilen = (gesamt + spalten - 1) // spalten
        breite = spalten * schritt + self.abstand
        hoehe = zeilen * schritt + self.abstand

        kopf = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{breite:g}" height="{hoehe:g}" '
            f'viewBox="0 0 {breite:g} {hoehe:g}">',
            f'  <!-- {name}.svg — {spec["beschreibung"]} -->',
            '  <!-- Erzeugt von tools/gen-plasma-svg.py. Die Element-IDs sind',
            '       die Schnittstelle zu Plasma: bitte nicht umbenennen. -->',
            '  <defs>',
            '    <style id="current-color-scheme" type="text/css">',
        ]
        for klasse, keys in STYLESHEET_KLASSEN:
            f = self.farbe(*keys)
            # stop-color mitgeben, damit auch Gradienten umgefaerbt werden
            kopf.append(f'      .{klasse} {{ color:{f}; stop-color:{f}; }}')
        kopf += ['    </style>', '  </defs>']

        for i, (praefix, ist_maske) in enumerate(saetze):
            ox = self.abstand + (i % spalten) * schritt
            oy = self.abstand + (i // spalten) * schritt

            basis = praefix[5:] if praefix.startswith("mask-") else praefix
            standard = spec.get("farbe", "flaeche")
            # Ein Widget darf einzelne Zustaende anders faerben als die
            # allgemeine Tabelle. Die Taskleiste braucht das: dort waere
            # die Akzentfarbe des Fokuszustands zwar richtig gemeint,
            # aber der Fenstertitel darauf nicht mehr lesbar.
            farb_key, invertiert, zustandsklasse = spec.get(
                "zustaende", {}).get(basis) or ZUSTANDSFARBE.get(
                basis, (standard, False, "ColorScheme-Background"))
            # Das Panel bekommt seine Farbe fest, nicht ueber das
            # Farbschema. Grund: Plasma faerbt Shell-Elemente aus der
            # Gruppe Colors:Window ein, nicht aus Complementary - ein
            # Panel, das sich von den Plasmoid-Flaechen abheben soll,
            # laesst sich darueber nicht getrennt steuern. Gemessen:
            # mit Klasse wurde das Panel #d8d8d0 statt #b8c4c4.
            klasse_hier = None if spec.get("fest") else zustandsklasse

            self.teile.append(f'  <!-- {praefix or "(Standardzustand)"} -->')
            if ist_maske:
                # Masken definieren nur die Form, nicht das Aussehen.
                # Deshalb weiss und ohne Farbschema-Klasse.
                alt_stil, self.stil = self.stil, "flach"
                alt_rahmen = self.p["rahmen"]
                self.p = dict(self.p, rahmen="#ffffff")
                self._neun_patch(praefix, ox, oy, "flaeche", klasse=None)
                self.p["rahmen"] = alt_rahmen
                self.stil = alt_stil
            else:
                self._neun_patch(praefix, ox, oy, farb_key, invertiert,
                                 klasse=klasse_hier,
                                 nur_rahmen=spec.get("nur_rahmen", False),
                                 dither=basis in spec.get("dither", ()))
                self._hints(praefix, ox, oy, hints)

        for j, (fid, (art, farbkey)) in enumerate(formen):
            i = len(saetze) + j
            ox = self.abstand + (i % spalten) * schritt
            oy = self.abstand + (i // spalten) * schritt
            self._form(fid, art, self.farbe(farbkey, "text"), ox, oy, self.zelle)

        # Der Kachel-Hinweis gilt fuer die ganze Datei, nicht je Zustand.
        # Er liegt ausserhalb der sichtbaren Flaeche - KSvg fragt nur, ob
        # das Element existiert, und zeichnet es nie. Breeze legt es in
        # derselben Datei ebenso ins Negative.
        if spec.get("tile_center"):
            self.teile.append(
                '  <!-- Mittelteil kacheln statt strecken -->\n'
                '    <rect id="hint-tile-center" x="0" y="-4" '
                'width="2" height="2" opacity="0"/>')

        self.ecke = self._ecke_original
        return "\n".join(kopf + self.teile + ['</svg>', ''])


# Reine Formen-Widgets verhalten sich sonst wie die anderen
WIDGETS.update({n: {**s, "praefixe": [], "hints": [], "masken": []}
                for n, s in FORM_WIDGETS.items()})


def main():
    ap = argparse.ArgumentParser(
        description="Erzeugt Plasma-Style-SVGs mit korrekter Element-Struktur.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Verfuegbare Widgets:  " + ", ".join(sorted(WIDGETS)))
    ap.add_argument("widget", nargs="?", help="Name des Widgets, z.B. button")
    ap.add_argument("--alle", action="store_true", help="alle Widgets erzeugen")
    ap.add_argument("--liste", action="store_true", help="Widgets auflisten")
    ap.add_argument("-o", "--ausgabe", type=Path,
                    help="Zielverzeichnis (sonst nach stdout)")
    ap.add_argument("--palette", default="platinum", choices=sorted(PALETTEN))
    ap.add_argument("--stil", default="bevel", choices=["bevel", "flach"],
                    help="bevel = 3D-Rahmen wie Mac OS 9, flach = einfarbig")
    ap.add_argument("--rahmen", type=int, default=1, help="Rahmenbreite in px")
    ap.add_argument("--rundung", type=int, default=0, help="Eckenradius in px")
    ap.add_argument("--aussenrahmen", type=int, default=0,
                    help="dunkler Rahmen um den 3D-Bevel (NT/Win95-Stil)")
    ap.add_argument("--zelle", type=int, default=32, help="Groesse eines Zustandssatzes")
    ap.add_argument("--ecke", type=int, default=6, help="Groesse der Eckelemente")
    args = ap.parse_args()

    if args.liste:
        print(f"{'Widget':<20} {'Zustaende':>10}  Beschreibung")
        for n, s in sorted(WIDGETS.items()):
            print(f"{n:<20} {len(s['praefixe']):>10}  {s['beschreibung']}")
        return 0

    if not args.alle and not args.widget:
        ap.error("Widget-Name oder --alle angeben (--liste zeigt alle).")
    if args.widget and args.widget not in WIDGETS:
        ap.error(f"Unbekanntes Widget '{args.widget}'. --liste zeigt alle.")

    g = Generator(PALETTEN[args.palette], rahmen=args.rahmen,
                  rundung=args.rundung, stil=args.stil,
                  zelle=args.zelle, ecke=args.ecke,
                  aussenrahmen=args.aussenrahmen)

    namen = sorted(WIDGETS) if args.alle else [args.widget]
    for name in namen:
        svg = g.erzeuge(name, WIDGETS[name])
        if args.ausgabe:
            spec = WIDGETS[name]
            unter = spec.get("ordner", "widgets")
            dateiname = spec.get("datei", name)
            ziele = [args.ausgabe / unter / f"{dateiname}.svg"]

            # Plasma waehlt je nach Umgebung einen Variantensatz:
            # solid (kein Blur), translucent (mit Blur), opaque. Fehlt
            # die passende Datei, faellt NUR sie auf Breeze zurueck -
            # das Panel wird dann transparent und mischt sich mit dem
            # Hintergrund, obwohl widgets/ vorhanden ist. Gemessen:
            # Panelflaeche #80807b statt #b8c4c4.
            if name in ("panel-background", "background", "background-dialog",
                        "tooltip"):
                # Breeze kennt fuer background nur solid und translucent -
                # opaque/widgets/background existiert dort nicht.
                varianten = ("solid", "translucent") if name == "background" \
                    else ("solid", "translucent", "opaque")
                for variante in varianten:
                    ziele.append(args.ausgabe / variante / unter / f"{dateiname}.svg")

            for ziel in ziele:
                ziel.parent.mkdir(parents=True, exist_ok=True)
                ziel.write_text(svg)
                print(f"  {ziel}")
        else:
            sys.stdout.write(svg)

    return 0


if __name__ == "__main__":
    sys.exit(main())
