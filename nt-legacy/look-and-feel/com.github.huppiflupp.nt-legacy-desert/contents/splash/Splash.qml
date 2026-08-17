import QtQuick

Rectangle {
    id: root
    color: "#a89878"
    property int stage

    // NT zeigte beim Start ein schlichtes Feld mit Produktnamen.
    Rectangle {
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.5, 460)
        height: 150
        color: "#d8d0c0"
        border.color: "#202628"
        border.width: 1

        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }
            height: 24
            color: "#7a5c2e"
            Text {
                anchors { left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }
                text: "NT Legacy Wueste"
                color: "#ffffff"
                font.bold: true
                font.pixelSize: 13
            }
        }

        // Fortschritt: stage laeuft von 1 bis 6
        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom
                       margins: 14 }
            height: 14
            color: "#f0ece0"
            border.color: "#8a8272"
            border.width: 1

            Rectangle {
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom
                           margins: 2 }
                width: Math.max(0, (parent.width - 4) * Math.min(root.stage, 6) / 6)
                color: "#96703a"
                Behavior on width { NumberAnimation { duration: 180 } }
            }
        }
    }
}
