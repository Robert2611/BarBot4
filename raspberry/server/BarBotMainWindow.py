from PyQt5.QtWidgets import QWidget, QApplication, QLayout, QVBoxLayout, QLabel, QScrollArea, QGridLayout
from PyQt5.QtWidgets import  QPushButton, QSizePolicy, QSizePolicy, QHBoxLayout, QGroupBox, QLayoutItem
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon, QFont
from database import database

class BarBotMainWindow(QWidget):

    db:database

    def __init__(self, _db:database):
        super().__init__()
        self.db = _db
        self.pages = {
            "Liste" : self.fillContentWithList,
            "Neu" : self.fillContentWithNewRecipe,
            "Nachschlag" : self.fillContentWithSingleIngredient,
            "Statistik" : self.fillContentWithStatistics
        }
        self.setupUi()

    def clear(self, item):
        if isinstance(item, QLayout):
            layout = item
        elif isinstance(item, QWidget):
            layout = item.layout()
        for i in reversed(range(layout.count())): 
            layout.itemAt(i).widget().setParent(None)
        
    def setupUi(self):                
        # remove borders and title bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(480, 800)
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.header = QWidget()
        layout.addWidget(self.header)

        #navigation
        self.navigation = QWidget()
        layout.addWidget(self.navigation)

        #content
        contentWrapper = QWidget()
        layout.addWidget(contentWrapper, 1)

        layout = QGridLayout()
        contentWrapper.setLayout(layout)

        scroller = QScrollArea()
        scroller.setWidgetResizable(True)
        scroller.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(scroller)

        self.contentWrapper =  QWidget()
        self.contentWrapper.setLayout(QGridLayout())
        scroller.setWidget(self.contentWrapper)

        #fill the parts
        self.fillHeader()
        self.fillContentWithList()
        self.fillNavigation()

        self.show()

    def fillHeader(self):
        headerLayout = QGridLayout()
        self.header.setLayout(headerLayout)

        label = QLabel("Bar-Bot 4.0")
        label.setFont(QFont("Arial", 20, 2))
        headerLayout.addWidget(label, 0, 0, Qt.AlignCenter)

        icon = QIcon("../gui/css/admin.png")
        button = QPushButton(icon, "")
        headerLayout.addWidget(button, 0, 0, Qt.AlignRight)


    def fillContentWithList(self):
        content = QWidget()
        self.contentWrapper.layout().addWidget(content)

        container_layout = QVBoxLayout()
        content.setLayout(container_layout)

        recipes = self.db.getRecipes()
        for recipe in recipes:
            recipeBox = QGroupBox(recipe["name"])
            container_layout.addWidget(recipeBox)

            recipeBoxLayout = QGridLayout()
            recipeBox.setLayout(recipeBoxLayout)

            recipeItemsContainer = QWidget()
            recipeBoxLayout.addWidget(recipeItemsContainer, 0, 0)
            recipeItemsContainerLayout = QVBoxLayout()
            recipeItemsContainer.setLayout(recipeItemsContainerLayout)

            for item in recipe["items"]:
                label = QLabel("%i cl %s" % (item["amount"], item["name"]))
                recipeItemsContainerLayout.addWidget(label)
    
    def fillContentWithNewRecipe(self):
        self.clear(self.contentWrapper)

        label = QLabel("New")
        self.contentWrapper.layout().addWidget(label)
    
    def fillContentWithSingleIngredient(self):
        print("single")

    def fillContentWithStatistics(self):
        print("statistics")
    
    def fillNavigation(self):
        #self.navigation.setStyleSheet("QWidget { background: blue; }")
        layout = QHBoxLayout()
        self.navigation.setLayout(layout)
        for text, method in self.pages.items():
            button = QPushButton(text)
            layout.addWidget(button)
            button.clicked.connect(method)