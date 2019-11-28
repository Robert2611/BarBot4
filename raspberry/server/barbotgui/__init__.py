from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import barbot
import os
import barbotgui
import logging

def set_no_spacing(layout):
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)

def css_path():
    script_dir = os.path.dirname(__file__)
    return os.path.join(script_dir, "asset")

def qt_icon_from_file_name(fileName):
    script_dir = os.path.dirname(__file__)
    path = os.path.join(script_dir, "asset", fileName)
    return Qt.QIcon(path)


class Keyboard(QtWidgets.QWidget):
    _is_widgets_created = False
    _is_shift = False
    target: QtWidgets.QLineEdit = None
    def __init__(self, target: QtWidgets.QLineEdit):
        super().__init__()
        self.target = target
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.update_keys()
        #move to bottom of the screen
        desktop = Qt.QApplication.desktop().availableGeometry()
        desired = Qt.QRect(Qt.QPoint(0,0), self.sizeHint())
        desired.moveBottomRight(desktop.bottomRight())
        desired.setLeft(desktop.left())
        self.setGeometry(desired)

    def update_keys(self):
	    #first row
        keys = [
            ["1","!"],["2","\""],["3","§"],["4","$"],["5","%"],
            ["6","&"],["7","/"],["8","("],["9",")"],["0","ß"]
        ]
        if not self._is_widgets_created:
            self.first_row = self.add_row([data[0] for data in keys])
        for index, data in enumerate(keys):
            self.first_row[index].setText(data[1] if self._is_shift else data[0])

	    #second row
        keys = ["q","w","e","r","t","z","u","i","o","p"]
        if not self._is_widgets_created:
            self.second_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.second_row[index].setText(str.upper(letter) if self._is_shift else letter)
        
	    #third row
        keys = ["a","s","d","f","g","h","j","k","l","ö"]
        if not self._is_widgets_created:
            self.third_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.third_row[index].setText(str.upper(letter) if self._is_shift else letter)

        #fourth row
        keys = ["y","x","c","v","b","n","m","ä","ü"]
        if not self._is_widgets_created:
            self.fourth_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.fourth_row[index].setText(str.upper(letter) if self._is_shift else letter)
        
        #last row
        if not self._is_widgets_created:
            row = QtWidgets.QWidget()
            row.setLayout(QtWidgets.QHBoxLayout())
            barbotgui.set_no_spacing(row.layout())
            #shift
            button = QtWidgets.QPushButton("▲")
            button.clicked.connect(lambda: self.button_clicked("shift"))
            row.layout().addWidget(button)
            #space
            button = QtWidgets.QPushButton(" ")
            button.clicked.connect(lambda: self.button_clicked(" "))
            row.layout().addWidget(button)
            #delete
            button = QtWidgets.QPushButton("←")
            button.clicked.connect(lambda: self.button_clicked("delete"))
            row.layout().addWidget(button)
            self.layout().addWidget(row)

        self._is_widgets_created = True

    def button_clicked(self, content):
        if self.target is None:
            return
        if content == "shift":
            self._is_shift = not self._is_shift
            self.update_keys()
        else:
            if content == "delete":
                self.target.setText(self.target.text()[:-1])
            else:
                self.target.setText(self.target.text() + content)
            #reset shift state
            if self._is_shift:
                self._is_shift = False
                self.update_keys()

    def add_row(self, keys):
        res =  []
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        barbotgui.set_no_spacing(row.layout())
        for letter in keys:
            button = QtWidgets.QPushButton(letter)
            button.clicked.connect(lambda checked, b=button: self.button_clicked(b.text()))
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res

class MainWindow(QtWidgets.QWidget):
    db:barbot.Database
    bot:barbot.StateMachine    
    _current_view = None
    _barbot_state_trigger = QtCore.pyqtSignal()
    _last_idle_view = None
    _keyboard: Keyboard = None
    is_admin = False
    _admin_password = ""
    
    def __init__(self, _db:barbot.Database, _bot:barbot.StateMachine, _admin_password):
        super().__init__()
        import barbotgui.views
        self.db = _db
        self.bot = _bot
        self._admin_password = _admin_password

        styles = open(os.path.join(css_path(), 'main.qss')).read()
        styles = styles.replace("#iconpath#", css_path().replace("\\","\\\\"))
        self.setStyleSheet(styles)

        self.mousePressEvent = lambda event: self.close_keyboard()

        #forward status changed
        self._barbot_state_trigger.connect(self.update_view)
        self.bot.on_state_changed = lambda: self._barbot_state_trigger.emit()

        #remove borders and title bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.setLayout(QtWidgets.QVBoxLayout())
        #header
        header = QtWidgets.QWidget()
        header.setLayout(QtWidgets.QGridLayout())
        self.layout().addWidget(header, 0)

        label = QtWidgets.QLabel("Bar-Bot 4.0")
        label.setProperty("class", "BarBotHeader")
        label.mouseDoubleClickEvent = lambda e: self.header_clicked(e)
        header.layout().addWidget(label, 0, 0, QtCore.Qt.AlignCenter)

        #content
        self._content_wrapper = QtWidgets.QWidget()
        self._content_wrapper.setLayout(QtWidgets.QGridLayout())
        self._content_wrapper.layout().setSpacing(0)
        self._content_wrapper.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(self._content_wrapper, 1)

        self.update_view()
        self.setFixedSize(480, 800)
        #show fullscreen on raspberry
        if "rasp" in os.name:
            self.showFullScreen()
            self.setCursor(QtCore.Qt.BlankCursor)
        else:
            self.show()

    def add_system_view(self, container):
        if container.layout() is None:
            container.setLayout(QtWidgets.QVBoxLayout())

        # title
        title = QtWidgets.QLabel("System")
        title.setProperty("class", "Headline")
        container.layout().setAlignment(title, QtCore.Qt.AlignTop)
        container.layout().addWidget(title)

        label = QtWidgets.QLabel("Software")
        container.layout().addWidget(label)
        # reopen software
        button = QtWidgets.QPushButton("Neu Starten")
        button.clicked.connect(lambda: self.restart_GUI())
        container.layout().addWidget(button)

        # close software
        button = QtWidgets.QPushButton("Schließen")
        button.clicked.connect(lambda: self.window.close())
        container.layout().addWidget(button)

        label = QtWidgets.QLabel("PI")
        container.layout().addWidget(label)

        # shutdown
        button = QtWidgets.QPushButton("Herunterfahren")
        button.clicked.connect(lambda: barbot.run_command("sudo shutdown now"))
        container.layout().addWidget(button)

        # reboot
        button = QtWidgets.QPushButton("Neu Starten")
        button.clicked.connect(lambda: barbot.run_command("sudo reboot"))
        container.layout().addWidget(button)

        # dummy
        container.layout().addWidget(QtWidgets.QWidget(), 1)

    def restart_GUI(self):
        self.window.close()
        barbot.run_command("python3 /home/pi/bar_bot/server/main.py")

    def header_clicked(self, e):
        if self.bot.state == barbot.State.idle:
            if self.is_admin:
                self.is_admin = False
                self.update_view(True)
            else:
                self.set_view(barbotgui.views.AdminLogin(self))
        else:
            view = QtWidgets.QWidget()
            self.add_system_view(view)           
            self.set_view(view)

    def close_keyboard(self):
        if self._keyboard is not None:
            self._keyboard.close()
            self._keyboard = None
    
    def open_keyboard(self, target: QtWidgets.QLineEdit):
        if self._keyboard is not None:
            self._keyboard.close()
        self._keyboard = Keyboard(target)
        self._keyboard.show()

    def set_view(self, view):
        logging.debug("Set view: '%s'" % view.__class__.__name__)
        if self._current_view == view:
            logging.debug("View is allready set")
            return
        #remove existing item from window
        if self._current_view is not None:
            #switch from idle to busy?
            if isinstance(self._current_view, barbotgui.views.IdleView)\
                and not isinstance(view, barbotgui.views.IdleView):
                #just remove it from the visuals
                self._current_view.setParent(None)
            else:
                #delete the view
                self._current_view.deleteLater()
        self._current_view = view
        #save the last used idle view        
        if isinstance(view, barbotgui.views.IdleView):
            self._last_idle_view = view
        self._content_wrapper.layout().addWidget(self._current_view)

    def update_view(self, force_reload = False):
        if self.bot.state == barbot.State.idle:
            if self.is_admin:
                self.set_view(barbotgui.views.AdminLogin(self))
            elif self._last_idle_view != self._current_view or self._last_idle_view is None or force_reload:
                if self._last_idle_view is None or force_reload:
                    self.set_view(barbotgui.views.ListRecipes(self))
                else:
                    self.set_view(self._last_idle_view)
        else:
            self.set_view(barbotgui.views.BusyView(self))

    def show_message(self, message):
        splash = QtWidgets.QLabel(message, flags=QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.FramelessWindowHint)
        splash.show()
        QtCore.QTimer.singleShot(1000, lambda splash=splash: splash.close())

    def combobox_amounts(self, selectedData = None):
        #add ingredient name
        wAmount = QtWidgets.QComboBox()
        wAmount.addItem("-", -1)
        wAmount.setCurrentIndex(0)
        for i in range(1, 17):
            wAmount.addItem(str(i), i)
            if i == selectedData:
                wAmount.setCurrentIndex(i)
            i = i+1
        return wAmount

    def combobox_ingredients(self, selectedData = None):
        ing = self.db.list_ingredients().values()
        #add ingredient name
        wIngredient = QtWidgets.QComboBox()
        wIngredient.addItem("-", -1)
        wIngredient.setCurrentIndex(0)
        i = 1
        for item in ing:
            wIngredient.addItem(str(item["name"]), item["id"])
            if item["id"] == selectedData:
                wIngredient.setCurrentIndex(i)
            i = i+1
        return wIngredient

class View(QtWidgets.QWidget):
    window: MainWindow
    dab: barbot.Database
    bot: barbot.StateMachine

    def __init__(self, window: MainWindow):
        super().__init__(window)
        self.window = window
        self.db = window.db
        self.bot = window.bot

