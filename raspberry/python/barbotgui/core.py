"""Core functionality of the barbot gui"""
import os
import platform
import sys
from typing import Optional
from venv import logger
from PyQt5 import QtWidgets, QtCore, QtGui
from barbot import BarBot, UserMessageType, BarBotState, run_command
from barbot.config import Ingredient, IngredientType
from barbot.recipes import RecipeCollection, RecipeFilter
from barbot import UserInputType
from barbotgui.controls import set_no_spacing

INGREDIENT_MAX_AMOUNT_OPTION = 17

def restart_barbot():
    """Callback to restart the barbot and gui"""
    QtWidgets.QApplication.instance().quit()
    filepath = os.path.join(sys.path[0], "main.py")
    run_command(filepath)

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


def qt_icon_from_file_name(file_name) -> QtGui.QIcon:
    """Get a QtIcon from containing an image located at a given path.
    :param file_name: Path to the image file"""
    script_dir = os.path.dirname(__file__)
    path = os.path.join(script_dir, "asset", file_name)
    return QtGui.QIcon(path)

class BarBotWindow(QtWidgets.QMainWindow):
    """Main window of the barbot, this is the entry point for the barbot gui"""
    # https://stackoverflow.com/questions/2970312/pyqt4-qtcore-pyqtsignal-object-has-no-attribute-connect
    _barbot_state_trigger = QtCore.pyqtSignal(BarBotState)
    _mixing_progress_trigger = QtCore.pyqtSignal(int)
    _message_trigger = QtCore.pyqtSignal(UserMessageType)
    _show_message_trigger = QtCore.pyqtSignal(str)

    def __init__(self, barbot_:BarBot, recipes: RecipeCollection):
        super().__init__()
        self.recipe_filter = RecipeFilter(descending = True)
        self._barbot = barbot_
        self._recipes = recipes

    @property
    def barbot_(self):
        """The barbot"""
        return self._barbot

    @property
    def recipes(self):
        """Get the collection of recipes"""
        return self._recipes

    def show_message(self, message: str):
        """Show a given message to the user.
        :param message: Message string"""
        self._show_message_trigger.emit(message)

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

    def combobox_ingredients(self, selected_ingredient: Optional[Ingredient]=None, only_available = False, \
                                    only_normal = False, only_weighed = False):
        """Create a combobox with options for ingredients selected by the filter parameters 
        
        :param only_available: If set to true, only return ingredients that \
            are currently connected to ports
        :param only_normal: If set to true, only return ingredients that are pumped
        :param only_weighed: If set to true, only return ingredients that are added by weight    
        """
        entries = self.barbot_.config.get_ingredient_list(
            self.barbot_.ports, only_available, only_normal, only_weighed
        )
        # add ingredient name
        widget = QtWidgets.QComboBox()
        widget.addItem("-", None)
        widget.setCurrentIndex(0)
        for i, item in enumerate(entries):
            widget.addItem(str(item.name), item)
            if item == selected_ingredient:
                widget.setCurrentIndex(i + 1)
        return widget

    def set_view(self, view: Optional["View"]):
        """Set the currrently visible view to the specified instance of View"""

class View(QtWidgets.QWidget):
    """Content that can be shown in the center of the main window"""

    def __init__(self, window: BarBotWindow, is_idle_view:bool = True):
        super().__init__(window)
        self._window = window
        self._is_idle_view = is_idle_view

    @property
    def is_idle_view(self) -> bool:
        """Get whether the view is an idle view"""
        return self._is_idle_view

    @property
    def window(self):
        """Get the window the view is used for"""
        return self._window

    @property
    def barbot_(self):
        """The barbot"""
        return self._window.barbot_

    @staticmethod
    def set_system_view(container: QtWidgets.QWidget):
        """Get the systems view widget."""
        container_layout = QtWidgets.QVBoxLayout()
        container.setLayout(container_layout)

        label = QtWidgets.QLabel("Software")
        container_layout.addWidget(label)
        # reopen software
        button = QtWidgets.QPushButton("Neu Starten")
        button.clicked.connect(restart_barbot)
        container_layout.addWidget(button)

        # close software
        button = QtWidgets.QPushButton("Schließen")
        button.clicked.connect(QtWidgets.QApplication.instance().quit)
        container_layout.addWidget(button)

        label = QtWidgets.QLabel("PI")
        container_layout.addWidget(label)

        # shutdown
        button = QtWidgets.QPushButton("Herunterfahren")
        button.clicked.connect(lambda: run_command("sudo shutdown now"))
        container_layout.addWidget(button)

        # reboot
        button = QtWidgets.QPushButton("Neu Starten")
        button.clicked.connect(lambda: run_command("sudo reboot"))
        container_layout.addWidget(button)

        # dummy
        container_layout.addWidget(QtWidgets.QWidget(), 1)

class SystemBusyView(View):
    """View to access system (eg. restart) when the mainboard is busy"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window, is_idle_view=False)

        self.setLayout(QtWidgets.QVBoxLayout())
        set_no_spacing(self.layout())

        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header)

        self._content = QtWidgets.QWidget()
        self.layout().addWidget(self._content)

        # add actual content
        View.set_system_view(self._content)

class BusyView(View):
    """Content that will be shown in the main window when the barbot is busy"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window, is_idle_view=False)

        self._message_widget = None

        grid_layout = QtWidgets.QGridLayout()
        self.setLayout(grid_layout)
        set_no_spacing(grid_layout)

        centered = QtWidgets.QFrame()
        centered.setLayout(QtWidgets.QVBoxLayout())
        centered.setProperty("class", "CenteredContent")
        # pylint: disable-next=no-member
        grid_layout.addWidget(centered, 0, 0, QtCore.Qt.AlignmentFlag.AlignCenter)

        self._title_label = QtWidgets.QLabel("")
        # pylint: disable-next=no-member
        self._title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
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

    def update_message(self, message:Optional[UserMessageType] = None):
        """Update the message shown to the user"""
        if message is None:
            message = UserMessageType.NONE
        # delete old message
        if self._message_widget is not None:
            self._message_widget.setParent(None) # type: ignore

        # if message is none show the content again
        if message == UserMessageType.NONE:
            self._message_container.setVisible(False)
            self._content_container.setVisible(True)
            self._title_label.setVisible(True)
            return

        self._message_widget = QtWidgets.QWidget()
        self._message_widget.setLayout(QtWidgets.QVBoxLayout())
        self._message_container.layout().addWidget(self._message_widget)

        message_label = QtWidgets.QLabel()
        self._message_widget.layout().addWidget(message_label)

        buttons_container = QtWidgets.QWidget()
        buttons_container.setLayout(QtWidgets.QHBoxLayout())
        self._message_widget.layout().addWidget(buttons_container)

        def add_button(text, result:UserInputType):
            button = QtWidgets.QPushButton(text)
            def callback():
                return self.barbot_.set_user_input(result)
            button.clicked.connect(callback)
            buttons_container.layout().addWidget(button)

        if message == UserMessageType.INGREDIENT_EMPTY:
            if self.barbot_.current_recipe_item is not None:
                ingredient = self.barbot_.current_recipe_item.ingredient
                if ingredient.type == IngredientType.SUGAR:
                    message_string = f"{ingredient.name} ist leer. Bitte nachfüllen."
                else:
                    ports = self.barbot_.ports
                    position = ports.port_of_ingredient(ingredient)
                    if position is not None:
                        position += 1
                    message_string = f"Die Zutat '{ingredient.name}'"
                    message_string += f" auf Position {position} ist leer.\n"
                    message_string += "Bitte neue Flasche anschließen."
                message_label.setText(message_string)

                add_button("Cocktail\nabbrechen", UserInputType.NO)
                add_button("Erneut\nversuchen", UserInputType.YES)
            else:
                logger.error("No current_recipe_item found while showing INGREDIENT_EMPTY message.")
                self.barbot_.set_user_input(UserInputType.NO)

        elif message == UserMessageType.PLACE_GLAS:
            message_label.setText("Bitte ein Glas auf die Plattform stellen.")

            add_button("abbrechen", UserInputType.NO)

        elif message == UserMessageType.MIXING_DONE_REMOVE_GLAS:
            if self.barbot_.was_aborted:
                message_label.setText("Cocktail abgebrochen!")
            else:
                options = self.barbot_.current_mixing_options
                if options is not None and options.recipe.post_instruction:
                    label = QtWidgets.QLabel("Zusätzliche Informationen:")
                    self._message_widget.layout().addWidget(label)

                    instruction = QtWidgets.QLabel(options.recipe.post_instruction)
                    self._message_widget.layout().addWidget(instruction)
                elif options is not None:
                    text = "Der Cocktail ist fertig gemischt.\n" + \
                        "Du kannst ihn von der Platform nehmen."
                    message_label.setText(text)

        elif message == UserMessageType.ASK_FOR_STRAW:
            message_label.setText(
                "Möchtest du einen Strohhalm haben?")

            add_button("Ja", UserInputType.YES)
            add_button("Nein", UserInputType.NO)

        elif message == UserMessageType.ASK_FOR_ICE:
            message_label.setText(
                "Möchtest du Eis in deinem Cocktail haben?")

            add_button("Ja", UserInputType.YES)
            add_button("Nein", UserInputType.NO)

        elif message == UserMessageType.STRAWS_EMPTY:
            message_label.setText("Strohhalm konnte nicht hinzugefügt werden.")

            add_button("Egal", UserInputType.NO)
            add_button("Erneut versuchen", UserInputType.YES)

        elif message == UserMessageType.CLEANING_ADAPTER:
            text = "Für die Reinigung muss der Reinigungsadapter angeschlossen sein.\n"
            text += "Ist der Adapter angeschlossen?"
            message_label.setText(text)

            add_button("Ja", UserInputType.YES)
            add_button("Abbrechen", UserInputType.NO)

        elif message == UserMessageType.I2C_ERROR:
            text = "Ein Kommunikationsfehler ist aufegtreten.\n"
            text += "Bitte überprüfe, ob alle Module richtig angeschlossen sind \
                und versuche es erneut"
            message_label.setText(text)

            add_button("OK", UserInputType.YES)

        elif message == UserMessageType.UNKNOWN_ERROR:
            text = "Ein unbekannter Fehler ist aufgetreten.\n"
            text += "Weitere Informationen findest du im Log"
            message_label.setText(text)

            add_button("OK", UserInputType.YES)

        elif message == UserMessageType.GLAS_REMOVED_WHILE_DRAFTING:
            text = "Das Glas wurde während des Mischens entfernt!\n"
            text += "Drücke auf OK, um zum Start zurück zu fahren"
            message_label.setText(text)

            add_button("OK", UserInputType.YES)

        elif message == UserMessageType.ICE_EMPTY:
            message_label.setText("Eis konnte nicht hinzugefügt werden.")

            add_button("Eis weg lassen", UserInputType.NO)
            add_button("Erneut versuchen", UserInputType.YES)

        elif message == UserMessageType.CRUSHER_COVER_OPEN:
            text = "Bitte den Deckel des Eiscrushers schließen!"
            message_label.setText(text)

            add_button("Eis weg lassen", UserInputType.NO)
            add_button("Erneut versuchen", UserInputType.YES)

        elif message == UserMessageType.CRUSHER_TIMEOUT:
            text = "Eis crushen hat zu lange gedauert, bitte überprüfe Crusher und Akku"
            message_label.setText(text)

            add_button("Eis weg lassen", UserInputType.NO)
            add_button("Erneut versuchen", UserInputType.YES)

        elif message == UserMessageType.BOARD_NOT_CONNECTED_BALANCE:
            text = "Waage konnte nicht gefunden werden. Bitte Verbindung überprüfen."
            message_label.setText(text)

            add_button("OK", UserInputType.YES)

        elif message == UserMessageType.BOARD_NOT_CONNECTED_CRUSHER:
            text = "Eis Crusher konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", UserInputType.YES)

        elif message == UserMessageType.BOARD_NOT_CONNECTED_MIXER:
            text = "Mixer konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", UserInputType.YES)

        elif message == UserMessageType.BOARD_NOT_CONNECTED_STRAW:
            text = "Strohhalm dispenser konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", UserInputType.YES)

        elif message == UserMessageType.BOARD_NOT_CONNECTED_SUGAR:
            text = "Zuckerdosierer konnte nicht gefunden werden. \
                Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", UserInputType.YES)

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
        if self.barbot_.state == BarBotState.MIXING:

            # ingredients
            recipe_items_list = QtWidgets.QWidget()
            grid_layout = QtWidgets.QGridLayout()
            recipe_items_list.setLayout(grid_layout)
            recipe_items_list.setProperty("class", "IngredientToDoList")
            self._content_container.layout().addWidget(recipe_items_list)
            self.recipe_list_widgets = []
            self._row_index = 0

            def add_widget(name):
                widget_item = QtWidgets.QLabel()
                self.recipe_list_widgets.append(widget_item)
                grid_layout.addWidget(widget_item, self._row_index, 0)
                grid_layout.addWidget(QtWidgets.QLabel(name), self._row_index, 1)
                self._row_index += 1

            options = self.barbot_.current_mixing_options
            if options is not None:
                for item in options.recipe.items:
                    add_widget(item.ingredient.name)

                if options.add_straw:
                    add_widget("Strohhalm")
                if options.add_ice:
                    add_widget("Eis")

            self.set_progress(0)

            # buttons
            button = QtWidgets.QPushButton("Abbrechen")
            button.clicked.connect(self.barbot_.abort_mixing)
            self._content_container.layout().addWidget(button)

            if options is not None:
                self._title_label.setText(f"'{options.recipe.name}'\nwird gemischt.")

        elif self.barbot_.state == BarBotState.CLEANING:
            self._title_label.setText("Reinigung")
        elif self.barbot_.state == BarBotState.CONNECTING:
            self._title_label.setText("Stelle Verbindung her")
        elif self.barbot_.state == BarBotState.SEARCHING:
            self._title_label.setText("Suche nach BarBots in der Nähe")
        elif self.barbot_.state == BarBotState.CLEANING_CYCLE:
            # buttons
            button = QtWidgets.QPushButton("Abbrechen")
            button.clicked.connect(self.barbot_.abort_mixing)
            self._content_container.layout().addWidget(button)
            self._title_label.setText("Reinigung (Zyklus)")
        elif self.barbot_.state == BarBotState.SINGLE_INGREDIENT:
            self._title_label.setText("Dein Nachschlag wird hinzugefügt")
        elif self.barbot_.state == BarBotState.STARTUP:
            self._title_label.setText("Starte BarBot, bitte warten")
        elif self.barbot_.state == BarBotState.CRUSHING:
            self._title_label.setText("Eis wird hinzugefügt")
        elif self.barbot_.state == BarBotState.STRAW:
            self._title_label.setText("Strohhalm wird hinzugefügt")
        else:
            self._title_label.setText(f"Unknown status: {self.barbot_.state}")
