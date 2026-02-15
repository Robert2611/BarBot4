"""Common helper functions for GUI controls"""

from PyQt5 import QtWidgets, Qt
from enum import Enum, auto


class InputMethod(Enum):
    KEYBOARD = auto()
    NUMPAD = auto()
    LIST = auto()


def move_widget_to_bottom_of_screen(window: QtWidgets.QWidget, reference_widget: QtWidgets.QWidget = None):
    """Move a widget to the bottom of the screen (or reference widget)"""
    if reference_widget is not None:
        ref_geo = reference_widget.geometry()
    else:
        ref_geo = Qt.QApplication.desktop().availableGeometry()
    
    # Use sizeHint but respect maximum size constraints
    size = window.sizeHint()
    if window.maximumHeight() < size.height():
        size.setHeight(window.maximumHeight())
    if window.maximumWidth() < size.width():
        size.setWidth(window.maximumWidth())

    desired = Qt.QRect(Qt.QPoint(0, 0), size)
    desired.moveBottomRight(ref_geo.bottomRight())
    desired.setLeft(ref_geo.left())
    window.setGeometry(desired)


def set_no_spacing(layout):
    """Set the spacing to zero for a given QtLayout
    :param layout: The layout"""
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
