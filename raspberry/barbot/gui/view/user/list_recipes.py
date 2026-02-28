from PyQt5 import QtWidgets, QtCore
from barbot.logic import RecipeCollection, BarBot
from barbot.logic.recipes import RecipeItem, Recipe
from barbot.logic.config import IngredientType
from ...common import qt_icon_from_file_name, set_no_spacing
from ...controls import GlasFilling, GlasIndicator
from .base import UserView

class ListRecipes(UserView):
    """List of known recipes"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        self._add_filter_alcoholic()
        self._add_filter_available()
        self._add_recipe_list_container()
        self._add_dummy_widget_to_content()

        self._update_recipe_list()

    def _add_filter_alcoholic(self):
        self._cb_alcoholic = QtWidgets.QCheckBox("Alkoholisch")
        self._fixed_content.layout().addWidget(self._cb_alcoholic)
        self._cb_alcoholic.setChecked(self.recipes.filter.show_alcoholic)
        self._cb_alcoholic.toggled.connect(self._update_recipe_list)

    def _add_filter_available(self):
        self._cb_available = QtWidgets.QCheckBox("Nur verfügbare")
        self._fixed_content.layout().addWidget(self._cb_available)
        self._cb_available.setChecked(self.recipes.filter.only_available)
        self._cb_available.toggled.connect(self._update_recipe_list)

    def _add_recipe_list_container(self):
        self._recipe_list_container = QtWidgets.QWidget()
        self._recipe_list_container.setLayout(QtWidgets.QVBoxLayout())
        self._content.layout().addWidget(self._recipe_list_container)
        set_no_spacing(self._recipe_list_container.layout())

    def _update_recipe_list(self):
        recipe_filter = self.recipes.filter
        recipe_filter.only_available = self._cb_available.isChecked()
        recipe_filter.show_alcoholic = self._cb_alcoholic.isChecked()
        recipe_filter.show_non_acloholic = not self._cb_alcoholic.isChecked()
        recipes = self.recipes.get_filtered( \
            self.barbot_.ports, self.barbot_.config)

        self._clear_recipe_list_container()
        for recipe in recipes:
            self._add_recipe_to_list_container(recipe)

        # dummy element
        self._recipe_list_container.layout().addWidget(QtWidgets.QWidget(), 1)

    def _clear_recipe_list_container(self):
        while self._recipe_list_container.layout().count():
            item = self._recipe_list_container.layout().takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _add_recipe_to_list_container(self, recipe):
        # box to hold the recipe
        recipe_widget = QtWidgets.QWidget()
        recipe_widget.setLayout(QtWidgets.QHBoxLayout())
        self._recipe_list_container.layout().addWidget(recipe_widget)

        self._add_left_column_to_recipe_widget(recipe_widget, recipe)
        self._add_right_column_to_recipe_widget(recipe_widget, recipe)

    def _add_left_column_to_recipe_widget(self, recipe_widget, recipe):
        # container
        left_column = QtWidgets.QWidget()
        left_column.setLayout(QtWidgets.QVBoxLayout())
        recipe_widget.layout().addWidget(left_column)

        # title with buttons
        recipe_title_container = QtWidgets.QWidget()
        recipe_title_container.setLayout(QtWidgets.QHBoxLayout())
        left_column.layout().addWidget(recipe_title_container)

        # edit button
        if not recipe.is_fixed:
            from .recipe_new_or_edit import RecipeNewOrEdit
            icon = qt_icon_from_file_name("edit.png")
            edit_button = QtWidgets.QPushButton(icon, "")
            edit_button.setProperty("class", "BtnEdit")
            edit_button.clicked.connect(
                lambda checked, r=recipe: self._open_edit(r))
            recipe_title_container.layout().addWidget(edit_button, 0)

        # title
        recipe_title = QtWidgets.QLabel(recipe.name)
        recipe_title.setProperty("class", "RecipeTitle")
        recipe_title_container.layout().addWidget(recipe_title, 1)

        # items container for holding the recipe items
        recipe_items_container = QtWidgets.QWidget()
        recipe_items_container.setLayout(QtWidgets.QVBoxLayout())
        left_column.layout().addWidget(recipe_items_container, 1)

        # add items
        item: RecipeItem
        for item in recipe.items:
            label = QtWidgets.QLabel()
            if item.ingredient.type == IngredientType.STIRR:
                label.setText(f"-{item.ingredient.name}-")
            elif item.ingredient.type == IngredientType.SUGAR:
                label.setText(f"{item.amount:.0f} TL {item.ingredient.name}")
            else:
                label.setText(f"{item.amount:.0f} cl {item.ingredient.name}")
            recipe_items_container.layout().addWidget(label)

    def _add_right_column_to_recipe_widget(self, recipe_widget, recipe):
        # container
        right_column = QtWidgets.QWidget()
        right_column.setLayout(QtWidgets.QVBoxLayout())
        recipe_widget.layout().addWidget(right_column)

        fillings = []
        for item in recipe.items:
            if item.ingredient.type != IngredientType.STIRR:
                relative = item.amount / self.barbot_.config.max_cocktail_size
                filling = GlasFilling(item.ingredient.color, relative)
                fillings.append(filling)
        indicator = GlasIndicator(fillings)
        right_column.layout().addWidget(indicator)
        right_column.layout().setAlignment(indicator, QtCore.Qt.AlignRight)

        # instruction
        if recipe.post_instruction:
            instruction = QtWidgets.QLabel(recipe.post_instruction)
            instruction.setWordWrap(True)
            right_column.layout().addWidget(instruction)

        # order button
        if recipe.is_available(self.barbot_.ports, self.barbot_.config):
            icon = qt_icon_from_file_name("order.png")
            order_button = QtWidgets.QPushButton(icon, "")
            order_button.setProperty("class", "BtnOrder")
            order_button.clicked.connect(
                lambda _, r=recipe: self._order(r))
            right_column.layout().addWidget(order_button, 0)
            right_column.layout().setAlignment(order_button, QtCore.Qt.AlignRight)

    def _open_edit(self, recipe: Recipe):
        from .recipe_new_or_edit import RecipeNewOrEdit
        self.switch_view_trigger.emit(RecipeNewOrEdit(self.barbot_, self.recipes, recipe))

    def _order(self, recipe):
        if self.barbot_.is_busy:
            self.show_message_trigger.emit(
                "Bitte warten bis die laufende\nAktion abgeschlossen ist.")
            return
        if recipe is None:
            self.show_message_trigger.emit("Rezept nicht gefunden")
            return
        from .order_recipe import OrderRecipe
        self.switch_view_trigger.emit(OrderRecipe(self.barbot_, self.recipes, recipe))
