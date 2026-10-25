import QtQuick

Rectangle {
    id: root
    color: "#1a2224"
    property int stage

    // At startup NT showed a plain box with the product name.
    Rectangle {
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.5, 460)
        height: 150
        color: "#2a3234"
        border.color: "#0a1012"
        border.width: 1

        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }
            height: 24
            color: "#000080"
            Text {
                anchors { left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }
                text: "NT Legacy 98 Night"
                color: "#ffffff"
                font.bold: true
                font.pixelSize: 13
            }
        }

        // Progress: stage runs from 1 to 6
        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom
                       margins: 14 }
            height: 14
            color: "#1e2628"
            border.color: "#0e1416"
            border.width: 1

            Rectangle {
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom
                           margins: 2 }
                width: Math.max(0, (parent.width - 4) * Math.min(root.stage, 6) / 6)
                color: "#6f6fb1"
                Behavior on width { NumberAnimation { duration: 180 } }
            }
        }
    }
}
