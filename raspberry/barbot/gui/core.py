"""Core functionality of the barbot gui"""

import os
import platform
import sys
import logging
from enum import Enum, auto
from PyQt5 import QtWidgets, Qt, QtCore
from barbot.logic import BarBot, UserMessageType, BarBotStateEnum, run_command
from barbot.logic.recipes import RecipeCollection
from .controls import Keyboard, Numpad, ListSelector, SelectorButton, set_no_spacing
from .controls.common import InputMethod

SPLASH_MESSAGE_DURATION_IN_SECONDS = 1.5

def restart_barbot():
    """Callback to restart the barbot and gui"""
    QtWidgets.QApplication.instance().quit()
    import shlex
    # Re-run the current script with the same arguments
    # os.path.abspath(sys.argv[0]) ensures we use the full path
    args = sys.argv[:]
    args[0] = os.path.abspath(args[0])
    cmd = shlex.join(args)
    run_command(cmd)

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

class MainWindow(QtWidgets.QMainWindow):
    """Main window for the barbot"""

    # https://stackoverflow.com/questions/2970312/pyqt4-qtcore-pyqtsignal-object-has-no-attribute-connect
    _barbot_state_trigger = QtCore.pyqtSignal(BarBotStateEnum)
    _mixing_progress_trigger = QtCore.pyqtSignal(int)
    _message_trigger = QtCore.pyqtSignal(UserMessageType)
    _show_message_trigger = QtCore.pyqtSignal(str)
    def __init__(self, barbot_: BarBot, recipes: RecipeCollection):
        super().__init__()
        self._barbot = barbot_
        self._recipes = recipes

        from .view.base import View # Local import to avoid circular dependency
        
        self._current_view = None
        self._last_idle_view = None
        self._keyboard: Keyboard = None
        self._timer: QtCore.QTimer
        self._admin_button_active: bool = False

        self.center = QtWidgets.QWidget()
        self.setCentralWidget(self.center)

        self.setProperty("class", "MainWindow")
        with open(os.path.join(css_path(), "main.qss"), encoding="utf-8") as file:
            self.styles = file.read()
        # replace the #iconpath# wildcard
        self.styles = self.styles.replace("#iconpath#", css_path().replace("\\", "/"))
        self.setStyleSheet(self.styles)

        def _handle_mouse_press(event):
            if self._keyboard is not None and self._keyboard.isVisible():
                # Get the global position of the click
                global_pos = self.mapToGlobal(event.pos())
                # Check if it is within the keyboard/selector's geometry
                if self._keyboard.geometry().contains(global_pos):
                    return
            self.close_keyboard()
        self.mousePressEvent = _handle_mouse_press

        # forward status changed
        self._barbot_state_trigger.connect(self.update_view)
        self._barbot.on_state_changed = self._barbot_state_trigger.emit

        # forward message changed
        self._message_trigger.connect(self._busyview_update_message)
        self._barbot.on_message_changed = self._message_trigger.emit

        # forward mixing progress changed
        self._mixing_progress_trigger.connect(self._busyview_set_progress)
        self._barbot.on_mixing_progress_changed = self._mixing_progress_trigger.emit

        # make sure the message splash is created from  thread
        self._show_message_trigger.connect(self._show_message_splash)

        # remove borders and title bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.center.setLayout(QtWidgets.QVBoxLayout())
        set_no_spacing(self.center.layout())

        # header
        header = QtWidgets.QWidget()
        header.setLayout(QtWidgets.QGridLayout())
        header.setProperty("class", "BarBotHeader")
        header.mousePressEvent = self.header_clicked
        self.center.layout().addWidget(header, 0)

        # content
        self._content_wrapper = QtWidgets.QWidget()
        self._content_wrapper.setLayout(QtWidgets.QGridLayout())
        set_no_spacing(self._content_wrapper.layout())
        self.center.layout().addWidget(self._content_wrapper, 1)

        self.update_view()
        self.setFixedSize(480, 800)
        # show fullscreen on raspberry
        if is_raspberry():
            self.showFullScreen()
            self.setCursor(QtCore.Qt.BlankCursor)
        else:
            self.show()

    @property
    def barbot_(self) -> BarBot:
        """The barbot"""
        return self._barbot

    @property
    def recipes(self) -> RecipeCollection:
        """The recipe collection"""
        return self._recipes

    def _busyview_set_progress(self, progress):
        """forward progress if the current view is a busyview"""
        from .view.general import BusyView
        if self._current_view is not None and isinstance(self._current_view, BusyView):
            self._current_view.set_progress(progress)

    def _busyview_update_message(self, message):
        """forward progress if the current view is a busyview"""
        from .view.general import BusyView
        if self._current_view is not None and isinstance(self._current_view, BusyView):
            self._current_view.update_message(message)

    def header_clicked(self, _):
        """Handle the header click"""
        from .view.admin import AdminLogin
        from .view.general import SystemBusyView
        if not self._admin_button_active:
            self._admin_button_active = True
            # reset the admin button after one second
            self._timer = QtCore.QTimer(self)

            def _reset_admin_button():
                self._admin_button_active = False

            self._timer.singleShot(1000, _reset_admin_button)
            return
        if not self._barbot.is_busy:
            self.set_view(AdminLogin(self._barbot, self._recipes))
        else:
            self.set_view(SystemBusyView(self._barbot, self._recipes))

    def close_keyboard(self):
        """Close the keyboard if it is visible"""
        if self._keyboard is not None:
            self._keyboard.close()
            self._keyboard = None

    def _open_input_method(self, target, method: InputMethod):
        if method == InputMethod.KEYBOARD:
            self.open_keyboard(target)
        elif method == InputMethod.NUMPAD:
            self.open_numpad(target)
        elif method == InputMethod.LIST:
            self.open_list_selector(target)

    def open_keyboard(self, target: QtWidgets.QLineEdit):
        """Open a keyboard for a given target widget
        :param target: The line edit that should be edited by the keyboard"""
        self.close_keyboard()
        self._keyboard = Keyboard(target, self.styles, self)
        self._keyboard.show()

    def open_numpad(self, target: QtWidgets.QSpinBox):
        """Open a numpad for a given target widget
        :param target: The spin box that should be edited by the keyboard"""
        self.close_keyboard()
        self._keyboard = Numpad(target, self.styles, self)
        self._keyboard.show()

    def open_list_selector(self, target: "SelectorButton"):
        """Open a list selector for a given target widget
        :param target: The selector button that should be edited by the keyboard"""
        self.close_keyboard()
        self._keyboard = ListSelector(target.get_items(), self.styles, self)
        self._keyboard.on_item_selected.connect(target.handle_selection)
        self._keyboard.show()

    def set_view(self, view):
        """Set the current view of the barbot to the given one.
        :param view: View to be shown"""
        logging.debug("Set view: '%s'", view.__class__.__name__)
        if self._current_view == view:
            logging.debug("View is allready set")
            return
        # remove existing item from window
        if self._current_view is not None:
            # switch from idle to busy?
            if self._current_view.is_idle_view and not view.is_idle_view:
                # just remove it from the visuals
                self._current_view.setParent(None)
            else:
                # delete the view
                self._current_view.deleteLater()
        self._current_view = view

        # connect signals
        self._current_view.switch_view_trigger.connect(self.set_view)
        self._current_view.show_message_trigger.connect(self._show_message_trigger.emit)
        self._current_view.open_input_method_trigger.connect(self._open_input_method)
        self._current_view.close_keyboard_trigger.connect(self.close_keyboard)

        # save the last used idle view
        if view.is_idle_view:
            self._last_idle_view = view
        self._content_wrapper.layout().addWidget(self._current_view)

    def update_view(self):
        """Set the view to the busy view if the barbot is busy.
        Else load the last idle view. If none was set, load the recipe list"""
        from .view.user import ListRecipes, OrderRecipe
        from .view.general import BusyView
        if not self._barbot.is_busy:
            # load the default view
            if self._last_idle_view is None or isinstance(
                self._last_idle_view, OrderRecipe
            ):
                self.set_view(ListRecipes(self._barbot, self._recipes))
            elif self._last_idle_view != self._current_view:
                self.set_view(self._last_idle_view)
        else:
            self.set_view(BusyView(self._barbot, self._recipes))

    def _show_message_splash(self, message):
        """Show a spash sceen with a given message.
        :param message: The message"""
        splash = QtWidgets.QLabel(message)
        splash.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint
        )
        splash.setProperty("class", "Splash")
        splash.setStyleSheet(self.styles)
        splash.show()
        # center on screen
        splash.move(
            QtWidgets.QApplication.desktop().screen().rect().center()
            - splash.rect().center()
        )

        # close the splash after some time
        def _close_message_splash():
            splash.close()

        QtCore.QTimer.singleShot(
            int(1000 * SPLASH_MESSAGE_DURATION_IN_SECONDS), _close_message_splash
        )
