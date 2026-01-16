"""Touch keyboard control"""

from typing import List
from PyQt5 import QtWidgets, QtCore

from .common import move_widget_to_bottom_of_screen, set_no_spacing


class Keyboard(QtWidgets.QWidget):
    """A keyboard used for touch input"""

    _is_widgets_created = False
    _is_shift = False
    target: QtWidgets.QLineEdit = None

    def __init__(self, target: QtWidgets.QLineEdit, style=None):
        super().__init__()

        self.target = target

        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setProperty("class", "Keyboard")
        if style is not None:
            self.setStyleSheet(style)
        self.setCursor(QtCore.Qt.BlankCursor)

        self._number_keys = [
            ["1", "!"],
            ["2", '"'],
            ["3", "§"],
            ["4", "$"],
            ["5", "%"],
            ["6", "&"],
            ["7", "/"],
            ["8", "("],
            ["9", ")"],
            ["0", "ß"],
        ]
        self._letter_keys = [
            ["q", "w", "e", "r", "t", "z", "u", "i", "o", "p"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ö"],
            ["y", "x", "c", "v", "b", "n", "m", "ä", "ü"],
        ]
        self._add_keys()
        self._update_keys()
        move_widget_to_bottom_of_screen(self)

    def _add_keys(self):
        # number keys
        self._numbers_row = self._add_row([data[0] for data in self._number_keys])
        # letter keys
        self._letters_rows = []
        for keys in self._letter_keys:
            row = self._add_row(keys)
            self._letters_rows.append(row)
        # special keys
        self._add_special_keys_row()

    def _update_keys(self):
        # number keys
        for index, data in enumerate(self._number_keys):
            new_text = data[1] if self._is_shift else data[0]
            self._numbers_row[index].setText()
        # letter keys
        for keys in self._letter_keys:
            for index, letter in enumerate(keys):
                new_text = str.upper(letter) if self._is_shift else letter
                self._letters_rows[index].setText(new_text)

    def _add_special_keys_row(self):
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        set_no_spacing(row.layout())
        # shift
        button = QtWidgets.QPushButton("▲")
        button.clicked.connect(lambda: self._button_clicked("shift"))
        row.layout().addWidget(button)
        # space
        button = QtWidgets.QPushButton(" ")
        button.clicked.connect(lambda: self._button_clicked(" "))
        row.layout().addWidget(button)
        # delete
        button = QtWidgets.QPushButton("←")
        button.clicked.connect(lambda: self._button_clicked("delete"))
        row.layout().addWidget(button)
        self.layout().addWidget(row)

    def _button_clicked(self, content):
        """Handle a button click"""
        if self.target is None:
            return
        if content == "shift":
            self._is_shift = not self._is_shift
            self._update_keys()
        else:
            if content == "delete":
                self.target.setText(self.target.text()[:-1])
            else:
                self.target.setText(self.target.text() + content)
            # reset shift state
            if self._is_shift:
                self._is_shift = False
                self._update_keys()

    def _add_row(self, keys: List[str]) -> List[QtWidgets.QPushButton]:
        """Add a row defined by a list of characters to the layout
        :param keys: List of key characters to be added
        :returns: List of buttons that were added
        """
        res = []
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        set_no_spacing(row.layout())
        for letter in keys:
            button = QtWidgets.QPushButton(letter)
            button.clicked.connect(lambda _, b=button: self._button_clicked(b.text()))
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res
