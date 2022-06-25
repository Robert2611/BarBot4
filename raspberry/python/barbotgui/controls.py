from PyQt5 import QtWidgets, Qt, QtCore, QtGui
from barbotgui import set_no_spacing


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
            bar = QtWidgets.QWidget()
            bar.setProperty("class", "BarChartBar")
            bar_wrapper.layout().addWidget(bar, w)

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

    def __init__(self, list):
        super().__init__()
        self.list = list
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
        path.moveTo(Qt.QPoint(center - w_start / 2,  + bottom))
        # bottom right
        path.quadTo(
            Qt.QPoint(center,  bottom + self._roundness),
            Qt.QPoint(center + w_start / 2,  bottom)
        )
        # top right
        path.lineTo(Qt.QPoint(center + w_end / 2,  top))
        # top left
        path.quadTo(
            Qt.QPoint(center,  top + self._roundness),
            Qt.QPoint(center - w_end / 2,  top)
        )
        # back to bottom left
        path.lineTo(Qt.QPoint(center - w_start / 2,  bottom))
        painter.drawPath(path)

        ### upper path ###
        if draw_top:
            path = QtGui.QPainterPath()
            # top left
            path.moveTo(Qt.QPoint(center - w_end / 2,  top))
            # upper bow to the right
            path.quadTo(
                Qt.QPoint(center,  top - self._roundness),
                Qt.QPoint(center + w_end / 2,  top)
            )
            # lower bow to the left
            path.quadTo(
                Qt.QPoint(center,  top + self._roundness),
                Qt.QPoint(center - w_end / 2,  top)
            )
            painter.drawPath(path)

    def paintEvent(self, e):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        total = 0
        self.draw_glas(painter)
        for filling in self.list:
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
            Qt.QPoint((self._top_width-self._bottom_width)/2, self._top_pos + self._height))
        # bottom right
        path.quadTo(
            Qt.QPoint(self._top_width/2, self._top_pos +
                      self._height + self._roundness),
            Qt.QPoint((self._top_width+self._bottom_width) /
                      2, self._top_pos + self._height)
        )
        # top right
        path.lineTo(Qt.QPoint(self._top_width, self._top_pos + 0))
        # top left
        path.quadTo(
            Qt.QPoint(self._top_width/2, self._top_pos + self._roundness),
            Qt.QPoint(0,  self._top_pos)
        )
        # back to bottom left
        path.lineTo(
            Qt.QPoint((self._top_width-self._bottom_width)/2, self._top_pos + self._height))
        painter.drawPath(path)

        ### top of the glas ###
        path = QtGui.QPainterPath()
        # move to left
        path.moveTo(Qt.QPoint(0,  self._top_pos))
        # upper bow to the right
        path.quadTo(
            Qt.QPoint(self._top_width/2, self._top_pos - self._roundness),
            Qt.QPoint(self._top_width, self._top_pos)
        )
        # lower bow to the left
        path.quadTo(
            Qt.QPoint(self._top_width/2, self._top_pos + self._roundness),
            Qt.QPoint(0, self._top_pos)
        )
        painter.drawPath(path)
