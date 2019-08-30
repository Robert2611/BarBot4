from PyQt5 import QtWidgets, Qt, QtCore
import BarBotMainWindow
import View

class ViewStatistics(View.View):
    def __init__(self, _mainWindow: BarBotMainWindow):
        super().__init__(_mainWindow)
        containerLayout = QtWidgets.QVBoxLayout()
        self.setLayout(containerLayout)
        
        containerLayout.addWidget(QtWidgets.QLabel("Statistics"))