from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import View
import BarBotMainWindow
import ViewListRecipes
import ViewRecipeNewOrEdit
import ViewSingleIngredient
import ViewStatistics

class ViewIdle(View.View):
    def __init__(self, _mainWindow: BarBotMainWindow):
        super().__init__(_mainWindow)
        self.pages = {
            "Liste" : lambda: self.mainWindow.showPage(ViewListRecipes.ViewListRecipes(self.mainWindow)),
            "Neu" : lambda: self.mainWindow.showPage(ViewRecipeNewOrEdit.ViewRecipeNewOrEdit(self.mainWindow)),
            "Nachschlag" : lambda: self.mainWindow.showPage(ViewSingleIngredient.ViewSingleIngredient(self.mainWindow)),
            "Statistik" : lambda: self.mainWindow.showPage(ViewStatistics.ViewStatistics(self.mainWindow))
        }
        self.setLayout(QtWidgets.QVBoxLayout())

        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header)

        #navigation
        self.navigation = QtWidgets.QWidget()
        self.layout().addWidget(self.navigation)

        self.navigation.setLayout(QtWidgets.QHBoxLayout())
        for text, method in self.pages.items():
            button = QtWidgets.QPushButton(text)
            self.navigation.layout().addWidget(button)
            button.clicked.connect(method)

        #content
        contentWrapper = QtWidgets.QWidget()
        self.layout().addWidget(contentWrapper, 1)

        contentWrapper.setLayout(QtWidgets.QGridLayout())

        self.scroller = QtWidgets.QScrollArea()
        self.scroller.setWidgetResizable(True)
        self.scroller.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        contentWrapper.layout().addWidget(self.scroller)

        self.setContent(ViewListRecipes.ViewListRecipes(self.mainWindow))

        #self.navigation.setStyleSheet("QWidget { background: blue; }")
    
    def setContent(self, view):
        if self.scroller.widget() != None:
            self.scroller.widget().setParent(None)
        self.scroller.setWidget(view)