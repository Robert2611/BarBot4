"""Common helper functions for GUI controls"""

from PyQt5 import QtWidgets, Qt


def move_widget_to_bottom_of_screen(window: QtWidgets.QWidget):
    """Move a widget to the bottom of the screen"""
    desktop = Qt.QApplication.desktop().availableGeometry()
    desired = Qt.QRect(Qt.QPoint(0, 0), window.sizeHint())
    desired.moveBottomRight(desktop.bottomRight())
    desired.setLeft(desktop.left())
    window.setGeometry(desired)


def set_no_spacing(layout):
    """Set the spacing to zero for a given QtLayout
    :param layout: The layout"""
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
