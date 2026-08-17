#!/usr/bin/env python3
"""Zeigt alle Qt-Standardwidgets in einem Fenster - zum Stilvergleich.

Warum es das gibt: Ein Plasma-Style faerbt die Shell, nicht die Qt-Widgets
in den Programmen. Die zeichnet der Widget-Stil (kdeglobals/KDE/widgetStyle).
Wo dessen Zeichnung nicht zum Theme passt, hilft kein Neubau der SVGs.

Um das zu trennen, braucht man dasselbe Fenster unter zwei Stilen:

    ./widget-testfenster.py --stil Windows --bild /tmp/win.png
    ./widget-testfenster.py --stil Breeze  --bild /tmp/breeze.png

Unterscheiden sich die Bilder an einer Stelle, entscheidet dort der
Widget-Stil - und das Theme kommt nicht heran. Sehen sie gleich aus, liegt
es an der Anwendung selbst.

Ohne --bild bleibt das Fenster offen.
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


def gruppe(titel, *widgets):
    g = QGroupBox(titel)
    lay = QVBoxLayout(g)
    for w in widgets:
        lay.addWidget(w)
    return g


def bauen():
    f = QWidget()
    f.setWindowTitle("Widget-Testfenster")
    raster = QGridLayout(f)

    # --- Knoepfe
    tb = QToolButton(); tb.setText("Werkzeug")
    knopf_aus = QPushButton("Ausgeschaltet"); knopf_aus.setEnabled(False)
    vor = QPushButton("Vorgabeknopf"); vor.setDefault(True)
    raster.addWidget(gruppe("Knoepfe", QPushButton("Normal"), vor,
                            knopf_aus, tb), 0, 0)

    # --- Auswahl
    an = QCheckBox("angekreuzt"); an.setChecked(True)
    teil = QCheckBox("teilweise"); teil.setTristate(True)
    teil.setCheckState(Qt.CheckState.PartiallyChecked)
    r1 = QRadioButton("gewaehlt"); r1.setChecked(True)
    raster.addWidget(gruppe("Auswahl", an, QCheckBox("leer"), teil,
                            r1, QRadioButton("nicht gewaehlt")), 0, 1)

    # --- Eingabe
    kombi = QComboBox(); kombi.addItems(["Eintrag A", "Eintrag B"])
    zahl = QSpinBox(); zahl.setValue(42)
    zeile = QLineEdit("Eingabefeld")
    raster.addWidget(gruppe("Eingabe", zeile, kombi, zahl), 0, 2)

    # --- Fortschritt und Schieber: hier faellt der Windows-Stil auf
    b1 = QProgressBar(); b1.setValue(45)
    b2 = QProgressBar(); b2.setValue(90)
    b3 = QProgressBar(); b3.setRange(0, 0)          # unbestimmt
    s = QSlider(Qt.Orientation.Horizontal); s.setValue(60)
    sb = QScrollBar(Qt.Orientation.Horizontal); sb.setValue(40)
    raster.addWidget(gruppe("Fortschritt und Schieber", b1, b2, b3, s, sb),
                     1, 0)

    # --- Listen
    liste = QListWidget(); liste.addItems(["Zeile 1", "Zeile 2", "Zeile 3"])
    liste.setCurrentRow(1)
    baum = QTreeWidget(); baum.setHeaderLabels(["Spalte", "Wert"])
    w = QTreeWidgetItem(["Zweig", "1"]); w.addChild(QTreeWidgetItem(["Blatt", "2"]))
    baum.addTopLevelItem(w); baum.expandAll()
    raster.addWidget(gruppe("Listen", liste, baum), 1, 1)

    # --- Reiter und Text
    reiter = QTabWidget()
    reiter.addTab(QTextEdit("Textfeld mit Inhalt"), "Erster")
    reiter.addTab(QWidget(), "Zweiter")
    d = QDial(); d.setValue(30)
    raster.addWidget(gruppe("Reiter", reiter, d), 1, 2)

    hin = QLabel("Stil: " + QApplication.style().objectName())
    hin.setAlignment(Qt.AlignmentFlag.AlignCenter)
    raster.addWidget(hin, 2, 0, 1, 3)
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stil", help=f"einer von: {', '.join(QStyleFactory.keys())}")
    ap.add_argument("--bild", help="Fenster abspeichern und beenden")
    args = ap.parse_args()

    app = QApplication(sys.argv)
    if args.stil:
        st = QStyleFactory.create(args.stil)
        if st is None:
            print(f"Stil '{args.stil}' unbekannt. Vorhanden: "
                  f"{', '.join(QStyleFactory.keys())}", file=sys.stderr)
            return 2
        app.setStyle(st)
        # Ohne die Stilpalette bleibt die des vorherigen Stils stehen -
        # dann vergleicht man Formen unter fremden Farben.
        app.setPalette(st.standardPalette())

    f = bauen()
    f.resize(1000, 700)
    f.show()

    if args.bild:
        def speichern():
            f.grab().save(args.bild)
            app.quit()
        # Zwei Durchlaeufe der Ereignisschleife abwarten, sonst sind
        # Rahmen und Text noch nicht fertig gezeichnet.
        QTimer.singleShot(1200, speichern)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
