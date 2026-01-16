"""Bar chart control for displaying data"""

from typing import List
from dataclasses import dataclass
from PyQt5 import QtWidgets

from .common import set_no_spacing


@dataclass
class BarChartRow:
    """Single bar in a bar chart"""

    name: str
    value: float


class BarChart(QtWidgets.QWidget):
    """Bar chart with labels"""

    def __init__(self, rows: List[BarChartRow]):
        super().__init__()
        self.setLayout(QtWidgets.QGridLayout())

        self._names = [row.name for row in rows]
        self._values = [row.value for row in rows]
        self._row_count = len(rows)

        max_value = max(self._values)
        self._values_relative = [v / max_value for v in self._values]

        for row_index in range(self._row_count):
            self._add_name_label(row_index)
            self._add_bar(row_index)
            self._add_value_label(row_index)

    def _add_bar(self, row_index):
        bar_wrapper = QtWidgets.QWidget()
        bar_wrapper.setProperty("class", "BarChartWrapper")
        bar_wrapper.setLayout(QtWidgets.QHBoxLayout())
        set_no_spacing(bar_wrapper.layout())
        self.layout().addWidget(bar_wrapper, row_index, 1)

        # set width of bar as horizontal stretch
        w = int(self._values_relative[row_index] * 100)
        bar_widget = QtWidgets.QWidget()
        bar_widget.setProperty("class", "BarChartBar")
        bar_wrapper.layout().addWidget(bar_widget, w)

        dummy = QtWidgets.QWidget()
        bar_wrapper.layout().addWidget(dummy, 100 - w)

    def _add_name_label(self, row_index):
        label = QtWidgets.QLabel(self._names[row_index])
        self.layout().addWidget(label, row_index, 0)

    def _add_value_label(self, row_index):
        label = QtWidgets.QLabel(str(self._values[row_index]))
        self.layout().addWidget(label, row_index, 2)
