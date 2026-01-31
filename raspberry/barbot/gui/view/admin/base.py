from PyQt5 import QtWidgets
from barbot.logic import RecipeCollection, BarBot
from ..user import UserView

class AdminView(UserView):
    """Base class for the admin views"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)

        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

    def _add_back_button_to_fixed_content(self):
        from .overview import Overview
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click():
            return self.switch_view_trigger.emit(Overview(self.barbot_, self.recipes))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)
