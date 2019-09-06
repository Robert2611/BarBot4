from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import BarBot
import os
import BarBotGui

def setNoSpacingAndMargin(layout):
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)

def setWidgetColor(widget, color):
    widget.setStyleSheet("QWidget { background: %s; }" % color)

def getCSSPath():
    script_dir = os.path.dirname(__file__)
    return os.path.join(script_dir, "../../gui/css")

def getQtIconFromFileName(fileName):
    script_dir = os.path.dirname(__file__)
    path = os.path.join(script_dir, "../../gui/css/", fileName)
    return Qt.QIcon(path)

class MainWindow(QtWidgets.QWidget):
    db:BarBot.Database
    bot:BarBot.StateMachine    
    currentView = None
    botStateChangedTrigger = QtCore.pyqtSignal()
    lastIdleSubView = None
    isAdmin = False
    def __init__(self, _db:BarBot.Database, _bot:BarBot.StateMachine):
        super().__init__()
        import BarBotGui.Views
        self.db = _db
        self.bot = _bot

        styles = """
            .BarBotHeader{
                font-size: 50px;
            }
            .Headline{
                font-size: 20px;
            }
            .RecipeTitle{
                font-size: 20px;
            }
            .AdminCheckbox::indicator{
                image: url(#iconpath#/admin.png);
                width: 20px;
                height: 20px;
                border-width: 2px;
                border-style: solid;
                border-color: gray;
            }
            .AdminCheckbox::indicator:checked{
                border-color: red;
            }
            .AdminCheckbox::indicator:unchecked{
            }
        """
        styles = styles.replace("#iconpath#", getCSSPath())
        self.setStyleSheet(styles)

        #forward status changed
        self.botStateChangedTrigger.connect(self.botStateChanged)
        self.bot.OnStateChanged = lambda: self.botStateChangedTrigger.emit()

        #remove borders and title bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(480, 800)

        self.setLayout(QtWidgets.QVBoxLayout())
        #header
        header = QtWidgets.QWidget()
        header.setLayout(QtWidgets.QGridLayout())
        self.layout().addWidget(header, 0)

        label = QtWidgets.QLabel("Bar-Bot 4.0")
        label.setProperty("class", "BarBotHeader")
        header.layout().addWidget(label, 0, 0, QtCore.Qt.AlignCenter)

        #content
        self.contentWrapper = QtWidgets.QWidget()
        self.contentWrapper.setLayout(QtWidgets.QGridLayout())
        self.contentWrapper.layout().setSpacing(0)
        self.contentWrapper.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(self.contentWrapper, 1)

        self.setView(BarBotGui.Views.IdleView(self))
        self.show()

    def setView(self, view):
        #remove existing item from window
        if self.currentView is not None:
            self.currentView.deleteLater()
        self.currentView = view
        self.contentWrapper.layout().addWidget(self.currentView)

    def botStateChanged(self):
        import BarBotGui.Views
        if isinstance(self.currentView, BarBotGui.Views.IdleView):
            self.lastIdleSubView = self.currentView.subViewName
        if self.bot.state == BarBot.State.IDLE and self.lastIdleSubView:
            self.setView(BarBotGui.Views.IdleView(self, self.lastIdleSubView))
        else:
            self.setView(BarBotGui.Views.BusyView(self))
        print("Status changed")

    def showPage(self, view):
        import BarBotGui.Views
        if not isinstance(self.currentView, BarBotGui.Views.IdleView):
            return
        self.currentView.setContent(view)

    def showMessage(self, message):
        splash = QtWidgets.QLabel(message, flags=QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.FramelessWindowHint)
        splash.show()
        QtCore.QTimer.singleShot(1000, lambda splash=splash: splash.close())

    def getAmountDropdown(self, selectedData = None):
        #add ingredient name
        wAmount = QtWidgets.QComboBox()
        wAmount.addItem("-", -1)
        wAmount.setCurrentIndex(0)
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
        wIngredient.setCurrentIndex(0)
        i = 1
        for item in ing:
            wIngredient.addItem(str(item["name"]), item["id"])
            if item["id"] == selectedData:
                wIngredient.setCurrentIndex(i)
            i = i+1
        return wIngredient

class View(QtWidgets.QWidget):
    mainWindow: MainWindow
    dab: BarBot.Database
    bot: BarBot.StateMachine

    def __init__(self, _mainWindow: MainWindow):
        super().__init__(_mainWindow)
        self.mainWindow = _mainWindow
        self.db = _mainWindow.db
        self.bot = _mainWindow.bot