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
    return os.path.join(script_dir, "asset")

def getQtIconFromFileName(fileName):
    script_dir = os.path.dirname(__file__)
    path = os.path.join(script_dir, "asset", fileName)
    return Qt.QIcon(path)


class Keyboard(QtWidgets.QWidget):
    widgetsCreated = False
    isShift = False
    target: QtWidgets.QLineEdit = None
    def __init__(self, target: QtWidgets.QLineEdit):
        super().__init__()
        self.target = target
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.updateKeys()
        #move to bottom of the screen
        desktop = Qt.QApplication.desktop().availableGeometry()
        keyboardDesired = Qt.QRect(Qt.QPoint(0,0), self.sizeHint())
        keyboardDesired.moveBottomRight(desktop.bottomRight())
        keyboardDesired.setLeft(desktop.left())
        self.setGeometry(keyboardDesired)

    def updateKeys(self):
	    #first row
        keys = [
            ["1","!"],["2","\""],["3","§"],["4","$"],["5","%"],
            ["6","&"],["7","/"],["8","("],["9",")"],["0","ß"]
        ]
        if not self.widgetsCreated:
            self.firstRow = self.addRow([data[0] for data in keys])
        for index, data in enumerate(keys):
            self.firstRow[index].setText(data[1] if self.isShift else data[0])

	    #second row
        keys = ["q","w","e","r","t","z","u","i","o","p"]
        if not self.widgetsCreated:
            self.secondRow = self.addRow(keys)
        for index, letter in enumerate(keys):
            self.secondRow[index].setText(str.upper(letter) if self.isShift else letter)
        
	    #third row
        keys = ["a","s","d","f","g","h","j","k","l","ö"]
        if not self.widgetsCreated:
            self.thirdRow = self.addRow(keys)
        for index, letter in enumerate(keys):
            self.thirdRow[index].setText(str.upper(letter) if self.isShift else letter)

        #fourth row
        keys = ["y","x","c","v","b","n","m","ä","ü"]
        if not self.widgetsCreated:
            self.fourthRow = self.addRow(keys)
        for index, letter in enumerate(keys):
            self.fourthRow[index].setText(str.upper(letter) if self.isShift else letter)
        
        #last row
        if not self.widgetsCreated:
            row = QtWidgets.QWidget()
            row.setLayout(QtWidgets.QHBoxLayout())
            BarBotGui.setNoSpacingAndMargin(row.layout())
            #shift
            button = QtWidgets.QPushButton("▲")
            button.clicked.connect(lambda checked, b=button: self.buttonClicked("shift"))
            row.layout().addWidget(button)
            #space
            button = QtWidgets.QPushButton(" ")
            button.clicked.connect(lambda checked, b=button: self.buttonClicked(" "))
            row.layout().addWidget(button)
            #delete
            button = QtWidgets.QPushButton("←")
            button.clicked.connect(lambda checked, b=button: self.buttonClicked("delete"))
            row.layout().addWidget(button)
            self.layout().addWidget(row)

        self.widgetsCreated = True

    def buttonClicked(self, content):
        if self.target is None:
            return
        if content == "shift":
            self.isShift = not self.isShift
            self.updateKeys()
        else:
            if content == "delete":
                self.target.setText(self.target.text()[:-1])
            else:
                self.target.setText(self.target.text() + content)
            #reset shift state
            if self.isShift:
                self.isShift = False
                self.updateKeys()

    def addRow(self, keys):
        res =  []
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        BarBotGui.setNoSpacingAndMargin(row.layout())
        for letter in keys:
            button = QtWidgets.QPushButton(letter)
            button.clicked.connect(lambda checked, b=button: self.buttonClicked(b.text()))
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res


class MainWindow(QtWidgets.QWidget):
    db:BarBot.Database
    bot:BarBot.StateMachine    
    currentView = None
    botStateChangedTrigger = QtCore.pyqtSignal()
    lastIdleSubView = None
    isAdmin = False
    keyboard: Keyboard = None
    def __init__(self, _db:BarBot.Database, _bot:BarBot.StateMachine):
        super().__init__()
        import BarBotGui.Views
        self.db = _db
        self.bot = _bot

        styles = open(os.path.join(getCSSPath(), 'main.qss')).read()
        styles = styles.replace("#iconpath#", getCSSPath())
        self.setStyleSheet(styles)

        self.mousePressEvent = lambda event: self.closeKeyboard()

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

    def closeKeyboard(self):
        if self.keyboard is not None:
            self.keyboard.close()
            self.keyboard = None
    
    def openKeyboard(self, target: QtWidgets.QLineEdit):
        if self.keyboard is not None:
            self.keyboard.close()
        self.keyboard = Keyboard(target)
        self.keyboard.show()

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

