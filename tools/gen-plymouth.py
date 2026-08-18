#!/usr/bin/env python3
"""Erzeugt ein Plymouth-Theme aus einer NT-Legacy-Palette.

Der Startbildschirm zeigt denselben Kasten wie Splash.qml: NT-Dialog
mit Titelleiste und Fortschrittsbalken. Damit ist die Kette geschlossen -
GRUB, Boot-Splash und Plasma-Startbildschirm sehen gleich aus.

    ./gen-plymouth.py --name nt-legacy-win2k --anzeige "NT Legacy 2000" \\
                      --palette '{"flaeche": "#d4d0c8", ...}' -o ziel/

Zwei Dinge, die ein Boot-Splash koennen MUSS und die man beim Bauen
leicht vergisst:

  * Die Passwortabfrage. Auf einem verschluesselten System fragt
    Plymouth nach der Passphrase. Ein Theme ohne diese Funktion zeigt
    einen stummen Bildschirm - der Rechner wartet auf eine Eingabe, und
    niemand sieht, worauf. Das macht die Platte nicht kaputt, aber es
    sieht aus, als haenge der Start.
  * Meldungen. systemd schickt Texte ueber denselben Weg ("Press any
    key to abort"), und fsck-Fortschritt ebenso.

Beides ist unten umgesetzt. Der Text kommt aus Image.Text() - die
Schrift dafuer stellt Plymouth, nicht das Theme.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("FEHLER: Pillow fehlt (dnf install python3-pillow)", file=sys.stderr)
    sys.exit(1)

BREITE = 460          # wie Splash.qml: Math.min(width * 0.5, 460)
HOEHE = 150
TITEL = 24
RAND = 1
BALKEN_H = 14


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def schrift(groesse, fett=False):
    kandidaten = [
        "/usr/share/fonts/google-noto/NotoSans-Bold.ttf" if fett
        else "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf" if fett
        else "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
    ]
    for k in kandidaten:
        if Path(k).exists():
            try:
                return ImageFont.truetype(k, groesse)
            except OSError:
                pass
    return ImageFont.load_default()


class Plymouth:
    def __init__(self, palette, ziel, name, anzeige):
        self.p = palette
        self.ziel = ziel
        self.name = name
        self.anzeige = anzeige

    def f(self, key, ersatz="#000000"):
        return self.p.get(key, ersatz)

    # ------------------------------------------------------------------
    def dialog(self):
        """Der Kasten samt Titelleiste und beschrifteter Titelzeile.

        Als ein Bild und nicht als Einzelteile: Plymouth-Skripte koennen
        zwar stapeln, aber jede Sprite ist eine eigene Ebene mit eigener
        Position - bei einem Kasten, dessen Teile fest zueinander stehen,
        ist ein Bild einfacher und sieht auf jeder Aufloesung gleich aus.
        """
        flaeche = rgb(self.f("flaeche"))
        rahmen = rgb(self.f("rahmen"))
        kopf = rgb(self.f("kopf_aktiv"))
        kopftext = rgb(self.f("auswahl_text"))

        im = Image.new("RGBA", (BREITE, HOEHE), flaeche + (255,))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, BREITE - 1, HOEHE - 1], outline=rahmen + (255,))
        d.rectangle([RAND, RAND, BREITE - 1 - RAND, RAND + TITEL],
                    fill=kopf + (255,))
        d.text((9, RAND + TITEL // 2), self.anzeige, font=schrift(13, True),
               fill=kopftext + (255,), anchor="lm")
        im.save(self.ziel / "dialog.png")

    def balken(self):
        """Rinne und Fuellung des Fortschrittsbalkens.

        Die Fuellung ist ein Pixel breit und wird im Skript gestreckt -
        so braucht der Balken kein Bild je Fortschrittsstufe.
        """
        rahmen = rgb(self.f("rahmen"))
        dunkel = rgb(self.f("dunkel"))
        akzent = rgb(self.f("kopf_aktiv"))

        breite = BREITE - 28
        track = Image.new("RGBA", (breite, BALKEN_H), dunkel + (255,))
        d = ImageDraw.Draw(track)
        d.rectangle([0, 0, breite - 1, BALKEN_H - 1], outline=rahmen + (255,))
        track.save(self.ziel / "bar-track.png")

        fill = Image.new("RGBA", (1, BALKEN_H - 4), akzent + (255,))
        fill.save(self.ziel / "bar-fill.png")

    def bullet(self):
        """Ein Kaestchen je eingegebenem Zeichen der Passphrase.

        NT zeigte Sternchen; ein gefuelltes Quadrat ist naeher an dem,
        was Plymouth ueblicherweise darstellt, und bei 10 px lesbarer.
        """
        akzent = rgb(self.f("kopf_aktiv"))
        rahmen = rgb(self.f("rahmen"))
        im = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 9, 9], fill=akzent + (255,), outline=rahmen + (255,))
        im.save(self.ziel / "bullet.png")

    # ------------------------------------------------------------------
    def script(self):
        t = rgb(self.f("text"))
        # Image.Text() erwartet Farbanteile von 0 bis 1.
        tr, tg, tb = (c / 255 for c in t)
        return f"""// NT Legacy - Plymouth-Theme, erzeugt von tools/gen-plymouth.py
//
// Derselbe Kasten wie im Plasma-Startbildschirm. Nicht von Hand
// aendern - der naechste build.py-Lauf ueberschreibt die Datei.

Window.SetBackgroundTopColor({", ".join(f"{c/255:.4f}" for c in rgb(self.f("desktop")))});
Window.SetBackgroundBottomColor({", ".join(f"{c/255:.4f}" for c in rgb(self.f("desktop")))});

dialog.image = Image("dialog.png");
dialog.sprite = Sprite(dialog.image);
dialog.x = Window.GetX() + (Window.GetWidth() - dialog.image.GetWidth()) / 2;
dialog.y = Window.GetY() + (Window.GetHeight() - dialog.image.GetHeight()) / 2;
dialog.sprite.SetPosition(dialog.x, dialog.y, 0);

track.image = Image("bar-track.png");
track.sprite = Sprite(track.image);
track.x = dialog.x + 14;
track.y = dialog.y + {HOEHE} - {BALKEN_H} - 14;
track.sprite.SetPosition(track.x, track.y, 1);

fill.image = Image("bar-fill.png");
fill.sprite = Sprite();
fill.sprite.SetPosition(track.x + 2, track.y + 2, 2);

// ── Fortschritt ────────────────────────────────────────────────────
// Plymouth ruft das mit der geschaetzten Bootdauer und dem Anteil auf.
fun fortschritt(dauer, anteil) {{
    breite = ({BREITE} - 28 - 4) * anteil;
    if (breite < 1) breite = 1;
    fill.sprite.SetImage(fill.image.Scale(breite, {BALKEN_H - 4}));
}}
Plymouth.SetBootProgressFunction(fortschritt);

// ── Passwortabfrage ────────────────────────────────────────────────
// Ohne diese Funktion bleibt der Bildschirm bei einer verschluesselten
// Platte stumm stehen: Plymouth wartet auf die Eingabe, zeigt aber
// nichts an. Der Aufforderungstext kommt vom System.
bullet.image = Image("bullet.png");
bullets = [];
prompt.sprite = Sprite();

fun passwort(aufforderung, anzahl) {{
    fill.sprite.SetOpacity(0);
    track.sprite.SetOpacity(0);

    prompt.image = Image.Text(aufforderung, {tr:.4f}, {tg:.4f}, {tb:.4f});
    prompt.sprite.SetImage(prompt.image);
    prompt.sprite.SetPosition(
        dialog.x + 14,
        dialog.y + {TITEL} + 22, 3);
    prompt.sprite.SetOpacity(1);

    for (i = 0; i < anzahl || i < bullets.GetSize(); i++) {{
        if (i < anzahl) {{
            if (!bullets[i]) bullets[i] = Sprite(bullet.image);
            bullets[i].SetPosition(dialog.x + 16 + i * 13,
                                   dialog.y + {HOEHE} - 34, 3);
            bullets[i].SetOpacity(1);
        }} else if (bullets[i]) {{
            bullets[i].SetOpacity(0);
        }}
    }}
}}
Plymouth.SetDisplayPasswordFunction(passwort);

// ── Zurueck zur normalen Anzeige ───────────────────────────────────
fun normal() {{
    prompt.sprite.SetOpacity(0);
    for (i = 0; i < bullets.GetSize(); i++) {{
        if (bullets[i]) bullets[i].SetOpacity(0);
    }}
    track.sprite.SetOpacity(1);
    fill.sprite.SetOpacity(1);
}}
Plymouth.SetDisplayNormalFunction(normal);

// ── Meldungen ──────────────────────────────────────────────────────
// systemd schickt hierueber Texte wie "Press any key to abort".
meldung.sprite = Sprite();
fun meldung(text) {{
    meldung.image = Image.Text(text, {tr:.4f}, {tg:.4f}, {tb:.4f});
    meldung.sprite.SetImage(meldung.image);
    meldung.sprite.SetPosition(
        Window.GetX() + (Window.GetWidth() - meldung.image.GetWidth()) / 2,
        dialog.y + {HOEHE} + 24, 4);
}}
Plymouth.SetMessageFunction(meldung);

// Beim Herunterfahren laeuft der Balken rueckwaerts leer - ohne diese
// Funktion bliebe er auf dem letzten Stand des Startvorgangs stehen.
fun beenden() {{
    fill.sprite.SetOpacity(0);
}}
Plymouth.SetQuitFunction(beenden);
"""

    def plymouth_datei(self):
        return f"""[Plymouth Theme]
Name={self.anzeige}
Description=Startbildschirm im Stil von Windows NT
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/{self.name}
ScriptFile=/usr/share/plymouth/themes/{self.name}/nt-legacy.script
"""

    def erzeuge(self):
        self.ziel.mkdir(parents=True, exist_ok=True)
        self.dialog()
        self.balken()
        self.bullet()
        (self.ziel / "nt-legacy.script").write_text(self.script())
        (self.ziel / f"{self.name}.plymouth").write_text(self.plymouth_datei())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--anzeige", required=True)
    ap.add_argument("--palette", required=True)
    ap.add_argument("-o", "--ausgabe", type=Path, required=True)
    args = ap.parse_args()

    ziel = args.ausgabe / args.name
    Plymouth(json.loads(args.palette), ziel, args.name, args.anzeige).erzeuge()
    print(f"  plymouth/{args.name}/  "
          f"({len(list(ziel.glob('*.png')))} Bilder, Skript)")


if __name__ == "__main__":
    main()
