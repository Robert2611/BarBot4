from PyQt5 import QtWidgets, QtCore
from barbot.logic.recipes import Recipe, RecipeFilter
from barbot.logic import RecipeCollection, BarBot
from .base import AdminView
from ...common import qt_icon_from_file_name

class RemoveRecipe(AdminView):
    """Remove recipes"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)

        self._list = None
        self._recipe:Recipe = None

        self._add_title_to_fixed_content("Rezepte löschen")
        self._add_back_button_to_fixed_content()
        self._add_confirmation_dialog()
        self._add_recipe_list()

    def _add_confirmation_dialog(self):
        self._confirmation_dialog = QtWidgets.QWidget()
        self._confirmation_dialog.setLayout(QtWidgets.QGridLayout())
        self._confirmation_dialog.setVisible(False)
        self._content.layout().addWidget(self._confirmation_dialog, 1)

        center_box = QtWidgets.QFrame()
        center_box.setLayout(QtWidgets.QVBoxLayout())
        self._confirmation_dialog.layout().addWidget(
            center_box, 0, 0, QtCore.Qt.AlignCenter)

        label = QtWidgets.QLabel("Wirklich löschen?")
        center_box.layout().addWidget(label)

        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        center_box.layout().addWidget(row)

        ok_button = QtWidgets.QPushButton("Löschen")
        ok_button.clicked.connect(self._remove)
        row.layout().addWidget(ok_button)

        cancel_button = QtWidgets.QPushButton("Abbrechen")
        cancel_button.clicked.connect(self._hide_confirmation)
        row.layout().addWidget(cancel_button)

    def _add_recipe_list(self):
        if self._list is not None:
            self._list.setParent(None)

        self._list = QtWidgets.QWidget()
        self._list.setLayout(QtWidgets.QVBoxLayout())
        self._content.layout().addWidget(self._list, 1)
        recipes = self.recipes.get_filtered(self.barbot_.ports, self.barbot_.config, RecipeFilter(only_available=False))
        for recipe in recipes:
            # box to hold the recipe
            recipe_box = QtWidgets.QWidget()
            recipe_box.setLayout(QtWidgets.QHBoxLayout())
            self._list.layout().addWidget(recipe_box)

            # title
            recipe_title = QtWidgets.QLabel(recipe.name)
            recipe_title.setProperty("class", "RecipeTitle")
            recipe_box.layout().addWidget(recipe_title, 1)

            # remove button
            icon = qt_icon_from_file_name("remove.png")
            remove_button = QtWidgets.QPushButton(icon, "")
            remove_button.clicked.connect(
                lambda _, r=recipe: self._show_confirmation(r))
            recipe_box.layout().addWidget(remove_button, 0)

    def _show_confirmation(self, recipe: Recipe):
        self._recipe = recipe
        self._list.setVisible(False)
        self._confirmation_dialog.setVisible(True)

    def _hide_confirmation(self):
        self._confirmation_dialog.setVisible(False)
        self._list.setVisible(True)

    def _remove(self):
        self.recipes.remove(self._recipe)
        self._hide_confirmation()
        self._add_recipe_list()
