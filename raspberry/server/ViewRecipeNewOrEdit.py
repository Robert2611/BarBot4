from PyQt5 import QtWidgets, Qt, QtCore
from database import database

class ViewRecipeNewOrEdit(QtWidgets.QWidget):
    db:database
    def __init__(self, db, recipe_id = None):
        super().__init__()
        self.db = db
        containerLayout = QtWidgets.QVBoxLayout()
        self.setLayout(containerLayout)

        self.NameWidget = QtWidgets.QLineEdit()
        self.InfoWidget = QtWidgets.QLineEdit()
        self.IngredientsContainer = QtWidgets.QWidget()
        self.IngredientsContainer.setLayout(QtWidgets.QGridLayout())
        self.SafeButton = QtWidgets.QPushButton("Speichern")

        containerLayout.addWidget(QtWidgets.QLabel("Name:"))
        containerLayout.addWidget(self.NameWidget)
        containerLayout.addWidget(QtWidgets.QLabel("Zusatzinfo:"))
        containerLayout.addWidget(self.InfoWidget)
        containerLayout.addWidget(QtWidgets.QLabel("Zutaten:"))
        containerLayout.addWidget(self.IngredientsContainer, 1)
        containerLayout.addWidget(self.SafeButton)

        self.ComboBoxItemsAmount = [{"data":i, "display": str(i)} for i in range(16)]
        self.ComboBoxItemsIngredients = [{"data":item["id"], "display": item["name"]} for item in self.db.getAllIngredients().values()]

        self.IngredientWidgets = []
        for i in range(12):
            wIngredient = QtWidgets.QComboBox()
            for row in self.ComboBoxItemsIngredients:
                wIngredient.addItem(row["display"], row["data"])
            self.IngredientsContainer.layout().addWidget(wIngredient, i, 0)
            wAmount = QtWidgets.QComboBox()
            for row in self.ComboBoxItemsAmount:
                wAmount.addItem(row["display"], row["data"])
            self.IngredientsContainer.layout().addWidget(wAmount, i, 1)
            self.IngredientWidgets.append({"ingredient": wIngredient, "amount": wAmount})
    