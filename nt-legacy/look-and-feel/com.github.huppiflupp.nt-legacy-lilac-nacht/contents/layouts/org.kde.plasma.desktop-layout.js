// nt-legacy-lilac-nacht - Panelvorgabe
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

var flaechen = desktops();
for (var j = 0; j < flaechen.length; j++) {
    flaechen[j].wallpaperPlugin = "org.kde.image";
    flaechen[j].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    flaechen[j].writeConfig("Image", "ntlegacy-lilac-nacht");
    flaechen[j].reloadConfig();
}
