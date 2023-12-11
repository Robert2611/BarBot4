from typing import List
from PyQt5 import QtWidgets, Qt, QtCore, QtGui

def set_no_spacing(layout):
    """Set the spacing to zero for a given QtLayout
    :param layout: The layout"""
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)

class BarChart(QtWidgets.QWidget):
    def __init__(self, data):
        super().__init__()
        self.setLayout(QtWidgets.QGridLayout())
        names = [item[0] for item in data]
        values = [item[1] for item in data]
        max_value = max(values)
        values_relative = [v/max_value for v in values]
        for row in range(len(data)):
            # name label
            label = QtWidgets.QLabel(names[row])
            self.layout().addWidget(label, row, 0)
            # bar
            bar_wrapper = QtWidgets.QWidget()
            bar_wrapper.setProperty("class", "BarChartWrapper")
            bar_wrapper.setLayout(QtWidgets.QHBoxLayout())
            set_no_spacing(bar_wrapper.layout())
            self.layout().addWidget(bar_wrapper, row, 1)

            # set width of bar as horizontal stretch
            w = int(values_relative[row] * 100)
            bar_widget = QtWidgets.QWidget()
            bar_widget.setProperty("class", "BarChartBar")
            bar_wrapper.layout().addWidget(bar_widget, w)

            dummy = QtWidgets.QWidget()
            bar_wrapper.layout().addWidget(dummy, 100 - w)

            # value label
            label = QtWidgets.QLabel(str(values[row]))
            self.layout().addWidget(label, row, 2)


class GlasFilling():
    color: str
    fraction: float

    def __init__(self, color, fraction):
        self.color = color
        self.fraction = fraction


class GlasIndicator(QtWidgets.QLabel):
    list = []
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

    def draw_filling(self, painter, start, end, draw_top=True):
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

    def paintEvent(self, e):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        total = 0
        self.draw_glas(painter)
        for filling in self._fillings:
            # transparent pen
            painter.setPen(QtGui.QColor("#FF999999"))
            painter.setBrush(QtGui.QColor(filling.color))
            self.draw_filling(painter, total, total + filling.fraction)
            total = total + filling.fraction
        painter.end()

    def draw_glas(self, painter):
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
    target: QtWidgets.QLineEdit = None

    def __init__(self, target: QtWidgets.QLineEdit, style=None):
        super().__init__()
        self.target = target
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.update_keys()
        self.setProperty("class", "Keyboard")
        if style is not None:
            self.setStyleSheet(style)
        self.setCursor(QtCore.Qt.BlankCursor)
        # move to bottom of the screen
        desktop = Qt.QApplication.desktop().availableGeometry()
        desired = Qt.QRect(Qt.QPoint(0, 0), self.sizeHint())
        desired.moveBottomRight(desktop.bottomRight())
        desired.setLeft(desktop.left())
        self.setGeometry(desired)

    def update_keys(self):
        """Update or, at first call, create the keyboard keys"""
            # first row
        keys = [
            ["1", "!"], ["2", "\""], ["3", "§"], ["4", "$"], ["5", "%"],
            ["6", "&"], ["7", "/"], ["8", "("], ["9", ")"], ["0", "ß"]
        ]
        if not self._is_widgets_created:
            self.first_row = self.add_row([data[0] for data in keys])
        for index, data in enumerate(keys):
            self.first_row[index].setText(
                data[1] if self._is_shift else data[0])

            # second row
        keys = ["q", "w", "e", "r", "t", "z", "u", "i", "o", "p"]
        if not self._is_widgets_created:
            self.second_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.second_row[index].setText(
                str.upper(letter) if self._is_shift else letter)

            # third row
        keys = ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ö"]
        if not self._is_widgets_created:
            self.third_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.third_row[index].setText(
                str.upper(letter) if self._is_shift else letter)

        # fourth row
        keys = ["y", "x", "c", "v", "b", "n", "m", "ä", "ü"]
        if not self._is_widgets_created:
            self.fourth_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.fourth_row[index].setText(
                str.upper(letter) if self._is_shift else letter)

        # last row
        if not self._is_widgets_created:
            row = QtWidgets.QWidget()
            row.setLayout(QtWidgets.QHBoxLayout())
            set_no_spacing(row.layout())
            # shift
            button = QtWidgets.QPushButton("▲")
            button.clicked.connect(lambda: self.button_clicked("shift"))
            row.layout().addWidget(button)
            # space
            button = QtWidgets.QPushButton(" ")
            button.clicked.connect(lambda: self.button_clicked(" "))
            row.layout().addWidget(button)
            # delete
            button = QtWidgets.QPushButton("←")
            button.clicked.connect(lambda: self.button_clicked("delete"))
            row.layout().addWidget(button)
            self.layout().addWidget(row)
        self._is_widgets_created = True

    def button_clicked(self, content):
        """Handle a button click"""
        if self.target is None:
            return
        if content == "shift":
            self._is_shift = not self._is_shift
            self.update_keys()
        else:
            if content == "delete":
                self.target.setText(self.target.text()[:-1])
            else:
                self.target.setText(self.target.text() + content)
            # reset shift state
            if self._is_shift:
                self._is_shift = False
                self.update_keys()

    def add_row(self, keys: list[str]) -> list[QtWidgets.QPushButton]:
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
                lambda checked, b=button: self.button_clicked(b.text()))
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res

class Numpad(QtWidgets.QWidget):
    """More simple version of a keyboard with only numbers"""
    target: QtWidgets.QSpinBox = None
    current_value: int = 0

    def __init__(self, target: QtWidgets.QSpinBox, style=None):
        super().__init__()
        self.target = target
        self.current_value = 0
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setProperty("class", "Keyboard")

        #value label
        self._value_label = QtWidgets.QLabel()
        self.layout().addWidget(self._value_label)
        #TODO: Make label white, maybe show current value in gray before first entry

        #keypad
        self.create_keypad()

        if style is not None:
            self.setStyleSheet(style)
        elf.setCursor(QtCore.Qt.BlankCursor)
        # move to bottom of the screen
        desktop = Qt.QApplication.desktop().availableGeometry()
        desired = Qt.QRect(Qt.QPoint(0, 0), self.sizeHint())
        desired.moveBottomRight(desktop.bottomRight())
        desired.setLeft(desktop.left())
        self.setGeometry(desired)

    def create_keypad(self):
        """Create the buttons for the keypad"""
        # numpad
        numpad = QtWidgets.QWidget()
        numpad.setLayout(QtWidgets.QGridLayout())
        self.layout().setAlignment(numpad, QtCore.Qt.AlignCenter)
        for y in range(0, 3):
            for x in range(0, 3):
                num = y * 3 + x + 1
                button = QtWidgets.QPushButton(str(num))
                button.clicked.connect(
                    lambda checked, value=num: self.button_clicked(value))
                numpad.layout().addWidget(button, y, x)
        # Cancel
        button = QtWidgets.QPushButton("Abbrechen")
        button.clicked.connect(lambda checked: self.close())
        numpad.layout().addWidget(button, 3, 0)
        # zero
        button = QtWidgets.QPushButton("0")
        button.clicked.connect(lambda checked: self.button_clicked(0))
        numpad.layout().addWidget(button, 3, 1)
        # enter
        button = QtWidgets.QPushButton("Ok")
        button.clicked.connect(lambda checked: self.apply())
        numpad.layout().addWidget(button, 3, 2)
        self.layout().addWidget(numpad)

    def apply(self):
        """Apply the new value to the target"""
        if self.target.minimum() <= self.current_value <= self.target.maximum():
            self.target.setValue(self.current_value)
        self.close()

    def button_clicked(self, number):
        """A number button was clicked, handle it"""
        if self.target is None:
            return
        self.current_value *= 10
        self.current_value += number
        self._value_label.setText(str(self.current_value))

    def add_row(self, keys:list[str]) -> list[QtWidgets.QPushButton]:
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
                lambda checked, b=button: self.button_clicked(b.text()))
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res