from PyQt5 import QtWidgets, Qt, QtCore
from database import database
from ViewListRecipes import ViewListRecipes
from ViewRecipeNewOrEdit import ViewRecipeNewOrEdit
from ViewSingleIngredient import ViewSingleIngredient
from ViewStatistics import ViewStatistics

class BarBotMainWindow(QtWidgets.QWidget):

    db:database

    def __init__(self, _db:database):
        super().__init__()
        self.db = _db
        self.pages = {
            "Liste" : lambda: self.showPage(ViewListRecipes(self.db.getRecipes())),
            "Neu" : lambda: self.showPage(ViewRecipeNewOrEdit(self.db)),
            "Nachschlag" : lambda: self.showPage(ViewSingleIngredient()),
            "Statistik" : lambda: self.showPage(ViewStatistics(None))
        }
        self.setupUi()

    def showPage(self, pageNameOrWidget):
        if self.scroller.widget() != None:
            self.scroller.widget().setParent(None)
        self.scroller.setWidget(pageNameOrWidget)

    def clear(self, item):
        if isinstance(item, QtWidgets.QLayout):
            layout = item
        elif isinstance(item, QtWidgets.QWidget):
            layout = item.layout()
        for i in reversed(range(layout.count())): 
            layout.itemAt(i).widget().setParent(None)
        
    def setupUi(self):                
        # remove borders and title bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(480, 800)
        
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.header = QtWidgets.QWidget()
        layout.addWidget(self.header)

        #navigation
        self.navigation = QtWidgets.QWidget()
        layout.addWidget(self.navigation)

        #content
        contentWrapper = QtWidgets.QWidget()
        layout.addWidget(contentWrapper, 1)

        layout = QtWidgets.QGridLayout()
        contentWrapper.setLayout(layout)

        self.scroller = QtWidgets.QScrollArea()
        self.scroller.setWidgetResizable(True)
        self.scroller.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        layout.addWidget(self.scroller)

        #fill the parts
        self.fillHeader()
        self.showPage(ViewListRecipes(self.db.getRecipes()))
        self.fillNavigation()

        self.show()

    def fillHeader(self):
        headerLayout = QtWidgets.QGridLayout()
        self.header.setLayout(headerLayout)

        label = QtWidgets.QLabel("Bar-Bot 4.0")
        label.setFont(Qt.QFont("Arial", 20, 2))
        headerLayout.addWidget(label, 0, 0, QtCore.Qt.AlignCenter)

        icon = Qt.QIcon("../gui/css/admin.png")
        button = QtWidgets.QPushButton(icon, "")
        headerLayout.addWidget(button, 0, 0, QtCore.Qt.AlignRight)
        
    def fillNavigation(self):
        #self.navigation.setStyleSheet("QWidget { background: blue; }")
        layout = QtWidgets.QHBoxLayout()
        self.navigation.setLayout(layout)
        for text, method in self.pages.items():
            button = QtWidgets.QPushButton(text)
            layout.addWidget(button)
            button.clicked.connect(method)