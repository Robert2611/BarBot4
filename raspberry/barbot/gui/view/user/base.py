from PyQt5 import QtWidgets, QtCore
from barbot.logic import RecipeCollection, BarBot
from ...core import set_no_spacing
from ..base import View

class UserView(View):
    """Base class for all user views"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)

        from .list_recipes import ListRecipes
        from .recipe_new_or_edit import RecipeNewOrEdit
        from .single_ingredient import SingleIngredient
        from .statistics import Statistics

        self.navigation_items = [
            ["Liste", ListRecipes],
            ["Neu", RecipeNewOrEdit],
            ["Nachschlag", SingleIngredient],
            ["Statistik", Statistics],
        ]
        self.setLayout(QtWidgets.QVBoxLayout())
        set_no_spacing(self.layout())

        self.__add_header()
        self.__add_navigation()

        content_wrapper = QtWidgets.QWidget()
        self.layout().addWidget(content_wrapper, 1)
        content_wrapper.setLayout(QtWidgets.QGridLayout())
        set_no_spacing(content_wrapper.layout())

        self.__add_fixed_content_to(content_wrapper)
        self.__add_scroller_and_content_to(content_wrapper)

    def __add_scroller_and_content_to(self, content_wrapper):
        scroller = QtWidgets.QScrollArea()
        scroller.setProperty("class", "ContentScroller")
        scroller.setWidgetResizable(True)
        scroller.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        content_wrapper.layout().addWidget(scroller)

        QtWidgets.QScroller.grabGesture(
            scroller.viewport(),
            QtWidgets.QScroller.LeftMouseButtonGesture
        )

        self._content = QtWidgets.QWidget()
        self._content.setProperty("class", "IdleContent")
        scroller.setWidget(self._content)

    def __add_fixed_content_to(self, content_wrapper):
        self._fixed_content = QtWidgets.QWidget()
        content_wrapper.layout().addWidget(self._fixed_content)

    def __add_header(self):
        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header)

    def __add_navigation(self):
        self.navigation = QtWidgets.QWidget()
        self.layout().addWidget(self.navigation)
        self.navigation.setLayout(QtWidgets.QHBoxLayout())

        for text, _class in self.navigation_items:
            button = QtWidgets.QPushButton(text)
            def btn_click(_, c=_class):
                return self.switch_view_trigger.emit(c(self.barbot_, self.recipes))
            button.clicked.connect(btn_click)
            self.navigation.layout().addWidget(button, 1)

    def _add_title_to_fixed_content(self, title_name):
        title = QtWidgets.QLabel(title_name)
        title.setProperty("class", "Headline")
        self._fixed_content.layout().setAlignment(title, QtCore.Qt.AlignTop)
        self._fixed_content.layout().addWidget(title)

    def _add_dummy_widget_to_content(self):
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)
