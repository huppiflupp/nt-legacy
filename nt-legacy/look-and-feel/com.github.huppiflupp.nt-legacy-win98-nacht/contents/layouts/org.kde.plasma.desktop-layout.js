// nt-legacy-win98-nacht - Panelvorgabe
var alle = panels();
for (var i = 0; i < alle.length; i++) {
    alle[i].remove();
}

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

// Die Laenge ausdruecklich auf die Bildschirmbreite setzen.
//
// Ohne diese vier Zeilen entsteht unter Plasma 6.7 ein Panel von 34
// Pixeln Breite - dreissig hoch, wie bestellt, aber nur so lang wie
// eine Handvoll Symbole. Auf dem Bildschirm sieht das aus, als waere
// gar kein Panel da: ein Stummel in der linken unteren Ecke.
//
// In beiden Test-VMs nachgestellt, Fedora wie EndeavourOS, und ueber
// die Skriptkonsole gemessen: "length=34" gegenueber "length=1920"
// bei einem von Hand angelegten Panel. Frueher genuegte die Angabe von
// height; die Laenge nahm sich das Panel selbst.
//
// Nach den Widgets, nicht davor: sonst zieht das Panel seine Laenge
// beim Hinzufuegen wieder auf den Inhalt zusammen.
//
// Zweistufig, weil "panel.screen" beim Anwenden eines Globalen Designs
// noch -1 sein kann: dann liefert screenGeometry ein leeres Rechteck,
// die Breite waere 0, und Plasma zieht das Panel auf die Breite seiner
// Symbole zusammen. Auf EndeavourOS genau so passiert (len=456), auf
// Fedora nicht - dort stand der Bildschirm schon fest.
var nr = panel.screen;
if (nr === undefined || nr < 0) { nr = 0; }
var geo = screenGeometry(nr);
var breite = (geo && geo.width > 0) ? geo.width : 0;
if (breite <= 0) {
    // Immer noch kein Bildschirm bekannt. Ein absichtlich zu grosser
    // Wert ist hier richtig: Plasma zeichnet das Panel dann ueber die
    // volle Kante, statt es auf den Inhalt zu schrumpfen. Gemessen.
    breite = 99999;
}
panel.length = breite;
panel.maximumLength = breite;
panel.minimumLength = breite;

var flaechen = desktops();
for (var j = 0; j < flaechen.length; j++) {
    flaechen[j].wallpaperPlugin = "org.kde.image";
    flaechen[j].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    flaechen[j].writeConfig("Image", "ntlegacy-win98-nacht");
    flaechen[j].reloadConfig();
}
