import pytest
from unittest.mock import MagicMock, patch
from PyQt5 import QtWidgets, QtCore, QtGui
from barbot.gui.controls import set_no_spacing, Keyboard, Numpad, BarChart, GlasIndicator
from barbot.gui.controls.bar_chart import BarChartRow
from barbot.gui.controls.glas_indicator import GlasFilling

def test_set_no_spacing():
    layout = QtWidgets.QVBoxLayout()
    set_no_spacing(layout)
    assert layout.spacing() == 0

def test_keyboard_initialization(qtbot):
    target = QtWidgets.QLineEdit()
    target.setText("Initial")
    keyboard = Keyboard(target, "")
    qtbot.addWidget(keyboard)
    # Keyboard is not shown by default in its __init__ (it calls its own show() if needed)
    # But it creates buttons.
    buttons = keyboard.findChildren(QtWidgets.QPushButton)
    assert len(buttons) > 0

def test_numpad_initialization(qtbot):
    target = QtWidgets.QSpinBox()
    numpad = Numpad(target, "")
    qtbot.addWidget(numpad)
    buttons = numpad.findChildren(QtWidgets.QPushButton)
    assert len(buttons) > 0

def test_barchart_initialization(qtbot):
    rows = [BarChartRow("A", 10), BarChartRow("B", 20)]
    chart = BarChart(rows)
    qtbot.addWidget(chart)
    chart.repaint()

def test_glasindicator_initialization(qtbot):
    fillings = [GlasFilling("red", 0.5), GlasFilling("blue", 0.5)]
    indicator = GlasIndicator(fillings)
    qtbot.addWidget(indicator)
    indicator.repaint()
