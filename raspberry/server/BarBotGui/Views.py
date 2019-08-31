from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import BarBotGui

class MixingView(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())

        self.layout().addWidget(QtWidgets.QLabel("mixing!"))

class IdleView(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        self.pages = {
            "Liste" : lambda: self.setSubViewByName("ListRecipes"),
            "Neu" : lambda: self.setSubViewByName("RecipeNewOrEdit"),
            "Nachschlag" : lambda: self.setSubViewByName("SingleIngredient"),
            "Statistik" : lambda: self.setSubViewByName("Statistics")
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

        self.setSubViewByName("ListRecipes")
    
    def setSubViewByName(self, name):
        import BarBotGui.IdleSubViews
        class_ = getattr(BarBotGui.IdleSubViews, name)
        self.setContent(class_(self.mainWindow))

        #self.navigation.setStyleSheet("QWidget { background: blue; }")
    
    def setContent(self, view):
        if self.scroller.widget() is not None:
            self.scroller.widget().setParent(None)
        self.scroller.setWidget(view)

