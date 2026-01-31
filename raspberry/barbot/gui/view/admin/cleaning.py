from PyQt5 import QtWidgets, QtCore
from barbot.logic import RecipeCollection, BarBot
from .base import AdminView

class Cleaning(AdminView):
    """Clean the ports"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)

        self.amount = 50

        self._add_title_to_fixed_content("Reinigung")
        self._add_back_button_to_fixed_content()
        self._add_button_clean_left()
        self._add_button_clean_right()
        self._add_button_grid_for_single_ports()

        self._add_dummy_widget_to_content()

    def _add_button_clean_left(self):
        button = QtWidgets.QPushButton("Reinigen linke Hälfte")
        button.clicked.connect(self._clean_left)
        self._content.layout().addWidget(button)

    def _add_button_clean_right(self):
        button = QtWidgets.QPushButton("Reinigen rechte Hälfte")
        button.clicked.connect(self._clean_right)
        self._content.layout().addWidget(button)

    def _add_button_grid_for_single_ports(self):
        grid = QtWidgets.QWidget()
        grid.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(grid)
        for column in range(6):
            for row in range(2):
                port = row * 6 + column
                button = QtWidgets.QPushButton(str(port + 1))
                button.clicked.connect(
                    lambda _, pid=port: self._clean_single(pid))
                grid.layout().addWidget(button, row, column)

    def _clean_left(self):
        data = range(0, 6)
        self.barbot_.start_cleaning_cycle(data)

    def _clean_right(self):
        data = range(6, 12)
        self.barbot_.start_cleaning_cycle(data)

    def _clean_single(self, port):
        self.barbot_.start_cleaning(port)
