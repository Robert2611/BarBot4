from PyQt5 import QtWidgets, Qt, QtCore

class ViewStatistics(QtWidgets.QWidget):
    def __init__(self, data):
        super().__init__()
        containerLayout = QtWidgets.QVBoxLayout()
        self.setLayout(containerLayout)
        
        containerLayout.addWidget(QtWidgets.QLabel("Statistics"))