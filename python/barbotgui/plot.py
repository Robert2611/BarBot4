from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import barbotgui

class BarChart(QtWidgets.QWidget):
    def __init__(self, data):
        super().__init__()
        self.setLayout(QtWidgets.QGridLayout())
        names = [item[0] for item in data]
        values = [item[1] for item in data]
        max_value = max(values)
        values_relative = [v/max_value for v in values]
        for row in range(len(data)):
            #name label
            label = QtWidgets.QLabel(names[row])
            self.layout().addWidget(label, row, 0)
            #bar
            bar_wrapper = QtWidgets.QWidget()
            bar_wrapper.setProperty("class", "BarChartWrapper")
            bar_wrapper.setLayout(QtWidgets.QHBoxLayout())
            barbotgui.set_no_spacing(bar_wrapper.layout())
            self.layout().addWidget(bar_wrapper, row, 1)

            #set width of bar as horizontal stretch
            w  = int(values_relative[row] * 100)
            bar = QtWidgets.QWidget()
            bar.setProperty("class", "BarChartBar")
            bar_wrapper.layout().addWidget(bar, w)

            dummy = QtWidgets.QWidget()
            bar_wrapper.layout().addWidget(dummy, 100 - w)

            #value label
            label = QtWidgets.QLabel(str(values[row]))
            self.layout().addWidget(label, row, 2)
