from PyQt5 import QtWidgets, Qt, QtCore

class ViewListRecipes(QtWidgets.QWidget):
    def __init__(self, recipes):
        super().__init__()
        container_layout = QtWidgets.QVBoxLayout()
        self.setLayout(container_layout)
        
        for recipe in recipes:
            #groupbox for each recipe
            recipeBox = QtWidgets.QGroupBox(recipe["name"])
            container_layout.addWidget(recipeBox)   
            recipeBoxLayout = QtWidgets.QGridLayout()
            recipeBox.setLayout(recipeBoxLayout)
            
            #items container for holding the recipe items
            recipeItemsContainer = QtWidgets.QWidget()
            recipeBoxLayout.addWidget(recipeItemsContainer, 0, 0)
            recipeItemsContainerLayout = QtWidgets.QVBoxLayout()
            recipeItemsContainer.setLayout(recipeItemsContainerLayout)

            #add items
            for item in recipe["items"]:
                label = QtWidgets.QLabel("%i cl %s" % (item["amount"], item["name"]))
                recipeItemsContainerLayout.addWidget(label)