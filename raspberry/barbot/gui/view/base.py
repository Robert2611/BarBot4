from PyQt5 import QtWidgets, QtCore
from barbot.logic import BarBot
from barbot.logic.recipes import RecipeCollection
from barbot.logic.config import Ingredient
from ..core import InputMethod, restart_barbot, run_command
from ..controls.list_selector import SelectorButton

INGREDIENT_MAX_AMOUNT_OPTION = 17

class View(QtWidgets.QWidget):
    """Content that can be shown in the center of the main window"""

    switch_view_trigger = QtCore.pyqtSignal(object)
    show_message_trigger = QtCore.pyqtSignal(str)
    open_input_method_trigger = QtCore.pyqtSignal(object, InputMethod)
    close_keyboard_trigger = QtCore.pyqtSignal()

    def __init__(self, barbot: BarBot, recipes: RecipeCollection, is_idle_view: bool = True):
        super().__init__()
        self._barbot = barbot
        self._recipes = recipes
        self._is_idle_view = is_idle_view

    @property
    def is_idle_view(self):
        """Get whether the view is an idle view"""
        return self._is_idle_view

    @property
    def barbot_(self):
        """The barbot"""
        return self._barbot

    @property
    def recipes(self):
        """Get the collection of recipes"""
        return self._recipes

    def combobox_amounts(self, selected_amount=None):
        """Create a selector for selecting the amount of a ingredient.
        :param selected_amount: The amount to preselect"""
        
        def get_items():
            items = [("-", -1)]
            for i in range(1, INGREDIENT_MAX_AMOUNT_OPTION):
                items.append((str(i), i))
            return items

        initial_text = str(selected_amount) if selected_amount is not None and selected_amount > 0 else "-"
        widget = SelectorButton(initial_text, get_items, self.styles if hasattr(self, "styles") else None, selected_amount)
        return widget

    def combobox_ingredients(
        self,
        selected_ingredient: Ingredient = None,
        only_available=False,
        only_normal=False,
        only_weighed=False,
    ):
        """Create a selector with options for ingredients selected by the filter parameters """

        def get_items():
            entries = self.barbot_.config.get_ingredient_list(
                self.barbot_.ports, only_available, only_normal, only_weighed
            )
            items = [("-", None)]
            for item in entries:
                items.append((str(item.name), item))
            return items

        initial_text = str(selected_ingredient.name) if selected_ingredient else "-"
        widget = SelectorButton(initial_text, get_items, self.styles if hasattr(self, "styles") else None, selected_ingredient)
        return widget

    @staticmethod
    def set_system_view(container: QtWidgets.QWidget):
        """Get the systems view widget."""
        if container.layout() is None:
            container.setLayout(QtWidgets.QVBoxLayout())

        label = QtWidgets.QLabel("Software")
        container.layout().addWidget(label)
        # reopen software
        button = QtWidgets.QPushButton("Neu Starten")
        button.clicked.connect(restart_barbot)
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
