#!/usr/bin/env python3
"""Shows all standard Qt widgets in one window - for comparing styles.

Why this exists: a Plasma style colours the shell, not the Qt widgets
in the programs. Those are drawn by the widget style (kdeglobals/KDE/widgetStyle).
Where its drawing does not match the theme, no rebuild of the SVGs helps.

To separate the two, you need the same window under two styles:

    ./widget-test-window.py --style Windows --image /tmp/win.png
    ./widget-test-window.py --style Breeze  --image /tmp/breeze.png

If the images differ in one spot, the widget style decides there
- and the theme cannot reach it. If they look the same, it is down to
the application itself.

Without --image the window stays open.
"""

import argparse
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDial, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QProgressBar, QPushButton,
    QRadioButton, QScrollBar, QSlider, QSpinBox, QStyleFactory, QTabWidget,
    QTextEdit, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QWidget,
)


def group(title, *widgets):
    g = QGroupBox(title)
    lay = QVBoxLayout(g)
    for w in widgets:
        lay.addWidget(w)
    return g


def build():
    f = QWidget()
    f.setWindowTitle("Widget test window")
    grid = QGridLayout(f)

    # --- Buttons
    tb = QToolButton(); tb.setText("Tool")
    btn_off = QPushButton("Disabled"); btn_off.setEnabled(False)
    dflt = QPushButton("Default button"); dflt.setDefault(True)
    grid.addWidget(group("Buttons", QPushButton("Normal"), dflt,
                         btn_off, tb), 0, 0)

    # --- Selection
    on = QCheckBox("checked"); on.setChecked(True)
    part = QCheckBox("partial"); part.setTristate(True)
    part.setCheckState(Qt.CheckState.PartiallyChecked)
    r1 = QRadioButton("selected"); r1.setChecked(True)
    grid.addWidget(group("Selection", on, QCheckBox("empty"), part,
                         r1, QRadioButton("not selected")), 0, 1)

    # --- Input
    combo = QComboBox(); combo.addItems(["Item A", "Item B"])
    num = QSpinBox(); num.setValue(42)
    line = QLineEdit("Input field")
    grid.addWidget(group("Input", line, combo, num), 0, 2)

    # --- Progress and sliders: this is where the Windows style stands out
    b1 = QProgressBar(); b1.setValue(45)
    b2 = QProgressBar(); b2.setValue(90)
    b3 = QProgressBar(); b3.setRange(0, 0)          # indeterminate
    s = QSlider(Qt.Orientation.Horizontal); s.setValue(60)
    sb = QScrollBar(Qt.Orientation.Horizontal); sb.setValue(40)
    grid.addWidget(group("Progress and sliders", b1, b2, b3, s, sb),
                   1, 0)

    # --- Lists
    lst = QListWidget(); lst.addItems(["Row 1", "Row 2", "Row 3"])
    lst.setCurrentRow(1)
    tree = QTreeWidget(); tree.setHeaderLabels(["Column", "Value"])
    w = QTreeWidgetItem(["Branch", "1"]); w.addChild(QTreeWidgetItem(["Leaf", "2"]))
    tree.addTopLevelItem(w); tree.expandAll()
    grid.addWidget(group("Lists", lst, tree), 1, 1)

    # --- Tabs and text
    tabs = QTabWidget()
    tabs.addTab(QTextEdit("Text field with content"), "First")
    tabs.addTab(QWidget(), "Second")
    d = QDial(); d.setValue(30)
    grid.addWidget(group("Tabs", tabs, d), 1, 2)

    hint = QLabel("Style: " + QApplication.style().objectName())
    hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
    grid.addWidget(hint, 2, 0, 1, 3)
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", help=f"one of: {', '.join(QStyleFactory.keys())}")
    ap.add_argument("--image", help="save the window and quit")
    args = ap.parse_args()

    app = QApplication(sys.argv)
    if args.style:
        st = QStyleFactory.create(args.style)
        if st is None:
            print(f"Style '{args.style}' unknown. Available: "
                  f"{', '.join(QStyleFactory.keys())}", file=sys.stderr)
            return 2
        app.setStyle(st)
        # Without the style's palette the previous style's palette stays -
        # then you compare shapes under foreign colours.
        app.setPalette(st.standardPalette())

    f = build()
    f.resize(1000, 700)
    f.show()

    if args.image:
        def save():
            f.grab().save(args.image)
            app.quit()
        # Wait for two passes of the event loop, otherwise
        # frames and text are not finished drawing yet.
        QTimer.singleShot(1200, save)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
