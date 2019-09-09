from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import BarBotGui
import BarBot


class BusyView(BarBotGui.View):
    mixingProgressChangedTrigger = QtCore.pyqtSignal()
    messageChangedTrigger = QtCore.pyqtSignal()
    message = None
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)

        #forward message changed
        self.messageChangedTrigger.connect(lambda: self.updateMessage())
        self.bot.OnMessageChanged = lambda: self.messageChangedTrigger.emit()

        self.setLayout(QtWidgets.QGridLayout())
        BarBotGui.setNoSpacingAndMargin(self.layout())

        centered = QtWidgets.QFrame()
        centered.setLayout(QtWidgets.QVBoxLayout())
        centered.setProperty("class", "CenteredContent")
        self.layout().addWidget(centered, 0, 0, QtCore.Qt.AlignCenter)

        self.titleLabel = QtWidgets.QLabel("")    
        self.titleLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.titleLabel.setProperty("class", "Headline")
        centered.layout().addWidget(self.titleLabel)

        self.contentContainer = QtWidgets.QWidget()
        self.contentContainer.setLayout(QtWidgets.QVBoxLayout())
        centered.layout().addWidget(self.contentContainer)

        self.messageContainer = QtWidgets.QWidget()
        self.messageContainer.setLayout(QtWidgets.QGridLayout())
        self.messageContainer.setVisible(False)
        centered.layout().addWidget(self.messageContainer)

        self.initByStatus()

        self.updateMessage()

    def updateMessage(self):
        #delete old message
        if self.message is not None:
            self.message.setParent(None)
        
        if self.bot.message is None:
            self.messageContainer.setVisible(False)
            self.contentContainer.setVisible(True)
            return
        
        self.message = QtWidgets.QWidget()
        self.message.setLayout(QtWidgets.QVBoxLayout())		
        self.messageContainer.layout().addWidget(self.message)
        
        messageLabel = QtWidgets.QLabel()
        self.message.layout().addWidget(messageLabel)

        if self.bot.message == BarBot.UserMessages.IngredientEmpty:
            messageLabel.setText("Die Zutat ist leer.\nBitte neue Flasche anschließen.")
            
            row = QtWidgets.QWidget()
            row.setLayout(QtWidgets.QHBoxLayout())
            self.message.layout().addWidget(row)

            cancelButton = QtWidgets.QPushButton("Cocktail abbrechen")
            cancelButton.clicked.connect(lambda: self.bot.setUserInput(False))
            row.layout().addWidget(cancelButton)

            continueButton = QtWidgets.QPushButton("Erneut versuchen")
            continueButton.clicked.connect(lambda: self.bot.setUserInput(True))
            row.layout().addWidget(continueButton)

        elif self.bot.message == BarBot.UserMessages.PlaceGlas:
            messageLabel.setText("Bitte ein Glas auf die Plattform stellen.")
        elif self.bot.message == BarBot.UserMessages.MixingDoneRemoveGlas:
            messageLabel.setText("Der Cocktail ist fertig gemischt.\nDu kannst ihn von der Platform nehmen.")
            
            if self.bot.data["recipe"]["instruction"]:
                label = QtWidgets.QLabel("Zusätzliche Informationen:")
                self.message.layout().addWidget(label)

                instruction = QtWidgets.QLabel(self.bot.data["recipe"]["instruction"])
                self.message.layout().addWidget(instruction)

        self.messageContainer.setVisible(True)
        self.contentContainer.setVisible(False)


    def initByStatus(self):
        #content
        if self.bot.state == BarBot.State.MIXING:
            #progressbar
            self.progressBar = QtWidgets.QProgressBar()
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(100)
            self.contentContainer.layout().addWidget(self.progressBar)

            #forward mixing progress changed
            self.mixingProgressChangedTrigger.connect(lambda: self.progressBar.setValue(int(self.bot.progress * 100)))
            self.bot.OnMixingProgressChanged = lambda: self.mixingProgressChangedTrigger.emit()

            self.titleLabel.setText("Cocktail\n'%s'\nwird gemischt." % self.bot.data["recipe"]["name"])
        elif self.bot.state == BarBot.State.CLEANING:
            self.titleLabel.setText("Reinigung")
        elif self.bot.state == BarBot.State.CLEANING_CYCLE:
            self.titleLabel.setText("Reinigung")
        elif self.bot.state == BarBot.State.SINGLE_INGREDIENT:
            self.titleLabel.setText("Dein Nachschlag wird hinzugefügt")

class IdleView(BarBotGui.View):
    subViewName = None
    def __init__(self, _mainWindow: BarBotGui.MainWindow, subViewName = "ListRecipes"):
        super().__init__(_mainWindow)
        self.pages = {
            "Liste" : lambda: self.setSubViewByName("ListRecipes"),
            "Neu" : lambda: self.setSubViewByName("RecipeNewOrEdit"),
            "Nachschlag" : lambda: self.setSubViewByName("SingleIngredient"),
            "Statistik" : lambda: self.setSubViewByName("Statistics")
        }
        self.adminPages = {
            "Übersicht" : lambda: self.setSubViewByName("AdminOverview"),
            "Positionen" : lambda: self.setSubViewByName("Ports"),
            "Reinigung" : lambda: self.setSubViewByName("Cleaning"),
            "System" : lambda: self.setSubViewByName("System"),
            "Löschen" : lambda: self.setSubViewByName("RemoveRecipe")
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

        #admin button
        self.adminButton = QtWidgets.QCheckBox("")
        self.adminButton.setProperty("class", "AdminCheckbox")
        self.adminButton.stateChanged.connect(self.adminStateChanged)
        self.adminButton.setChecked(self.mainWindow.isAdmin)
        self.navigation.layout().addWidget(self.adminButton, 0)

        #admin navigation
        self.adminNavigation = QtWidgets.QWidget()
        self.adminNavigation.setLayout(QtWidgets.QHBoxLayout())
        self.adminNavigation.setVisible(self.mainWindow.isAdmin)
        self.layout().addWidget(self.adminNavigation)

        for text, method in self.adminPages.items():
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(method)
            self.adminNavigation.layout().addWidget(button, 1)

        #content
        contentWrapper = QtWidgets.QWidget()
        self.layout().addWidget(contentWrapper, 1)
        contentWrapper.setLayout(QtWidgets.QGridLayout())
        BarBotGui.setNoSpacingAndMargin(contentWrapper.layout())

        self.scroller = QtWidgets.QScrollArea()
        self.scroller.setWidgetResizable(True)
        self.scroller.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        contentWrapper.layout().addWidget(self.scroller)

        self.setSubViewByName(subViewName)
    
    def adminStateChanged(self, admin):
        self.mainWindow.isAdmin = admin
        #gui must be initialized
        if hasattr(self, "adminNavigation"):
            self.adminNavigation.setVisible(self.mainWindow.isAdmin)
    
    def setSubViewByName(self, name):
        self.subViewName = name
        import BarBotGui.IdleSubViews
        class_ = getattr(BarBotGui.IdleSubViews, name)
        self.setContent(class_(self.mainWindow))
    
    def setContent(self, view):
        if self.scroller.widget() is not None:
            self.scroller.widget().setParent(None)
        self.scroller.setWidget(view)

