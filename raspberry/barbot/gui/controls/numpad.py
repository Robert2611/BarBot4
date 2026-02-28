"""Numpad control for numeric input"""

from typing import List
from PyQt5 import QtWidgets, QtCore

from ..common import move_widget_to_bottom_of_screen, set_no_spacing


class Numpad(QtWidgets.QWidget):
    """More simple version of a keyboard with only numbers"""

    target: QtWidgets.QSpinBox = None
    current_value: int = 0

    def __init__(self, target: QtWidgets.QSpinBox, style=None, reference_widget: QtWidgets.QWidget = None):
        super().__init__()
        self.target = target
        self.current_value = 0

        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setProperty("class", "Keyboard")
        if style is not None:
            self.setStyleSheet(style)
        self.setCursor(QtCore.Qt.BlankCursor)

        self._add_value_label()
        self._add_keypad()

        move_widget_to_bottom_of_screen(self, reference_widget)

    def _add_value_label(self):
        self._value_label = QtWidgets.QLabel()
        self.layout().addWidget(self._value_label)
        # TODO: Make label white, maybe show current value in gray before first entry

    def _add_keypad(self):
        # numpad
        numpad = QtWidgets.QWidget()
        numpad.setLayout(QtWidgets.QGridLayout())
        self.layout().setAlignment(numpad, QtCore.Qt.AlignCenter)
        for y in range(0, 3):
            for x in range(0, 3):
                num = y * 3 + x + 1
                button = QtWidgets.QPushButton(str(num))
                button.clicked.connect(lambda _, value=num: self._button_clicked(value))
                numpad.layout().addWidget(button, y, x)
        # Cancel
        button = QtWidgets.QPushButton("Abbrechen")
        button.clicked.connect(self.close)
        numpad.layout().addWidget(button, 3, 0)
        # zero
        button = QtWidgets.QPushButton("0")
        button.clicked.connect(lambda _: self._button_clicked(0))
        numpad.layout().addWidget(button, 3, 1)
        # enter
        button = QtWidgets.QPushButton("Ok")
        button.clicked.connect(self._apply_value_to_target)
        numpad.layout().addWidget(button, 3, 2)
        self.layout().addWidget(numpad)

    def _apply_value_to_target(self):
        if self.target.minimum() <= self.current_value <= self.target.maximum():
            self.target.setValue(self.current_value)
        self.close()

    def _button_clicked(self, number):
        if self.target is None:
            return
        self.current_value *= 10
        self.current_value += number
        self._value_label.setText(str(self.current_value))

    def add_row(self, keys: List[str]) -> List[QtWidgets.QPushButton]:
        """Add a row defined by a list of characters to the layout
        :param keys: List of key characters to be added
        :retunrs: List of buttons that were added
        """
        res = []
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())

        set_no_spacing(row.layout())
        for letter in keys:
            button = QtWidgets.QPushButton(letter)
            button.clicked.connect(
                lambda checked, b=button: self._button_clicked(b.text())
            )
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res
