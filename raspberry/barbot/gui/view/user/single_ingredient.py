from enum import Enum, auto
from PyQt5 import QtWidgets, QtCore
from barbot.logic.recipes import RecipeItem
from barbot.logic.config import IngredientType, Stir as StirIngredient
from barbot.logic import RecipeCollection, BarBot
from ...common import qt_icon_from_file_name
from .base import UserView

class SingleIngredient(UserView):
    """View for adding single ingredients"""
    class ActionType(Enum):
        """The type of ingredient that should be added"""
        INGREDIENT = auto()
        STIR = auto()
        STRAW = auto()
        ICE = auto()

    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)

        self._ice_index = -2
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        self._add_title_to_fixed_content("Nachschlag")
        self._add_info_text()
        self._add_ingredient_section()

        if self.barbot_.config.straw_dispenser_connected:
            self._add_straw_button()
        if self.barbot_.config.stirrer_connected:
            self._add_stir_button()
        if self.barbot_.config.ice_crusher_connected:
            self._add_crusher_button()

        self._add_dummy_widget_to_content()

    def _add_info_text(self):
        text = QtWidgets.QLabel(
            "Ist dein Cocktail noch nicht perfekt?\nHier kannst du nachhelfen.")
        self._content.layout().addWidget(text)

    def _add_ingredient_section(self):
        panel = QtWidgets.QWidget()
        panel.setProperty("class", "CenterPanel")
        panel.setLayout(QtWidgets.QVBoxLayout())
        self._content.layout().addWidget(panel)
        self._content.layout().setAlignment(panel, QtCore.Qt.AlignCenter)

        # ingredient selector
        self._ingredient_widget = self.combobox_ingredients(
            only_available=True,
            only_weighed=True
        )
        panel.layout().addWidget(self._ingredient_widget)

        # amount selector
        self._amount_widget = self.combobox_amounts()
        panel.layout().addWidget(self._amount_widget)

        # start button
        self._start_button = QtWidgets.QPushButton("Los")
        self._start_button.clicked.connect(
            lambda: self._start(self.ActionType.INGREDIENT)
        )
        panel.layout().addWidget(self._start_button)

    def _add_stir_button(self):
        icon = qt_icon_from_file_name("stir.png")
        stir_button = QtWidgets.QPushButton(icon, "")
        stir_button.setProperty("class", "IconButton")
        stir_button.clicked.connect(
            lambda: self._start(self.ActionType.STIR)
        )
        self._content.layout().addWidget(stir_button)
        self._content.layout().setAlignment(stir_button, QtCore.Qt.AlignCenter)

    def _add_straw_button(self):
        icon = qt_icon_from_file_name("straw.png")
        straw_button = QtWidgets.QPushButton(icon, "")
        straw_button.setProperty("class", "IconButton")
        straw_button.clicked.connect(
            lambda: self._start(self.ActionType.STRAW)
        )
        self._content.layout().addWidget(straw_button)
        self._content.layout().setAlignment(straw_button, QtCore.Qt.AlignCenter)

    def _add_crusher_button(self):
        icon = qt_icon_from_file_name("ice.png")
        ice_button = QtWidgets.QPushButton(icon, "")
        ice_button.setProperty("class", "IconButton")
        ice_button.clicked.connect(
            lambda: self._start(self.ActionType.ICE)
        )
        self._content.layout().addWidget(ice_button)
        self._content.layout().setAlignment(ice_button, QtCore.Qt.AlignCenter)

    def _start(self, action_type: ActionType):
        if not self.barbot_.can_start_order:
            self.show_message_trigger.emit(
                "Bitte warten bis die laufende\nAktion abgeschlossen ist.")
            return
        config = self.barbot_.config
        if action_type == self.ActionType.INGREDIENT:
            ingredient = self._ingredient_widget.currentData()
            amount = self._amount_widget.currentData()
            if ingredient is not None and amount > 0:
                item = RecipeItem(ingredient, amount)
                if item.ingredient.type == IngredientType.SUGAR:
                    pass
                else:
                    # normal ingredient
                    port = self.barbot_.ports.port_of_ingredient(ingredient)
                    if port is None:
                        self.show_message_trigger.emit(
                            "Diese Zutat ist nicht anschlossen")
                        return
                item.amount = amount
                item.ingredient = ingredient
                self.barbot_.start_single_ingredient(item)
                self.show_message_trigger.emit("Zutat wird hinzugefügt")
            else:
                self.show_message_trigger.emit(
                    "Bitte eine Zutat und\neine Menge auswählen")
        elif action_type == self.ActionType.STIR and config.stirrer_connected:
            item = RecipeItem(StirIngredient, 0)
            self.barbot_.start_single_ingredient(item)
            self.show_message_trigger.emit("Cocktail wird gerührt")
        elif action_type == self.ActionType.ICE and config.ice_crusher_connected:
            self.barbot_.start_crushing()
            self.show_message_trigger.emit("Eis wird hinzugefügt")
        elif action_type == self.ActionType.STRAW and config.straw_dispenser_connected:
            self.barbot_.start_straw()
            self.show_message_trigger.emit("Strohhalm wird hinzugefügt")
