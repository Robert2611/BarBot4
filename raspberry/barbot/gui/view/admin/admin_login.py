from PyQt5 import QtWidgets, QtCore
from barbot.logic import RecipeCollection, BarBot
from .base import AdminView

class AdminLogin(AdminView):
    """Login for the admin area"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)
        self._entered_password = ""

        self._add_title_to_fixed_content("Admin Login")
        self._add_password_widget()
        self._add_numpad()

        self._add_dummy_widget_to_content()

    def _add_password_widget(self):
        self.password_widget = QtWidgets.QLabel()
        self.password_widget.setProperty("class", "PasswordBox")
        self.password_widget.setText(" ")
        self._content.layout().addWidget(self.password_widget)

    def _add_numpad(self):
        numpad = QtWidgets.QWidget()
        numpad.setLayout(QtWidgets.QGridLayout())
        self._content.layout().setAlignment(numpad, QtCore.Qt.AlignCenter)
        for y in range(0, 3):
            for x in range(0, 3):
                num = y * 3 + x + 1
                button = QtWidgets.QPushButton(str(num))
                button.setProperty("class", "NumpadButton")
                button.clicked.connect(
                    lambda checked, value=num: self._numpad_button_clicked(value))
                numpad.layout().addWidget(button, y, x)
        # clear
        button = QtWidgets.QPushButton("Clear")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self._clear_password())
        numpad.layout().addWidget(button, 3, 0)
        # zero
        button = QtWidgets.QPushButton("0")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self._numpad_button_clicked(0))
        numpad.layout().addWidget(button, 3, 1)
        # enter
        button = QtWidgets.QPushButton("Enter")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self._check_password())
        numpad.layout().addWidget(button, 3, 2)

        self._content.layout().addWidget(numpad, 1)

    def _update(self):
        self.password_widget.setText(
            "".join("*" for letter in self._entered_password))

    def _numpad_button_clicked(self, value):
        self._entered_password = self._entered_password + str(value)
        self._update()

    def _clear_password(self):
        self._entered_password = ""
        self._update()

    def _check_password(self):
        from .overview import Overview
        if self._entered_password == self.barbot_.config.admin_password:
            self.switch_view_trigger.emit(Overview(self.barbot_, self.recipes))
        self._clear_password()
