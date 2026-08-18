# Veröffentlichen auf store.kde.org (kde-look.org)

Die Archive entstehen mit

```bash
./tools/mach-paket.sh
```

und liegen danach in `dist/`. Sie sind **nicht** im Repository — sie
lassen sich jederzeit reproduzieren, und Binärdateien blähen die
Historie nur auf.

```
dist/
├── nt-legacy-full-manual-install-0.2.10.tar.xz    14 MB   Gesamtpaket
├── nt-legacy-global-theme-<farbwelt>-0.2.10.tar.xz       10 Stück
├── nt-legacy-plasma-style-<farbwelt>-0.2.10.tar.xz       10 Stück
├── nt-legacy-icons-0.2.10.tar.xz                1,4 MB   (hell und Nachtfassung)
├── nt-legacy-window-decorations-0.2.10.tar.xz    12 KB
├── nt-legacy-cursors-0.2.10.tar.xz               12 KB
├── nt-legacy-color-schemes-0.2.10.tar.xz        4,0 KB
├── nt-legacy-wallpaper-<name>-0.2.10.tar.xz              26 Stück
├── nt-legacy-wallpapers-manual-install-0.2.10.tar.xz  69 MB
├── screenshots/                                 16 Bilder (10 + 5 Tag/Nacht + Übersicht)
└── SHA256SUMS
```

## Die Hintergründe

Seit 0.2.7 liegen 26 Hintergrundpakete bei: zehn Landschaften (je
Farbwelt eine Tag- und eine Nachtfassung), zwölf nahtlose Kacheln und
vier Großbilder in 4096×4096.

Die Landschaften stecken im Gesamtpaket — auf sie zeigt
`contents/defaults` jeder Variante, ohne sie hätte das Design keinen
Hintergrund. Kacheln und Großbilder nicht: das sind 61 der 69 MB, und
mit ihnen wäre das Gesamtpaket 72 statt 14 MB groß.

**Je Paket ein Archiv, auch hier** — aus zwei Gründen, und der erste
ist der eigentliche.

*Ein Hintergrundpaket ist ein Bild.* So ist das Format definiert: ein
Verzeichnis, eine `metadata.json`, darin `contents/images/<breite>x<höhe>`
— mehrere Dateien bedeuten mehrere **Auflösungen desselben Bildes**, nicht
mehrere Bilder. Nachprüfbar an jedem der rund sechzig Pakete unter
`/usr/share/wallpapers/`. 26 Bilder in einem Paket gäbe es also gar nicht;
in der Auswahl stünde eine Kachel mit einem Namen, und Plasma zeigte
davon eines.

*Und mehrere Pakete in ein Archiv geht auch nicht.* `wallpaper.knsrc`
sagt `Uncompress=subdir-archive` — KNewStuff erwartet im Archiv ein
einzelnes Verzeichnis. Was es mit mehreren macht, ist hier nicht
nachgestellt worden; nach dem Verlauf von 0.2.2, wo `kpackage` bei zehn
Ordnern an der Wurzel das Archiv selbst für das Paket nahm, ist das
Risiko nicht wert, getestet zu werden.

Für den Store heißt das: die 26 Einzelarchive an den Eintrag hängen.
`nt-legacy-wallpapers-manual-install` gehört ins GitHub-Release, nicht in
den Store — es ist zum Entpacken nach `~/.local/share/wallpapers/`
gedacht und über *Neue holen …* genauso falsch wie das Gesamtpaket.

## Warum mehrere Archive?

Der Store kennt je Eintrag genau **eine** Kategorie. Ein Theme wie dieses
besteht aber aus sechs Ebenen. Deshalb gibt es beides:

- **Das Gesamtpaket** mit `install.sh` — für Leute, die alles auf einmal
  wollen. Es gehört ins GitHub-Release, **nicht** in den Store: Es ist ein
  Abzug des Arbeitsverzeichnisses, und der Downloader kann damit nichts
  anfangen. Warum das wichtig ist, steht weiter unten.
- **Einzelarchive je Ebene** — nur damit funktioniert *Neue holen …*
  direkt in den Systemeinstellungen.

## Warum Global Themes und Plasma-Stile je Variante ein Archiv sind

Bis 0.2.2 lagen alle zehn Fassungen in einem Archiv. Über *Neue holen …*
war das Ergebnis: fünf bis sechs namenlose Einträge, die aussehen wie
Breeze, und kein einziges NT-Design. Aus der Community gemeldet und mit
`kpackagetool6` nachgestellt.

Der Grund steht in den `knsrc`-Dateien von Plasma. Es gibt zwei Sorten:

| `Uncompress=` | Verhalten | Bündel erlaubt? |
|---|---|---|
| `archive`, `true` | entpackt stumpf ins Zielverzeichnis | ja |
| `kpackage` | reicht an `kpackagetool6` weiter | **nein** |

`kpackagetool6` erwartet **genau ein** Paket, dessen `metadata.json` an
der Archivwurzel liegt. Lagen dort zehn Ordner, nahm es das Archiv selbst
für das Paket und benannte es nach der Datei:

```
$ kpackagetool6 -t Plasma/LookAndFeel -i nt-legacy-global-themes-0.2.2.tar.xz
Erfolgreich installiert: …/plasma/look-and-feel/nt-legacy-global-themes-0/
```

Ein Ordner ohne `metadata.json` — kein Design, ein namenloser Eintrag, und
der nächste Versuch legt `-1` daneben. Bei den Plasma-Stilen schlägt schon
die Installation fehl („Das Paket wird als ungültig betrachtet").

Global Themes und Plasma Themes laufen beide über `kpackage`. Aurorae,
Symbole, Mauszeiger und Farbschemata über `archive` — dort bleiben die
Bündel.

**Beim Hochladen:** die alten Bündelarchive im Store **löschen**, nicht
nur die neuen daneben legen. Wer die alte Datei zieht, bekommt weiter die
kaputten Einträge.

## Das Gesamtpaket gehört nicht in den Global-Themes-Eintrag

Nach 0.2.3 kam dieselbe Meldung ein zweites Mal — diesmal ohne unser
Zutun: Der Nutzer hatte im Downloader auf `nt-legacy-0.2.3.tar.xz`
geklickt, also auf das **Gesamtpaket**. Das ist ein Abzug des
Arbeitsverzeichnisses mit `install.sh`, kein kpackage-Paket:

```
$ kpackagetool6 -t Plasma/LookAndFeel -i nt-legacy-0.2.4.tar.xz
Erfolgreich installiert: …/plasma/look-and-feel/nt-legacy-0/
```

Derselbe namenlose Ordner wie beim alten Bündel. Die Archive sind in
Ordnung — der Store-Eintrag ist es nicht.

Der Downloader setzt neben **jede** Datei eines Eintrags einen Knopf und
sagt nicht dazu, welche zur Kategorie passt. Solange das Gesamtpaket im
Global-Themes-Eintrag liegt, wird jemand darauf klicken.

**Also:**

1. Im Eintrag unter *Global Themes* liegen **nur** die zehn
   `nt-legacy-global-theme-<farbwelt>-…tar.xz`.
2. Das Gesamtpaket kommt in ein **GitHub-Release** (der Tag ist gesetzt)
   und wird im Beschreibungstext verlinkt — nicht als Store-Datei.

Der Dateiname `nt-legacy-full-manual-install-…` warnt zusätzlich, falls es
doch einmal dort landet. Verlassen sollte man sich darauf nicht.

### Ein kaputtes Paket verdirbt die ganze Liste

In der Test-VM nachgestellt, und das erklärt die Meldung erst wirklich.
Ausgangslage: ein Nutzerverzeichnis mit genau zwei Paketen — einem
gültigen NT-Design und dem Ordner ohne `metadata.json`, den das
Gesamtpaket hinterlässt.

| Zustand | Was *Globales Design* zeigt |
|---|---|
| mit dem kaputten Ordner | **neun** Kacheln, alle „Breeze", alle mit demselben Vorschaubild |
| ohne ihn | Breeze, Breeze Dämmerung, Fedora, Fedora Dark, Fedora Light, **NT Legacy 2000** — jedes mit Namen und eigener Vorschau |

Ein einziges Paket ohne `metadata.json` reicht also, damit das Modul
**alle** Einträge als „Breeze" darstellt — auch die von Fedora und KDE
mitgelieferten, die damit nichts zu tun haben. Wer das sieht, denkt
zwangsläufig, die Installation habe Breeze-Kopien angelegt. Tatsächlich
sind es die vorhandenen Designs, nur falsch beschriftet.

Praktisch heißt das: Der Ordner muss weg, dann ist die Liste sofort
wieder in Ordnung. Für Betroffene:

```bash
rm -rf ~/.local/share/plasma/look-and-feel/nt-legacy-*
```

(Die eigenen Pakete heißen `com.github.huppiflupp.nt-legacy-…` und
bleiben.)

Format ist `tar.xz`: kleiner als ZIP, unter Linux überall auspackbar, und
es erhält symbolische Verweise. Das Symbolset besteht fast zur Hälfte aus
Verweisen — ein ZIP würde daraus Kopien machen.

## Was gehört in welche Kategorie?

| Datei | Kategorie im Store | Systemeinstellungen |
|---|---|---|
| `nt-legacy-full-manual-install-…` | **nicht in den Store** | GitHub-Release, manuell mit `install.sh` |
| `nt-legacy-global-theme-<farbwelt>-…` (10×) | Global Themes | Erscheinungsbild → Globales Design |
| `nt-legacy-plasma-style-<farbwelt>-…` (10×) | Plasma Themes | Erscheinungsbild → Plasma-Stil |
| `nt-legacy-window-decorations-…` | Window Decorations | Erscheinungsbild → Fensterdekorationen |
| `nt-legacy-icons-…` | Icon Sets | Erscheinungsbild → Symbole |
| `nt-legacy-cursors-…` | Cursors | Erscheinungsbild → Mauszeiger |
| `nt-legacy-color-schemes-…` | Color Schemes | Erscheinungsbild → Farben |

**Empfehlung:** Ein Eintrag unter *Global Themes* mit den zehn
Einzelarchiven, und das Gesamtpaket im GitHub-Release daneben. Hier stand
früher das Gegenteil — Gesamtpaket in den Store, Einzelarchive später —,
und genau daraus ist die zweite Fehlermeldung entstanden: Der Downloader
zieht, worauf geklickt wird, und das Gesamtpaket ist kein
kpackage-Paket.

## Angaben für den Eintrag

**Lizenz:** GPL-2.0-or-later — im Formular als *GPL 2.0* auswählen.

**Beschreibungstext:** `nt-legacy/INSTALL.md` liegt im Gesamtpaket und ist
auf Englisch geschrieben — Voraussetzungen, beide Installationswege, die
zehn Fassungen, Fehlersuche, Rückweg. Für das Beschreibungsfeld im Store
reichen die Abschnitte *Requirements*, *Option 1* und *The ten versions*;
der Rest steht ohnehin im Archiv daneben.

**Dieser Satz gehört dazu**, direkt unter die Installationszeilen — sonst
versprechen die Bildschirmfotos mehr, als eine Installation ohne
`--panel` liefert:

> The screenshots show the theme with its own panel — run
> `./apply.sh <variant> --panel` to get it; without that flag your
> existing panel is left untouched.

**Wichtig:** Das Theme enthält **kein Fremdmaterial**. Symbole, SVGs,
Fensterdekoration, Mauszeiger und Hintergründe sind vollständig erzeugt
(`tools/gen-icons.py`, `gen-plasma-svg.py`, `gen-aurorae.py`,
`gen-cursor.py`). Details in `nt-legacy/ATTRIBUTION.md`. Chicago95 ist
ausdrücklich **nicht** enthalten — dessen Lizenzlage ist ungeklärt.

**Screenshots:** liegen in `dist/screenshots/` und werden von
`mach-paket.sh` miterzeugt:

| Datei | Maße | Zweck |
|---|---|---|
| `00-uebersicht.jpg` | 1956×744 | alle fünf Farbwelten, je Tag und Nacht |
| `01-tag-nacht-*.jpg` … `05-…` | 1920×1080 | eine Farbwelt, diagonal geteilt |
| `nt-legacy.jpg` | 1920×1080 | Petrol — die Grundfassung |
| `nt-legacy-*.jpg` | 1920×1080 | je eine einzelne Fassung |

Jedes Vollbild zeigt drei Programme **nebeneinander**, mit englischer
Oberfläche und englischen Ordnernamen:

| Fenster | Was es zeigt |
|---|---|
| Dolphin | den persönlichen Ordner in Symbolansicht — acht Ordner, jeder mit seiner eigenen Marke |
| KWrite | `INSTALL.md`, also eine eingefärbte Textansicht |
| Konsole | ein farbiges `ls`, damit die auf Kontrast kalibrierten ANSI-Farben sichtbar sind |

Vorher standen vier Fenster versetzt übereinander. Die Idee war, auf einem
Bild eine aktive und mehrere inaktive Titelleisten zu zeigen — der Preis
war, dass von den unteren Fenstern je ein Streifen übrig blieb und
ausgerechnet der Dateimanager zur Hälfte verdeckt war. Nebeneinander ist
jedes Fenster ganz zu sehen; Dolphin öffnet zuletzt und trägt damit
weiterhin die aktive Titelleiste, die beiden anderen die inaktive.

Die englische Oberfläche stellt `gen-vorschau.sh` nur für diese drei
Programme her (`LANGUAGE=en_US`), nicht für die ganze Sitzung — Panel und
Uhr bleiben deutsch, was im Bild nicht auffällt. Die Benutzerordner werden
dabei mit umbenannt, sonst stünde eine englische Seitenleiste neben
deutschen Ordnernamen.

**Die geteilten Bilder** legen Tag- und Nachtfassung derselben Farbwelt in
ein Bild: Schnitt diagonal von oben rechts nach unten links, oben links
Tag, unten rechts Nacht. Im Store ist das die übliche Darstellung für
Themes mit zwei Fassungen — zwei fast gleiche Vollbilder nebeneinander
liest man dagegen leicht als Wiederholung.

Das funktioniert nur, weil `gen-vorschau.sh` für jede Variante dieselben
Programme in derselben Reihenfolge bei derselben Auflösung öffnet. Die
Fensterkanten laufen dadurch über den Schnitt hinweg durch. Wer die
Aufnahmen anders erzeugt, bekommt zwei versetzte Bilder statt einer
geteilten Fläche.

**Reihenfolge in der Galerie:** `00-uebersicht.jpg` zuerst — es zeigt die
Bandbreite auf einen Blick, und danach entscheidet sich, ob jemand
weiterklickt. Dann die fünf geteilten Bilder, dann die Einzelfassungen für
alle, die eine bestimmte Variante ganz sehen wollen. Die Dateinamen sind
so sortiert, dass ein `ls` schon die richtige Reihenfolge ergibt.

**Abhängigkeiten**, die in die Beschreibung gehören:

- Plasma 6 (getestet auf 6.7, Fedora 44)
- Der Anwendungsstil steht auf *MS Windows 9x* — der ist in Qt eingebaut,
  es muss nichts nachinstalliert werden
- PCManFM-Qt ist **optional**. `anmutung.sh` setzt es als Dateimanager,
  weil Dolphins Speicheranzeige am Widget-Stil vorbei zeichnet. Ohne
  PCManFM-Qt funktioniert alles, nur diese eine Leiste sieht fremd aus

## Vor dem Hochladen prüfen

```bash
./tools/mach-paket.sh --pruefen   # was käme hinein?
sha256sum -c dist/SHA256SUMS      # Archive unbeschädigt?
```

Das Paketskript bricht ab, wenn Chicago95-Symbole im Archiv landen
würden — auch dann, wenn `fetch-icons.sh` sie vorher lokal installiert
hat.

## Nach dem Hochladen

Der Store zieht die Versionsnummer nicht automatisch. Bei einer neuen
Fassung:

1. `KPlugin.Version` in allen `metadata.json` erhöhen (macht `build.py`)
2. `./tools/mach-paket.sh` neu laufen lassen
3. Neue Dateien im bestehenden Eintrag hinzufügen, alte nicht löschen —
   sonst brechen Verweise aus Foren und Sammlungen

**Eine Ausnahme:** `nt-legacy-global-themes-0.2.2.tar.xz` und
`nt-legacy-plasma-styles-0.2.2.tar.xz` (beide Plural) gehören gelöscht.
Sie lassen sich über *Neue holen …* nicht installieren und hinterlassen
kaputte Einträge — siehe oben. Ein toter Verweis ist besser als eine
Datei, die den Rechner des Nutzers vollmüllt.

Die Versionsnummer steckt auch im Namen des Render-Caches
(`~/.cache/plasma_theme_<name>_v<version>.kcache`). Wer sie nicht erhöht,
liefert ein Update aus, das beim Nutzer nicht sichtbar wird.
