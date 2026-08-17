#!/usr/bin/env python3
"""Erzeugt die Werkzeugleisten-Symbole, die ReactOS nicht liefert.

ReactOS hat die Shell-Symbole (Ordner, Laufwerke, Papierkorb), aber keine
verwertbaren Werkzeugleisten-Symbole: Kopieren, Einfuegen, Zurueck,
Ansichtsmodi. Die liegen dort als Bitmap-Streifen in Programmressourcen
oder gar nicht vor.

Weil genau diese Symbole in Dolphin und PCManFM-Qt staendig sichtbar sind
und ohne sie der Breeze-Rueckfall greift - flache graue Striche neben
Pixelart - werden sie hier selbst erzeugt. Das hat drei Vorteile: es ist
lizenzrein (Eigenerzeugnis unter der Theme-Lizenz), stilistisch
kontrollierbar, und die Farben kommen aus derselben Palette wie der Rest.

    ./gen-icons-aktionen.py <icon-theme-verzeichnis>
    ./gen-icons-aktionen.py <verz> --palette desert

Gezeichnet wird bewusst grob: 16 px sind 16 px. Feine Linien verschwinden
beim Skalieren, deshalb liegen alle Formen auf ganzen Pixeln und die
Strichstaerke waechst mit der Groesse.
"""

import argparse
import subprocess
from pathlib import Path

# Die Groessen, die Dolphin in seinem Zoomregler anbietet - alle davon.
#
# Bis 0.2.6 endete die Reihe bei 48, und darueber sollte ein
# scalable-Verzeichnis uebernehmen. Das tut es nicht: Gemessen an den
# Zugriffszeiten der Dateien liest Dolphin bei 200 px das 48er-PNG und
# zieht es hoch, waehrend die SVG im scalable-Ordner unberuehrt bleibt.
# Mit QIcon war der Rueckfall korrekt - KDE-Programme laden Symbole aber
# ueber KIconLoader, und der entscheidet anders. Aus der Community
# zweimal gemeldet, hier nachgestellt.
#
# Deshalb jetzt echte Bitmaps in jeder Groesse. Das ist mehr Ballast
# (rund 650 Dateien mehr), aber es haengt nicht davon ab, wie ein
# Symbol-Lader Verzeichnisse gewichtet.
GROESSEN = (16, 22, 32, 48, 64, 96, 128, 256)

# Ueber 48 px hoert die Bitmapfassung auf. Dolphin bietet 64, 96, 128 und
# 256 an, und weil unser Satz den Namen abfaengt, wird Breeze nie gefragt -
# der Loader nimmt das 48er PNG und zieht es hoch. Aus der Community
# gemeldet: "icons become pixelated when enlarging in Dolphin".
#
# Behoben ueber ein scalable-Verzeichnis mit genau der Quelle, aus der
# auch die PNGs entstehen. Ab MinSize gewinnt es, darunter bleiben die
# Bitmaps unangetastet - und das muessen sie: die Formen liegen auf einem
# 32er Raster, bei 16 px ist jede Kante von Hand gesetzt. Ein
# durchgehendes Scalable von 8 bis 512 haette genau das zerstoert.
#
# MinSize 64, nicht 49: zwischen 49 und 63 laege der Abstand zum
# 48er-Bitmap naeher, der Loader wuerde ohnehin dieses waehlen. So steht
# die Grenze dort, wo Dolphin seine naechste Stufe hat.
SKALIERBAR_AB = 64
SKALIERBAR_BIS = 512

# Die Symbolfarben sind bewusst NICHT die Farben der Oberflaeche.
#
# Windows NT hat seine Symbole nicht mit dem Farbschema mitgefaerbt: der
# Ordner blieb gelb, das Laufwerk grau, egal welche Farbwelt eingestellt
# war. Genau das wird hier nachgebildet - nur Linien- und Akzentfarbe
# folgen der Variante, die Gegenstandsfarben bleiben.
GEGENSTAND = {
    "o_hell":   "#FFE870",   # Ordner: Lichtkante
    "o_mitte":  "#E8C020",   # Ordner: Flaeche
    "o_dunkel": "#8A6A10",   # Ordner: Schattenkante
    "m_hell":   "#F0F0F0",   # Metall/Kunststoff: Lichtkante
    "m_mitte":  "#C0C0C0",   # Metall: Flaeche - das Win95-Grau
    "m_dunkel": "#707070",   # Metall: Schattenkante
    "papier":   "#FFFFFF",
    "glas":     "#88B8C8",   # Bildschirme, CDs
    "rot":      "#A83232",
    "gruen":    "#39734A",
}

PALETTEN = {
    "teal":   {"linie": "#202628", "flaeche": "#D8D8D0", "hell": "#F0F0E8",
               "akzent": "#287F8C", "warn": "#C87922", "gut": "#39734A",
               "papier": "#FFFFFF", "gold": "#D6A23A"},
    "desert": {"linie": "#2A2620", "flaeche": "#D8D0C0", "hell": "#F0EADC",
               "akzent": "#8C6A28", "warn": "#C87922", "gut": "#5A6B32",
               "papier": "#FFFFFF", "gold": "#D6A23A"},
    "lilac":  {"linie": "#252230", "flaeche": "#D8D8D0", "hell": "#F0F0E8",
               "akzent": "#6A5A8C", "warn": "#C87922", "gut": "#39734A",
               "papier": "#FFFFFF", "gold": "#D6A23A"},
}
for _p in PALETTEN.values():
    _p.update(GEGENSTAND)


class Zeichner:
    """Zeichnet auf einem 32x32-Raster; die Ausgabe wird skaliert."""

    def __init__(self, p):
        self.p = p

    # -- Bausteine ------------------------------------------------------
    def blatt(self, x=8, y=4, b=16, h=24, farbe=None):
        """Ein Dokument mit umgeknickter Ecke - die Grundform vieler
        Datei-Symbole."""
        f = farbe or self.p["papier"]
        knick = 6
        return (f'<path d="M{x},{y} h{b-knick} l{knick},{knick} v{h-knick} '
                f'h{-b} z" fill="{f}" stroke="{self.p["linie"]}" '
                f'stroke-width="1.5"/>'
                f'<path d="M{x+b-knick},{y} v{knick} h{knick} z" '
                f'fill="{self.p["flaeche"]}" stroke="{self.p["linie"]}" '
                f'stroke-width="1.5"/>')

    def zeilen(self, x=11, y=13, b=10, n=3, farbe=None):
        f = farbe or self.p["linie"]
        return "".join(
            f'<rect x="{x}" y="{y + i*4}" width="{b}" height="1.5" fill="{f}"/>'
            for i in range(n))

    def pfeil(self, richtung, farbe=None, mx=16, my=16, gr=9):
        """Ein massives Dreieck. Bei 16 px ist alles andere Matsch."""
        f = farbe or self.p["akzent"]
        pkt = {
            "links":  f"{mx-gr},{my} {mx+gr//2},{my-gr} {mx+gr//2},{my+gr}",
            "rechts": f"{mx+gr},{my} {mx-gr//2},{my-gr} {mx-gr//2},{my+gr}",
            "hoch":   f"{mx},{my-gr} {mx-gr},{my+gr//2} {mx+gr},{my+gr//2}",
            "runter": f"{mx},{my+gr} {mx-gr},{my-gr//2} {mx+gr},{my-gr//2}",
        }[richtung]
        return (f'<polygon points="{pkt}" fill="{f}" '
                f'stroke="{self.p["linie"]}" stroke-width="1.2" '
                f'stroke-linejoin="round"/>')

    def ordner(self, x=3, y=8, b=26, h=18, farbe=None):
        f = farbe or self.p["gold"]
        return (f'<path d="M{x},{y+4} v{h-4} h{b} v{-h+2} h{-b//2} '
                f'l-3,-3 h{-b//2+3} z" fill="{f}" '
                f'stroke="{self.p["linie"]}" stroke-width="1.5" '
                f'stroke-linejoin="round"/>')

    def lupe(self, cx=14, cy=14, r=7):
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{self.p["hell"]}" '
                f'stroke="{self.p["linie"]}" stroke-width="2"/>'
                f'<line x1="{cx+r-1}" y1="{cy+r-1}" x2="{cx+r+7}" '
                f'y2="{cy+r+7}" stroke="{self.p["linie"]}" stroke-width="3" '
                f'stroke-linecap="round"/>')

    def kreuz(self, cx=16, cy=16, r=8, farbe=None):
        f = farbe or self.p["linie"]
        return (f'<line x1="{cx-r}" y1="{cy-r}" x2="{cx+r}" y2="{cy+r}" '
                f'stroke="{f}" stroke-width="3.5" stroke-linecap="round"/>'
                f'<line x1="{cx+r}" y1="{cy-r}" x2="{cx-r}" y2="{cy+r}" '
                f'stroke="{f}" stroke-width="3.5" stroke-linecap="round"/>')

    def plus(self, cx=16, cy=16, r=8, farbe=None):
        f = farbe or self.p["gut"]
        return (f'<line x1="{cx-r}" y1="{cy}" x2="{cx+r}" y2="{cy}" '
                f'stroke="{f}" stroke-width="4" stroke-linecap="round"/>'
                f'<line x1="{cx}" y1="{cy-r}" x2="{cx}" y2="{cy+r}" '
                f'stroke="{f}" stroke-width="4" stroke-linecap="round"/>')

    def minus(self, cx=16, cy=16, r=8, farbe=None):
        f = farbe or self.p["warn"]
        return (f'<line x1="{cx-r}" y1="{cy}" x2="{cx+r}" y2="{cy}" '
                f'stroke="{f}" stroke-width="4" stroke-linecap="round"/>')

    def kasten(self, x, y, b, h, farbe=None, rand=None):
        return (f'<rect x="{x}" y="{y}" width="{b}" height="{h}" '
                f'fill="{farbe or self.p["hell"]}" '
                f'stroke="{rand or self.p["linie"]}" stroke-width="1.5"/>')

    # -- Bausteine fuer Shell-Symbole -----------------------------------
    def nt_ordner(self, offen=False, x=2, y=7, b=28, h=19):
        """Der gelbe Ordner - das meistgesehene Symbol ueberhaupt.

        Aufbau wie bei NT: Ruecken hinten, Lasche oben links, Deckel
        vorn, dazu eine Lichtkante oben und eine Schattenkante unten.
        """
        p = self.p
        lasche = b // 2
        ruecken = (f'<path d="M{x},{y+3} v{h-3} h{b} v{-h+1} h{-lasche} '
                   f'l-3,-3 z" fill="{p["o_mitte"]}" stroke="{p["linie"]}" '
                   f'stroke-width="1.5" stroke-linejoin="round"/>')
        if not offen:
            kanten = (f'<line x1="{x+2}" y1="{y+5}" x2="{x+b-2}" y2="{y+5}" '
                      f'stroke="{p["o_hell"]}" stroke-width="1.5"/>'
                      f'<line x1="{x+2}" y1="{y+h-1}" x2="{x+b-2}" '
                      f'y2="{y+h-1}" stroke="{p["o_dunkel"]}" '
                      f'stroke-width="1.5"/>')
            return ruecken + kanten
        # Offen: der Deckel kippt nach vorn weg und gibt den Ruecken frei.
        # Er muss deutlich heller sein als der Ruecken, sonst sieht der
        # Ordner bei 16 px nur nach einem schiefen Kasten aus.
        deckel = (f'<path d="M{x+1},{y+h+3} l6,-13 h{b+1} l-6,13 z" '
                  f'fill="{p["o_hell"]}" stroke="{p["linie"]}" '
                  f'stroke-width="1.5" stroke-linejoin="round"/>'
                  f'<line x1="{x+8}" y1="{y+h-8}" x2="{x+b+1}" y2="{y+h-8}" '
                  f'stroke="{p["o_dunkel"]}" stroke-width="1"/>')
        return ruecken + deckel

    def marke(self, inhalt, mx=22, my=21, r=8):
        """Kleines Abzeichen unten rechts auf einem Ordner.

        Damit werden aus einem Ordner zwanzig: folder-music,
        folder-videos, folder-print. Ein eigenes Symbol je Variante zu
        zeichnen waere zwanzigfache Arbeit fuer denselben Wiedererkennungs-
        wert.
        """
        return (f'<circle cx="{mx}" cy="{my}" r="{r}" '
                f'fill="{self.p["flaeche"]}" stroke="{self.p["linie"]}" '
                f'stroke-width="1.5"/>'
                f'<g transform="translate({mx},{my}) scale(0.42) '
                f'translate(-16,-16)">{inhalt}</g>')

    def geraet(self, x=3, y=10, b=26, h=13, farbe=None):
        """Ein Kasten mit NT-typischer 3D-Kante: hell oben, dunkel unten."""
        p = self.p
        f = farbe or p["m_mitte"]
        return (f'<rect x="{x}" y="{y}" width="{b}" height="{h}" fill="{f}" '
                f'stroke="{p["linie"]}" stroke-width="1.5"/>'
                f'<line x1="{x+1.5}" y1="{y+1.5}" x2="{x+b-1.5}" y2="{y+1.5}" '
                f'stroke="{p["m_hell"]}" stroke-width="1.5"/>'
                f'<line x1="{x+1.5}" y1="{y+h-1.5}" x2="{x+b-1.5}" '
                f'y2="{y+h-1.5}" stroke="{p["m_dunkel"]}" stroke-width="1.5"/>')

    def monitor(self, glas=None):
        p = self.p
        return (self.kasten(3, 5, 26, 19, p["m_mitte"]) +
                f'<rect x="6" y="8" width="20" height="13" '
                f'fill="{glas or p["glas"]}" stroke="{p["linie"]}" '
                f'stroke-width="1"/>' +
                self.kasten(12, 24, 8, 3, p["m_dunkel"]) +
                self.kasten(8, 27, 16, 3, p["m_mitte"]))

    def scheibe(self, cx=16, cy=16, r=12, farbe=None):
        p = self.p
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{farbe or p["glas"]}" stroke="{p["linie"]}" '
                f'stroke-width="1.5"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{r*0.45:.0f}" '
                f'fill="{p["flaeche"]}" stroke="{p["linie"]}" '
                f'stroke-width="1"/>'
                f'<circle cx="{cx}" cy="{cy}" r="2" fill="{p["linie"]}"/>')

    def person(self, cx=16, cy=16, s=1.0, farbe=None):
        p = self.p
        f = farbe or p["akzent"]
        k, sx, sy = 5 * s, cx, cy - 6 * s
        return (f'<circle cx="{sx}" cy="{sy}" r="{k}" fill="{f}" '
                f'stroke="{p["linie"]}" stroke-width="1.5"/>'
                f'<path d="M{cx-9*s},{cy+11*s} a{9*s},{9*s} 0 0 1 {18*s},0 z" '
                f'fill="{f}" stroke="{p["linie"]}" stroke-width="1.5"/>')

    def kreis_zeichen(self, zeichen, farbe, textfarbe="#FFFFFF"):
        p = self.p
        return (f'<circle cx="16" cy="16" r="12" fill="{farbe}" '
                f'stroke="{p["linie"]}" stroke-width="1.5"/>'
                f'<text x="16" y="23" text-anchor="middle" '
                f'font-family="sans-serif" font-size="19" font-weight="bold" '
                f'fill="{textfarbe}">{zeichen}</text>')


def symbole(z: Zeichner):
    """Name -> SVG-Inhalt. Die Namen sind die, die Dolphin und
    PCManFM-Qt tatsaechlich anfordern."""
    p = z.p
    s = {}

    # --- Navigation
    s["go-previous"] = z.pfeil("links")
    s["go-next"] = z.pfeil("rechts")
    s["go-up"] = z.pfeil("hoch")
    s["go-down"] = z.pfeil("runter")
    s["go-parent-folder"] = z.pfeil("hoch")
    s["go-home"] = (z.ordner(farbe=p["gold"]) +
                    f'<path d="M16,6 l9,8 h-4 v7 h-10 v-7 h-4 z" '
                    f'fill="{p["hell"]}" stroke="{p["linie"]}" '
                    f'stroke-width="1.5" stroke-linejoin="round"/>')

    # --- Ansichtsmodi: die auffaelligste Luecke in Dolphins Leiste
    s["view-list-icons"] = "".join(
        z.kasten(4 + sp * 12, 4 + ze * 12, 9, 9, p["akzent"])
        for ze in range(2) for sp in range(2))
    s["view-list-details"] = (
        "".join(z.kasten(4, 5 + i * 8, 6, 5, p["akzent"]) for i in range(3)) +
        "".join(f'<rect x="13" y="{6 + i*8}" width="15" height="3" '
                f'fill="{p["linie"]}"/>' for i in range(3)))
    s["view-list-text"] = s["view-list-details"]
    s["view-list-tree"] = (
        f'<line x1="7" y1="5" x2="7" y2="26" stroke="{p["linie"]}" '
        f'stroke-width="1.5"/>' +
        "".join(f'<line x1="7" y1="{9 + i*8}" x2="13" y2="{9 + i*8}" '
                f'stroke="{p["linie"]}" stroke-width="1.5"/>'
                f'<rect x="14" y="{6 + i*8}" width="13" height="6" '
                f'fill="{p["akzent"]}" stroke="{p["linie"]}" '
                f'stroke-width="1"/>' for i in range(3)))
    s["view-file-columns"] = "".join(
        z.kasten(4 + i * 9, 5, 7, 22, p["akzent"] if i == 0 else p["hell"])
        for i in range(3))
    s["view-preview"] = z.blatt() + z.lupe(cx=20, cy=20, r=6)
    s["view-sort-ascending"] = (
        z.pfeil("hoch", mx=8, my=16, gr=6) +
        "".join(f'<rect x="16" y="{7 + i*7}" width="{6 + i*4}" height="3" '
                f'fill="{p["linie"]}"/>' for i in range(3)))
    s["view-sort-descending"] = (
        z.pfeil("runter", mx=8, my=16, gr=6) +
        "".join(f'<rect x="16" y="{7 + i*7}" width="{14 - i*4}" height="3" '
                f'fill="{p["linie"]}"/>' for i in range(3)))
    s["view-sort"] = s["view-sort-ascending"]
    s["view-refresh"] = (
        f'<path d="M25,16 a9,9 0 1 1 -3,-6.7" fill="none" '
        f'stroke="{p["gut"]}" stroke-width="3.5"/>'
        f'<polygon points="26,4 26,13 17,10" fill="{p["gut"]}"/>')
    s["view-hidden"] = z.blatt() + z.kreuz(cx=20, cy=22, r=5, farbe=p["warn"])
    s["view-visible"] = z.blatt() + z.lupe(cx=20, cy=20, r=6)

    # --- Bearbeiten
    s["edit-copy"] = (z.blatt(x=4, y=3, b=14, h=20) +
                      z.blatt(x=13, y=9, b=14, h=20))
    s["edit-cut"] = (
        f'<line x1="9" y1="4" x2="21" y2="22" stroke="{p["linie"]}" '
        f'stroke-width="2"/>'
        f'<line x1="23" y1="4" x2="11" y2="22" stroke="{p["linie"]}" '
        f'stroke-width="2"/>'
        f'<circle cx="9" cy="25" r="4" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="2"/>'
        f'<circle cx="23" cy="25" r="4" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="2"/>')
    s["edit-paste"] = (
        z.kasten(6, 5, 20, 24, p["gold"]) +
        z.kasten(10, 2, 12, 6, p["flaeche"]) +
        z.kasten(10, 12, 12, 14, p["papier"]))
    s["edit-delete"] = z.blatt() + z.kreuz(cx=21, cy=22, r=6, farbe="#A83232")
    s["edit-rename"] = (
        z.blatt() +
        f'<path d="M18,22 l7,-7 3,3 -7,7 -4,1 z" fill="{p["gold"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.2"/>')
    s["edit-find"] = z.lupe()
    s["edit-clear"] = z.kreuz(farbe=p["warn"])
    s["edit-undo"] = (
        f'<path d="M8,18 a9,9 0 1 1 9,9" fill="none" stroke="{p["akzent"]}" '
        f'stroke-width="3.5"/><polygon points="3,17 13,17 8,25" '
        f'fill="{p["akzent"]}"/>')
    s["edit-redo"] = (
        f'<path d="M24,18 a9,9 0 1 0 -9,9" fill="none" stroke="{p["akzent"]}" '
        f'stroke-width="3.5"/><polygon points="29,17 19,17 24,25" '
        f'fill="{p["akzent"]}"/>')
    s["edit-select-all"] = (
        f'<rect x="4" y="4" width="24" height="24" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="1.5" stroke-dasharray="3,2"/>' +
        z.kasten(9, 9, 14, 14, p["akzent"]))

    # --- Dateien
    s["document-new"] = z.blatt() + z.plus(cx=22, cy=22, r=5)
    s["document-open"] = z.ordner(farbe=p["gold"])
    s["document-save"] = (
        z.kasten(4, 4, 24, 24, p["akzent"]) +
        z.kasten(10, 4, 12, 9, p["flaeche"]) +
        z.kasten(8, 18, 16, 10, p["hell"]))
    s["document-properties"] = z.blatt() + z.lupe(cx=21, cy=21, r=5)
    s["folder-new"] = z.ordner() + z.plus(cx=23, cy=21, r=5)
    s["list-add"] = z.plus()
    s["list-remove"] = z.minus()

    # --- Zoom
    s["zoom-in"] = z.lupe() + (
        f'<line x1="10" y1="14" x2="18" y2="14" stroke="{p["linie"]}" '
        f'stroke-width="2.5"/><line x1="14" y1="10" x2="14" y2="18" '
        f'stroke="{p["linie"]}" stroke-width="2.5"/>')
    s["zoom-out"] = z.lupe() + (
        f'<line x1="10" y1="14" x2="18" y2="14" stroke="{p["linie"]}" '
        f'stroke-width="2.5"/>')
    s["zoom-original"] = z.lupe()
    s["zoom-fit-best"] = z.lupe() + (
        f'<rect x="10" y="10" width="8" height="8" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>')

    # --- Fenster und Dialoge
    s["window-close"] = z.kreuz(farbe="#A83232")
    s["dialog-close"] = s["window-close"]
    # Der Menuepunkt "Beenden" in jedem Programm. Ohne dieses Symbol
    # kuerzt die Suche application-exit auf die Klasse und liefert unser
    # Dateisymbol - im Datei-Menue stand ein Blatt Papier neben
    # "Beenden". Tuer mit Pfeil hinaus, wie es KDE seit jeher zeigt.
    s["application-exit"] = (
        z.kasten(6, 3, 13, 26, p["m_mitte"]) +
        f'<circle cx="16" cy="16" r="1.5" fill="{p["linie"]}"/>' +
        f'<line x1="20" y1="16" x2="29" y2="16" stroke="{p["gut"]}" '
        f'stroke-width="3" stroke-linecap="round"/>'
        f'<polyline points="25,11 30,16 25,21" fill="none" '
        f'stroke="{p["gut"]}" stroke-width="3" stroke-linecap="round" '
        f'stroke-linejoin="round"/>')
    s["application-quit"] = s["application-exit"]
    s["dialog-ok"] = (
        f'<polyline points="6,17 13,24 26,8" fill="none" '
        f'stroke="{p["gut"]}" stroke-width="4" stroke-linecap="round" '
        f'stroke-linejoin="round"/>')
    s["dialog-cancel"] = z.kreuz(farbe="#A83232")
    s["tab-new"] = z.kasten(4, 8, 24, 20, p["hell"]) + z.plus(cx=16, cy=18, r=5)
    s["tab-close"] = z.kasten(4, 8, 24, 20, p["hell"]) + z.kreuz(cx=16, cy=18, r=5)

    # --- Menue und Einstellungen
    s["application-menu"] = "".join(
        f'<rect x="6" y="{7 + i*7}" width="20" height="3.5" '
        f'fill="{p["linie"]}"/>' for i in range(3))
    s["open-menu"] = s["application-menu"]
    s["show-menu"] = s["application-menu"]
    # Zahnrad, nicht Sonne. Vorher standen acht schmale Striche mit 2 px
    # Abstand um einen Kreis - aus der Community kam dafuer "looks more
    # like a gray sun". Zwei Dinge machen den Unterschied: die Zaehne
    # muessen den Kranz beruehren (hier ueberlappen sie ihn um 1 px), und
    # sie muessen breiter als der Zwischenraum sein. Dazu eine helle Nabe,
    # damit in der Mitte ein Loch sitzt und keine Scheibe.
    s["configure"] = (
        f'<circle cx="16" cy="16" r="8" fill="{p["m_mitte"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>' +
        "".join(f'<rect x="13.5" y="1.5" width="5" height="7" '
                f'fill="{p["m_mitte"]}" stroke="{p["linie"]}" '
                f'stroke-width="1.5" stroke-linejoin="round" '
                f'transform="rotate({a},16,16)"/>'
                for a in range(0, 360, 60)) +
        f'<circle cx="16" cy="16" r="8" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="2"/>'
        f'<circle cx="16" cy="16" r="3" fill="{p["flaeche"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>')
    s["settings-configure"] = s["configure"]
    s["configure-toolbars"] = s["configure"]

    # --- Sonstiges aus Dolphins Leiste
    s["view-split-left-right"] = (
        z.kasten(3, 6, 12, 20, p["hell"]) + z.kasten(17, 6, 12, 20, p["akzent"]))
    s["swap-panels"] = (z.pfeil("rechts", mx=16, my=10, gr=7) +
                        z.pfeil("links", mx=16, my=22, gr=7))
    s["view-filter"] = (
        f'<polygon points="4,5 28,5 19,16 19,27 13,23 13,16" '
        f'fill="{p["akzent"]}" stroke="{p["linie"]}" stroke-width="1.5" '
        f'stroke-linejoin="round"/>')
    s["object-locked"] = (
        z.kasten(8, 14, 16, 14, p["gold"]) +
        f'<path d="M12,14 v-4 a4,4 0 0 1 8,0 v4" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="2.5"/>')
    s["object-unlocked"] = (
        z.kasten(8, 14, 16, 14, p["hell"]) +
        f'<path d="M12,14 v-4 a4,4 0 0 1 8,0" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="2.5"/>')

    return s


def shell_symbole(z: Zeichner):
    """Orte, Geraete, Dateitypen und Programme im NT-Stil.

    Ersetzt die zuvor aus ReactOS uebernommenen Symbole. Deren Optik war
    moderner als NT 4.0 - blaue Ordner mit Verlaeufen statt gelber
    Flaechen - und passte damit nicht zum Rest des Themes.
    """
    p = z.p
    s = {}

    # ── Ordner und Orte ────────────────────────────────────────────────
    s["folder"] = z.nt_ordner()
    s["folder-open"] = z.nt_ordner(offen=True)
    s["user-home"] = z.nt_ordner() + z.marke(
        f'<path d="M16,5 l11,10 h-4 v10 h-14 v-10 h-4 z" fill="{p["rot"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>')
    s["folder-documents"] = z.nt_ordner() + z.marke(
        z.blatt(x=8, y=3, b=16, h=25) + z.zeilen(x=11, y=11, b=10, n=3))
    s["folder-music"] = z.nt_ordner() + z.marke(
        f'<path d="M12,24 v-16 l12,-3 v16" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="3"/><circle cx="9" cy="24" r="4" fill="{p["linie"]}"/>'
        f'<circle cx="21" cy="21" r="4" fill="{p["linie"]}"/>')
    s["folder-videos"] = z.nt_ordner() + z.marke(
        z.kasten(4, 8, 24, 16, p["linie"]) +
        f'<polygon points="13,13 13,23 23,18" fill="{p["papier"]}"/>')
    s["folder-pictures"] = z.nt_ordner() + z.marke(
        z.kasten(4, 7, 24, 18, p["glas"]) +
        f'<circle cx="11" cy="13" r="3" fill="{p["o_hell"]}"/>'
        f'<polygon points="6,24 14,15 20,24" fill="{p["gruen"]}"/>')
    s["folder-download"] = z.nt_ordner() + z.marke(
        z.pfeil("runter", farbe=p["gut"], gr=11))
    s["folder-publicshare"] = z.nt_ordner() + z.marke(z.person(s=1.4))
    s["folder-print"] = z.nt_ordner() + z.marke(
        z.geraet(x=4, y=12, b=24, h=12) + z.kasten(9, 4, 14, 9, p["papier"]))
    s["folder-saved-search"] = z.nt_ordner() + z.marke(z.lupe(cx=15, cy=14, r=9))
    s["folder-system"] = z.nt_ordner() + z.marke(
        f'<circle cx="16" cy="16" r="7" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="4"/>' +
        "".join(f'<rect x="14" y="1" width="4" height="7" fill="{p["linie"]}" '
                f'transform="rotate({a},16,16)"/>' for a in range(0, 360, 60)))
    s["folder-remote"] = z.nt_ordner() + z.marke(
        f'<circle cx="16" cy="16" r="11" fill="{p["glas"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>'
        f'<ellipse cx="16" cy="16" rx="5" ry="11" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="2"/>'
        f'<line x1="5" y1="16" x2="27" y2="16" stroke="{p["linie"]}" '
        f'stroke-width="2"/>')
    s["folder-network"] = s["folder-remote"]
    s["folder-applications"] = z.nt_ordner() + z.marke(
        z.kasten(4, 6, 24, 20, p["glas"]) + z.kasten(4, 6, 24, 5, p["akzent"]))
    s["folder-edit"] = z.nt_ordner() + z.marke(
        f'<path d="M6,26 l3,-8 12,-12 5,5 -12,12 z" fill="{p["o_hell"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>')
    s["folder-favorites"] = z.nt_ordner() + z.marke(
        f'<polygon points="16,4 20,13 29,13 22,19 25,28 16,22 7,28 10,19 '
        f'3,13 12,13" fill="{p["o_hell"]}" stroke="{p["linie"]}" '
        f'stroke-width="2" stroke-linejoin="round"/>')

    # Die uebrigen Ordner der Seitenleiste.
    #
    # Dolphin fragt fuer jeden XDG-Benutzerordner einen eigenen Namen an -
    # folder-desktop fuer ~/Schreibtisch, folder-templates fuer ~/Vorlagen
    # und so fort. Fehlt der Name, kuerzt die Symbolsuche ihn am
    # Bindestrich, findet unser schlichtes "folder" und hoert auf zu
    # suchen: alle Benutzerordner sehen dann gleich aus, und weil der
    # Treffer aus dem eigenen Satz kommt, wird Breeze gar nicht erst
    # gefragt. Die Marken sind deshalb bewusst massive Flaechen statt
    # feiner Linien - im Kreis bleiben bei 16 px nur rund sechs Pixel
    # uebrig, und darin ueberlebt nur eine Silhouette.
    s["folder-desktop"] = z.nt_ordner() + z.marke(
        f'<rect x="3" y="5" width="26" height="18" fill="{p["linie"]}"/>'
        f'<rect x="6" y="8" width="20" height="12" fill="{p["glas"]}"/>'
        f'<rect x="12" y="23" width="8" height="4" fill="{p["linie"]}"/>'
        f'<rect x="6" y="27" width="20" height="4" fill="{p["linie"]}"/>')
    # Vorlagen sind Blaetter zum Abpausen: ein zweites, farbiges Blatt
    # hinter dem weissen. Der Versatz ist das, was bei 16 px von
    # folder-documents unterscheidet - Zeilen taeten es dort nicht.
    s["folder-templates"] = z.nt_ordner() + z.marke(
        f'<rect x="2" y="2" width="18" height="24" fill="{p["akzent"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>'
        f'<rect x="12" y="8" width="18" height="24" fill="{p["papier"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>')
    # Wichtiges bekommt ein Ausrufezeichen statt eines zweiten Sterns:
    # neben folder-favorites waere ein Stern nicht mehr zu unterscheiden,
    # und der rote Balken ist die kraeftigste Form, die in die Marke passt.
    s["folder-important"] = z.nt_ordner() + z.marke(
        f'<rect x="12" y="2" width="9" height="18" fill="{p["rot"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>'
        f'<rect x="12" y="23" width="9" height="8" fill="{p["rot"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>')
    # Spitze Klammern wie bei applications-development, aber als dicke
    # Linien gezogen: der Schriftzug "</>" faellt in der Marke auseinander.
    # Der Abstand zwischen beiden Klammern ist das eigentliche Zeichen -
    # beruehren sie sich, wird bei 16 px ein schwarzer Klumpen daraus.
    s["folder-development"] = z.nt_ordner() + z.marke(
        f'<polyline points="10,4 2,16 10,28" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="6" stroke-linecap="round" '
        f'stroke-linejoin="round"/>'
        f'<polyline points="22,4 30,16 22,28" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="6" stroke-linecap="round" '
        f'stroke-linejoin="round"/>')
    # Spielkarte statt Joystick: ein Knauf auf einem Sockel hat dieselbe
    # Silhouette wie die Person auf folder-publicshare und ist bei 16 px
    # nur an der Farbe zu unterscheiden. Das rote Karo auf Weiss hat im
    # ganzen Satz keinen Zwilling - und Solitaer war das Spiel, das jedes
    # Windows dabei hatte.
    s["folder-games"] = z.nt_ordner() + z.marke(
        f'<rect x="6" y="2" width="21" height="28" fill="{p["papier"]}" '
        f'stroke="{p["linie"]}" stroke-width="2.5"/>'
        f'<polygon points="16,8 23,16 16,24 9,16" fill="{p["rot"]}"/>')

    # Papierkorb: bei NT ein Drahtkorb, keine Tonne
    korb = (f'<path d="M9,10 l2,18 h10 l2,-18 z" fill="{p["m_mitte"]}" '
            f'stroke="{p["linie"]}" stroke-width="1.5" '
            f'stroke-linejoin="round"/>'
            f'<ellipse cx="16" cy="10" rx="7" ry="2.5" fill="{p["m_hell"]}" '
            f'stroke="{p["linie"]}" stroke-width="1.5"/>' +
            "".join(f'<line x1="{12+i*4}" y1="12" x2="{12.8+i*3.4}" y2="27" '
                    f'stroke="{p["m_dunkel"]}" stroke-width="1"/>'
                    for i in range(3)))
    s["user-trash"] = korb
    s["user-trash-full"] = (
        f'<path d="M11,9 l3,-5 4,3 3,-4 2,6 z" fill="{p["papier"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.2"/>' + korb)

    # ── Rechner und Netz ───────────────────────────────────────────────
    s["computer"] = z.monitor()
    s["computer-laptop"] = (
        z.kasten(5, 6, 22, 15, p["m_mitte"]) +
        f'<rect x="8" y="9" width="16" height="9" fill="{p["glas"]}" '
        f'stroke="{p["linie"]}" stroke-width="1"/>' +
        f'<path d="M2,26 h28 l-3,-5 h-22 z" fill="{p["m_hell"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5" stroke-linejoin="round"/>')
    s["video-display"] = z.monitor()
    s["network-workgroup"] = (
        z.kasten(2, 4, 14, 11, p["m_mitte"]) +
        f'<rect x="4" y="6" width="10" height="7" fill="{p["glas"]}"/>' +
        z.kasten(16, 17, 14, 11, p["m_mitte"]) +
        f'<rect x="18" y="19" width="10" height="7" fill="{p["glas"]}"/>'
        f'<path d="M9,15 v4 h14 v-2" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="1.5"/>')
    s["network-server"] = (
        "".join(z.geraet(x=6, y=4 + i * 8, b=20, h=7) for i in range(3)) +
        "".join(f'<circle cx="10" cy="{7.5 + i*8}" r="1.5" '
                f'fill="{p["gruen"]}"/>' for i in range(3)))
    s["network-offline"] = s["network-workgroup"] + z.kreuz(
        cx=24, cy=8, r=6, farbe=p["rot"])

    # ── Laufwerke und Geraete ──────────────────────────────────────────
    s["drive-harddisk"] = (
        z.geraet(y=9, h=15) +
        f'<circle cx="24" cy="20" r="2" fill="{p["gruen"]}"/>'
        f'<line x1="7" y1="20" x2="19" y2="20" stroke="{p["m_dunkel"]}" '
        f'stroke-width="1.5"/>')
    s["drive-harddisk-solidstate"] = (
        z.geraet(y=9, h=15) +
        "".join(f'<rect x="{8+i*5}" y="14" width="3" height="6" '
                f'fill="{p["linie"]}"/>' for i in range(4)))
    s["drive-removable-media"] = z.geraet(y=11, h=11) + z.kasten(
        7, 14, 11, 5, p["m_dunkel"])
    s["drive-removable-media-usb"] = (
        z.kasten(4, 12, 18, 9, p["m_mitte"]) +
        z.kasten(22, 14, 7, 5, p["m_dunkel"]) +
        f'<line x1="8" y1="16.5" x2="17" y2="16.5" stroke="{p["akzent"]}" '
        f'stroke-width="2"/>')
    s["media-floppy"] = (
        z.kasten(4, 4, 24, 24, p["linie"]) +
        z.kasten(9, 4, 14, 10, p["m_mitte"]) +
        f'<rect x="17" y="6" width="4" height="6" fill="{p["m_dunkel"]}"/>' +
        z.kasten(8, 17, 16, 11, p["m_hell"]))
    s["drive-optical"] = z.geraet(y=11, h=11) + f'<circle cx="16" cy="16.5" ' \
        f'r="3.5" fill="none" stroke="{p["m_dunkel"]}" stroke-width="1.5"/>'
    s["media-optical"] = z.scheibe()
    s["media-optical-audio"] = z.scheibe() + (
        f'<path d="M14,22 v-9 l7,-2 v9" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="2"/>')
    s["media-optical-dvd"] = z.scheibe(farbe=p["akzent"])
    s["media-optical-recordable"] = z.scheibe(farbe=p["gut"])
    s["media-optical-rewritable"] = z.scheibe(farbe=p["warn"])
    s["media-flash"] = (
        z.kasten(8, 4, 16, 24, p["linie"]) +
        "".join(f'<rect x="{10+i*4}" y="7" width="3" height="6" '
                f'fill="{p["o_mitte"]}"/>' for i in range(3)))
    s["media-flash-sd"] = (
        f'<path d="M8,4 h12 l4,4 v20 h-16 z" fill="{p["akzent"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5" stroke-linejoin="round"/>' +
        "".join(f'<rect x="{10+i*4}" y="8" width="2.5" height="5" '
                f'fill="{p["m_hell"]}"/>' for i in range(3)))
    s["printer"] = (
        z.kasten(8, 3, 16, 9, p["papier"]) +
        z.geraet(x=3, y=12, b=26, h=11) +
        z.kasten(8, 20, 16, 9, p["papier"]))
    s["printer-network"] = s["printer"] + z.marke(
        # Weltkugel als Netzmarke - dasselbe Zeichen wie bei folder-remote,
        # damit "im Netz" ueberall gleich aussieht
        f'<circle cx="16" cy="16" r="12" fill="{p["glas"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>'
        f'<ellipse cx="16" cy="16" rx="5" ry="12" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="2"/>'
        f'<line x1="4" y1="16" x2="28" y2="16" stroke="{p["linie"]}" '
        f'stroke-width="2"/>', mx=24, my=24, r=7)
    s["printer-fax"] = s["printer"]
    s["scanner"] = (
        z.geraet(x=3, y=14, b=26, h=10) +
        z.kasten(7, 5, 18, 9, p["glas"]) +
        f'<line x1="9" y1="19" x2="23" y2="19" stroke="{p["rot"]}" '
        f'stroke-width="2"/>')
    s["camera-photo"] = (
        z.geraet(x=3, y=9, b=26, h=16) +
        z.kasten(11, 5, 8, 4, p["m_dunkel"]) +
        f'<circle cx="16" cy="17" r="6" fill="{p["glas"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>'
        f'<circle cx="16" cy="17" r="2.5" fill="{p["linie"]}"/>')
    s["camera-video"] = (
        z.geraet(x=2, y=10, b=19, h=13) +
        f'<polygon points="21,16 29,11 29,22 21,19" fill="{p["m_dunkel"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5" stroke-linejoin="round"/>'
        f'<circle cx="9" cy="8" r="4" fill="{p["m_hell"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>')
    s["input-mouse"] = (
        f'<path d="M16,4 a9,9 0 0 1 9,9 v9 a9,9 0 0 1 -18,0 v-9 '
        f'a9,9 0 0 1 9,-9 z" fill="{p["m_mitte"]}" stroke="{p["linie"]}" '
        f'stroke-width="1.5"/>'
        f'<line x1="16" y1="5" x2="16" y2="14" stroke="{p["linie"]}" '
        f'stroke-width="1.5"/>'
        f'<line x1="7" y1="14" x2="25" y2="14" stroke="{p["linie"]}" '
        f'stroke-width="1.5"/>')
    s["audio-input-microphone"] = (
        f'<rect x="12" y="3" width="8" height="14" rx="4" '
        f'fill="{p["m_mitte"]}" stroke="{p["linie"]}" stroke-width="1.5"/>'
        f'<path d="M8,15 a8,8 0 0 0 16,0" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="2"/>'
        f'<line x1="16" y1="23" x2="16" y2="28" stroke="{p["linie"]}" '
        f'stroke-width="2"/>')

    # ── Lautstaerke ────────────────────────────────────────────────────
    #
    # Diese vier Namen fehlten, und ihr Fehlen war schlimmer als eine
    # Luecke. Die Symbolsuche kuerzt einen unbekannten Namen an den
    # Bindestrichen, bis etwas passt: audio-volume-high wurde zu
    # audio-volume, dann zu audio - und landete auf unserem
    # audio-x-generic. Im Panel stand deshalb ein Blatt Papier mit einer
    # Note statt eines Lautsprechers, und weil der Treffer aus unserem
    # eigenen Satz kam, wurde Breeze nie gefragt. Mit kiconfinder6
    # nachgestellt.
    #
    # Merksatz fuer neue Symbole: ein kurzer Name faengt alle laengeren
    # ab, die mit ihm beginnen. Wer audio-x-generic mitliefert, muss die
    # audio-volume-Reihe mitliefern.
    def _lautsprecher(bogen, zusatz=""):
        # Kasten und Trichter in einem Zug, damit an der Naht keine
        # Linie durchs Symbol laeuft.
        korpus = (
            f'<path d="M4,12 h5 l7,-6 v20 l-7,-6 h-5 z" '
            f'fill="{p["m_mitte"]}" stroke="{p["linie"]}" '
            f'stroke-width="1.5" stroke-linejoin="round"/>')
        # Die Boegen muessen auf der Mittelachse des Korpus sitzen, also
        # auf y=16. Sie standen 2 px zu tief, was aus der Community
        # gemeldet wurde: Der Anfangspunkt war 13-2,5i und die Bogenhoehe
        # 10+5i, macht eine Mitte bei 13-2,5i+(10+5i)/2 = 18. Der
        # Startpunkt muss um dieselben 2 px hoeher, dann hebt sich das i
        # wieder weg und jeder Bogen ist um 16 zentriert.
        wellen = "".join(
            f'<path d="M{18 + i*4},{11 - i*2.5} a{5 + i*4},{5 + i*4} 0 0 1 '
            f'0,{10 + i*5}" fill="none" stroke="{p["linie"]}" '
            f'stroke-width="2" stroke-linecap="round"/>'
            for i in range(bogen))
        return korpus + wellen + zusatz

    # Dieselbe Falle, andere Namen: das Lautstaerkemenue und die
    # Systemeinstellungen fragen nach Geraeten, und auch die landeten
    # bisher auf audio-x-generic. Gefunden mit
    # tools/pruefe-symbolfalle.py.
    s["audio-card"] = (
        z.kasten(4, 10, 24, 14, p["m_mitte"]) +
        f'<rect x="7" y="24" width="4" height="5" fill="{p["m_dunkel"]}" '
        f'stroke="{p["linie"]}" stroke-width="1"/>'
        f'<rect x="21" y="24" width="4" height="5" fill="{p["m_dunkel"]}" '
        f'stroke="{p["linie"]}" stroke-width="1"/>'
        f'<circle cx="12" cy="17" r="3.5" fill="{p["m_dunkel"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>'
        f'<circle cx="22" cy="17" r="2.5" fill="{p["m_dunkel"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>')
    s["audio-headphones"] = (
        f'<path d="M5,20 v-4 a11,11 0 0 1 22,0 v4" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="2.5"/>' +
        z.kasten(2, 18, 6, 10, p["m_mitte"]) +
        z.kasten(24, 18, 6, 10, p["m_mitte"]))
    s["audio-headset"] = (
        s["audio-headphones"] +
        f'<path d="M8,26 q-4,4 0,4 h5" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="2"/>')

    s["audio-volume-high"] = _lautsprecher(3)
    s["audio-volume-medium"] = _lautsprecher(2)
    s["audio-volume-low"] = _lautsprecher(1)
    s["audio-volume-muted"] = _lautsprecher(
        0,
        f'<line x1="19" y1="11" x2="29" y2="21" stroke="{p["rot"]}" '
        f'stroke-width="3" stroke-linecap="round"/>'
        f'<line x1="29" y1="11" x2="19" y2="21" stroke="{p["rot"]}" '
        f'stroke-width="3" stroke-linecap="round"/>')
    s["pda"] = (
        z.kasten(8, 2, 16, 28, p["m_mitte"]) +
        f'<rect x="11" y="5" width="10" height="16" fill="{p["glas"]}" '
        f'stroke="{p["linie"]}" stroke-width="1"/>'
        f'<circle cx="16" cy="25" r="2.5" fill="{p["m_dunkel"]}" '
        f'stroke="{p["linie"]}" stroke-width="1"/>')
    s["phone"] = s["pda"]

    # ── Programme und Einstellungen ────────────────────────────────────
    # Dasselbe Zahnrad wie bei "configure", nur einen Tick groesser -
    # aus demselben Grund: Zaehne am Kranz, Nabe in der Mitte. Vorher
    # standen die Zaehne als einzelne dunkle Bloecke davor.
    s["applications-system"] = (
        f'<circle cx="16" cy="16" r="9" fill="{p["m_mitte"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>' +
        "".join(f'<rect x="13" y="0.5" width="6" height="8" '
                f'fill="{p["m_mitte"]}" stroke="{p["linie"]}" '
                f'stroke-width="1.5" stroke-linejoin="round" '
                f'transform="rotate({a},16,16)"/>'
                for a in range(0, 360, 60)) +
        f'<circle cx="16" cy="16" r="9" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="2"/>'
        f'<circle cx="16" cy="16" r="3.5" fill="{p["flaeche"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>')
    s["preferences-system"] = s["applications-system"]

    # ── Die Kategorien der Systemeinstellungen ─────────────────────────
    #
    # Aus der Community: In der Seitenleiste der Systemeinstellungen trug
    # ein Dutzend Kategorien dasselbe Zahnrad - Sitzung, Benutzer,
    # Energie, Datum, Anmeldebildschirm, Fensterverwaltung, Netzwerk,
    # Laufwerke, Bluetooth. Ursache ist die Namenskuerzung: Alle heissen
    # preferences-system-<etwas>, keiner davon war gezeichnet, und die
    # Suche fiel auf unser preferences-system zurueck. Ein Symbolsatz,
    # der nur den Oberbegriff liefert, macht aus zwoelf Kategorien
    # zwoelfmal dasselbe Bild.
    #
    # Deshalb hier die Namen, die Plasmas eigene KCMs anfordern -
    # ermittelt aus /usr/share/applications/kcm_*.desktop, nicht geraten.
    s["preferences-system-time"] = (
        f'<circle cx="16" cy="16" r="12" fill="{p["papier"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>'
        f'<line x1="16" y1="16" x2="16" y2="8" stroke="{p["linie"]}" '
        f'stroke-width="2.5" stroke-linecap="round"/>'
        f'<line x1="16" y1="16" x2="22" y2="19" stroke="{p["linie"]}" '
        f'stroke-width="2.5" stroke-linecap="round"/>')
    s["preferences-system-users"] = (
        z.person(cx=12, cy=17, s=0.8, farbe=p["m_mitte"]) +
        z.person(cx=21, cy=15, s=0.85))
    s["preferences-system-power-management"] = (
        # Batterie liegend, mit Blitz. Der Stecker waere bei 16 px ein
        # Fleck; der Blitz bleibt als Silhouette lesbar.
        z.kasten(3, 10, 22, 13, p["m_mitte"]) +
        z.kasten(25, 14, 4, 5, p["m_dunkel"]) +
        f'<polygon points="15,11 9,17 13,17 11,22 18,15 14,15" '
        f'fill="{p["warn"]}" stroke="{p["linie"]}" stroke-width="1.2" '
        f'stroke-linejoin="round"/>')
    s["preferences-system-bluetooth"] = (
        f'<circle cx="16" cy="16" r="12" fill="{p["akzent"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>'
        # Die Bluetooth-Rune: Mittelachse mit zwei Dreiecken.
        f'<path d="M13,10 L20,15 L13,21 L13,10 M13,21 L20,17 L13,11" '
        f'fill="none" stroke="{p["papier"]}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<line x1="13" y1="16" x2="9" y2="13" stroke="{p["papier"]}" '
        f'stroke-width="2" stroke-linecap="round"/>'
        f'<line x1="13" y1="16" x2="9" y2="19" stroke="{p["papier"]}" '
        f'stroke-width="2" stroke-linecap="round"/>')
    s["preferences-system-network"] = (
        # Weltkugel mit Laengen- und Breitenkreis.
        f'<circle cx="16" cy="16" r="12" fill="{p["glas"]}" '
        f'stroke="{p["linie"]}" stroke-width="2"/>'
        f'<ellipse cx="16" cy="16" rx="5" ry="12" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>'
        f'<line x1="4" y1="16" x2="28" y2="16" stroke="{p["linie"]}" '
        f'stroke-width="1.5"/>'
        f'<path d="M6.5,9.5 h19 M6.5,22.5 h19" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="1.2"/>')
    s["preferences-system-login"] = (
        # Anmeldebildschirm: Monitor mit Person darauf.
        z.kasten(2, 4, 28, 20, p["m_mitte"]) +
        z.kasten(5, 7, 22, 14, p["akzent"]) +
        z.person(cx=16, cy=15, s=0.55, farbe=p["papier"]) +
        z.kasten(11, 25, 10, 3, p["m_dunkel"]))
    s["preferences-system-windows"] = (
        # Zwei versetzte Fenster mit Titelbalken - Fensterverwaltung.
        z.kasten(3, 6, 18, 15, p["papier"]) +
        f'<rect x="3" y="6" width="18" height="4" fill="{p["m_dunkel"]}" '
        f'stroke="{p["linie"]}" stroke-width="1"/>' +
        z.kasten(11, 13, 18, 15, p["papier"]) +
        f'<rect x="11" y="13" width="18" height="4" fill="{p["akzent"]}" '
        f'stroke="{p["linie"]}" stroke-width="1"/>')
    s["preferences-system-session-services"] = (
        # Dienste: gestapelte Riegel mit Statuspunkt.
        "".join(z.kasten(4, 5 + i * 8, 24, 6, p["m_mitte"]) +
                f'<circle cx="8.5" cy="{8 + i * 8}" r="1.8" '
                f'fill="{p["gut"]}"/>'
                for i in range(3)))
    s["preferences-system-splash"] = (
        z.monitor() +
        f'<circle cx="16" cy="14" r="4" fill="{p["gold"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.2"/>')

    # Wo Plasma laengere Namen anfragt, reicht ein Verweis - siehe die
    # ALIASE-Tabelle weiter unten. Hier nur die, die inhaltlich dasselbe
    # meinen wie ein bereits gezeichnetes Symbol.
    s["preferences-system-windows-actions"] = s["preferences-system-windows"]
    s["preferences-system-tabbox"] = s["preferences-system-windows"]

    # ── Der Anwendungsstarter ──────────────────────────────────────────
    #
    # Frueher zeigte "start-here" auf applications-system - dasselbe
    # Zahnrad wie die Systemeinstellungen. Im Panel standen damit zwei
    # identische Symbole nebeneinander, und der Starter, das am
    # haeufigsten geklickte Element ueberhaupt, war nicht auf einen Blick
    # zu finden.
    #
    # Stattdessen ein Sprossenfenster: Aussenrahmen, Kreuzsprosse, und in
    # jedem der vier Felder ein eigener Titelbalken - vier kleine Fenster
    # in einem grossen. Das sagt "alle Programme", ohne ein fremdes Logo
    # zu bemuehen, und bleibt bis 16 px als Fensterkreuz lesbar.
    def _feld(fx, fy, fb, fh):
        # Titelbalken oben, Scheibe darunter. Zwei Rechtecke statt eines
        # mit Rahmen: bei 16 px verschmelzen sonst Balken und Rahmen.
        return (f'<rect x="{fx}" y="{fy}" width="{fb}" height="{fh}" '
                f'fill="{p["papier"]}"/>'
                f'<rect x="{fx}" y="{fy}" width="{fb}" height="3" '
                f'fill="{p["akzent"]}"/>')

    s["start-here"] = (
        # Rahmen und Flaeche des grossen Fensters
        z.kasten(3, 3, 26, 26, p["flaeche"]) +
        # Die vier Scheiben
        _feld(6, 6, 9, 9) + _feld(17, 6, 9, 9) +
        _feld(6, 17, 9, 9) + _feld(17, 17, 9, 9) +
        # Die Kreuzsprosse zuletzt, damit sie ueber den Scheiben liegt
        f'<line x1="16" y1="4" x2="16" y2="28" stroke="{p["linie"]}" '
        f'stroke-width="2"/>'
        f'<line x1="4" y1="16" x2="28" y2="16" stroke="{p["linie"]}" '
        f'stroke-width="2"/>')
    s["applications-other"] = (
        z.kasten(3, 5, 26, 22, p["flaeche"]) +
        z.kasten(3, 5, 26, 5, p["akzent"]) +
        "".join(f'<rect x="{7+i*7}" y="14" width="5" height="5" '
                f'fill="{p["akzent"]}"/>' for i in range(3)))
    s["applications-internet"] = (
        f'<circle cx="16" cy="16" r="12" fill="{p["glas"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>'
        f'<ellipse cx="16" cy="16" rx="5" ry="12" fill="none" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>'
        f'<line x1="4" y1="16" x2="28" y2="16" stroke="{p["linie"]}" '
        f'stroke-width="1.5"/>'
        f'<path d="M6,9 a20,20 0 0 0 20,0 M6,23 a20,20 0 0 1 20,0" '
        f'fill="none" stroke="{p["linie"]}" stroke-width="1.2"/>')
    s["applications-multimedia"] = z.scheibe() + (
        f'<polygon points="13,11 13,21 22,16" fill="{p["linie"]}"/>')
    s["applications-development"] = (
        z.kasten(3, 6, 26, 20, p["papier"]) +
        f'<text x="16" y="21" text-anchor="middle" font-family="monospace" '
        f'font-size="13" font-weight="bold" fill="{p["akzent"]}">&lt;/&gt;</text>')
    s["system-users"] = z.person(cx=11, s=0.85, farbe=p["m_mitte"]) + \
        z.person(cx=20, s=0.85)
    s["system-search"] = z.lupe()
    s["help-browser"] = z.kreis_zeichen("?", p["akzent"])
    s["help-contents"] = z.kreis_zeichen("?", p["akzent"])
    s["office-calendar"] = (
        z.kasten(3, 6, 26, 23, p["papier"]) +
        z.kasten(3, 6, 26, 7, p["rot"]) +
        "".join(f'<rect x="{7+sp*7}" y="{17+ze*6}" width="4" height="4" '
                f'fill="{p["m_dunkel"]}"/>'
                for ze in range(2) for sp in range(3)))
    s["preferences-desktop-screensaver"] = z.monitor(glas=p["linie"]) + (
        f'<circle cx="12" cy="13" r="1.5" fill="{p["o_hell"]}"/>'
        f'<circle cx="20" cy="17" r="1.5" fill="{p["o_hell"]}"/>')
    s["preferences-desktop-wallpaper"] = z.monitor(glas=p["gut"]) + (
        f'<circle cx="21" cy="12" r="2.5" fill="{p["o_hell"]}"/>')
    s["preferences-desktop-theme"] = z.monitor() + (
        f'<path d="M6,21 l6,-8 5,5 4,-4 5,7 z" fill="{p["akzent"]}"/>')
    s["preferences-desktop-display"] = z.monitor()
    s["preferences-desktop-font"] = (
        z.kasten(4, 4, 24, 24, p["papier"]) +
        f'<text x="16" y="24" text-anchor="middle" font-family="serif" '
        f'font-size="22" fill="{p["linie"]}">A</text>')
    s["preferences-desktop-accessibility"] = (
        f'<circle cx="16" cy="16" r="12" fill="{p["akzent"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5"/>'
        f'<circle cx="16" cy="8" r="2.5" fill="{p["papier"]}"/>'
        f'<path d="M9,13 h14 M16,13 v7 l-4,7 M16,20 l4,7" fill="none" '
        f'stroke="{p["papier"]}" stroke-width="2.2" stroke-linecap="round"/>')

    # ── Dateitypen ─────────────────────────────────────────────────────
    s["text-x-generic"] = z.blatt() + z.zeilen(n=4)
    s["text-x-preview"] = s["text-x-generic"]
    s["application-x-generic"] = z.blatt()
    s["application-x-executable"] = z.blatt() + z.marke(
        s["applications-system"], mx=21, my=22, r=7)
    s["application-x-archive"] = (
        z.kasten(4, 7, 24, 21, p["o_mitte"]) +
        z.kasten(4, 4, 24, 5, p["o_dunkel"]) +
        z.kasten(13, 11, 6, 6, p["m_hell"]))
    s["audio-x-generic"] = z.blatt() + z.marke(
        f'<path d="M12,24 v-16 l12,-3 v16" fill="none" stroke="{p["linie"]}" '
        f'stroke-width="4"/><circle cx="9" cy="24" r="5" '
        f'fill="{p["linie"]}"/><circle cx="21" cy="21" r="5" '
        f'fill="{p["linie"]}"/>', mx=21, my=22, r=7)
    s["video-x-generic"] = z.blatt() + z.marke(
        f'<polygon points="10,8 10,24 24,16" fill="{p["linie"]}"/>',
        mx=21, my=22, r=7)
    s["image-x-generic"] = (
        z.kasten(3, 6, 26, 20, p["papier"]) +
        f'<circle cx="10" cy="13" r="3" fill="{p["o_mitte"]}"/>'
        f'<polygon points="5,25 14,14 21,25" fill="{p["gruen"]}"/>'
        f'<polygon points="17,25 23,17 28,25" fill="{p["akzent"]}"/>')
    s["font-x-generic"] = s["preferences-desktop-font"]
    s["x-office-document"] = z.blatt() + z.zeilen(n=4)
    s["x-office-presentation"] = (
        z.kasten(4, 5, 24, 17, p["papier"]) +
        f'<polygon points="8,18 14,11 18,15 24,9 24,18" fill="{p["akzent"]}"/>'
        f'<line x1="16" y1="22" x2="16" y2="27" stroke="{p["linie"]}" '
        f'stroke-width="2"/>'
        f'<line x1="9" y1="28" x2="23" y2="28" stroke="{p["linie"]}" '
        f'stroke-width="2"/>')

    # ── Status ─────────────────────────────────────────────────────────
    s["dialog-error"] = z.kreis_zeichen("!", p["rot"])
    s["dialog-warning"] = (
        f'<polygon points="16,3 30,28 2,28" fill="{p["warn"]}" '
        f'stroke="{p["linie"]}" stroke-width="1.5" stroke-linejoin="round"/>'
        f'<text x="16" y="26" text-anchor="middle" font-family="sans-serif" '
        f'font-size="17" font-weight="bold" fill="{p["linie"]}">!</text>')
    s["dialog-information"] = z.kreis_zeichen("i", p["akzent"])
    s["dialog-question"] = z.kreis_zeichen("?", p["akzent"])

    return s


# Zusaetzliche Namen, die auf ein vorhandenes Symbol zeigen.
#
# Ohne inode-directory zeigt PCManFM-Qt fuer gewoehnliche Ordner das
# Breeze-Symbol - mitten zwischen den eigenen. Der Name ist der
# MIME-Typ eines Verzeichnisses und wird oefter angefragt als "folder"
# selbst.
WEITERE_NAMEN = {
    "inode-directory":        "folder",
    "folder-blue":            "folder",
    "folder-orange":          "folder",
    # Fuer dieselbe Sache sind zwei bis drei Namen im Umlauf - Breeze legt
    # sie ebenfalls auf ein Bild. Einmal zeichnen genuegt, sonst pflegt man
    # dasselbe Symbol dreifach.
    "folder-downloads":       "folder-download",
    "folder-text":            "folder-documents",
    "folder-txt":             "folder-documents",
    "folder-image":           "folder-pictures",
    "folder-images":          "folder-pictures",
    # folder-image faengt sonst folder-image-people ab, ohne es zu
    # bedienen - der Ordner mit den Personenfotos ist ein Bilderordner,
    # also bekommt er dasselbe Bild statt eines halben Treffers.
    "folder-image-people":    "folder-pictures",
    "folder-picture":         "folder-pictures",
    "folder-sound":           "folder-music",
    "folder-video":           "folder-videos",
    "folder-public":          "folder-publicshare",
    "unknown":                "application-x-generic",
    "application-octet-stream": "application-x-generic",
    "text-plain":             "text-x-generic",
    "text-x-script":          "text-x-generic",
    "text-x-python":          "text-x-generic",
    "text-x-python3":         "text-x-generic",
    "text-html":              "text-x-generic",
    "application-pdf":        "x-office-document",
    "application-zip":        "application-x-archive",
    "application-x-tar":      "application-x-archive",
    "application-x-gzip":     "application-x-archive",
    "package-x-generic":      "application-x-archive",
    "audio-mpeg":             "audio-x-generic",
    # Damit die Klasse audio- vollstaendig ist und audio-x-generic nichts
    # mehr abfaengt, was kein Dateityp ist - siehe
    # tools/pruefe-symbolfalle.py.
    "audio-speakers":         "audio-volume-high",
    "audio-on":               "audio-volume-high",
    "audio-ready":            "audio-volume-high",
    "audio-off":              "audio-volume-muted",
    "audio-volume-high-danger":  "audio-volume-muted",
    "audio-volume-high-warning": "audio-volume-medium",
    "video-mp4":              "video-x-generic",
    "image-png":              "image-x-generic",
    "image-jpeg":             "image-x-generic",
    "user-desktop":           "video-display",
    # Der Menueeintrag "Systemeinstellungen" fragt unter diesem Namen an
    # und bekam bisher das Breeze-Symbol - mit kiconfinder6 geprueft.
    # Neben unserem Zahnrad fiel das auf.
    "systemsettings":         "applications-system",
    # Die Netzwerk-Unterpunkte meinen alle dasselbe Bild. Ohne diese
    # Verweise faengt preferences-system sie ab und sie bekaemen wieder
    # das Zahnrad - genau das, was gemeldet wurde.
    "preferences-system-network-connection": "preferences-system-network",
    "preferences-system-network-proxy":      "preferences-system-network",
    "preferences-system-network-remote":     "preferences-system-network",
    "user-trash-symbolic":    "user-trash",
    "emblem-favorite":        "folder-favorites",
    # Kickoff und seine Geschwister fragen unter mehreren Namen nach dem
    # Starter-Symbol - je nach Plasma-Fassung und Distribution. Fehlt
    # einer davon, zeigt das Panel wieder das Zahnrad des Fallbacks.
    "start-here-kde":         "start-here",
    "start-here-kde-plasma":  "start-here",
    "start-here-kde-symbolic": "start-here",
    "distributor-logo":       "start-here",
    "system-file-manager":    "folder-open",
    "system-run":             "application-x-executable",
    "utilities-terminal":     "applications-development",
}


# Verzeichnisname -> Context-Wert der index.theme.
#
# Die beiden stimmen NICHT durchgehend ueberein, und ein einfaches
# capitalize() erzeugt zwei spezifikationswidrige Werte: aus apps wird
# "Apps" statt "Applications", aus mimetypes "Mimetypes" statt
# "MimeTypes" - mit grossem T. Nachgeprueft an Breeze
# (/usr/share/icons/breeze/index.theme): dort heissen die Verzeichnisse
# apps/ und mimetypes/, die Kontexte aber Applications und MimeTypes.
#
# Gueltig sind laut Icon Theme Specification nur: Actions, Animations,
# Applications, Categories, Devices, Emblems, Emotes, International,
# MimeTypes, Places, Status.
KONTEXT_NAME = {
    "actions":   "Actions",
    "apps":      "Applications",
    "devices":   "Devices",
    "mimetypes": "MimeTypes",
    "places":    "Places",
    "status":    "Status",
    "emblems":   "Emblems",
    "categories": "Categories",
}


def index_theme(theme: Path, name="NT Legacy Icons"):
    """Schreibt die index.theme. Ohne sie ist das Verzeichnis kein Theme."""
    kontexte = sorted(d.name for d in theme.iterdir() if d.is_dir())
    verzeichnisse = [f"{k}/{g}" for k in kontexte for g in GROESSEN
                     if (theme / k / str(g)).is_dir()]
    verzeichnisse += [f"{k}/scalable" for k in kontexte
                      if (theme / k / "scalable").is_dir()]
    zeilen = ["[Icon Theme]",
              f"Name={name}",
              "Comment=Symbole im Stil von Windows NT 4.0, vollstaendig erzeugt",
              # Breeze als Rueckfallebene: was fehlt, landet ohnehin dort -
              # so steht es wenigstens ausdruecklich da.
              "Inherits=breeze,hicolor",
              f"Directories={','.join(verzeichnisse)}", ""]
    unbekannt = []
    for v in verzeichnisse:
        kontext, groesse = v.split("/")
        ctx = KONTEXT_NAME.get(kontext)
        if ctx is None:
            unbekannt.append(kontext)
            ctx = kontext.capitalize()
        if groesse == "scalable":
            zeilen += [f"[{v}]", f"Size={SKALIERBAR_AB}", f"Context={ctx}",
                       "Type=Scalable", f"MinSize={SKALIERBAR_AB}",
                       f"MaxSize={SKALIERBAR_BIS}", ""]
        else:
            zeilen += [f"[{v}]", f"Size={groesse}", f"Context={ctx}",
                       "Type=Fixed", ""]
    (theme / "index.theme").write_text("\n".join(zeilen))
    if unbekannt:
        print(f"  WARNUNG: unbekannter Kontext {sorted(set(unbekannt))} - "
              f"bitte in KONTEXT_NAME eintragen")
    return len(verzeichnisse)


def weitere_namen(theme: Path):
    """Legt die Zusatznamen als Verweise an - in derselben Groesse und
    demselben Kontext wie die Quelle."""
    angelegt = 0
    for ziel, quelle in WEITERE_NAMEN.items():
        # Auch die Vektorfassung: ein Zusatzname, den es nur als Bitmap
        # gibt, waere ueber 48 px wieder der pixelige Fall.
        for endung in (".png", ".svg"):
            for q in theme.rglob(f"{quelle}{endung}"):
                z = q.with_name(f"{ziel}{endung}")
                if z.exists() or z.is_symlink():
                    continue
                z.symlink_to(q.name)
                angelegt += 1
    return angelegt


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", type=Path)
    ap.add_argument("--palette", default="teal", choices=sorted(PALETTEN))
    ap.add_argument("--kontext", default="actions")
    args = ap.parse_args()

    z = Zeichner(PALETTEN[args.palette])

    # Kontext je Symbol. Freedesktop sucht nach Kontext, und ein Symbol im
    # falschen Verzeichnis wird schlicht nicht gefunden.
    KONTEXT = {}
    for n in symbole(z):
        KONTEXT[n] = args.kontext
    sh = shell_symbole(z)
    for n in sh:
        if n.startswith(("folder", "user-", "computer", "network")):
            KONTEXT[n] = "places"
        elif n.startswith(("drive", "media", "printer", "scanner", "camera",
                           "input-", "audio-input", "pda", "phone",
                           "video-display")):
            KONTEXT[n] = "devices"
        elif n.startswith(("text-", "application-x", "audio-x", "video-x",
                           "image-x", "font-x", "x-office")):
            KONTEXT[n] = "mimetypes"
        elif n.startswith("dialog-"):
            KONTEXT[n] = "status"
        else:
            KONTEXT[n] = "apps"
    # computer-laptop und video-display sind Geraete, keine Orte
    KONTEXT["computer-laptop"] = "devices"
    KONTEXT["video-display"] = "devices"
    KONTEXT["network-offline"] = "status"
    # Die Lautstaerke ist Zustand, kein Geraet - Breeze legt sie ebenso
    # unter status/. Im Kontext devices wuerde das Panel sie nicht finden.
    for _n in ("audio-volume-high", "audio-volume-medium",
               "audio-volume-low", "audio-volume-muted"):
        KONTEXT[_n] = "status"
    # Die Wiedergabegeraete dagegen schon - dort liegen sie auch in Breeze.
    for _n in ("audio-card", "audio-headphones", "audio-headset"):
        KONTEXT[_n] = "devices"

    alle = dict(symbole(z))
    alle.update(sh)
    geschrieben = 0

    for name, inhalt in alle.items():
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="32" '
               f'height="32" viewBox="0 0 32 32">\n'
               f'  <!-- Erzeugt von tools/gen-icons-aktionen.py -->\n'
               f'  {inhalt}\n</svg>\n')
        for g in GROESSEN:
            ziel = args.theme / KONTEXT[name] / str(g) / f"{name}.png"
            ziel.parent.mkdir(parents=True, exist_ok=True)
            # Liegt am Zielort ein Verweis aus einem frueheren Lauf,
            # schreibt magick DURCH ihn hindurch - und beschaedigt die
            # Datei, auf die er zeigt. Genau so hat ein neu gezeichnetes
            # start-here das Zahnrad von applications-system ueberschrieben,
            # auf das es vorher selbst verwiesen hatte. Der Verweis muss
            # weg, bevor hier ein echtes Symbol entsteht.
            if ziel.is_symlink():
                ziel.unlink()
            tmp = ziel.with_suffix(".svg")
            tmp.write_text(svg)
            try:
                subprocess.run(
                    ["magick", "-background", "none", "-density",
                     str(int(g * 96 / 32)), str(tmp), "-resize", f"{g}x{g}",
                     str(ziel)], check=True, capture_output=True)
                geschrieben += 1
            except subprocess.CalledProcessError as e:
                print(f"  {name} {g}px: {e.stderr.decode()[:80]}")
            finally:
                tmp.unlink(missing_ok=True)

        # Dieselbe Quelle noch einmal, unveraendert, fuer alles ueber
        # 48 px. Kein zweites Zeichnen, keine zweite Palette - was
        # Dolphin gross anzeigt, ist Zeichen fuer Zeichen dasselbe Bild
        # wie das 16er, nur ohne Rasterung.
        vek = args.theme / KONTEXT[name] / "scalable" / f"{name}.svg"
        vek.parent.mkdir(parents=True, exist_ok=True)
        if vek.is_symlink():
            vek.unlink()
        vek.write_text(svg)
        geschrieben += 1

    verweise = weitere_namen(args.theme)
    verz = index_theme(args.theme)
    print(f"  {len(alle)} Symbole, {geschrieben} Dateien, "
          f"{verweise} Zusatznamen ({args.palette}) nach {args.theme}/")
    print(f"  index.theme mit {verz} Verzeichnissen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
