#!/usr/bin/env python3
"""Erzeugt ein GRUB-Theme aus einer NT-Legacy-Palette.

Das Bootmenue sieht aus wie ein NT-Dialog: grauer Kasten mit 3D-Kante,
farbige Titelleiste, Auswahlbalken in der Akzentfarbe. Dieselbe
Formensprache wie der Startbildschirm (Splash.qml) und die
Fensterdekoration - wer den Rechner einschaltet, sieht ab der ersten
Sekunde dasselbe Design.

    ./gen-grub.py --name NTLegacyWin2k --anzeige "NT Legacy 2000" \\
                  --palette '{"flaeche": "#d4d0c8", ...}' -o ziel/

GRUB zeichnet das Menue aus einem 9-Patch: neun PNGs, von denen die
Kanten gestreckt und die Ecken fest gezeichnet werden. Die Titelleiste
steckt im oberen Rand (menu_n.png) - GRUB kennt kein eigenes Element
dafuer, aber der obere Rand darf beliebig hoch sein.

Kein Vollbild-Hintergrund: 'desktop-color' im theme.txt reicht und
haelt das Theme bei wenigen Kilobyte. Ein 1920x1080-PNG waere auf einem
4K-Schirm ohnehin falsch skaliert.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("FEHLER: Pillow fehlt (dnf install python3-pillow)", file=sys.stderr)
    sys.exit(1)

# Masse des Kastens. Rand 1 px aussen, dann die 3D-Kante, dann Flaeche -
# dieselben Werte wie in gen-plasma-svg.py, damit Bootmenue und Fenster
# denselben Rahmen tragen.
RAHMEN = 1      # schwarze Aussenlinie
BEVEL = 2       # helle bzw. dunkle 3D-Kante
TITEL = 26      # Hoehe der Titelleiste
ECKE = 8        # Kantenlaenge der Eckbilder
MENUE_B = 620   # Breite des Menuekastens, auch fuer das Titelbild


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ttf(groesse, fett=False):
    for k in ["/usr/share/fonts/google-noto/NotoSans-Bold.ttf" if fett
              else "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
              "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf" if fett
              else "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"]:
        if Path(k).exists():
            try:
                return ImageFont.truetype(k, groesse)
            except OSError:
                pass
    return ImageFont.load_default()


class Grub:
    def __init__(self, palette, ziel, name, anzeige):
        self.p = palette
        self.ziel = ziel
        self.name = name
        self.anzeige = anzeige

    def f(self, key, ersatz="#000000"):
        return self.p.get(key, ersatz)

    # ------------------------------------------------------------------
    def _kasten(self, praefix, oben_hoch, titel):
        """Ein 9-Patch.

        praefix     Dateiname-Praefix (menu, select)
        oben_hoch   Hoehe des oberen Randes
        titel       Titelleiste in den oberen Rand zeichnen?
        """
        flaeche = rgb(self.f("flaeche"))
        rahmen = rgb(self.f("rahmen"))
        hell = rgb(self.f("hell"))
        dunkel = rgb(self.f("dunkel"))
        kopf = rgb(self.f("kopf_aktiv"))

        def bild(breite, hoehe, zeichne):
            im = Image.new("RGBA", (breite, hoehe), flaeche + (255,))
            zeichne(ImageDraw.Draw(im), breite, hoehe)
            return im

        r, b = RAHMEN, BEVEL

        # Ecken oben: Aussenlinie, Lichtkante, dann Titelfarbe.
        #
        # Die linke obere Ecke traegt den Titeltext. Das ist kein
        # Schoenheitsfehler, sondern der einzige verlaessliche Weg:
        # GRUB zeichnet ein "+ label" ueber dem Menue nicht (in der
        # Test-VM mit zwei verschiedenen Schriften geprueft, auch mit
        # einer, die garantiert geladen war). Die Ecken eines 9-Patch
        # streckt GRUB dagegen NICHT - was dort steht, steht fest.
        def ecke_oben(links):
            def z(d, w, h):
                d.rectangle([0, 0, w - 1, h - 1], fill=kopf + (255,))
                # Aussenrahmen an der jeweiligen Aussenseite
                d.line([(0, 0), (w - 1, 0)], fill=rahmen + (255,))
                x = 0 if links else w - 1
                d.line([(x, 0), (x, h - 1)], fill=rahmen + (255,))
                # Lichtkante innen
                d.line([(r, r), (w - 1, r)], fill=hell + (255,))
                xi = r if links else w - 1 - r
                d.line([(xi, r), (xi, h - 1)], fill=hell + (255,))
            return bild(ECKE, oben_hoch, z)

        def ecke_unten(links):
            def z(d, w, h):
                d.rectangle([0, 0, w - 1, h - 1], fill=flaeche + (255,))
                d.line([(0, h - 1), (w - 1, h - 1)], fill=rahmen + (255,))
                x = 0 if links else w - 1
                d.line([(x, 0), (x, h - 1)], fill=rahmen + (255,))
                # Schattenkante innen
                d.line([(r, h - 1 - r), (w - 1, h - 1 - r)],
                       fill=dunkel + (255,))
                xi = r if links else w - 1 - r
                if not links:
                    d.line([(xi, 0), (xi, h - 1 - r)], fill=dunkel + (255,))
                else:
                    d.line([(xi, 0), (xi, h - 1 - r)], fill=hell + (255,))
            return bild(ECKE, ECKE, z)

        def rand_oben(d, w, h):
            d.rectangle([0, 0, w - 1, h - 1], fill=kopf + (255,))
            d.line([(0, 0), (w - 1, 0)], fill=rahmen + (255,))
            d.line([(0, r), (w - 1, r)], fill=hell + (255,))
            if titel:
                d.text((2, (h + RAHMEN + BEVEL) / 2), self.anzeige,
                       font=ttf(15, True),
                       fill=rgb(self.f("auswahl_text")) + (255,),
                       anchor="lm")

        def rand_unten(d, w, h):
            d.rectangle([0, 0, w - 1, h - 1], fill=flaeche + (255,))
            d.line([(0, h - 1), (w - 1, h - 1)], fill=rahmen + (255,))
            d.line([(0, h - 1 - r), (w - 1, h - 1 - r)], fill=dunkel + (255,))

        def rand_links(d, w, h):
            d.rectangle([0, 0, w - 1, h - 1], fill=flaeche + (255,))
            d.line([(0, 0), (0, h - 1)], fill=rahmen + (255,))
            d.line([(r, 0), (r, h - 1)], fill=hell + (255,))

        def rand_rechts(d, w, h):
            d.rectangle([0, 0, w - 1, h - 1], fill=flaeche + (255,))
            d.line([(w - 1, 0), (w - 1, h - 1)], fill=rahmen + (255,))
            d.line([(w - 1 - r, 0), (w - 1 - r, h - 1)], fill=dunkel + (255,))

        teile = {
            "nw": ecke_oben(True),
            "ne": ecke_oben(False),
            "sw": ecke_unten(True),
            "se": ecke_unten(False),
            "n": bild(self.titelrand() if titel else 1,
                      oben_hoch, rand_oben),
            "s": bild(1, ECKE, rand_unten),
            "w": bild(ECKE, 1, rand_links),
            "e": bild(ECKE, 1, rand_rechts),
            "c": bild(1, 1, lambda d, w, h: d.point((0, 0), flaeche + (255,))),
        }
        for teil, im in teile.items():
            im.save(self.ziel / f"{praefix}_{teil}.png")

    def kasten_menue(self):
        """Der Menuekasten - oberer Rand traegt die Titelleiste."""
        self._kasten("menu", RAHMEN + BEVEL + TITEL, titel=True)

    def titelrand(self):
        """Der obere Rand des Kastens - mit dem Titel darin.

        Drei Wege ausprobiert, zwei davon in der Test-VM verworfen:

          1. "+ label" ueber dem Menue: wird nicht gezeichnet. Auch
             nicht mit einer Schrift, die nachweislich geladen war.
          2. "+ image" ueber dem Menue: ebenfalls unsichtbar - das
             boot_menu fuellt seinen Bereich samt Rand und deckt alles
             zu, was danach kommt.
          3. Titel in die linke obere Ecke: sichtbar, aber die Ecken
             bestimmen den Innenrand des Menues - bei 230 px Titel stand
             die Haelfte jedes Eintrags ausserhalb des Kastens.

        Bleibt der obere Rand (menu_n). GRUB streckt ihn zwischen die
        Ecken, also auf MENUE_B - 2 * ECKE Pixel. Genau in dieser Breite
        wird er hier gezeichnet - dann ist die Streckung ein 1:1-Fall
        und der Text bleibt unverzerrt. Das haelt nur, solange die
        Menuebreite in theme.txt dieselbe Konstante benutzt.
        """
        return MENUE_B - 2 * ECKE

    def kasten_auswahl(self):
        """Der Auswahlbalken. Vollton in der Akzentfarbe, ohne Rand -
        so markiert NT einen ausgewaehlten Eintrag in einer Liste."""
        auswahl = rgb(self.f("auswahl")) + (255,)
        for teil, (w, h) in {"c": (1, 1), "n": (1, 1), "s": (1, 1),
                             "w": (1, 1), "e": (1, 1), "nw": (1, 1),
                             "ne": (1, 1), "sw": (1, 1), "se": (1, 1)}.items():
            im = Image.new("RGBA", (w, h), auswahl)
            im.save(self.ziel / f"select_{teil}.png")

    # ------------------------------------------------------------------
    def theme_txt(self):
        # Keine eigene Schrift.
        #
        # Der erste Entwurf lieferte eine mit grub2-mkfont erzeugte
        # .pf2 mit (90 KB je Variante). In der Test-VM wurde sie laut
        # grub.cfg per loadfont geladen, der Name im Dateikopf stimmte
        # mit item_font ueberein - und GRUB zeichnete trotzdem seine
        # eingebaute Schrift. Auch mit 20 statt 16 Pixel: kein
        # Unterschied im Bild.
        #
        # Statt 900 KB mitzuschleppen, die nichts bewirken, bleibt
        # item_font weg. GRUB nimmt dann seine Standardschrift - genau
        # das, was ohnehin zu sehen war, und sie passt mit ihrem
        # Bitmap-Charakter gut zu einem NT-Bootmenue.
        return f"""# NT Legacy - GRUB-Theme, erzeugt von tools/gen-grub.py
#
# Das Bootmenue in der Formensprache des Themes: ein NT-Dialog mit
# Titelleiste. Nicht von Hand aendern - der naechste build.py-Lauf
# ueberschreibt die Datei.

title-text: ""
desktop-color: "{self.f('desktop')}"

# Der Kasten. Die Titelleiste steckt im oberen Rand des 9-Patch,
# deshalb sitzt der erste Eintrag {RAHMEN + BEVEL + TITEL} Pixel unter dem oberen Rand.
+ boot_menu {{
    left                       = 50%-{MENUE_B // 2}
    top                        = 30%
    width                      = {MENUE_B}
    height                     = 260
    item_color                 = "{self.f('text')}"
    selected_item_color        = "{self.f('auswahl_text')}"
    item_height                = 26
    item_padding               = 12
    item_spacing               = 2
    icon_width                 = 0
    icon_height                = 0
    menu_pixmap_style          = "menu_*.png"
    selected_item_pixmap_style = "select_*.png"
    scrollbar                  = false
}}

# Der Countdown, im Stil einer NT-Statuszeile unter dem Kasten.
+ label {{
    left  = 50%-{MENUE_B // 2}
    top   = 30%+272
    width = {MENUE_B}
    align = "center"
    id    = "__timeout__"
    text  = "Starting in %d s"
    color = "{self.f('auswahl_text')}"
}}
"""

    def erzeuge(self):
        self.ziel.mkdir(parents=True, exist_ok=True)
        self.kasten_menue()
        self.kasten_auswahl()
        (self.ziel / "theme.txt").write_text(self.theme_txt())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="Verzeichnisname, z.B. NTLegacyWin2k")
    ap.add_argument("--anzeige", required=True, help="Titel im Bootmenue")
    ap.add_argument("--palette", required=True, help="Palette als JSON")
    ap.add_argument("-o", "--ausgabe", type=Path, required=True)
    args = ap.parse_args()

    palette = json.loads(args.palette)
    ziel = args.ausgabe / args.name
    Grub(palette, ziel, args.name, args.anzeige).erzeuge()
    print(f"  grub/{args.name}/  ({len(list(ziel.glob('*.png')))} Bilder)")


if __name__ == "__main__":
    main()
