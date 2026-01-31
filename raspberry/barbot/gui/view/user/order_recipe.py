from PyQt5 import QtWidgets, QtCore
from barbot.logic import MixingOptions
from barbot.logic.recipes import Recipe
from barbot.logic import RecipeCollection, BarBot
from ...core import qt_icon_from_file_name
from .base import UserView

class OrderRecipe(UserView):
    """Shown when the order button is clicked for a recipe"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection, recipe: Recipe = None):
        super().__init__(barbot, recipes)

        self._recipe = recipe
        self._cb_ice = None
        self._cb_straw = None

        self._content.setLayout(QtWidgets.QGridLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        self._add_title_to_fixed_content("Cocktail mischen")
        self._add_centered_content_to_content()
        self._add_cocktail_name_to_centered_content()
        self._add_special_ingredient_buttons()
        if recipe.pre_instruction:
            self._add_pre_instruction_to_centered_content()
        self._add_order_and_cancel_button_to_centered_content()

    def _add_order_and_cancel_button_to_centered_content(self):
        buttons_container = QtWidgets.QWidget()
        buttons_container.setLayout(QtWidgets.QHBoxLayout())
        self._centered_content.layout().addWidget(buttons_container)

        # cancel
        button = QtWidgets.QPushButton("Abbrechen")

        def show_list():
            from .list_recipes import ListRecipes
            self.switch_view_trigger.emit(ListRecipes(self.barbot_, self.recipes))
        button.clicked.connect(show_list)
        buttons_container.layout().addWidget(button)
        # order
        button = QtWidgets.QPushButton("Los!")
        button.clicked.connect(self._order)
        buttons_container.layout().addWidget(button)

    def _add_cocktail_name_to_centered_content(self):
        label = QtWidgets.QLabel(self._recipe.name)
        label.setProperty("class", "Headline")
        self._centered_content.layout().addWidget(label)

    def _add_pre_instruction_to_centered_content(self):
        text = "Bitte Glas vorbereiten:\n" + self._recipe.pre_instruction
        label = QtWidgets.QLabel(text)
        self._centered_content.layout().addWidget(label)

    def _add_centered_content_to_content(self):
        self._centered_content = QtWidgets.QWidget()
        self._centered_content.setLayout(QtWidgets.QVBoxLayout())
        self._centered_content.setProperty("class", "CenteredContent")
        self._content.layout().addWidget(self._centered_content, 0, 0, QtCore.Qt.AlignCenter)

    def _add_special_ingredient_buttons(self):
        # container
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QHBoxLayout())
        self._centered_content.layout().addWidget(container)

        # ask for ice if module is connected
        if self.barbot_.config.ice_crusher_connected:
            self._add_ice_button_to(container)

        # ask for straw if module is connected
        if self.barbot_.config.straw_dispenser_connected:
            self._add_straw_button_to(container)

    def _add_ice_button_to(self, container):
        icon = qt_icon_from_file_name("ice.png")
        ice_button = QtWidgets.QPushButton(icon, "")
        ice_button.setCheckable(True)
        ice_button.setProperty("class", "IconCheckButton")
        container.layout().addWidget(ice_button)
        container.layout().setAlignment(ice_button, QtCore.Qt.AlignCenter)
        self._cb_ice = ice_button

    def _add_straw_button_to(self, container):
        icon = qt_icon_from_file_name("straw.png")
        straw_button = QtWidgets.QPushButton(icon, "")
        straw_button.setCheckable(True)
        straw_button.setProperty("class", "IconCheckButton")
        container.layout().addWidget(straw_button)
        container.layout().setAlignment(straw_button, QtCore.Qt.AlignCenter)
        self._cb_straw = straw_button

    def _order(self):
        add_ice = self._cb_ice.isChecked() if self._cb_ice is not None else False
        add_straw = self._cb_straw.isChecked() if self._cb_straw is not None else False
        self.barbot_.start_mixing(
            MixingOptions(
                self._recipe,
                add_straw=add_straw,
                add_ice=add_ice
            )
        )
