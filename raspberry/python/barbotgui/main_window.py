"""The main window of the barbot gui"""
import logging
import os

from PyQt5 import QtWidgets, Qt, QtCore

from barbot import BarBot
from barbot.recipes import RecipeCollection

from barbotgui.core import BarBotWindow, SystemBusyView, View, BusyView, css_path, is_raspberry
from barbotgui.controls import Keyboard, Numpad, set_no_spacing
from barbotgui.adminviews import AdminLogin
from barbotgui.userviews import ListRecipes, OrderRecipe

class MainWindow(BarBotWindow):
    """Main window for the barbot"""
    def __init__(self, barbot_:BarBot, recipes: RecipeCollection):
        super().__init__(barbot_, recipes)

        self._current_view : View = None
        self._last_idle_view : View = None
        self._keyboard: Keyboard = None
        self._timer: QtCore.QTimer
        self._admin_button_active : bool = False

        self.center = QtWidgets.QWidget()
        self.setCentralWidget(self.center)

        self.setProperty("class", "MainWindow")
        with open(os.path.join(css_path(), 'main.qss'), encoding="utf-8") as file:
            self.styles = file.read()
        # replace the #iconpath# wildcard
        self.styles = self.styles.replace("#iconpath#", css_path().replace("\\", "/"))
        self.setStyleSheet(self.styles)

        self.mousePressEvent = lambda _: self.close_keyboard()

        # forward status changed
        self._barbot_state_trigger.connect(self.update_view)
        self._barbot.on_state_changed = self._barbot_state_trigger.emit

        # forward message changed
        self._message_trigger.connect(self._busyview_update_message)
        self._barbot.on_message_changed = self._message_trigger.emit

        # forward mixing progress changed
        self._mixing_progress_trigger.connect(self._busyview_set_progress)
        self._barbot.on_mixing_progress_changed = self._mixing_progress_trigger.emit

        # make sure the message splash is created from gui thread
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

    def _busyview_set_progress(self, progress):
        """forward progress if the current view is a busyview"""
        if self._current_view is not None and isinstance(self._current_view, BusyView):
            self._current_view.set_progress(progress)

    def _busyview_update_message(self, message):
        """forward progress if the current view is a busyview"""
        if self._current_view is not None and isinstance(self._current_view, BusyView):
            self._current_view.update_message(message)

    def header_clicked(self, _):
        """Handle the header click"""
        if not self._admin_button_active:
            self._admin_button_active = True
            # reset the admin button after one second
            self._timer = QtCore.QTimer(self)
            def _reset_admin_button():
                self._admin_button_active = False
            self._timer.singleShot(1000, _reset_admin_button)
            return
        if not self._barbot.is_busy:
            self.set_view(AdminLogin(self))
        else:
            self.set_view(SystemBusyView(self))

    def close_keyboard(self):
        """Close the keyboard if it is visible"""
        if self._keyboard is not None:
            self._keyboard.close()
            self._keyboard = None

    def open_keyboard(self, target: QtWidgets.QLineEdit):
        """Open a keyboard for a given target widget
        :param target: The line edit that should be edited by the keyboard"""
        self.close_keyboard()
        self._keyboard = Keyboard(target, self.styles)
        self._keyboard.show()

    def open_numpad(self, target: QtWidgets.QSpinBox):
        """Open a numpad for a given target widget
        :param target: The spin box that should be edited by the keyboard"""
        self.close_keyboard()
        self._keyboard = Numpad(target, self.styles)
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
        # save the last used idle view
        if view.is_idle_view:
            self._last_idle_view = view
        self._content_wrapper.layout().addWidget(self._current_view)

    def update_view(self):
        """Set the view to the busy view if the barbot is busy.
        Else load the last idle view. If none was set, load the recipe list """
        if not self._barbot.is_busy:
            # load the default view
            if self._last_idle_view is None or isinstance(self._last_idle_view, OrderRecipe):
                self.set_view(ListRecipes(self))
            elif self._last_idle_view != self._current_view:
                self.set_view(self._last_idle_view)
        else:
            self.set_view(BusyView(self))

    def _show_message_splash(self, message):
        """Show a spash sceen with a given message.
        :param message: The message"""
        splash = QtWidgets.QSplashScreen()
        splash.showMessage(message, alignment=QtCore.Qt.AlignCenter)
        splash.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |
                              QtCore.Qt.FramelessWindowHint)
        splash.setProperty("class", "Splash")
        splash.setStyleSheet(self.styles)
        path = os.path.join(css_path(), "splash.png")
        splash.setPixmap(Qt.QPixmap(path))
        splash.show()
        QtCore.QTimer.singleShot(
            1000, lambda s=splash, window=self: s.finish(window))
