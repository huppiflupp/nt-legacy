import QtQuick
import org.kde.plasma.components as PlasmaComponents

Item {
    id: root
    signal logoutRequested()
    signal haltRequested()
    signal suspendRequested(int spdMethod)
    signal rebootRequested()
    signal rebootRequested2(int opt)
    signal cancelRequested()
    signal lockScreenRequested()

    property string mode
    property var currentAction

    // Uebersetzung aus Plasmas Katalog, ohne den Kuerzel-Marker.
    function nt_i18n(text) {
        return i18nd("plasma_lookandfeel_org.kde.lookandfeel", text)
                   .replace("&", "")
    }

    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.55
        MouseArea { anchors.fill: parent; onClicked: root.cancelRequested() }
    }

    Rectangle {
        anchors.centerIn: parent
        width: 340
        height: 150
        color: "#c0c0c0"
        border.color: "#000000"
        border.width: 1

        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top
                       margins: 1 }
            height: 22
            color: "#000080"
            Text {
                anchors { left: parent.left; leftMargin: 8
                           verticalCenter: parent.verticalCenter }
                text: root.nt_i18n("&Shut Down")
                color: "#ffffff"
                font.bold: true
            }
        }

        Row {
            anchors.centerIn: parent
            spacing: 10
            PlasmaComponents.Button {
                text: root.nt_i18n("&Log Out"); onClicked: root.logoutRequested()
            }
            PlasmaComponents.Button {
                text: root.nt_i18n("&Restart"); onClicked: root.rebootRequested()
            }
            PlasmaComponents.Button {
                text: root.nt_i18n("&Shut Down"); onClicked: root.haltRequested()
            }
        }

        PlasmaComponents.Button {
            anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter
                       bottomMargin: 10 }
            text: root.nt_i18n("&Cancel")
            onClicked: root.cancelRequested()
        }
    }
}
