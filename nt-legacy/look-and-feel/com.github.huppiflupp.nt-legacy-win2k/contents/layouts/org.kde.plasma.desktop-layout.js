// nt-legacy-win2k - panel default

// One panel per screen.
//
// Up to 0.2.14 this script created exactly ONE - just like Plasma's own
// template (layout-templates/org.kde.plasma.desktop.defaultPanel). On a
// machine with one screen that is correct. On two it is not: Plasma then
// decides by itself which screen the one panel lands on, and the other
// has no taskbar. Reported as "when I switch back to NT Legacy, there is
// no taskbar any more" - and because the choice can differ from run to
// run, it looked as if it depended on the variant.
//
// Measured on a machine with two 2560 screens: screenCount=2,
// panels().length=1, panel.screen=0.
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) {
    allPanels[i].remove();
}

for (var s = 0; s < screenCount; s++) {
    // Further screens only if Plasma already has a desktop there. When the
    // design is applied in a running Plasma (System Settings, "Desktop
    // layout") it does not know the second screen yet: the second panel
    // landed nowhere, was removed again below - and that took the first
    // one with it (screen -1, both screens black until plasmashell was
    // restarted). In the VM with two screens: before, in every second
    // switch; this way, clean in 8 out of 8.
    if (s > 0 && !desktopForScreen(s)) {
        continue;
    }
    var panel = new Panel;
    panel.screen = s;
    panel.location = "bottom";
    panel.height = 30;
    panel.floating = false;
    panel.hiding = "none";
    panel.alignment = "left";

    // The application menu, not the application launcher.
    //
    // org.kde.plasma.kickoff is Plasma's default: a window with a search
    // field, a tile grid and tabs. org.kde.plasma.kicker is the cascading
    // menu with submenus - what Windows 95 to 2000 had, and the only one
    // of the two that fits this design language. It also brings the
    // sidebar that the Plasma style colors (widgets/frame, prefix
    // "plain").
    panel.addWidget("org.kde.plasma.kicker");
    panel.addWidget("org.kde.plasma.icontasks");
    panel.addWidget("org.kde.plasma.systemtray");
    panel.addWidget("org.kde.plasma.digitalclock");

    // From the second screen on: only keep it if it really sits there.
    // setScreen goes through Corona::setScreenForContainment and can
    // fail - then all panels would lie on top of each other on the same
    // screen, and that would be worse than the state before. The first
    // one is NEVER removed: one panel too few is exactly the bug this
    // file is meant to fix.
    if (s > 0 && panel.screen !== s) {
        panel.remove();
    }
}

// Up to 0.2.14 there was a block here that set the length, minimum and
// maximum length of the panel to the screen width - against a panel that
// supposedly only became 34 pixels wide.
//
// That never existed. "panel.length" does not return the drawn width but
// the width of the CONTENT; the diagnosis was based on this misreading.
// Measured in the test VM: without any length setting lengthMode is
// "fill", minimumLength and maximumLength are 1280 - and on the screenshot
// the panel is drawn across the full width, while "length" reports 388.
//
// The block was harmful on top of that: setting minimumLength and
// maximumLength to the same value pins the panel to a fixed size. On a
// second screen of a different width it no longer fits, and the fallback
// value 99999 (for the case that screenGeometry does not know anything
// yet) pins it to a width that exists nowhere.
//
// Plasma's own template does not set the length either.

var desktopList = desktops();
for (var j = 0; j < desktopList.length; j++) {
    desktopList[j].wallpaperPlugin = "org.kde.image";
    desktopList[j].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktopList[j].writeConfig("Image", "ntlegacy-win2k");
    desktopList[j].reloadConfig();
}
