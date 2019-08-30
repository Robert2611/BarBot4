from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import View
import BarBotMainWindow
import ViewRecipeNewOrEdit

class ViewListRecipes(View.View):
    def __init__(self, _mainWindow: BarBotMainWindow):
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
        page = ViewRecipeNewOrEdit.ViewRecipeNewOrEdit(self.mainWindow, id)
        self.mainWindow.showPage(page)
    
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