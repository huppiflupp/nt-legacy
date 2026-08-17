#!/usr/bin/env python3
"""Erzeugt eine Aurorae-Fensterdekoration aus Parametern.

Aurorae ist die SVG-basierte Dekorations-Engine von KWin. Eine
Dekoration besteht aus:

    decoration.svg   9-Patch fuer aktiv, inaktiv und maximiert
    close/maximize/minimize/restore.svg   je fuenf Zustaende
    <Name>rc         Geometrie: Rahmenbreiten, Titelhoehe, Buttons
    metadata.desktop Registrierung bei KWin

Die Element-IDs sind der Vertrag mit KWin - fehlt einer, zeichnet
KWin an der Stelle nichts, ohne Fehlermeldung.

    ./gen-aurorae.py --name NTLegacy -o nt-legacy/aurorae/
"""

import argparse
from pathlib import Path

# Aurorae kennt genau diese Zustandssaetze in der Dekoration.
# maximized-* wird gezeichnet, wenn das Fenster maximiert ist -
# dort entfaellt der Rahmen, nur die Titelleiste bleibt.
DEKO_SAETZE = ["decoration", "decoration-inactive"]
BUTTON_ZUSTAENDE = ["active", "inactive", "hover", "pressed", "deactivated"]
BUTTONS = ["close", "maximize", "minimize", "restore", "alldesktops",
           "keepabove", "keepbelow", "shade", "help", "menu"]


class Aurorae:
    def __init__(self, palette, titelhoehe=22, rahmen=4, aussen=1,
                 bevel=1, buttongroesse=14):
        self.p = palette
        self.th = titelhoehe
        self.rahmen = rahmen
        self.aussen = aussen
        self.bevel = bevel
        self.bg = buttongroesse

    def f(self, *keys):
        for k in keys:
            if k in self.p:
                return self.p[k]
        return "#000000"

    # ------------------------------------------------------------------
    def _patch(self, praefix, ox, oy, breite, hoehe, titel, flaeche):
        """Ein 9-Patch fuer die Dekoration.

        Oben liegt die Titelleiste in Volltonfarbe, an den uebrigen
        Seiten nur der Rahmen. Die Ecken oben gehoeren zur Titelleiste,
        die unteren zum Rahmen - sonst bricht die Titelleiste optisch
        an den Seiten ab.
        """
        r, a, b = self.rahmen, self.aussen, self.bevel
        aussenfarbe = self.f("rahmen")
        hell, dunkel = self.f("hell"), self.f("dunkel")
        t = []

        def rect(x, y, w, h, farbe):
            if w > 0 and h > 0:
                t.append(f'    <rect x="{x:g}" y="{y:g}" width="{w:g}" '
                         f'height="{h:g}" fill="{farbe}"/>')

        def feld(name, x, y, w, h, grund, kanten):
            t.append(f'  <g id="{praefix}-{name}">')
            rect(x, y, w, h, grund)
            # Aussenrahmen
            if "t" in kanten: rect(x, y, w, a, aussenfarbe)
            if "b" in kanten: rect(x, y + h - a, w, a, aussenfarbe)
            if "l" in kanten: rect(x, y, a, h, aussenfarbe)
            if "r" in kanten: rect(x + w - a, y, a, h, aussenfarbe)
            # 3D-Kante innen davon
            if "t" in kanten: rect(x + (a if "l" in kanten else 0), y + a,
                                   w - (a if "l" in kanten else 0) - (a if "r" in kanten else 0), b, hell)
            if "l" in kanten: rect(x + a, y + (a if "t" in kanten else 0), b,
                                   h - (a if "t" in kanten else 0) - (a if "b" in kanten else 0), hell)
            if "b" in kanten: rect(x + (a if "l" in kanten else 0), y + h - a - b,
                                   w - (a if "l" in kanten else 0) - (a if "r" in kanten else 0), b, dunkel)
            if "r" in kanten: rect(x + w - a - b, y + (a if "t" in kanten else 0), b,
                                   h - (a if "t" in kanten else 0) - (a if "b" in kanten else 0), dunkel)
            t.append('  </g>')

        th = self.th
        mitte_h = hoehe - th - r
        # Titelzeile
        feld("topleft",     ox,               oy,      r,             th, titel, "tl")
        feld("top",         ox + r,           oy,      breite - 2*r,  th, titel, "t")
        feld("topright",    ox + breite - r,  oy,      r,             th, titel, "tr")
        # Fensterinhalt. Die Mitte traegt die Rahmenfarbe, obwohl das
        # Fenster sie normalerweise vollstaendig verdeckt.
        #
        # Grund: Stellt der Nutzer die Rahmengroesse hoch (Systemein-
        # stellungen > Fensterdekorationen > Rahmengroesse), meldet KWin
        # einen breiteren Rand als unsere Grafik zeichnet - Large ist
        # Faktor 1.5, aus 4 px werden 6. Die Elemente left/right/bottom
        # behalten dabei ihre natuerliche Breite; die Differenz faellt in
        # das center-Feld. Die Aurorae-Doku sagt das ausdruecklich:
        # "the borders may extend into the center element if the border
        # size is changed". War center transparent, schien dort der
        # Desktop durch - eine Luecke zwischen Rahmen und Fensterinhalt.
        #
        # Preis: Bei einem Fenster, das selbst durchscheinend ist, sieht
        # man hinter ihm diese Flaeche statt des Desktops. Fuer ein
        # deckendes NT-Theme ist das der richtige Tausch.
        feld("left",        ox,               oy + th, r,             mitte_h, flaeche, "l")
        t.append(f'  <g id="{praefix}-center">')
        t.append(f'    <rect x="{ox + r:g}" y="{oy + th:g}" '
                 f'width="{breite - 2*r:g}" height="{mitte_h:g}" fill="{flaeche}"/>')
        t.append('  </g>')
        feld("right",       ox + breite - r,  oy + th, r,             mitte_h, flaeche, "r")
        # Unterkante
        feld("bottomleft",  ox,               oy + hoehe - r, r,            r, flaeche, "bl")
        feld("bottom",      ox + r,           oy + hoehe - r, breite - 2*r, r, flaeche, "b")
        feld("bottomright", ox + breite - r,  oy + hoehe - r, r,            r, flaeche, "br")
        return t

    def decoration(self):
        b, h = 200, 120
        luft = 20
        teile = []
        # aktiv
        teile += self._patch("decoration", luft, luft, b, h,
                             self.f("kopf_aktiv"), self.f("flaeche"))
        # inaktiv
        teile += self._patch("decoration-inactive", luft, luft + h + luft, b, h,
                             self.f("kopf_inaktiv"), self.f("flaeche"))

        # Maximiert: nur die Titelleiste, kein Rahmen ringsum.
        for name, farbe, oy in [
            ("decoration-maximized-center", self.f("kopf_aktiv"), luft + 2*(h+luft)),
            ("decoration-maximized-inactive-center", self.f("kopf_inaktiv"),
             luft + 2*(h+luft) + self.th + luft),
        ]:
            teile.append(f'  <g id="{name}">')
            teile.append(f'    <rect x="{luft}" y="{oy}" width="{b}" '
                         f'height="{self.th}" fill="{farbe}"/>')
            teile.append(f'    <rect x="{luft}" y="{oy + self.th - self.aussen}" '
                         f'width="{b}" height="{self.aussen}" fill="{self.f("rahmen")}"/>')
            teile.append('  </g>')

        gh = luft + 2*(h+luft) + 2*(self.th + luft)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{b + 2*luft}" '
                f'height="{gh}" viewBox="0 0 {b + 2*luft} {gh}">\n'
                '  <!-- Erzeugt von tools/gen-aurorae.py.\n'
                '       Die IDs sind der Vertrag mit KWin - nicht umbenennen. -->\n'
                + "\n".join(teile) + '\n</svg>\n')

    def button(self, art):
        """Ein Knopf je Zustand - ausschliesslich als "center"-Element.

        Die Aurorae-Dokumentation ist hier eindeutig:
        "Each button has to provide the center element. Borders are not
        supported." (develop.kde.org/docs/plasma/aurorae/)

        Ein Versuch mit vollem 9-Patch waere naheliegend gewesen, weil
        AuroraeButton.qml ein KSvg.FrameSvgItem verwendet - technisch
        haette es vielleicht funktioniert, dokumentiert ist es nicht.
        Und das Symbol muss ohnehin IM center liegen: FrameSvgItem
        zeichnet nur die Rasterfelder, ein separates Symbol-Element
        waere nie gezeichnet worden.

        Folge davon: KWin streckt die Grafik auf die eingestellte
        Knopfgroesse (Fensterdekorations-KCM, Zahnrad). Bei stark
        abweichenden Groessen werden die 1px-Kanten weich. Das ist eine
        Eigenheit von Aurorae, kein Fehler dieses Themes - deshalb sind
        die Knoepfe hier grosszuegig gezeichnet, damit beim Verkleinern
        genug Substanz bleibt.
        """
        g, a, b = self.bg, self.aussen, self.bevel
        luft = 6
        teile = []

        for i, zustand in enumerate(BUTTON_ZUSTAENDE):
            ox = luft + i * (g + luft)
            oy = luft
            gedrueckt = zustand == "pressed"
            grund = self.f("hover") if zustand == "hover" else self.f("flaeche")
            if zustand == "deactivated":
                grund = self.f("dunkel")
            hell = self.f("dunkel" if gedrueckt else "hell")
            dunkel = self.f("hell" if gedrueckt else "dunkel")
            rahmen = self.f("rahmen")
            strich = self.f("text")

            teile.append(f'  <g id="{zustand}-center">')
            teile.append(f'    <rect x="{ox}" y="{oy}" width="{g}" height="{g}" '
                         f'fill="{grund}"/>')
            # Aussenrahmen
            for x, y, w, h in [(ox, oy, g, a), (ox, oy + g - a, g, a),
                               (ox, oy, a, g), (ox + g - a, oy, a, g)]:
                teile.append(f'    <rect x="{x:g}" y="{y:g}" width="{w:g}" '
                             f'height="{h:g}" fill="{rahmen}"/>')
            # 3D-Kante innen davon
            teile.append(f'    <rect x="{ox+a}" y="{oy+a}" width="{g-2*a}" '
                         f'height="{b}" fill="{hell}"/>')
            teile.append(f'    <rect x="{ox+a}" y="{oy+a}" width="{b}" '
                         f'height="{g-2*a}" fill="{hell}"/>')
            teile.append(f'    <rect x="{ox+a}" y="{oy+g-a-b}" width="{g-2*a}" '
                         f'height="{b}" fill="{dunkel}"/>')
            teile.append(f'    <rect x="{ox+g-a-b}" y="{oy+a}" width="{b}" '
                         f'height="{g-2*a}" fill="{dunkel}"/>')

            # Das Symbol liegt im selben Element - siehe oben.
            v = 1 if gedrueckt else 0
            cx, cy = ox + g / 2 + v, oy + g / 2 + v
            s = (g - 2 * (a + b)) * 0.72 / 2
            sw = max(1.5, g * 0.09)
            teile.append(self._symbol(art, cx, cy, s, sw, strich))
            teile.append('  </g>')

        breite = luft + len(BUTTON_ZUSTAENDE) * (g + luft)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{breite}" '
                f'height="{g + 2*luft}" viewBox="0 0 {breite} {g + 2*luft}">\n'
                + "\n".join(teile) + '\n</svg>\n')

    def _symbol(self, art, m, n, s, sw, farbe):
        """Das Zeichen im Knopf. Jede Funktion braucht ihr eigenes -
        sechs Knoepfe mit demselben Balken sind nicht unterscheidbar."""
        if art == "close":
            return (f'    <path d="M{m-s:g},{n-s:g} L{m+s:g},{n+s:g} '
                    f'M{m+s:g},{n-s:g} L{m-s:g},{n+s:g}" stroke="{farbe}" '
                    f'stroke-width="{sw:g}"/>')
        if art == "maximize":
            return (f'    <rect x="{m-s:g}" y="{n-s:g}" width="{2*s:g}" '
                    f'height="{2*s:g}" fill="none" stroke="{farbe}" '
                    f'stroke-width="{sw:g}"/>')
        if art == "minimize":
            return (f'    <rect x="{m-s:g}" y="{n+s-sw:g}" width="{2*s:g}" '
                    f'height="{sw:g}" fill="{farbe}"/>')
        if art == "restore":
            return (f'    <rect x="{m-s:g}" y="{n-s+sw:g}" width="{2*s-sw:g}" '
                    f'height="{2*s-sw:g}" fill="none" stroke="{farbe}" '
                    f'stroke-width="{sw*0.8:g}"/>\n'
                    f'    <path d="M{m-s+sw:g},{n-s+sw:g} L{m-s+sw:g},{n-s:g} '
                    f'L{m+s:g},{n-s:g} L{m+s:g},{n+s-sw:g}" fill="none" '
                    f'stroke="{farbe}" stroke-width="{sw*0.8:g}"/>')
        if art == "shade":
            # Einklappen: Balken oben plus Pfeil nach oben
            return (f'    <rect x="{m-s:g}" y="{n-s:g}" width="{2*s:g}" '
                    f'height="{sw:g}" fill="{farbe}"/>\n'
                    f'    <path d="M{m:g},{n+s:g} L{m-s*0.6:g},{n:g} '
                    f'L{m+s*0.6:g},{n:g} Z" fill="{farbe}"/>')
        if art == "keepabove":
            return (f'    <path d="M{m:g},{n-s:g} L{m-s:g},{n+s*0.3:g} '
                    f'L{m+s:g},{n+s*0.3:g} Z" fill="{farbe}"/>\n'
                    f'    <rect x="{m-s:g}" y="{n+s*0.6:g}" width="{2*s:g}" '
                    f'height="{sw:g}" fill="{farbe}"/>')
        if art == "keepbelow":
            return (f'    <path d="M{m:g},{n+s:g} L{m-s:g},{n-s*0.3:g} '
                    f'L{m+s:g},{n-s*0.3:g} Z" fill="{farbe}"/>\n'
                    f'    <rect x="{m-s:g}" y="{n-s:g}" width="{2*s:g}" '
                    f'height="{sw:g}" fill="{farbe}"/>')
        if art == "alldesktops":
            # Vier kleine Felder = mehrere Arbeitsflaechen
            q = s * 0.8
            return "\n".join(
                f'    <rect x="{m + dx*q - q*0.85:g}" y="{n + dy*q - q*0.85:g}" '
                f'width="{q*0.7:g}" height="{q*0.7:g}" fill="{farbe}"/>'
                for dx in (0, 1) for dy in (0, 1))
        if art == "help":
            return (f'    <text x="{m:g}" y="{n+s*0.8:g}" font-size="{2.2*s:g}" '
                    f'font-family="sans-serif" font-weight="bold" '
                    f'text-anchor="middle" fill="{farbe}">?</text>')
        if art == "menu":
            # Drei Striche
            return "\n".join(
                f'    <rect x="{m-s:g}" y="{n + (k-1)*s*0.75 - sw/2:g}" '
                f'width="{2*s:g}" height="{sw:g}" fill="{farbe}"/>'
                for k in range(3))
        return (f'    <rect x="{m-s:g}" y="{n-sw/2:g}" width="{2*s:g}" '
                f'height="{sw:g}" fill="{farbe}"/>')

    def rc(self, name):
        def rgb(h):
            h = h.lstrip("#")
            return ",".join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))
        r = self.rahmen
        return f"""[General]
ActiveTextColor={rgb(self.f("auswahl_text", "fenster"))}
InactiveTextColor={rgb(self.f("fenster"))}
TitleAlignment=Left
TitleVerticalAlignment=Center
UseTextShadow=false
Animation=0
Shadow=true

[Layout]
BorderLeft={r}
BorderRight={r}
BorderBottom={r}
TitleHeight={self.th}
TitleEdgeTop=0
TitleEdgeTopMaximized=0
TitleEdgeBottom=0
TitleEdgeBottomMaximized=0
TitleEdgeLeft={r}
TitleEdgeLeftMaximized=2
TitleEdgeRight={r}
TitleEdgeRightMaximized=2
TitleBorderLeft=4
TitleBorderRight=4
ButtonWidth={self.bg}
ButtonHeight={self.bg}
ButtonSpacing=2
ButtonMarginTop={max(0, (self.th - self.bg) // 2)}
ExplicitButtonSpacer=4
PaddingTop=0
PaddingBottom=0
PaddingLeft=0
PaddingRight=0
"""

    def config_main_xml(self):
        """KConfigXT-Beschreibung der einstellbaren Werte.

        Das Fensterdekorations-KCM (kcm_auroraedecoration.so) laedt
        contents/config/main.xml und contents/ui/config.ui, wenn ein
        Aurorae-Thema sie mitbringt - die Strings stehen im Plugin, und
        es benutzt QUiLoader. Gespeichert wird in ~/.config/auroraerc.

        ACHTUNG: Es gibt systemweit kein einziges Aurorae-Thema mit
        Konfigurationsseite, und die Dokumentation beschreibt das Format
        nicht. Der Aufbau folgt hier den ueblichen KConfigXT-Regeln
        (Widget "kcfg_<Name>" wird an den Eintrag "<Name>" gebunden).
        Ob das KCM die Seite tatsaechlich anzeigt, ist damit nicht
        garantiert - im Zweifel bleibt das Thema bei seinen rc-Werten,
        kaputt geht nichts.
        """
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<kcfg xmlns="http://www.kde.org/standards/kcfg/1.0"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.kde.org/standards/kcfg/1.0
                          http://www.kde.org/standards/kcfg/1.0/kcfg.xsd">
  <kcfgfile name=""/>
  <group name="General">
    <entry name="TitleHeight" type="Int">
      <label>Hoehe der Titelleiste</label>
      <default>{self.th}</default>
      <min>16</min>
      <max>48</max>
    </entry>
    <entry name="ButtonHeight" type="Int">
      <label>Groesse der Knoepfe</label>
      <default>{self.bg}</default>
      <min>10</min>
      <max>40</max>
    </entry>
    <entry name="BorderLeft" type="Int">
      <label>Rahmenbreite</label>
      <default>{self.rahmen}</default>
      <min>0</min>
      <max>12</max>
    </entry>
    <entry name="TitleAlignment" type="String">
      <label>Ausrichtung des Titels</label>
      <default>Left</default>
    </entry>
  </group>
</kcfg>
"""

    def config_ui(self):
        """Die Oberflaeche dazu. Widgetnamen "kcfg_<Eintrag>" binden an
        die Eintraege aus main.xml - das macht KConfigDialogManager."""
        def spin(name, label, mini, maxi, wert, suffix=" px"):
            return f"""   <item row="{spin.zeile}" column="0">
    <widget class="QLabel" name="label_{name}">
     <property name="text"><string>{label}</string></property>
    </widget>
   </item>
   <item row="{spin.zeile}" column="1">
    <widget class="QSpinBox" name="kcfg_{name}">
     <property name="minimum"><number>{mini}</number></property>
     <property name="maximum"><number>{maxi}</number></property>
     <property name="value"><number>{wert}</number></property>
     <property name="suffix"><string>{suffix}</string></property>
    </widget>
   </item>
"""
        spin.zeile = 0
        teile = []
        for name, label, mini, maxi, wert in [
            ("TitleHeight", "Titelleiste:", 16, 48, self.th),
            ("ButtonHeight", "Knoepfe:", 10, 40, self.bg),
            ("BorderLeft", "Rahmen:", 0, 12, self.rahmen),
        ]:
            teile.append(spin(name, label, mini, maxi, wert))
            spin.zeile += 1

        return """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>NTLegacyConfig</class>
 <widget class="QWidget" name="NTLegacyConfig">
  <layout class="QGridLayout" name="gridLayout">
""" + "".join(teile) + """   <item row="3" column="0" colspan="2">
    <spacer name="spacer">
     <property name="orientation"><enum>Qt::Vertical</enum></property>
    </spacer>
   </item>
  </layout>
 </widget>
 <resources/>
 <connections/>
</ui>
"""

    def metadata(self, name, anzeige, beschreibung, autor, lizenz, version):
        # Aurorae nutzt metadata.desktop - hier ist das kein Legacy,
        # sondern das vorgesehene Format. Der Praefix
        # __aurorae__svg__ ist Pflicht und muss dem Ordnernamen folgen.
        return f"""[Desktop Entry]
Name={anzeige}
Comment={beschreibung}
Type=Service
X-KDE-ServiceTypes=KWin/Decoration
X-KDE-Library=kwin3_aurorae
X-KDE-PluginInfo-Name=__aurorae__svg__{name}
X-KDE-PluginInfo-Author={autor}
X-KDE-PluginInfo-License={lizenz}
X-KDE-PluginInfo-Version={version}
"""


PALETTE_NT = {
    "flaeche": "#d8d8d0", "fenster": "#f0f0e8",
    "kopf_aktiv": "#176b78", "kopf_inaktiv": "#60777a",
    "hell": "#f4f4ee", "dunkel": "#8a8a82", "rahmen": "#202628",
    "text": "#202628", "auswahl_text": "#ffffff", "hover": "#d6a23a",
}


def main():
    ap = argparse.ArgumentParser(description="Erzeugt eine Aurorae-Dekoration.")
    ap.add_argument("--name", default="NTLegacy")
    ap.add_argument("--anzeige", default="NT Legacy")
    ap.add_argument("-o", "--ausgabe", type=Path, required=True)
    ap.add_argument("--titelhoehe", type=int, default=22)
    ap.add_argument("--rahmen", type=int, default=4)
    ap.add_argument("--button", type=int, default=14)
    ap.add_argument("--autor", default="huppiflupp")
    ap.add_argument("--lizenz", default="GPL-2.0-or-later")
    ap.add_argument("--version", default="0.1.0")
    args = ap.parse_args()

    a = Aurorae(PALETTE_NT, titelhoehe=args.titelhoehe,
                rahmen=args.rahmen, buttongroesse=args.button)
    ziel = args.ausgabe / args.name
    ziel.mkdir(parents=True, exist_ok=True)

    (ziel / "decoration.svg").write_text(a.decoration())
    print(f"  {ziel.name}/decoration.svg")
    for btn in BUTTONS:
        (ziel / f"{btn}.svg").write_text(a.button(btn))
    print(f"  {ziel.name}/*.svg ({len(BUTTONS)} Buttons)")
    (ziel / "contents" / "config").mkdir(parents=True, exist_ok=True)
    (ziel / "contents" / "ui").mkdir(parents=True, exist_ok=True)
    (ziel / "contents" / "config" / "main.xml").write_text(a.config_main_xml())
    (ziel / "contents" / "ui" / "config.ui").write_text(a.config_ui())
    print(f"  {ziel.name}/contents/  (Konfigurationsseite)")

    (ziel / f"{args.name}rc").write_text(a.rc(args.name))
    print(f"  {ziel.name}/{args.name}rc")
    (ziel / "metadata.desktop").write_text(a.metadata(
        args.name, args.anzeige,
        "Windows NT 4.0 in Petrol - eckige Rahmen, quadratische Knoepfe",
        args.autor, args.lizenz, args.version))
    print(f"  {ziel.name}/metadata.desktop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
