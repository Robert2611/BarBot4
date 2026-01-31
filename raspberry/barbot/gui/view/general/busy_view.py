from PyQt5 import QtWidgets, QtCore
from barbot.logic import BarBot, UserMessageType, BarBotStateEnum, UserInputType
from barbot.logic.config import IngredientType
from barbot.logic.recipes import RecipeCollection
from ..base import View
from ...core import qt_icon_from_file_name, set_no_spacing

class BusyView(View):
    """Content that will be shown in the main window when the barbot is busy"""

    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes, is_idle_view=False)

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

    def update_message(self, message: str = None):
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

        def add_button(text, result: UserInputType):
            button = QtWidgets.QPushButton(text)

            def callback():
                return self.barbot_.set_user_input(result)

            button.clicked.connect(callback)
            buttons_container.layout().addWidget(button)

        if message == UserMessageType.INGREDIENT_EMPTY:
            ingredient = self.barbot_.current_recipe_item.ingredient
            if ingredient.type == IngredientType.SUGAR:
                message_string = f"{ingredient.name} ist leer. Bitte nachfüllen."
            else:
                ports = self.barbot_.ports
                position = ports.port_of_ingredient(ingredient) + 1
                message_string = f"Die Zutat '{ingredient.name}'"
                message_string += f" auf Position {position} ist leer.\n"
                message_string += "Bitte neue Flasche anschließen."
            message_label.setText(message_string)

            add_button("Cocktail\nabbrechen", UserInputType.NO)
            add_button("Erneut\nversuchen", UserInputType.YES)

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
                    self._message.layout().addWidget(label)

                    instruction = QtWidgets.QLabel(options.recipe.post_instruction)
                    self._message.layout().addWidget(instruction)
                elif options is not None:
                    text = (
                        "Der Cocktail ist fertig gemischt.\n"
                        + "Du kannst ihn von der Platform nehmen."
                    )
                    message_label.setText(text)

        elif message == UserMessageType.ASK_FOR_STRAW:
            message_label.setText("Möchtest du einen Strohhalm haben?")

            add_button("Ja", UserInputType.YES)
            add_button("Nein", UserInputType.NO)

        elif message == UserMessageType.ASK_FOR_ICE:
            message_label.setText("Möchtest du Eis in deinem Cocktail haben?")

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

    def set_progress(self, progress: int):
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
        state = self.barbot_.state
        if state == BarBotStateEnum.MIXING:

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
                recipe_items_list.layout().addWidget(
                    QtWidgets.QLabel(name), self._row_index, 1
                )
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
        elif state == BarBotStateEnum.CONNECTING:
            self._title_label.setText("Stelle Verbindung her")
        elif state == BarBotStateEnum.SEARCHING:
            self._title_label.setText("Suche nach BarBots in der Nähe")
        elif state == BarBotStateEnum.CLEANING_CYCLE:
            # buttons
            button = QtWidgets.QPushButton("Abbrechen")
            button.clicked.connect(self.barbot_.abort_mixing)
            self._content_container.layout().addWidget(button)
            self._title_label.setText("Reinigung (Zyklus)")
        elif state == BarBotStateEnum.SINGLE_INGREDIENT:
            self._title_label.setText("Dein Nachschlag wird hinzugefügt")
        elif state == BarBotStateEnum.STARTUP:
            self._title_label.setText("Starte BarBot, bitte warten")
        elif state == BarBotStateEnum.CRUSHING:
            self._title_label.setText("Eis wird hinzugefügt")
        elif state == BarBotStateEnum.STRAW:
            self._title_label.setText("Strohhalm wird hinzugefügt")
        else:
            self._title_label.setText(f"Unknown status: {state}")
