from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import BarBotGui

class MixingView(BarBotGui.View):
    mixingProgressChangedTrigger = QtCore.pyqtSignal()
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)

        self.setLayout(QtWidgets.QVBoxLayout())
        BarBotGui.setNoSpacingAndMargin(self.layout())

        label = QtWidgets.QLabel("Cocktail\n'%s'\nwird gemischt." % self.bot.data["recipe"]["name"])    
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setProperty("class", "Headline")
        self.layout().addWidget(label)

        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        #forward mixing progress changed
        self.mixingProgressChangedTrigger.connect(self.mixingProgressChanged)
        self.bot.OnMixingProgressChanged = lambda: self.mixingProgressChangedTrigger.emit()

        self.layout().addWidget(self.progressBar)

    def mixingProgressChanged(self):
        self.progressBar.setValue(int(self.bot.progress * 100))

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
        BarBotGui.setNoSpacingAndMargin(self.layout())

        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header)

        #navigation
        self.navigation = QtWidgets.QWidget()
        self.layout().addWidget(self.navigation)

        self.navigation.setLayout(QtWidgets.QHBoxLayout())
        for text, method in self.pages.items():
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(method)
            self.navigation.layout().addWidget(button, 1)

        icon = BarBotGui.getImage("admin.png")
        button = QtWidgets.QPushButton(icon, "")
        button.clicked.connect(lambda: self.mainWindow.close())
        self.navigation.layout().addWidget(button, 0)

        #content
        contentWrapper = QtWidgets.QWidget()
        self.layout().addWidget(contentWrapper, 1)
        contentWrapper.setLayout(QtWidgets.QGridLayout())
        BarBotGui.setNoSpacingAndMargin(contentWrapper.layout())

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

