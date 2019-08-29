from PyQt5 import QtWidgets, Qt, QtCore

class ViewSingleIngredient(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        containerLayout = QtWidgets.QVBoxLayout()
        self.setLayout(containerLayout)
        
        containerLayout.addWidget(QtWidgets.QLabel("Single ingredient"))