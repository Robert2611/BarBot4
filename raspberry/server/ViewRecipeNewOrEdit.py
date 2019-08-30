from PyQt5 import QtWidgets, Qt, QtCore
import View
import BarBotMainWindow

class ViewRecipeNewOrEdit(View.View):
    def __init__(self, _mainWindow: BarBotMainWindow, recipe_id = None):
        super().__init__(_mainWindow)
        self.id = recipe_id
        if self.id != None:
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
            if self.id != None and i<len(self.recipeData["items"]):
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
        if self.id != None and not self.db.recipeChanged(self.id, name, items, instruction):
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
        page = ViewRecipeNewOrEdit(self.mainWindow, self.id)
        self.mainWindow.showPage(page)
        self.mainWindow.showMessage(message)

    