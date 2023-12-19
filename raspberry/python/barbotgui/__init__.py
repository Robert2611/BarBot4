"""The barbot gui"""
import os
import logging
import platform
import sys
from PyQt5 import QtWidgets, Qt, QtCore, QtGui
from barbot import BarBot, UserMessageType, BarBotState, run_command
from barbot.config import Ingredient, IngredientType
from barbot.recipes import RecipeCollection, RecipeFilter
from barbotgui.controls import Keyboard, Numpad, set_no_spacing

INGREDIENT_MAX_AMOUNT_OPTION = 17


def is_raspberry() -> bool:
    """Check whether we are running on a raspberry pi"""
    if platform.system() != "Linux":
        return False
    try:
        uname = getattr(os, "uname")
        name = uname().nodename
    except AttributeError:
        return False
    return "raspberry" in name


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
    _barbot_state_trigger = QtCore.pyqtSignal(BarBotState)
    _mixing_progress_trigger = QtCore.pyqtSignal(int)
    _message_trigger = QtCore.pyqtSignal(UserMessageType)
    _show_message_trigger = QtCore.pyqtSignal(str)
    
    def __init__(self, barbot_:BarBot, recipes: RecipeCollection):
        super().__init__()
        self._barbot = barbot_
        self._current_view : View = None
        self._last_idle_view : View = None
        self._keyboard: Keyboard = None
        self._timer: QtCore.QTimer
        self._admin_button_active : bool = False
        self.recipe_filter = RecipeFilter(Descending = True)
        self._recipes = recipes
        from barbotgui.adminviews import AdminLogin
        self.admin_login = lambda: AdminLogin(self)
        from barbotgui.userviews import ListRecipes
        self.default_view = lambda: ListRecipes(self)

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

    @property
    def recipes(self):
        """Get the collection of recipes"""
        return self._recipes

    @property
    def barbot_(self):
        """The barbot"""
        return self._barbot

    def _busyview_set_progress(self, progress):
        """forward progress if the current view is a busyview"""
        if self._current_view is not None and isinstance(self._current_view, BusyView):
            self._current_view.set_progress(progress)

    def _busyview_update_message(self, message):
        """forward progress if the current view is a busyview"""
        if self._current_view is not None and isinstance(self._current_view, BusyView):
            self._current_view.update_message(message)
            
    def set_system_view(self, container: QtWidgets.QWidget):
        """Get the systems view widget."""
        if container.layout() is None:
            container.setLayout(QtWidgets.QVBoxLayout())

        label = QtWidgets.QLabel("Software")
        container.layout().addWidget(label)
        # reopen software
        button = QtWidgets.QPushButton("Neu Starten")
        button.clicked.connect(self.restart_barbot)
        container.layout().addWidget(button)

        # close software
        button = QtWidgets.QPushButton("Schließen")
        button.clicked.connect(QtWidgets.QApplication.instance().quit)
        container.layout().addWidget(button)

        label = QtWidgets.QLabel("PI")
        container.layout().addWidget(label)

        # shutdown
        button = QtWidgets.QPushButton("Herunterfahren")
        button.clicked.connect(lambda: run_command("sudo shutdown now"))
        container.layout().addWidget(button)

        # reboot
        button = QtWidgets.QPushButton("Neu Starten")
        button.clicked.connect(lambda: run_command("sudo reboot"))
        container.layout().addWidget(button)

        # dummy
        container.layout().addWidget(QtWidgets.QWidget(), 1)
    
    def restart_barbot(self):
        """Callback to restart the barbot and gui"""
        QtWidgets.QApplication.instance().quit()
        filepath = os.path.join(sys.path[0], "main.py")
        run_command(filepath)

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
            self.set_view(self.admin_login())
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

    def update_view(self, force_reload=False):
        """Set the view to the busy view if the barbot is busy.
        Else load the last idle view. If none was set, load the recipe list """
        if not self._barbot.is_busy:
            if self._last_idle_view is None or force_reload:
                self.set_view(self.default_view())
            if self._last_idle_view != self._current_view:
                self.set_view(self._last_idle_view)
        else:
            self.set_view(BusyView(self))

    def show_message(self, message: str):
        """Show a given message to the user.
        :param message: Message string"""
        self._show_message_trigger.emit(message)

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

    def combobox_amounts(self, selected_amount=None):
        """Create a combobox for selecting the amount of a ingredient.
        Set it to the selected data if provided.
        :param selected_amount: The amount to preselect"""
        # add ingredient name
        widget = QtWidgets.QComboBox()
        widget.addItem("-", -1)
        widget.setCurrentIndex(0)
        for i in range(1, INGREDIENT_MAX_AMOUNT_OPTION):
            widget.addItem(str(i), i)
            if i == selected_amount:
                widget.setCurrentIndex(i)
        return widget

    def combobox_ingredients(self, selected_ingredient: Ingredient=None, only_available = False, \
                                    only_normal = False, only_weighed = False):
        """Create a combobox with options for ingredients selected by the filter parameters 
        
        :param only_available: If set to true, only return ingredients that \
            are currently connected to ports
        :param only_normal: If set to true, only return ingredients that are pumped
        :param only_weighed: If set to true, only return ingredients that are added by weight    
        """
        entries = self.barbot_.config.get_ingredient_list(only_available, only_normal, only_weighed)
        # add ingredient name
        widget = QtWidgets.QComboBox()
        widget.addItem("-", None)
        widget.setCurrentIndex(0)
        for i, item in enumerate(entries):
            widget.addItem(str(item.name), item)
            if item == selected_ingredient:
                widget.setCurrentIndex(i + 1)
        return widget

class View(QtWidgets.QWidget):
    """Content that can be shown in the center of the main window"""

    def __init__(self, window: MainWindow, is_idle_view:bool = True):
        super().__init__(window)
        self._window = window
        self._is_idle_view = is_idle_view

    @property
    def is_idle_view(self):
        """Get whether the view is an idle view"""
        return self._is_idle_view

    @property
    def window(self):
        """Get the window the view is used for"""
        return self._window

class SystemBusyView(View):
    def __init__(self, window: MainWindow):
        super().__init__(window, is_idle_view=False)
        
        self.setLayout(QtWidgets.QVBoxLayout())
        set_no_spacing(self.layout())
        
        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header)
        
        self._content = QtWidgets.QWidget()
        self.layout().addWidget(self._content)
                     
        # add actual content
        self.window.set_system_view(self._content)
        
class BusyView(View):
    """Content that will be shown in the main window when the barbot is busy"""
    def __init__(self, window: MainWindow):
        super().__init__(window)

        self._message = None

        self.setLayout(QtWidgets.QGridLayout())
        set_no_spacing(self.layout())

        centered = QtWidgets.QFrame()
        centered.setLayout(QtWidgets.QVBoxLayout())
        centered.setProperty("class", "CenteredContent")
        self.layout().addWidget(centered, 0, 0, QtCore.Qt.AlignCenter)

        self._title_label = QtWidgets.QLabel("")
        self._title_label.setAlignment(QtCore.Qt.AlignCenter)
        self._title_label.setProperty("class", "Headline")
        centered.layout().addWidget(self._title_label)

        self._content_container = QtWidgets.QWidget()
        self._content_container.setLayout(QtWidgets.QVBoxLayout())
        centered.layout().addWidget(self._content_container)

        self._message_container = QtWidgets.QWidget()
        self._message_container.setLayout(QtWidgets.QGridLayout())
        self._message_container.setVisible(False)
        centered.layout().addWidget(self._message_container)

        self._init_by_status()

        self.update_message(None)

    def update_message(self, message:str = None):
        """Update the message shown to the user"""
        if message is None:
            message = UserMessageType.NONE
        # delete old message
        if self._message is not None:
            self._message.setParent(None)

        # if message is none show the content again
        if message == UserMessageType.NONE:
            self._message_container.setVisible(False)
            self._content_container.setVisible(True)
            self._title_label.setVisible(True)
            return

        self._message = QtWidgets.QWidget()
        self._message.setLayout(QtWidgets.QVBoxLayout())
        self._message_container.layout().addWidget(self._message)

        message_label = QtWidgets.QLabel()
        self._message.layout().addWidget(message_label)

        buttons_container = QtWidgets.QWidget()
        buttons_container.setLayout(QtWidgets.QHBoxLayout())
        self._message.layout().addWidget(buttons_container)

        def add_button(text, result):
            button = QtWidgets.QPushButton(text)
            def callback():
                return self._mainboard.set_user_input(result)
            button.clicked.connect(callback)
            buttons_container.layout().addWidget(button)

        if message == UserMessageType.INGREDIENT_EMPTY:
            ingredient = self._mainboard.current_recipe_item().ingredient
            if ingredient.type == IngredientType.SUGAR:
                message_string = f"{ingredient.name} ist leer. Bitte nachfüllen."
            else:
                ports = self.window.barbot_.config.ports
                ingredient = self._mainboard.current_recipe_item().ingredient
                position = ports.port_of_ingredient(ingredient) + 1
                message_string = f"Die Zutat '{ingredient.name}'"
                message_string += f" auf Position {position} ist leer.\n"
                message_string += "Bitte neue Flasche anschließen."
            message_label.setText(message_string)

            add_button("Cocktail\nabbrechen", False)
            add_button("Erneut\nversuchen", True)

        elif message == UserMessageType.PLACE_GLAS:
            message_label.setText("Bitte ein Glas auf die Plattform stellen.")

        elif message == UserMessageType.MIXING_DONE_REMOVE_GLAS:
            if self._mainboard.was_aborted():
                message_label.setText("Cocktail abgebrochen!")
            else:
                if self._mainboard.current_recipe().post_instruction:
                    label = QtWidgets.QLabel("Zusätzliche Informationen:")
                    self._message.layout().addWidget(label)

                    instruction = QtWidgets.QLabel(
                        self._mainboard.current_recipe().post_instruction)
                    self._message.layout().addWidget(instruction)
                else:
                    text = "Der Cocktail ist fertig gemischt.\n" + \
                        "Du kannst ihn von der Platform nehmen."
                    message_label.setText(text)

        elif message == UserMessageType.ASK_FOR_STRAW:
            message_label.setText(
                "Möchtest du einen Strohhalm haben?")

            add_button("Ja", True)
            add_button("Nein", False)

        elif message == UserMessageType.ASK_FOR_ICE:
            message_label.setText(
                "Möchtest du Eis in deinem Cocktail haben?")

            add_button("Ja", True)
            add_button("Nein", False)

        elif message == UserMessageType.STRAWS_EMPTY:
            message_label.setText("Strohhalm konnte nicht hinzugefügt werden.")

            add_button("Egal", False)
            add_button("Erneut versuchen", True)

        elif message == UserMessageType.CLEANING_ADAPTER:
            text = "Für die Reinigung muss der Reinigungsadapter angeschlossen sein.\n"
            text += "Ist der Adapter angeschlossen?"
            message_label.setText(text)

            add_button("Ja", True)
            add_button("Abbrechen", False)

        elif message == UserMessageType.I2C_ERROR:
            text = "Ein Kommunikationsfehler ist aufegtreten.\n"
            text += "Bitte überprüfe, ob alle Module richtig angeschlossen sind \
                und versuche es erneut"
            message_label.setText(text)

            add_button("OK", True)

        elif message == UserMessageType.UNKNOWN_ERROR:
            text = "Ein unbekannter Fehler ist aufgetreten.\n"
            text += "Weitere Informationen findest du im Log"
            message_label.setText(text)

            add_button("OK", True)

        elif message == UserMessageType.GLAS_REMOVED_WHILE_DRAFTING:
            text = "Das Glas wurde während des Mischens entfernt!\n"
            text += "Drücke auf OK, um zum Start zurück zu fahren"
            message_label.setText(text)

            add_button("OK", True)

        elif message == UserMessageType.ICE_EMPTY:
            message_label.setText("Eis konnte nicht hinzugefügt werden.")

            add_button("Eis weg lassen", False)
            add_button("Erneut versuchen", True)

        elif message == UserMessageType.CRUSHER_COVER_OPEN:
            text = "Bitte den Deckel des Eiscrushers schließen!"
            message_label.setText(text)

            add_button("Eis weg lassen", False)
            add_button("Erneut versuchen", True)

        elif message == UserMessageType.CRUSHER_TIMEOUT:
            text = "Eis crushen hat zu lange gedauert, bitte überprüfe Crusher und Akku"
            message_label.setText(text)

            add_button("Eis weg lassen", False)
            add_button("Erneut versuchen", True)

        elif message == UserMessageType.BOARD_NOT_CONNECTED_BALANCE:
            text = "Waage konnte nicht gefunden werden. Bitte Verbindung überprüfen."
            message_label.setText(text)

            add_button("OK", True)

        elif message == UserMessageType.BOARD_NOT_CONNECTED_CRUSHER:
            text = "Eis Crusher konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", True)

        elif message == UserMessageType.BOARD_NOT_CONNECTED_MIXER:
            text = "Mixer konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", True)

        elif message == UserMessageType.BOARD_NOT_CONNECTED_STRAW:
            text = "Strohhalm dispenser konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", True)

        elif message == UserMessageType.BOARD_NOT_CONNECTED_SUGAR:
            text = "Zuckerdosierer konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", True)

        self._message_container.setVisible(True)
        self._content_container.setVisible(False)
        self._title_label.setVisible(False)

    def set_progress(self, progress:int):
        """Set the progress for the items of recipe_list_widgets.
        :param process: The current process"""
        for i, widget in enumerate(self.recipe_list_widgets):
            if progress is not None and i < progress:
                icon = qt_icon_from_file_name("done.png")
            elif progress is not None and i == progress:
                icon = qt_icon_from_file_name("processing.png")
            else:
                icon = qt_icon_from_file_name("queued.png")
            widget.setPixmap(icon.pixmap(icon.availableSizes()[0]))

    def _init_by_status(self):
        # content
        if self.window.barbot_.state == BarBotState.MIXING:

            # ingredients
            recipe_items_list = QtWidgets.QWidget()
            recipe_items_list.setLayout(QtWidgets.QGridLayout())
            recipe_items_list.setProperty("class", "IngredientToDoList")
            self._content_container.layout().addWidget(recipe_items_list)
            self.recipe_list_widgets = []
            self._row_index = 0

            def add_widget(name):
                widget_item = QtWidgets.QLabel()
                self.recipe_list_widgets.append(widget_item)
                recipe_items_list.layout().addWidget(widget_item, self._row_index, 0)
                recipe_items_list.layout().addWidget(QtWidgets.QLabel(name), self._row_index, 1)
                self._row_index += 1

            for item in self.window.barbot_.current_recipe.items:
                add_widget(item.ingredient.name)

            if self.window.barbot_._add_straw:
                add_widget("Strohhalm")
            if self._mainboard.add_ice:
                add_widget("Eis")

            self.set_progress(0)

            # buttons
            button = QtWidgets.QPushButton("Abbrechen")
            button.clicked.connect(self._mainboard.abort_mixing)
            self._content_container.layout().addWidget(button)

            self._title_label.setText(f"'{self._mainboard.current_recipe().name}'\nwird gemischt.")

        elif self.window.barbot_.state == BarBotState.CLEANING:
            self._title_label.setText("Reinigung")
        elif self.window.barbot_.state == BarBotState.CONNECTING:
            self._title_label.setText("Stelle Verbindung her")
        elif self.window.barbot_.state == BarBotState.SEARCHING:
            self._title_label.setText("Suche nach BarBots in der Nähe")
        elif self.window.barbot_.state == BarBotState.CLEANING_CYCLE:
            # buttons
            button = QtWidgets.QPushButton("Abbrechen")
            button.clicked.connect(self._mainboard.abort_mixing)
            self._content_container.layout().addWidget(button)
            self._title_label.setText("Reinigung (Zyklus)")
        elif self.window.barbot_.state == BarBotState.SINGLE_INGREDIENT:
            self._title_label.setText("Dein Nachschlag wird hinzugefügt")
        elif self.window.barbot_.state == BarBotState.STARTUP:
            self._title_label.setText("Starte BarBot, bitte warten")
        elif self.window.barbot_.state == BarBotState.CRUSHING:
            self._title_label.setText("Eis wird hinzugefügt")
        elif self.window.barbot_.state == BarBotState.STRAW:
            self._title_label.setText("Strohhalm wird hinzugefügt")
        else:
            self._title_label.setText(f"Unknown status: {self.window.barbot_.state}")
