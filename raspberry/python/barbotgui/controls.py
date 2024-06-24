"""Controls used by the barbot gui"""
from typing import List, Optional
from dataclasses import dataclass
from PyQt5 import QtWidgets, QtCore, QtGui

def move_widget_to_bottom_of_screen(window: QtWidgets.QWidget):
    """Move a widget to the bottom of the screen"""
    desktop = QtWidgets.QApplication.desktop().availableGeometry()
    desired = QtCore.QRect(QtCore.QPoint(0, 0), window.sizeHint())
    desired.moveBottomRight(desktop.bottomRight())
    desired.setLeft(desktop.left())
    window.setGeometry(desired)

def set_no_spacing(layout):
    """Set the spacing to zero for a given QtLayout
    :param layout: The layout"""
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)

@dataclass
class BarChartRow():
    """Single bar in a bar chart"""
    name: str
    value: float

class BarChart(QtWidgets.QWidget):
    """Bar chart with labels"""
    def __init__(self, rows: List[BarChartRow]):
        super().__init__()
        self._grid_layout = QtWidgets.QGridLayout()
        self.setLayout(self._grid_layout)

        self._names = [row.name for row in rows]
        self._values = [row.value for row in rows]
        self._row_count = len(rows)

        max_value = max(self._values)
        self._values_relative = [v/max_value for v in self._values]

        for row_index in range(self._row_count):
            self._add_name_label(row_index)
            self._add_bar(row_index)
            self._add_value_label(row_index)

    def _add_bar(self, row_index):
        bar_wrapper = QtWidgets.QWidget()
        bar_wrapper.setProperty("class", "BarChartWrapper")
        wrapper_layout = QtWidgets.QHBoxLayout()
        bar_wrapper.setLayout(wrapper_layout)
        set_no_spacing(wrapper_layout)
        self._grid_layout.addWidget(bar_wrapper, row_index, 1)

        # set width of bar as horizontal stretch
        w = int(self._values_relative[row_index] * 100)
        bar_widget = QtWidgets.QWidget()
        bar_widget.setProperty("class", "BarChartBar")
        wrapper_layout.addWidget(bar_widget, w)

        dummy = QtWidgets.QWidget()
        wrapper_layout.addWidget(dummy, 100 - w)

    def _add_name_label(self, row_index):
        label = QtWidgets.QLabel(self._names[row_index])
        self._grid_layout.addWidget(label, row_index, 0)

    def _add_value_label(self, row_index):
        label = QtWidgets.QLabel(str(self._values[row_index]))
        self._grid_layout.addWidget(label, row_index, 2)

@dataclass
class GlasFilling():
    """Single part of a a glass filling"""
    color: str
    fraction: float

class GlasIndicator(QtWidgets.QLabel):
    """Visual representation of the ingredients inside a glas"""
    _top_width = 80
    _bottom_width = 70
    _height = 120
    _h_offset = 4
    _w_offset = 4
    _top_pos = 10
    _roundness = 10

    def __init__(self, fillings: List[GlasFilling]):
        super().__init__()
        self._fillings = fillings
        self.setMinimumSize(QtCore.QSize(
            self._top_width, self._height + 2 * self._roundness))

    def _draw_filling(self, painter, start, end, draw_top=True):
        # create some support variables so the points are easier to read
        w_b = self._bottom_width
        w_t = self._top_width
        w_start = w_b + start * (w_t - w_b) - 2 * self._w_offset
        w_end = w_b + end * (w_t - w_b) - 2 * self._w_offset
        center = w_t / 2
        h = self._height - 2 * self._h_offset
        bottom = self._top_pos + self._h_offset + h * (1-start)
        top = self._top_pos + self._h_offset + h * (1-end)

        ### front path ##
        path = QtGui.QPainterPath()
        # bottom left
        path.moveTo(QtCore.QPointF(center - w_start / 2,  + bottom))
        # bottom right
        path.quadTo(
            QtCore.QPointF(center,  bottom + self._roundness),
            QtCore.QPointF(center + w_start / 2,  bottom)
        )
        # top right
        path.lineTo(QtCore.QPointF(center + w_end / 2,  top))
        # top left
        path.quadTo(
            QtCore.QPointF(center,  top + self._roundness),
            QtCore.QPointF(center - w_end / 2,  top)
        )
        # back to bottom left
        path.lineTo(QtCore.QPointF(center - w_start / 2,  bottom))
        painter.drawPath(path)

        ### upper path ###
        if draw_top:
            path = QtGui.QPainterPath()
            # top left
            path.moveTo(QtCore.QPointF(center - w_end / 2,  top))
            # upper bow to the right
            path.quadTo(
                QtCore.QPointF(center,  top - self._roundness),
                QtCore.QPointF(center + w_end / 2,  top)
            )
            # lower bow to the left
            path.quadTo(
                QtCore.QPointF(center,  top + self._roundness),
                QtCore.QPointF(center - w_end / 2,  top)
            )
            painter.drawPath(path)

    # pylint: disable=locally-disabled, invalid-name, missing-function-docstring
    def paintEvent(self, _):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        self._draw_glas(painter)

        sum_of_fractions = 0
        for filling in self._fillings:
            # transparent pen
            painter.setPen(QtGui.QColor("#FF999999"))
            painter.setBrush(QtGui.QColor(filling.color))
            self._draw_filling(painter, sum_of_fractions, sum_of_fractions + filling.fraction)
            sum_of_fractions += filling.fraction
        painter.end()

    def _draw_glas(self, painter):
        painter.setPen(QtGui.QColor("#FF999999"))
        painter.setBrush(QtGui.QColor("#55FFFFFF"))

        path = QtGui.QPainterPath()
        # bottom left
        path.moveTo(
            QtCore.QPointF((self._top_width-self._bottom_width)/2, self._top_pos + self._height))
        # bottom right
        path.quadTo(
            QtCore.QPointF(self._top_width/2, self._top_pos +
                      self._height + self._roundness),
            QtCore.QPointF((self._top_width+self._bottom_width) /
                      2, self._top_pos + self._height)
        )
        # top right
        path.lineTo(QtCore.QPointF(self._top_width, self._top_pos + 0))
        # top left
        path.quadTo(
            QtCore.QPointF(self._top_width/2, self._top_pos + self._roundness),
            QtCore.QPointF(0,  self._top_pos)
        )
        # back to bottom left
        path.lineTo(
            QtCore.QPointF((self._top_width-self._bottom_width)/2, self._top_pos + self._height))
        painter.drawPath(path)

        ### top of the glas ###
        path = QtGui.QPainterPath()
        # move to left
        path.moveTo(QtCore.QPointF(0,  self._top_pos))
        # upper bow to the right
        path.quadTo(
            QtCore.QPointF(self._top_width/2, self._top_pos - self._roundness),
            QtCore.QPointF(self._top_width, self._top_pos)
        )
        # lower bow to the left
        path.quadTo(
            QtCore.QPointF(self._top_width/2, self._top_pos + self._roundness),
            QtCore.QPointF(0, self._top_pos)
        )
        painter.drawPath(path)

class Keyboard(QtWidgets.QWidget):
    """A keyboard used for touch input"""
    _is_widgets_created = False
    _is_shift = False
    target: Optional[QtWidgets.QLineEdit] = None

    def __init__(self, target: QtWidgets.QLineEdit, style=None):
        super().__init__()

        self.target = target

        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setProperty("class", "Keyboard")
        if style is not None:
            self.setStyleSheet(style)
        self.setCursor(QtCore.Qt.CursorShape.BlankCursor)

        self._number_keys = [
            ["1", "!"], ["2", "\""], ["3", "§"], ["4", "$"], ["5", "%"],
            ["6", "&"], ["7", "/"], ["8", "("], ["9", ")"], ["0", "ß"]
        ]
        self._letter_keys = [
            ["q", "w", "e", "r", "t", "z", "u", "i", "o", "p"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ö"],
            ["y", "x", "c", "v", "b", "n", "m", "ä", "ü"]
        ]
        self._add_keys()
        self._update_keys()
        move_widget_to_bottom_of_screen(self)

    def _add_keys(self):
        #number keys
        self._numbers_row = self._add_row([data[0] for data in self._number_keys])
        #letter keys
        self._letters_rows = []
        for keys in self._letter_keys:
            row = self._add_row(keys)
            self._letters_rows.append(row)
        #special keys
        self._add_special_keys_row()

    def _update_keys(self):
        #number keys
        for index, data in enumerate(self._number_keys):
            new_text = data[1] if self._is_shift else data[0]
            self._numbers_row[index].setText(new_text)
        #letter keys
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
            button.clicked.connect(
                lambda _, b=button: self._button_clicked(b.text()))
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res

class Numpad(QtWidgets.QWidget):
    """More simple version of a keyboard with only numbers"""
    def __init__(self, target: QtWidgets.QSpinBox, style=None):
        super().__init__()
        self.target = target
        self.current_value = 0

        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setProperty("class", "Keyboard")
        if style is not None:
            self.setStyleSheet(style)
        self.setCursor(QtCore.Qt.CursorShape.BlankCursor)

        self._add_value_label()
        self._add_keypad()

        move_widget_to_bottom_of_screen(self)

    def _add_value_label(self):
        self._value_label = QtWidgets.QLabel()
        self.layout().addWidget(self._value_label)
        #TODO: Make label white, maybe show current value in gray before first entry

    def _add_keypad(self):
        # numpad
        numpad = QtWidgets.QWidget()
        numpad_layout = QtWidgets.QGridLayout()
        numpad.setLayout(numpad_layout)
        self.layout().setAlignment(numpad, QtCore.Qt.AlignmentFlag.AlignCenter)
        for y in range(0, 3):
            for x in range(0, 3):
                num = y * 3 + x + 1
                button = QtWidgets.QPushButton(str(num))
                button.clicked.connect(
                    lambda _, value=num: self._button_clicked(value))
                numpad_layout.addWidget(button, y, x)
        # Cancel
        button = QtWidgets.QPushButton("Abbrechen")
        button.clicked.connect(self.close)
        numpad_layout.addWidget(button, 3, 0)
        # zero
        button = QtWidgets.QPushButton("0")
        button.clicked.connect(lambda _: self._button_clicked(0))
        numpad_layout.addWidget(button, 3, 1)
        # enter
        button = QtWidgets.QPushButton("Ok")
        button.clicked.connect(self._apply_value_to_target)
        numpad_layout.addWidget(button, 3, 2)
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
                lambda checked, b=button: self._button_clicked(b.text()))
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res
