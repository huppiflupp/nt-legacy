import QtQuick

Rectangle {
    id: root
    color: "#899a9a"
    property int stage

    // NT zeigte beim Start ein schlichtes Feld mit Produktnamen.
    Rectangle {
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.5, 460)
        height: 150
        color: "#d8d8d0"
        border.color: "#202628"
        border.width: 1

        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }
            height: 24
            color: "#176b78"
            Text {
                anchors { left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }
                text: "NT Legacy"
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
            color: "#f0f0e8"
            border.color: "#8a8a82"
            border.width: 1

            Rectangle {
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom
                           margins: 2 }
                width: Math.max(0, (parent.width - 4) * Math.min(root.stage, 6) / 6)
                color: "#287f8c"
                Behavior on width { NumberAnimation { duration: 180 } }
            }
        }
    }
}
