from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import View
import BarBotMainWindow

class ViewSingleIngredient(View.View):
    def __init__(self, _mainWindow: BarBotMainWindow):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())

        #title
        title = QtWidgets.QLabel("Nachschlag")
        title.setFont(QtGui.QFont("Arial", 20, 2))
        self.layout().addWidget(title)

        #text
        text = QtWidgets.QLabel("Ist dein Cocktail noch nicht perfekt?\nHier kannst du nachhelfen.")
        self.layout().addWidget(text)

        #selectors
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(row)

        #ingredient selector
        self.ingredientSelector = self.mainWindow.getIngredientDropdown()
        row.layout().addWidget(self.ingredientSelector)

        #ingredient selector
        self.amountSelector = self.mainWindow.getAmountDropdown()
        row.layout().addWidget(self.amountSelector)

        #button
        button = QtWidgets.QPushButton("Los")
        button.clicked.connect(self.start)
        self.layout().addWidget(button)

        #dummy
        self.layout().addWidget(QtWidgets.QWidget(), 1)

    def start(self):
        if self.bot.isArduinoBusy():
            self.mainWindow.showMessage("Bitte warten bis die laufende Aktion abgeschlossen ist.")
            return
        iid = self.ingredientSelector.currentData()
        amount = self.amountSelector.currentData()
        if iid < 0 or amount < 0:
            self.mainWindow.showMessage("Bitte eine Zutat und eine Menge auswählen")
            return
        port_cal = self.db.getPortAndCalibration(iid)
        if port_cal == None:
            self.mainWindow.showMessage("Diese Zutat ist nicht anschlossen")
            return
        self.bot.startSingleIngredient({
            "port": port_cal["port"],
            "calibration":port_cal["calibration"],
            "amount":amount
        })
        self.mainWindow.showMessage("Zutat wird hinzugefügt")
        return