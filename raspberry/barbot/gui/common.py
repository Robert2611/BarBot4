import os
import sys
import platform
import logging
import shlex
from enum import Enum, auto
from PyQt5 import QtWidgets, Qt

class InputMethod(Enum):
    KEYBOARD = auto()
    NUMPAD = auto()
    LIST = auto()

def is_raspberry() -> bool:
    """Check whether we are running on a raspberry pi"""
    if platform.system() != "Linux":
        return False
    try:
        with open("/proc/device-tree/model", "r", encoding="utf-8") as f:
            model = f.read()
            return "Raspberry Pi" in model
    except FileNotFoundError:
        return False

def restart_barbot():
    """Callback to restart the barbot and gui"""
    QtWidgets.QApplication.instance().quit()
    # Re-run the current script with the same arguments
    # os.path.abspath(sys.argv[0]) ensures we use the full path
    args = sys.argv[:]
    args[0] = os.path.abspath(args[0])
    cmd = shlex.join(args)
    # We import run_command here to avoid circular dependency if it was in logic
    from barbot.logic import run_command
    run_command(cmd)

def css_path() -> str:
    """Get the absolute path to the css folder"""
    script_dir = os.path.dirname(__file__)
    return os.path.join(script_dir, "asset")

def qt_icon_from_file_name(file_name) -> Qt.QIcon:
    """Get a QtIcon from containing an image located at a given path.
    :param file_name: Path to the image file"""
    script_dir = os.path.dirname(__file__)
    path = os.path.join(script_dir, "asset", file_name)
    return Qt.QIcon(path)

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
