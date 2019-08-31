from PyQt5 import QtWidgets, Qt, QtCore, QtGui
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
            icon = Qt.QIcon(self.mainWindow.imagePath("edit.png"))
            editButton = QtWidgets.QPushButton(icon, "")
            editButton.clicked.connect(lambda checked,rid=recipe["id"]: self.openEdit(rid))
            recipeTitleContainer.layout().addWidget(editButton, 0)

            #title 
            recipeTitle = QtWidgets.QLabel(recipe["name"])
            recipeTitle.setFont(QtGui.QFont("Arial", 20, 2))
            recipeTitleContainer.layout().addWidget(recipeTitle, 1)

            #order button
            if recipe["available"]:
                icon = Qt.QIcon(self.mainWindow.imagePath("order.png"))
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

class Statistics(BarBotGui.View):
    def __init__(self, _mainWindow: BarBotGui.MainWindow):
        super().__init__(_mainWindow)
        containerLayout = QtWidgets.QVBoxLayout()
        self.setLayout(containerLayout)
        
        containerLayout.addWidget(QtWidgets.QLabel("Statistics"))

