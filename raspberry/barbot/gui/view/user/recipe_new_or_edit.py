from PyQt5 import QtWidgets, QtCore
from barbot.logic.recipes import RecipeItem, Recipe, RecipeFilter
from barbot.logic.config import IngredientType
from barbot.logic import RecipeCollection, BarBot
from ...core import InputMethod
from .base import UserView

class RecipeNewOrEdit(UserView):
    """View for editing existing recpies and creating new ones"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection, recipe: Recipe = None):
        super().__init__(barbot, recipes)

        if recipe is None:
            self._init_new_recipe()
        else:
            self._init_recipe(recipe)

        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        title = "Neues Rezept" if self._is_new_cocktail else "Rezept bearbeiten"
        self._add_title_to_fixed_content(title)

        self._add_name_and_instruction()
        self._add_ingredients(10)
        self._add_filling_and_save_button()

        self._add_dummy_widget_to_content()

        self._update_view()

    def _init_new_recipe(self):
        self._recipe = Recipe()
        self._original_recipe = None
        self._is_new_cocktail = True

    def _init_recipe(self, recipe):
        self._original_recipe = recipe
        self._recipe = recipe.copy()
        self._is_new_cocktail = False

    def _add_name_and_instruction(self):
        # wrapper for name and instruction
        wrapper = QtWidgets.QWidget()
        wrapper.setLayout(QtWidgets.QFormLayout())
        wrapper.layout().setContentsMargins(0, 0, 0, 0)
        self._content.layout().addWidget(wrapper)

        # name
        self._name_widget = QtWidgets.QLineEdit(self._recipe.name)
        self._name_widget.mousePressEvent = self._open_keyboard_for_name_widget
        label = QtWidgets.QLabel("Name:")
        wrapper.layout().addRow(label, self._name_widget)

        # pre instruction
        self._pre_instruction_widget = QtWidgets.QLineEdit()
        self._pre_instruction_widget.setText(self._recipe.pre_instruction)
        self._pre_instruction_widget.mousePressEvent = self._open_keyboard_for_pre_instruction
        label = QtWidgets.QLabel("Vorher:")
        wrapper.layout().addRow(label, self._pre_instruction_widget)

        # post instruction
        widget  = QtWidgets.QLineEdit()
        widget.setText(self._recipe.post_instruction)
        widget.mousePressEvent = self._open_keyboard_for_post_instruction_widget
        self._post_instruction_widget = widget
        label = QtWidgets.QLabel("Nachher:")
        wrapper.layout().addRow(label, self._post_instruction_widget)

    def _open_keyboard_for_name_widget(self, _):
        self.open_input_method_trigger.emit(self._name_widget, InputMethod.KEYBOARD)

    def _open_keyboard_for_pre_instruction(self, _):
        self.open_input_method_trigger.emit(self._pre_instruction_widget, InputMethod.KEYBOARD)

    def _open_keyboard_for_post_instruction_widget(self, _):
        self.open_input_method_trigger.emit(self._post_instruction_widget, InputMethod.KEYBOARD)

    def _add_ingredients(self, max_count):
        self._content.layout().addWidget(QtWidgets.QLabel("Zutaten:"))
        ingredients_container = QtWidgets.QWidget()
        ingredients_container.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(ingredients_container, 1)
        # fill grid
        self._ingredient_widgets = []
        for i in range(max_count):
            # get selected checkbox entry or default
            if not self._is_new_cocktail and i < len(self._recipe.items):
                selected_amount = self._recipe.items[i].amount
                selected_ingredient = self._recipe.items[i].ingredient
            else:
                selected_amount = 0
                selected_ingredient = None
            # add ingredient name
            ingredient_widget = self.combobox_ingredients(selected_ingredient)
            ingredient_widget.currentIndexChanged.connect(self._update_view)
            ingredients_container.layout().addWidget(ingredient_widget, i, 0)
            # add ingredient amount
            amount_widget = self.combobox_amounts(selected_amount)
            amount_widget.currentIndexChanged.connect(self._update_view)
            if(i >= len(self._recipe.items) \
               or self._recipe.items[i].ingredient.type == IngredientType.STIRR):
                amount_widget.setVisible(False)
            ingredients_container.layout().addWidget(amount_widget, i, 1)

            # safe references for later
            self._ingredient_widgets.append([ingredient_widget, amount_widget])

    def _add_filling_and_save_button(self):
        # row for label and button
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        self._content.layout().addWidget(row)
        # label
        self._filling_label = QtWidgets.QLabel()
        row.layout().addWidget(self._filling_label)
        # save button
        button = QtWidgets.QPushButton("Speichern")
        button.clicked.connect(self._save)
        row.layout().addWidget(button)
        row.layout().setAlignment(button, QtCore.Qt.AlignCenter)

    def _get_cocktail_size(self):
        size = 0
        for ingredient_widget, amount_widget in self._ingredient_widgets:
            ingredient = ingredient_widget.currentData()
            amount = int(amount_widget.currentData())
            # ignore the stirring when accumulating size
            if ingredient is None:
                continue
            if ingredient.type == IngredientType.STIRR:
                continue
            if amount < 0:
                continue
            size = size + amount
        return size

    def _force_redraw(self, element):
        element.style().unpolish(element)
        element.style().polish(element)

    def _update_view(self):
        # cocktail size
        size = self._get_cocktail_size()
        max_size = self.barbot_.config.max_cocktail_size
        label = self._filling_label
        label.setText(f"{size} von {max_size} cl")
        has_error = size > max_size
        label.setProperty("class", "HasError" if has_error else "")
        self._force_redraw(label)
        # visibility
        for ingredient_widget, amount_widget in self._ingredient_widgets:
            ingredient = ingredient_widget.currentData()
            should_be_visible = ingredient is not None and ingredient.type != IngredientType.STIRR
            if amount_widget.isVisible() != should_be_visible:
                amount_widget.setVisible(should_be_visible)

    def _save(self):
        # check data
        self._recipe.name = self._name_widget.text()
        if self._recipe.name is None or self._recipe.name == "":
            self.show_message_trigger.emit("Bitte einen Namen eingeben")
            return
        if self._is_new_cocktail or self._recipe.name != self._original_recipe.name:
            # name changed or new recipe
            names = [
                recipe.name
                for recipe
                in self.recipes.get_filtered(self.barbot_.ports, self.barbot_.config, RecipeFilter(only_available=False))
            ]
            if self._recipe.name in names:
                self.show_message_trigger.emit("Ein Cocktail mit diesem Namen existiert bereits")
                return
        size = self._get_cocktail_size()
        if size > self.barbot_.config.max_cocktail_size:
            self.show_message_trigger.emit("Dein Cocktail ist zu groß.")
            return
        if size == 0:
            self.show_message_trigger.emit("Der Cocktail ist leer.")
            return
        self._recipe.pre_instruction = self._pre_instruction_widget.text()
        self._recipe.post_instruction = self._post_instruction_widget.text()
        # prepare data
        self._recipe.items = []
        for ingredient_widget, amount_widget in self._ingredient_widgets:
            ingredient = ingredient_widget.currentData()
            amount = int(amount_widget.currentData())
            if ingredient is None:
                continue
            if amount == 0 and ingredient.type != IngredientType.STIRR:
                continue

            if ingredient.type == IngredientType.STIRR:
                item = RecipeItem(ingredient, 2000)
            else:
                item = RecipeItem(ingredient, amount)
            self._recipe.items.append(item)
        if not self._is_new_cocktail and self._recipe.equal_to(self._original_recipe):
            self.show_message_trigger.emit("Rezept wurde nicht verändert")
            return
        # save copy or new recipe
        if not self._is_new_cocktail:
            self.recipes.remove(self._original_recipe)
        self.recipes.add(self._recipe)
        if self._is_new_cocktail:
            self._reload_with_message("Neues Rezept gespeichert")
        else:
            self._reload_with_message("Rezept gespeichert")

    def _reload_with_message(self, message):
        self.switch_view_trigger.emit(RecipeNewOrEdit(self.barbot_, self.recipes, self._recipe))
        self.show_message_trigger.emit(message)
