from PyQt5 import QtWidgets
import BarBotMainWindow
import Database
import Statemachine

class View(QtWidgets.QWidget):
    mainWindow: BarBotMainWindow
    dab: Database.Database
    bot: Statemachine.StateMachine

    def __init__(self, _mainWindow: BarBotMainWindow):
        super().__init__(_mainWindow)
        self.mainWindow = _mainWindow
        self.db = _mainWindow.db
        self.bot = _mainWindow.bot