from PyQt5 import QtWidgets, Qt, QtCore, QtGui, QtChart
import BarBotGui

class ListRecipes(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        self.recipes = self.db.getRecipes()
        self.setLayout(QtWidgets.QVBoxLayout())

        for recipe in self.recipes:
            #box to hold the recipe
            recipeBox = QtWidgets.QWidget()
            recipeBox.setLayout(QtWidgets.QVBoxLayout())
            self.layout().addWidget(recipeBox)

            #title with buttons
            recipeTitleContainer = QtWidgets.QWidget()
            recipeTitleContainer.setLayout(QtWidgets.QHBoxLayout())
            recipeBox.layout().addWidget(recipeTitleContainer)

            #edit button
            icon = BarBotGui.getQtIconFromFileName("edit.png")
            editButton = QtWidgets.QPushButton(icon, "")
            editButton.clicked.connect(lambda checked,rid=recipe["id"]: self.openEdit(rid))
            recipeTitleContainer.layout().addWidget(editButton, 0)

            #title 
            recipeTitle = QtWidgets.QLabel(recipe["name"])
            recipeTitle.setProperty("class", "RecipeTitle")
            recipeTitleContainer.layout().addWidget(recipeTitle, 1)

            #order button
            if recipe["available"]:
                icon = BarBotGui.getQtIconFromFileName("order.png")
                editButton = QtWidgets.QPushButton(icon, "")
                editButton.clicked.connect(lambda checked,rid=recipe["id"]: self.order(rid))
                recipeTitleContainer.layout().addWidget(editButton, 0)
            
            #items container for holding the recipe items
            recipeItemsContainer = QtWidgets.QWidget()
            recipeItemsContainer.setLayout(QtWidgets.QVBoxLayout())
            recipeBox.layout().addWidget(recipeItemsContainer, 1)

            #add items
            for item in recipe["items"]:
                label = QtWidgets.QLabel("%i cl %s" % (item["amount"], item["name"]))
                recipeItemsContainer.layout().addWidget(label)

    def openEdit(self, id):
        self.mainWindow.showPage(RecipeNewOrEdit(self.mainWindow, id))
    
    def order(self, id):
        if self.bot.isArduinoBusy():
            self.mainWindow.showMessage("Bitte warten bis die laufende Aktion abgeschlossen ist.")
            return
        recipe = self.db.getRecipe(id)
        if recipe == None:
            self.mainWindow.showMessage("Rezept nicht gefunden")
            return
        self.db.startOrder(recipe["id"])
        self.bot.startMixing(recipe)
        self.mainWindow.showMessage("Mixen gestartet")

class RecipeNewOrEdit(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow, recipe_id = None):
        super().__init__(_mainWindow)
        self.id = recipe_id
        if self.id is not None:
            self.recipeData = self.db.getRecipe(self.id)
        else:
            self.recipeData = {"name" : "", "instruction": ""}
        self.setLayout(QtWidgets.QVBoxLayout())

        #title
        title = QtWidgets.QLabel("Neues Rezept" if self.id is None else "Rezept bearbeiten")
        title.setProperty("class", "Headline")
        self.layout().addWidget(title)

        #name
        self.layout().addWidget(QtWidgets.QLabel("Name:"))
        self.NameWidget = QtWidgets.QLineEdit(self.recipeData["name"])
        self.layout().addWidget(self.NameWidget)        
        #instruction
        self.layout().addWidget(QtWidgets.QLabel("Zusatzinfo:"))
        self.InstructionWidget = QtWidgets.QLineEdit(self.recipeData["instruction"])
        self.layout().addWidget(self.InstructionWidget)

        #ingredients
        self.layout().addWidget(QtWidgets.QLabel("Zutaten:"))
        self.IngredientsContainer = QtWidgets.QWidget()
        self.IngredientsContainer.setLayout(QtWidgets.QGridLayout())
        self.layout().addWidget(self.IngredientsContainer, 1)
        #fill grid
        self.IngredientWidgets = []
        for i in range(10):
            if self.id is not None and i<len(self.recipeData["items"]):
                selectedAmount = self.recipeData["items"][i]["amount"]
                selectedIngredient = self.recipeData["items"][i]["iid"]
            else:
                selectedAmount = 0
                selectedIngredient = 0
            #add ingredient name
            wIngredient = self.mainWindow.getIngredientDropdown(selectedIngredient)
            self.IngredientsContainer.layout().addWidget(wIngredient, i, 0)
            #add ingredient amount
            wAmount = self.mainWindow.getAmountDropdown(selectedAmount)
            self.IngredientsContainer.layout().addWidget(wAmount, i, 1)

            #safe references for later
            self.IngredientWidgets.append([wIngredient, wAmount])

        #save button
        button = QtWidgets.QPushButton("Speichern")
        button.clicked.connect(lambda: self.save())
        self.layout().addWidget(button)
        self.layout().setAlignment(button, QtCore.Qt.AlignCenter)

        #dummy
        self.layout().addWidget(QtWidgets.QWidget(), 1)

    def save(self):
        # check data
        name = self.NameWidget.text()
        if name == None or name == "":
            self.mainWindow.showMessage("Bitte einen Namen eingeben")
            return
        instruction = self.InstructionWidget.text()
        # prepare data
        items = []
        for wIngredient, wAmount in self.IngredientWidgets:
            ingredient = int(wIngredient.currentData())
            amount = int(wAmount.currentData())
            if ingredient >= 0 and amount >= 0:
                items.append({"ingredient": ingredient, "amount": amount})
        if self.id is not None and not self.db.recipeChanged(self.id, name, items, instruction):
            self.mainWindow.showMessage("Rezept wurde nicht verändert")
            return
        print("id: %i" % self.id)
        # update Database
        new_id = self.db.createOrUpdateRecipe(name, instruction, self.id)
        self.db.addRecipeItems(new_id, items)
        self.id = new_id
        if self.id == None:
            self.reloadWithMessage("Neues Rezept gespeichert")
        else:
            self.reloadWithMessage("Rezept gespeichert")

    def reloadWithMessage(self, message):
        self.mainWindow.showPage(RecipeNewOrEdit(self.mainWindow, self.id))
        self.mainWindow.showMessage(message)

class SingleIngredient(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())

        #title
        title = QtWidgets.QLabel("Nachschlag")
        title.setProperty("class", "Headline")
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
        button.clicked.connect(lambda: self.start())
        self.layout().addWidget(button)
        self.layout().setAlignment(button, QtCore.Qt.AlignCenter)

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

class Statistics(BarBotGui.View):
    content = None
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())

        #title
        title = QtWidgets.QLabel("Statistik")
        title.setProperty("class", "Headline")
        self.layout().addWidget(title)

        #date selector
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(row)

        label = QtWidgets.QLabel("Datum")
        row.layout().addWidget(label)
        
        self.parties = self.db.getParties()
        cbDates = QtWidgets.QComboBox()
        for party in self.parties:
            cbDates.addItem(party["partydate"])
        cbDates.currentTextChanged.connect(lambda newDate: self.update(newDate))
        row.layout().addWidget(cbDates)

        self.contentWrapper = QtWidgets.QWidget()
        self.contentWrapper.setLayout(QtWidgets.QGridLayout())
        BarBotGui.setNoSpacingAndMargin(self.contentWrapper.layout())
        self.layout().addWidget(self.contentWrapper)

        #initialize with date of last party
        self.update(self.parties[0]["partydate"] if self.parties else None)

    def createBarChart(self, data):
        barSet = QtChart.QBarSet("")
        xNames = []
        for name, value in data:
            xNames.append(name)
            barSet.append(value)
        series = QtChart.QHorizontalStackedBarSeries()
        series.append(barSet)
        series.setLabelsVisible()
        nameAxis = QtChart.QBarCategoryAxis()
        nameAxis.append(xNames)
        chart = QtChart.QChart()
        chart.createDefaultAxes()
        chart.setAxisY(nameAxis)
        chart.legend().setVisible(False)
        chart.addSeries(series)
        chart.setMinimumHeight(500)
        chart.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        chartView = QtChart.QChartView(chart)
        chartView.setRenderHint(QtGui.QPainter.Antialiasing)
        return chartView

    def update(self, date):
        if not date:
            return
        #self.total_count = self.parties[0]["ordercount"]

        #get data from database
        cocktail_count = self.db.getOrderedCocktailCount(date)
        ingredients_amount = self.db.getOrderedIngredientsAmount(date)
        cocktails_by_time = self.db.getOrderedCocktailsByTime(date)
        #create container
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QVBoxLayout())
        
        #total ordered cocktails
        totalCocktails = sum(c["count"] for c in cocktail_count)
        label = QtWidgets.QLabel("Bestellte Cocktails (%i)" % totalCocktails)
        container.layout().addWidget(label)
        #ordered cocktails by name
        data = [(c["name"],c["count"]) for c in reversed(cocktail_count)]
        chart = self.createBarChart(data)
        container.layout().addWidget(chart)
        
        #total liters
        total_amount = sum([amount["liters"] for amount in ingredients_amount])
        label = QtWidgets.QLabel("Verbrauchte Zutaten (%i l)" % total_amount)
        container.layout().addWidget(label)
        #ingrediends
        data = [(c["ingredient"],c["liters"]) for c in reversed(ingredients_amount)]
        chart = self.createBarChart(data)
        container.layout().addWidget(chart)

        #label
        label = QtWidgets.QLabel("Bestellungen")
        container.layout().addWidget(label)
        #cocktails vs. time chart
        data = [(c["hour"],c["count"]) for c in reversed(cocktails_by_time)]
        chart = self.createBarChart(data)
        container.layout().addWidget(chart)

        #set content
        if self.content is not None:
            #setting the parent of the previos content to None will destroy it
            self.content.setParent(None)
        self.content = container
        self.contentWrapper.layout().addWidget(container)

class AdminOverview(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())

        #title
        title = QtWidgets.QLabel("Übersicht")
        title.setProperty("class", "Headline")
        self.layout().addWidget(title)

        #table
        table = QtWidgets.QWidget()
        table.setLayout(QtWidgets.QGridLayout())
        self.layout().addWidget(table)
        #fill table
        ingredients = self.db.getAllIngredients()
        ports = self.db.getIngredientOfPort()
        for i in range(12):
            label = QtWidgets.QLabel("Position %i" % (i+1))
            table.layout().addWidget(label, i, 0)
            if i in ports.keys() and ports[i] in ingredients.keys():
                ingredient = ingredients[ports[i]]
                label = QtWidgets.QLabel(ingredient["name"])
                table.layout().addWidget(label, i, 1)
                label = QtWidgets.QLabel(str(ingredient["calibration"]))
                table.layout().addWidget(label, i, 2)
                #calibrate button
                button = QtWidgets.QPushButton(BarBotGui.getQtIconFromFileName("calibrate.png"), "")
                button.clicked.connect(lambda checked, portId=i: self.openCalibration(portId))
                table.layout().addWidget(button, i, 3, QtCore.Qt.AlignLeft)
        #dummy
        self.layout().addWidget(QtWidgets.QWidget(), 1)

    def openCalibration(self, id):
        self.mainWindow.showPage(Calibration(self.mainWindow, id))

class Ports(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())

        #title
        title = QtWidgets.QLabel("Positionen")
        title.setProperty("class", "Headline")
        self.layout().addWidget(title)

        #table
        table = QtWidgets.QWidget()
        table.setLayout(QtWidgets.QGridLayout())
        self.layout().addWidget(table)
        #fill table
        ingredients = self.db.getAllIngredients()
        ports = self.db.getIngredientOfPort()
        self.IngredientWidgets = dict()
        for i in range(12):
            label = QtWidgets.QLabel("Position %i" % (i+1))
            table.layout().addWidget(label, i, 0)
            selectedPort = ports[i] if i in ports.keys() else 0
            cbPort = self.mainWindow.getIngredientDropdown(selectedPort)
            self.IngredientWidgets[i] = cbPort
            table.layout().addWidget(cbPort, i, 1)
            
        #save button
        button = QtWidgets.QPushButton("Speichern")
        button.clicked.connect(lambda: self.save())
        self.layout().addWidget(button)
        self.layout().setAlignment(button, QtCore.Qt.AlignCenter)
        
        #dummy
        self.layout().addWidget(QtWidgets.QWidget(), 1)
    
    def save(self):
        ports = dict()
        for port, cb in self.IngredientWidgets.items():
            ingredient = cb.currentData()
            if ingredient not in ports.values():
                ports[port] = ingredient
            else:
                self.mainWindow.showMessage("Jede Zutat darf nur einer Position zugewiesen werden!")
                return
        self.mainWindow.showMessage("Positionen wurden gespeichert.")
        self.db.setPorts(ports)

class Calibration(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow, portId = -1):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel("Kalibrierung"))

class Cleaning(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())

        self.ingredients = self.db.getAllIngredients()
        self.ports = self.db.getIngredientOfPort()
        self.amount = 50
        #assume calibration value of water
        self.calibration = 1000

        #title
        title = QtWidgets.QLabel("Reinigung")
        title.setProperty("class", "Headline")
        self.layout().setAlignment(title, QtCore.Qt.AlignTop)
        self.layout().addWidget(title)

        #clean left
        button = QtWidgets.QPushButton("Reinigen linke Hälfte")
        button.clicked.connect(lambda: self.cleanLeft())
        self.layout().addWidget(button)

        #clean right
        button = QtWidgets.QPushButton("Reinigen rechte Hälfte")
        button.clicked.connect(lambda: self.cleanRight())
        self.layout().addWidget(button)

        #grid
        grid = QtWidgets.QWidget()
        grid.setLayout(QtWidgets.QGridLayout())
        self.layout().addWidget(grid)
        #fill with buttons
        for column in range(6):
            for row in range(2):
                port = row * 6 + column
                button = QtWidgets.QPushButton(str(port + 1))
                button.clicked.connect(lambda checked, pid=port: self.cleanSingle(pid))
                grid.layout().addWidget(button, row, column)

        #dummy
        self.layout().addWidget(QtWidgets.QWidget(), 1)

    def cleanLeft(self):
        data = []
        for i in range(0, 6):
            data.append({"port": i, "amount": self.amount, "calibration": self.calibration})
        self.bot.startCleaningCycle(data)

    def cleanRight(self):
        data = []
        for i in range(6, 12):
            data.append({"port": i, "amount": self.amount, "calibration": self.calibration})
        self.bot.startCleaningCycle(data)
    
    def cleanSingle(self, port):
        self.bot.startCleaning(port, self.amount * self.calibration)

class System(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel("System"))

class RemoveRecipe(BarBotGui.View):
    list = None
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        self.setLayout(QtWidgets.QVBoxLayout())

        #title
        title = QtWidgets.QLabel("Positionen")
        title.setProperty("class", "Headline")
        self.layout().setAlignment(title, QtCore.Qt.AlignTop)
        self.layout().addWidget(title)

        #confirmationDialog
        self.addConfirmationDialog()
        #list
        self.addList()


    def addConfirmationDialog(self):
        self.confirmationDialog = QtWidgets.QWidget()
        self.confirmationDialog.setLayout(QtWidgets.QGridLayout())
        self.confirmationDialog.setVisible(False)
        self.layout().addWidget(self.confirmationDialog, 1)

        centerBox = QtWidgets.QFrame()
        centerBox.setLayout(QtWidgets.QVBoxLayout())
        self.confirmationDialog.layout().addWidget(centerBox, 0, 0, QtCore.Qt.AlignCenter)

        label = QtWidgets.QLabel("Wirklich löschen?")
        centerBox.layout().addWidget(label)

        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        centerBox.layout().addWidget(row)

        okButton = QtWidgets.QPushButton("Löschen")
        okButton.clicked.connect(lambda: self.remove())
        row.layout().addWidget(okButton)

        cancelButton = QtWidgets.QPushButton("Abbrechen")
        cancelButton.clicked.connect(lambda: self.hideConfirmationDialog())
        row.layout().addWidget(cancelButton)
    
    def addList(self):
        if self.list is not None:
            self.list.setParent(None)

        self.list = QtWidgets.QWidget()
        self.list.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.list, 1)

        self.recipes = self.db.getRecipes()
        for recipe in self.recipes:
            #box to hold the recipe
            recipeBox = QtWidgets.QWidget()
            recipeBox.setLayout(QtWidgets.QHBoxLayout())
            self.list.layout().addWidget(recipeBox)

            #title 
            recipeTitle = QtWidgets.QLabel(recipe["name"])
            recipeTitle.setProperty("class", "RecipeTitle")
            recipeBox.layout().addWidget(recipeTitle, 1)

            #remove button
            icon = BarBotGui.getQtIconFromFileName("remove.png")
            removeButton = QtWidgets.QPushButton(icon, "")
            removeButton.clicked.connect(lambda checked,rid=recipe["id"]: self.showConfirmationDialog(rid))
            recipeBox.layout().addWidget(removeButton, 0)

    def showConfirmationDialog(self, id):
        self.id = id
        self.list.setVisible(False)
        self.confirmationDialog.setVisible(True)
    
    def hideConfirmationDialog(self):
        self.confirmationDialog.setVisible(False)
        self.list.setVisible(True)

    def remove(self):
        self.db.removeRecipe(self.id)
        self.addList()