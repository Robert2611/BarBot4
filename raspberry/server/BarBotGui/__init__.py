from PyQt5 import QtWidgets, Qt, QtCore, QtGui
from Database import Database
import Statemachine
import os
import BarBotGui

class MainWindow(QtWidgets.QWidget):
    db:Database
    bot:Statemachine.StateMachine
    botStateChangedTrigger = QtCore.pyqtSignal()
    mixingProgressChangedTrigger = QtCore.pyqtSignal()
    currentView = None
    def __init__(self, _db:Database, _bot:Statemachine.StateMachine):
        super().__init__()
        import BarBotGui.Views
        self.db = _db
        self.bot = _bot
        #forward status changed
        self.botStateChangedTrigger.connect(self.botStateChanged)
        self.bot.OnStateChanged = lambda: self.botStateChangedTrigger.emit()
        #forward mixing progress changed
        self.mixingProgressChangedTrigger.connect(self.mixingProgressChanged)
        self.bot.OnMixingProgressChanged = lambda: self.mixingProgressChangedTrigger.emit()
        #remove borders and title bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(480, 800)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header, 0)
        self.wholeContent = QtWidgets.QWidget()
        self.wholeContent.setLayout(QtWidgets.QGridLayout())
        self.layout().addWidget(self.wholeContent, 1)
        self.fillHeader()
        self.setView(BarBotGui.Views.IdleView(self))
        self.show()

    def setView(self, view):
        #remove existing item from window
        if self.currentView is not None:
            self.currentView.deleteLater()
        self.currentView = view
        self.wholeContent.layout().addWidget(self.currentView)

    def botStateChanged(self):
        import BarBotGui.Views
        if self.bot.state == Statemachine.State.MIXING:
            self.setView(BarBotGui.Views.MixingView(self))
        print("Status changed")
    
    def mixingProgressChanged(self):
        print("mixing progress changed")

    def showPage(self, view):
        import BarBotGui.Views
        if not isinstance(self.currentView, BarBotGui.Views.IdleView):
            return
        self.currentView.setContent(view)

    def clear(self, item):
        if isinstance(item, QtWidgets.QLayout):
            layout = item
        elif isinstance(item, QtWidgets.QWidget):
            layout = item.layout()
        for i in reversed(range(layout.count())): 
            layout.itemAt(i).widget().setParent(None)
        
    def fillHeader(self):
        headerLayout = QtWidgets.QGridLayout()
        self.header.setLayout(headerLayout)

        label = QtWidgets.QLabel("Bar-Bot 4.0")
        label.setFont(Qt.QFont("Arial", 20, 2))
        headerLayout.addWidget(label, 0, 0, QtCore.Qt.AlignCenter)

        icon = Qt.QIcon(self.imagePath("admin.png"))
        button = QtWidgets.QPushButton(icon, "")
        button.clicked.connect(lambda: self.close())
        headerLayout.addWidget(button, 0, 0, QtCore.Qt.AlignRight)
        

    def showMessage(self, message):
        splash = QtWidgets.QLabel(message, flags=QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.FramelessWindowHint)
        splash.show()
        QtCore.QTimer.singleShot(1000, lambda splash=splash: splash.close())

    def imagePath(self, fileName):
        script_dir = os.path.dirname(__file__)
        return os.path.join(script_dir, "../../gui/css/", fileName)

    def getAmountDropdown(self, selectedData = None):
        #add ingredient name
        wAmount = QtWidgets.QComboBox()
        wAmount.addItem("-", -1)
        for i in range(1, 17):
            wAmount.addItem(str(i), i)
            if i == selectedData:
                wAmount.setCurrentIndex(i)
            i = i+1
        return wAmount

    def getIngredientDropdown(self, selectedData = None):
        ing = self.db.getAllIngredients().values()
        #add ingredient name
        wIngredient = QtWidgets.QComboBox()
        wIngredient.addItem("-", -1)
        i = 1
        for item in ing:
            wIngredient.addItem(str(item["name"]), item["id"])
            if item["id"] == selectedData:
                wIngredient.setCurrentIndex(i)
            i = i+1
        return wIngredient

class View(QtWidgets.QWidget):
    mainWindow: MainWindow
    dab: Database
    bot: Statemachine.StateMachine

    def __init__(self, _mainWindow: MainWindow):
        super().__init__(_mainWindow)
        self.mainWindow = _mainWindow
        self.db = _mainWindow.db
        self.bot = _mainWindow.bot