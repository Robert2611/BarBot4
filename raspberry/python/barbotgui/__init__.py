"""The barbot gui"""
import os
import logging
import platform
import sys
from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import barbot
from barbot.ingredients import Ingredient, IngredientType
from barbot.ingredients import get_list as get_ingredient_list
from barbot import recipes
from barbot import BarBot, BarBotConfig, BarBotState, UserMessageType
from barbotgui.userviews import ListRecipes
from barbotgui.adminviews import AdminLogin
from barbot.recipes import RecipeCollection
from barbotgui.userviews import ListRecipes, RecipeNewOrEdit, SingleIngredient, Statistics

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

def set_no_spacing(layout):
    """Set the spacing to zero for a given QtLayout
    :param layout: The layout"""
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)


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


class Keyboard(QtWidgets.QWidget):
    """A keyboard used for touch input"""
    _is_widgets_created = False
    _is_shift = False
    target: QtWidgets.QLineEdit = None

    def __init__(self, target: QtWidgets.QLineEdit, style=None):
        super().__init__()
        self.target = target
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.update_keys()
        self.setProperty("class", "Keyboard")
        if style is not None:
            self.setStyleSheet(style)
        if is_raspberry():
            self.setCursor(QtCore.Qt.BlankCursor)
        # move to bottom of the screen
        desktop = Qt.QApplication.desktop().availableGeometry()
        desired = Qt.QRect(Qt.QPoint(0, 0), self.sizeHint())
        desired.moveBottomRight(desktop.bottomRight())
        desired.setLeft(desktop.left())
        self.setGeometry(desired)

    def update_keys(self):
        """Update or, at first call, create the keyboard keys"""
            # first row
        keys = [
            ["1", "!"], ["2", "\""], ["3", "§"], ["4", "$"], ["5", "%"],
            ["6", "&"], ["7", "/"], ["8", "("], ["9", ")"], ["0", "ß"]
        ]
        if not self._is_widgets_created:
            self.first_row = self.add_row([data[0] for data in keys])
        for index, data in enumerate(keys):
            self.first_row[index].setText(
                data[1] if self._is_shift else data[0])

            # second row
        keys = ["q", "w", "e", "r", "t", "z", "u", "i", "o", "p"]
        if not self._is_widgets_created:
            self.second_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.second_row[index].setText(
                str.upper(letter) if self._is_shift else letter)

            # third row
        keys = ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ö"]
        if not self._is_widgets_created:
            self.third_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.third_row[index].setText(
                str.upper(letter) if self._is_shift else letter)

        # fourth row
        keys = ["y", "x", "c", "v", "b", "n", "m", "ä", "ü"]
        if not self._is_widgets_created:
            self.fourth_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.fourth_row[index].setText(
                str.upper(letter) if self._is_shift else letter)

        # last row
        if not self._is_widgets_created:
            row = QtWidgets.QWidget()
            row.setLayout(QtWidgets.QHBoxLayout())
            set_no_spacing(row.layout())
            # shift
            button = QtWidgets.QPushButton("▲")
            button.clicked.connect(lambda: self.button_clicked("shift"))
            row.layout().addWidget(button)
            # space
            button = QtWidgets.QPushButton(" ")
            button.clicked.connect(lambda: self.button_clicked(" "))
            row.layout().addWidget(button)
            # delete
            button = QtWidgets.QPushButton("←")
            button.clicked.connect(lambda: self.button_clicked("delete"))
            row.layout().addWidget(button)
            self.layout().addWidget(row)
        self._is_widgets_created = True

    def button_clicked(self, content):
        """Handle a button click"""
        if self.target is None:
            return
        if content == "shift":
            self._is_shift = not self._is_shift
            self.update_keys()
        else:
            if content == "delete":
                self.target.setText(self.target.text()[:-1])
            else:
                self.target.setText(self.target.text() + content)
            # reset shift state
            if self._is_shift:
                self._is_shift = False
                self.update_keys()

    def add_row(self, keys: list[str]) -> list[QtWidgets.QPushButton]:
        """Add a row defined by a list of characters to the layout
        :param keys: List of key characters to be added
        :retunrs: List of buttons that were added
        """
        res = []
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        set_no_spacing(row.layout())
        for letter in keys:
            button = QtWidgets.QPushButton(letter)
            button.clicked.connect(
                lambda checked, b=button: self.button_clicked(b.text()))
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res

class Numpad(QtWidgets.QWidget):
    """More simple version of a keyboard with only numbers"""
    target: QtWidgets.QSpinBox = None
    current_value: int = 0

    def __init__(self, target: QtWidgets.QSpinBox, style=None):
        super().__init__()
        self.target = target
        self.current_value = 0
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setProperty("class", "Keyboard")

        #value label
        self._value_label = QtWidgets.QLabel()
        self.layout().addWidget(self._value_label)
        #TODO: Make label white, maybe show current value in gray before first entry

        #keypad
        self.create_keypad()

        if style is not None:
            self.setStyleSheet(style)
        if is_raspberry():
            self.setCursor(QtCore.Qt.BlankCursor)
        # move to bottom of the screen
        desktop = Qt.QApplication.desktop().availableGeometry()
        desired = Qt.QRect(Qt.QPoint(0, 0), self.sizeHint())
        desired.moveBottomRight(desktop.bottomRight())
        desired.setLeft(desktop.left())
        self.setGeometry(desired)

    def create_keypad(self):
        """Create the buttons for the keypad"""
        # numpad
        numpad = QtWidgets.QWidget()
        numpad.setLayout(QtWidgets.QGridLayout())
        self.layout().setAlignment(numpad, QtCore.Qt.AlignCenter)
        for y in range(0, 3):
            for x in range(0, 3):
                num = y * 3 + x + 1
                button = QtWidgets.QPushButton(str(num))
                button.clicked.connect(
                    lambda checked, value=num: self.button_clicked(value))
                numpad.layout().addWidget(button, y, x)
        # Cancel
        button = QtWidgets.QPushButton("Abbrechen")
        button.clicked.connect(lambda checked: self.close())
        numpad.layout().addWidget(button, 3, 0)
        # zero
        button = QtWidgets.QPushButton("0")
        button.clicked.connect(lambda checked: self.button_clicked(0))
        numpad.layout().addWidget(button, 3, 1)
        # enter
        button = QtWidgets.QPushButton("Ok")
        button.clicked.connect(lambda checked: self.apply())
        numpad.layout().addWidget(button, 3, 2)
        self.layout().addWidget(numpad)

    def apply(self):
        """Apply the new value to the target"""
        if self.target.minimum() <= self.current_value <= self.target.maximum():
            self.target.setValue(self.current_value)
        self.close()

    def button_clicked(self, number):
        """A number button was clicked, handle it"""
        if self.target is None:
            return
        self.current_value *= 10
        self.current_value += number
        self._value_label.setText(str(self.current_value))

    def add_row(self, keys:list[str]) -> list[QtWidgets.QPushButton]:
        """Add a row defined by a list of characters to the layout
        :param keys: List of key characters to be added
        :retunrs: List of buttons that were added
        """
        res = []
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())

        set_no_spacing(row.layout())
        for letter in keys:
            button = QtWidgets.QPushButton(letter)
            button.clicked.connect(
                lambda checked, b=button: self.button_clicked(b.text()))
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res


class MainWindow(QtWidgets.QMainWindow):
    """Main window for the barbot"""
    def __init__(self, barbot_:BarBot, recipes: RecipeCollection):
        super().__init__()
        self._barbot = barbot_
        self.recipe_filter: recipes.RecipeFilter
        self._current_view = None
        self._barbot_state_trigger = QtCore.pyqtBoundSignal(barbot.BarBotState)
        self._mixing_progress_trigger = QtCore.pyqtBoundSignal(int)
        self._message_trigger = QtCore.pyqtBoundSignal(barbot.UserMessageType)
        self._show_message_trigger = QtCore.pyqtBoundSignal(str)
        self._last_idle_view = None
        self._keyboard: Keyboard = None
        self._timer: QtCore.QTimer
        self._admin_button_active = False
        self.recipe_filter = recipes.RecipeFilter()
        self.recipe_filter.Descending = True
        self._recipes = recipes

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

    def get_system_view(self) -> QtWidgets.QWidget:
        """Get the systems view widget."""
        container = QtWidgets.QWidget()
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
        button.clicked.connect(
            lambda: QtWidgets.QApplication.instance().quit())
        container.layout().addWidget(button)

        label = QtWidgets.QLabel("PI")
        container.layout().addWidget(label)

        # shutdown
        button = QtWidgets.QPushButton("Herunterfahren")
        button.clicked.connect(lambda: barbot.run_command("sudo shutdown now"))
        container.layout().addWidget(button)

        # reboot
        button = QtWidgets.QPushButton("Neu Starten")
        button.clicked.connect(lambda: barbot.run_command("sudo reboot"))
        container.layout().addWidget(button)

        # dummy
        container.layout().addWidget(QtWidgets.QWidget(), 1)

        return container

    def restart_barbot(self):
        """Callback to restart the barbot and gui"""
        QtWidgets.QApplication.instance().quit()
        filepath = os.path.join(sys.path[0], "main.py")
        barbot.run_command(filepath)

    def header_clicked(self, _):
        """Handle the header click"""
        if not self._admin_button_active:
            self._admin_button_active = True
            # reset the admin button after one second
            self._timer = QtCore.QTimer(self)
            def _reset_admin_button():
                self._admin_button_active = False
            self._timer.singleShot(1000, self._reset_admin_button)
            return
        if not self._barbot.is_busy:
            self.set_view(AdminLogin(self))
        else:
            self.set_view(self.get_systems_view())

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
            if isinstance(self._current_view, IdleView)\
                    and not isinstance(view, IdleView):
                # just remove it from the visuals
                self._current_view.setParent(None)
            else:
                # delete the view
                self._current_view.deleteLater()
        self._current_view = view
        # save the last used idle view
        if isinstance(view, IdleView):
            self._last_idle_view = view
        self._content_wrapper.layout().addWidget(self._current_view)

    def update_view(self, force_reload=False):
        """Set the view to the busy view if the barbot is busy.
        Else load the last idle view. If none was set, load the recipe list """
        if not self._barbot.is_busy():
            if self._last_idle_view is None or force_reload:
                self.set_view(ListRecipes(self))
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
        entries = get_ingredient_list(only_available, only_normal, only_weighed)
        # add ingredient name
        widget = QtWidgets.QComboBox()
        widget.addItem("-", None)
        widget.setCurrentIndex(0)
        for i, item in enumerate(entries):
            widget.addItem(str(item.name), item)
            if item == selected_ingredient:
                widget.setCurrentIndex(i)
        return widget

class View(QtWidgets.QWidget):
    """Content that can be shown in the center of the main window"""
    window: MainWindow

    def __init__(self, window: MainWindow):
        super().__init__(window)
        self.window = window


class BusyView(View):
    """Content that will be shown in the main window when the barbot is busy"""
    _message = None

    def __init__(self, window: MainWindow):
        super().__init__(window)

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

        if message == barbot.UserMessageType.INGREDIENT_EMPTY:
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

        elif message == barbot.UserMessageType.PLACE_GLAS:
            message_label.setText("Bitte ein Glas auf die Plattform stellen.")

        elif message == barbot.UserMessageType.MIXING_DONE_REMOVE_GLAS:
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

        elif message == barbot.UserMessageType.ASK_FOR_STRAW:
            message_label.setText(
                "Möchtest du einen Strohhalm haben?")

            add_button("Ja", True)
            add_button("Nein", False)

        elif message == barbot.UserMessageType.ASK_FOR_ICE:
            message_label.setText(
                "Möchtest du Eis in deinem Cocktail haben?")

            add_button("Ja", True)
            add_button("Nein", False)

        elif message == barbot.UserMessageType.STRAWS_EMPTY:
            message_label.setText("Strohhalm konnte nicht hinzugefügt werden.")

            add_button("Egal", False)
            add_button("Erneut versuchen", True)

        elif message == barbot.UserMessageType.CLEANING_ADAPTER:
            text = "Für die Reinigung muss der Reinigungsadapter angeschlossen sein.\n"
            text += "Ist der Adapter angeschlossen?"
            message_label.setText(text)

            add_button("Ja", True)
            add_button("Abbrechen", False)

        elif message == barbot.UserMessageType.I2C_ERROR:
            text = "Ein Kommunikationsfehler ist aufegtreten.\n"
            text += "Bitte überprüfe, ob alle Module richtig angeschlossen sind \
                und versuche es erneut"
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessageType.UNKNOWN_ERROR:
            text = "Ein unbekannter Fehler ist aufgetreten.\n"
            text += "Weitere Informationen findest du im Log"
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessageType.GLAS_REMOVED_WHILE_DRAFTING:
            text = "Das Glas wurde während des Mischens entfernt!\n"
            text += "Drücke auf OK, um zum Start zurück zu fahren"
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessageType.ICE_EMPTY:
            message_label.setText("Eis konnte nicht hinzugefügt werden.")

            add_button("Eis weg lassen", False)
            add_button("Erneut versuchen", True)

        elif message == barbot.UserMessageType.CRUSHER_COVER_OPEN:
            text = "Bitte den Deckel des Eiscrushers schließen!"
            message_label.setText(text)

            add_button("Eis weg lassen", False)
            add_button("Erneut versuchen", True)

        elif message == barbot.UserMessageType.CRUSHER_TIMEOUT:
            text = "Eis crushen hat zu lange gedauert, bitte überprüfe Crusher und Akku"
            message_label.setText(text)

            add_button("Eis weg lassen", False)
            add_button("Erneut versuchen", True)

        elif message == barbot.UserMessageType.BOARD_NOT_CONNECTED_BALANCE:
            text = "Waage konnte nicht gefunden werden. Bitte Verbindung überprüfen."
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessageType.BOARD_NOT_CONNECTED_CRUSHER:
            text = "Eis Crusher konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessageType.BOARD_NOT_CONNECTED_MIXER:
            text = "Mixer konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessageType.BOARD_NOT_CONNECTED_STRAW:
            text = "Strohhalm dispenser konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessageType.BOARD_NOT_CONNECTED_SUGAR:
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
        if self._mainboard.get_state() == self._mainboard.BarBotState.MIXING:

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

            for item in self._mainboard.current_recipe().items:
                add_widget(item.ingredient.name)

            if self._mainboard.add_straw:
                add_widget("Strohhalm")
            if self._mainboard.add_ice:
                add_widget("Eis")

            self.set_progress(0)

            # buttons
            button = QtWidgets.QPushButton("Abbrechen")
            button.clicked.connect(self._mainboard.abort_mixing)
            self._content_container.layout().addWidget(button)

            self._title_label.setText(f"'{self._mainboard.current_recipe().name}'\nwird gemischt.")

        elif self._mainboard.get_state() == self._mainboard.BarBotState.CLEANING:
            self._title_label.setText("Reinigung")
        elif self._mainboard.get_state() == self._mainboard.BarBotState.CONNECTING:
            self._title_label.setText("Stelle Verbindung her")
        elif self._mainboard.get_state() == self._mainboard.BarBotState.SEARCHING:
            self._title_label.setText("Suche nach BarBots in der Nähe")
        elif self._mainboard.get_state() == self._mainboard.BarBotState.CLEANING_CYCLE:
            # buttons
            button = QtWidgets.QPushButton("Abbrechen")
            button.clicked.connect(self._mainboard.abort_mixing)
            self._content_container.layout().addWidget(button)
            self._title_label.setText("Reinigung (Zyklus)")
        elif self._mainboard.get_state() == self._mainboard.BarBotState.SINGLE_INGREDIENT:
            self._title_label.setText("Dein Nachschlag wird hinzugefügt")
        elif self._mainboard.get_state() == self._mainboard.BarBotState.STARTUP:
            self._title_label.setText("Starte BarBot, bitte warten")
        elif self._mainboard.get_state() == self._mainboard.BarBotState.CRUSHING:
            self._title_label.setText("Eis wird hinzugefügt")
        elif self._mainboard.get_state() == self._mainboard.BarBotState.STRAW:
            self._title_label.setText("Strohhalm wird hinzugefügt")
        else:
            self._title_label.setText(f"Unknown status: {self._mainboard.get_state()}")


class IdleView(View):
    def __init__(self, window: MainWindow):
        super().__init__(window)
        self.navigation_items = [
            ["Liste", ListRecipes],
            ["Neu", RecipeNewOrEdit],
            ["Nachschlag", SingleIngredient],
            ["Statistik", Statistics],
        ]
        self.setLayout(QtWidgets.QVBoxLayout())
        set_no_spacing(self.layout())

        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header)

        # navigation
        self.navigation = QtWidgets.QWidget()
        self.layout().addWidget(self.navigation)
        self.navigation.setLayout(QtWidgets.QHBoxLayout())

        for text, _class in self.navigation_items:
            button = QtWidgets.QPushButton(text)
            def btn_click(_, c=_class):
                return self.window.set_view(c(self.window))
            button.clicked.connect(btn_click)
            self.navigation.layout().addWidget(button, 1)

        # content
        content_wrapper = QtWidgets.QWidget()
        self.layout().addWidget(content_wrapper, 1)
        content_wrapper.setLayout(QtWidgets.QGridLayout())
        set_no_spacing(content_wrapper.layout())

        # fixed content
        self._fixed_content = QtWidgets.QWidget()
        content_wrapper.layout().addWidget(self._fixed_content)

        scroller = QtWidgets.QScrollArea()
        scroller.setProperty("class", "ContentScroller")
        scroller.setWidgetResizable(True)
        scroller.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        content_wrapper.layout().addWidget(scroller)

        QtWidgets.QScroller.grabGesture(
            scroller.viewport(),
            QtWidgets.QScroller.LeftMouseButtonGesture
        )

        self._content = QtWidgets.QWidget()
        self._content.setProperty("class", "IdleContent")
        scroller.setWidget(self._content)
