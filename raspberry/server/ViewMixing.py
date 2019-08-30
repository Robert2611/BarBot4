from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import View
import BarBotMainWindow

class ViewMixing(View.View):
    def __init__(self, _mainWindow: BarBotMainWindow):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())

        self.layout().addWidget(QtWidgets.QLabel("mixing!"))