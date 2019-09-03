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
            icon = BarBotGui.getImage("edit.png")
            editButton = QtWidgets.QPushButton(icon, "")
            editButton.clicked.connect(lambda checked,rid=recipe["id"]: self.openEdit(rid))
            recipeTitleContainer.layout().addWidget(editButton, 0)

            #title 
            recipeTitle = QtWidgets.QLabel(recipe["name"])
            recipeTitle.setProperty("class", "RecipeTitle")
            recipeTitleContainer.layout().addWidget(recipeTitle, 1)

            #order button
            if recipe["available"]:
                icon = BarBotGui.getImage("order.png")
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

        self.NameWidget = QtWidgets.QLineEdit(self.recipeData["name"])
        self.InstructionWidget = QtWidgets.QLineEdit(self.recipeData["instruction"])
        self.IngredientsContainer = QtWidgets.QWidget()
        self.IngredientsContainer.setLayout(QtWidgets.QGridLayout())
        self.SafeButton = QtWidgets.QPushButton("Speichern")
        self.SafeButton.clicked.connect(self.save)

        self.layout().addWidget(QtWidgets.QLabel("Name:"))
        self.layout().addWidget(self.NameWidget)
        self.layout().addWidget(QtWidgets.QLabel("Zusatzinfo:"))
        self.layout().addWidget(self.InstructionWidget)
        self.layout().addWidget(QtWidgets.QLabel("Zutaten:"))
        self.layout().addWidget(self.IngredientsContainer, 1)
        self.layout().addWidget(self.SafeButton)


        self.IngredientWidgets = []
        for i in range(12):
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

    def save(self, e):
        if not self.mainWindow.bot.canManipulateDatabase():

            return
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
        cbDates.currentTextChanged.connect(self.partyDataChanged)
        row.layout().addWidget(cbDates)

        self.contentWrapper = QtWidgets.QWidget()
        self.contentWrapper.setLayout(QtWidgets.QGridLayout())
        BarBotGui.setNoSpacingAndMargin(self.contentWrapper.layout())
        self.layout().addWidget(self.contentWrapper)

        #initialize with date of last party
        self.update(self.parties[0]["partydate"] if self.parties else None)

    def partyDataChanged(self, newDate):
        self.update(newDate)

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
        self.setContent(container)
    
    def setContent(self, content):
        if self.content is not None:
            #setting the parent of the previos content to None will destroy it
            self.content.setParent(None)
        self.content = content
        self.contentWrapper.layout().addWidget(content)