from PyQt5 import QtWidgets, QtCore
from barbot.logic.communication import BoardType
from barbot.logic import version as barbot_version
from barbot.logic import RecipeCollection, BarBot
from .base import AdminView
from ...core import qt_icon_from_file_name

from .system import System
from .ports import Ports
from .settings import Settings
from .cleaning import Cleaning
from .remove_recipe import RemoveRecipe
from .balance_calibration import BalanceCalibration

class Overview(AdminView):
    """Overview over the admin views"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)

        self.admin_navigation_items = [
            ["System", System],
            ["Positionen", Ports],
            ["Einstellungen", Settings],
            ["Reinigung", Cleaning],
            ["Cocktails Löschen", RemoveRecipe],
            ["Waage kalibrieren", BalanceCalibration]
        ]

        self._add_title_to_fixed_content("Übersicht")
        self._add_admin_navigation_by_items()
        self._add_board_list()
        self._add_version_label()

        self._add_dummy_widget_to_content()

        self._start_updating_weight()

    def _start_updating_weight(self):
        # Timer for updating the current weight display
        self._update_timer = QtCore.QTimer(self)
        self._update_timer.timeout.connect(
            lambda: self.barbot_.get_weight(self._set_weight_label)
        )
        self._update_timer.start(500)

        self.barbot_.get_weight(self._set_weight_label)

    def _add_admin_navigation_by_items(self):
        self.admin_navigation = QtWidgets.QWidget()
        self.admin_navigation.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(self.admin_navigation)

        columns = 1
        column = 0
        row = 0
        for text, _class in self.admin_navigation_items:
            button = QtWidgets.QPushButton(text)
            def btn_click(_, c=_class):
                return self.switch_view_trigger.emit(c(self.barbot_, self.recipes))
            button.clicked.connect(btn_click)
            self.admin_navigation.layout().addWidget(button, row, column)
            column += 1
            if column >= columns:
                column = 0
                row += 1

    def _add_board_list(self):
        self.boards = [
            [BoardType.BALANCE, "balance.png"],
            [BoardType.STRAW, "straw.png"],
            [BoardType.CRUSHER, "ice.png"],
            [BoardType.MIXER, "stir.png"],
            [BoardType.SUGAR, "sugar.png"]
        ]
        self._board_widgets = {}
        row = 1
        # wrapper
        wrapper = QtWidgets.QWidget()
        wrapper.setProperty("class", "Boards")
        wrapper.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(wrapper)
        for board, icon in self.boards:
            connected = board in self.barbot_.connected_boards
            # board icon
            icon = qt_icon_from_file_name(icon)
            button_board_icon = QtWidgets.QPushButton(icon, "")
            button_board_icon.setProperty("class", "IconPresenter")
            button_board_icon.setEnabled(connected)
            wrapper.layout().addWidget(button_board_icon, row, 0, 1, 1)
            # connected / disconnected icon
            icon = qt_icon_from_file_name("plug-on.png" if connected else "plug-off.png")
            button = QtWidgets.QPushButton(icon, "")
            button.setProperty("class", "IconPresenter")
            button.setEnabled(connected)
            wrapper.layout().addWidget(button, row, 1, 1, 1)

            self._board_widgets[board] = [button_board_icon, button]

            if board == BoardType.BALANCE:
                # weight label
                self._weight_label = QtWidgets.QLabel()
                wrapper.layout().addWidget(self._weight_label, row, 2, 1, 3)
            row += 1
        # dummy
        wrapper.layout().addWidget(QtWidgets.QWidget(), 0, 0)
        wrapper.layout().addWidget(QtWidgets.QWidget(), row, 0)

    def _add_version_label(self):
        version_label = QtWidgets.QLabel(f"Version: {barbot_version}")
        self._content.layout().addWidget(version_label)

    def _set_weight_label(self, weight):
        weight = weight if weight is not None else "-"
        text = f"Gewicht: {weight} g"
        try:
            # this would cause a problem if the label was allready deleted
            self._weight_label.setText(text)
        except Exception:
            pass
