from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import os
import barbotgui
import logging
import platform
import sys
import barbot
from barbot import ingredients
from barbot import recipes
from barbot import statemachine
from barbot import UserMessages


def is_raspberry() -> bool:
    if platform.system() != "Linux":
        return False
    try:
        uname = getattr(os, "uname")
        name = uname().nodename
    except AttributeError:
        return False
    return "raspberry" in name


def set_no_spacing(layout):
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)


def css_path() -> str:
    script_dir = os.path.dirname(__file__)
    return os.path.join(script_dir, "asset")


def qt_icon_from_file_name(fileName) -> Qt.QIcon:
    script_dir = os.path.dirname(__file__)
    path = os.path.join(script_dir, "asset", fileName)
    return Qt.QIcon(path)


class Keyboard(QtWidgets.QWidget):
    _is_widgets_created = False
    _is_shift = False
    target: QtWidgets.QLineEdit = None

    def __init__(self, target: QtWidgets.QLineEdit, style=None):
        super().__init__()
        self.target = target
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.update_keys()
        self.setProperty("class", "Keyboard")
        if style is not None:
            self.setStyleSheet(style)
        if is_raspberry():
            self.setCursor(QtCore.Qt.BlankCursor)
        # move to bottom of the screen
        desktop = Qt.QApplication.desktop().availableGeometry()
        desired = Qt.QRect(Qt.QPoint(0, 0), self.sizeHint())
        desired.moveBottomRight(desktop.bottomRight())
        desired.setLeft(desktop.left())
        self.setGeometry(desired)

    def update_keys(self):
            # first row
        keys = [
            ["1", "!"], ["2", "\""], ["3", "§"], ["4", "$"], ["5", "%"],
            ["6", "&"], ["7", "/"], ["8", "("], ["9", ")"], ["0", "ß"]
        ]
        if not self._is_widgets_created:
            self.first_row = self.add_row([data[0] for data in keys])
        for index, data in enumerate(keys):
            self.first_row[index].setText(
                data[1] if self._is_shift else data[0])

            # second row
        keys = ["q", "w", "e", "r", "t", "z", "u", "i", "o", "p"]
        if not self._is_widgets_created:
            self.second_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.second_row[index].setText(
                str.upper(letter) if self._is_shift else letter)

            # third row
        keys = ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ö"]
        if not self._is_widgets_created:
            self.third_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.third_row[index].setText(
                str.upper(letter) if self._is_shift else letter)

        # fourth row
        keys = ["y", "x", "c", "v", "b", "n", "m", "ä", "ü"]
        if not self._is_widgets_created:
            self.fourth_row = self.add_row(keys)
        for index, letter in enumerate(keys):
            self.fourth_row[index].setText(
                str.upper(letter) if self._is_shift else letter)

        # last row
        if not self._is_widgets_created:
            row = QtWidgets.QWidget()
            row.setLayout(QtWidgets.QHBoxLayout())
            barbotgui.set_no_spacing(row.layout())
            # shift
            button = QtWidgets.QPushButton("▲")
            button.clicked.connect(lambda: self.button_clicked("shift"))
            row.layout().addWidget(button)
            # space
            button = QtWidgets.QPushButton(" ")
            button.clicked.connect(lambda: self.button_clicked(" "))
            row.layout().addWidget(button)
            # delete
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
            # reset shift state
            if self._is_shift:
                self._is_shift = False
                self.update_keys()

    def add_row(self, keys):
        res = []
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        barbotgui.set_no_spacing(row.layout())
        for letter in keys:
            button = QtWidgets.QPushButton(letter)
            button.clicked.connect(
                lambda checked, b=button: self.button_clicked(b.text()))
            res.append(button)
            row.layout().addWidget(button)
        self.layout().addWidget(row)
        return res


class MainWindow(QtWidgets.QMainWindow):
    recipe_filter: recipes.RecipeFilter
    _current_view = None
    _barbot_state_trigger = QtCore.pyqtSignal(statemachine.State)
    _mixing_progress_trigger = QtCore.pyqtSignal(int)
    _message_trigger = QtCore.pyqtSignal(barbot.UserMessages)
    _show_message_trigger = QtCore.pyqtSignal(str)
    _last_idle_view = None
    _keyboard: Keyboard = None
    _timer: QtCore.QTimer
    _admin_button_active = False

    def __init__(self):
        super().__init__()
        self.recipe_filter = recipes.RecipeFilter()
        self.recipe_filter.DESC = True

        self.center = QtWidgets.QWidget()
        self.setCentralWidget(self.center)

        self.setProperty("class", "MainWindow")
        self.styles = open(os.path.join(css_path(), 'main.qss')).read()
        self.styles = self.styles.replace(
            "#iconpath#", css_path().replace("\\", "/"))
        self.setStyleSheet(self.styles)

        self.mousePressEvent = lambda _: self.close_keyboard()

        # forward status changed
        self._barbot_state_trigger.connect(self.update_view)
        statemachine.on_state_changed = lambda state: self._barbot_state_trigger.emit(
            state)

        # forward message changed
        self._message_trigger.connect(self._busyview_update_message)
        statemachine.on_message_changed = lambda message: self._message_trigger.emit(
            message)

        # forward mixing progress changed
        self._mixing_progress_trigger.connect(self._busyview_set_progress)
        statemachine.on_mixing_progress_changed = lambda progress: self._mixing_progress_trigger.emit(
            progress)

        # make sure the message splash is created from gui thread
        self._show_message_trigger.connect(self._add_message_splash)

        # remove borders and title bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.center.setLayout(QtWidgets.QVBoxLayout())
        set_no_spacing(self.center.layout())

        # header
        header = QtWidgets.QWidget()
        header.setLayout(QtWidgets.QGridLayout())
        header.setProperty("class", "BarBotHeader")
        header.mousePressEvent = lambda e: self.header_clicked(e)
        self.center.layout().addWidget(header, 0)

        # content
        self._content_wrapper = QtWidgets.QWidget()
        self._content_wrapper.setLayout(QtWidgets.QGridLayout())
        set_no_spacing(self._content_wrapper.layout())
        self.center.layout().addWidget(self._content_wrapper, 1)

        self.update_view()
        self.setFixedSize(480, 800)
        # show fullscreen on raspberry
        if is_raspberry():
            self.showFullScreen()
            self.setCursor(QtCore.Qt.BlankCursor)
        else:
            self.show()

    def _busyview_set_progress(self, progress):
        # forward progress if the current view is a busyview
        if self._current_view is not None and isinstance(self._current_view, BusyView):
            self._current_view.set_progress(progress)

    def _busyview_update_message(self, message):
        # forward progress if the current view is a busyview
        if self._current_view is not None and isinstance(self._current_view, BusyView):
            self._current_view.update_message(message)

    def add_system_view(self, container):
        if container.layout() is None:
            container.setLayout(QtWidgets.QVBoxLayout())

        label = QtWidgets.QLabel("Software")
        container.layout().addWidget(label)
        # reopen software
        button = QtWidgets.QPushButton("Neu Starten")
        button.clicked.connect(lambda: self.restart_GUI())
        container.layout().addWidget(button)

        # close software
        button = QtWidgets.QPushButton("Schließen")
        button.clicked.connect(
            lambda: QtWidgets.QApplication.instance().quit())
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
        QtWidgets.QApplication.instance().quit()
        filepath = os.path.join(sys.path[0], "main.py")
        barbot.run_command(filepath)

    def _reset_admin_button(self):
        self._admin_button_active = False

    def header_clicked(self, _):
        if not self._admin_button_active:
            self._admin_button_active = True
            # reset the admin button after one second
            self._timer = QtCore.QTimer(self)
            self._timer.singleShot(1000, self._reset_admin_button)
            return
        if not statemachine.is_busy():
            from barbotgui.adminviews import AdminLogin
            self.set_view(AdminLogin(self))
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
        self._keyboard = Keyboard(target, self.styles)
        self._keyboard.show()

    def set_view(self, view):
        logging.debug("Set view: '%s'" % view.__class__.__name__)
        if self._current_view == view:
            logging.debug("View is allready set")
            return
        # remove existing item from window
        if self._current_view is not None:
            # switch from idle to busy?
            if isinstance(self._current_view, IdleView)\
                    and not isinstance(view, IdleView):
                # just remove it from the visuals
                self._current_view.setParent(None)
            else:
                # delete the view
                self._current_view.deleteLater()
        self._current_view = view
        # save the last used idle view
        if isinstance(view, IdleView):
            self._last_idle_view = view
        self._content_wrapper.layout().addWidget(self._current_view)

    def update_view(self, force_reload=False):
        if not statemachine.is_busy():
            if self._last_idle_view != self._current_view or self._last_idle_view is None or force_reload:
                if self._last_idle_view is None or force_reload:
                    from barbotgui.userviews import ListRecipes
                    self.set_view(ListRecipes(self))
                else:
                    self.set_view(self._last_idle_view)
        else:
            self.set_view(BusyView(self))

    def show_message(self, message: str):
        self._show_message_trigger.emit(message)

    def _add_message_splash(self, message):
        splash = QtWidgets.QSplashScreen()
        splash.showMessage(message, alignment=QtCore.Qt.AlignCenter)
        splash.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |
                              QtCore.Qt.FramelessWindowHint)
        splash.setProperty("class", "Splash")
        splash.setStyleSheet(self.styles)
        path = os.path.join(css_path(), "splash.png")
        splash.setPixmap(Qt.QPixmap(path))
        splash.show()
        QtCore.QTimer.singleShot(
            1000, lambda s=splash, window=self: s.finish(window))

    def combobox_amounts(self, selectedData=None):
        # add ingredient name
        wAmount = QtWidgets.QComboBox()
        wAmount.addItem("-", -1)
        wAmount.setCurrentIndex(0)
        for i in range(1, 17):
            wAmount.addItem(str(i), i)
            if i == selectedData:
                wAmount.setCurrentIndex(i)
            i = i+1
        return wAmount

    def combobox_ingredients(self, selectedData=None, only_available=False, special_ingredients=True):
        entries = ingredients.get(only_available, special_ingredients)
        # add ingredient name
        wIngredient = QtWidgets.QComboBox()
        wIngredient.addItem("-", None)
        wIngredient.setCurrentIndex(0)
        i = 1
        for item in entries:
            wIngredient.addItem(str(item.name), item)
            if item == selectedData:
                wIngredient.setCurrentIndex(i)
            i += 1
        return wIngredient


class View(QtWidgets.QWidget):
    window: MainWindow

    def __init__(self, window: MainWindow):
        super().__init__(window)
        self.window = window


class BusyView(View):
    _message = None

    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)

        self.setLayout(QtWidgets.QGridLayout())
        barbotgui.set_no_spacing(self.layout())

        centered = QtWidgets.QFrame()
        centered.setLayout(QtWidgets.QVBoxLayout())
        centered.setProperty("class", "CenteredContent")
        self.layout().addWidget(centered, 0, 0, QtCore.Qt.AlignCenter)

        self._title_label = QtWidgets.QLabel("")
        self._title_label.setAlignment(QtCore.Qt.AlignCenter)
        self._title_label.setProperty("class", "Headline")
        centered.layout().addWidget(self._title_label)

        self._content_container = QtWidgets.QWidget()
        self._content_container.setLayout(QtWidgets.QVBoxLayout())
        centered.layout().addWidget(self._content_container)

        self._message_container = QtWidgets.QWidget()
        self._message_container.setLayout(QtWidgets.QGridLayout())
        self._message_container.setVisible(False)
        centered.layout().addWidget(self._message_container)

        self._init_by_status()

        self.update_message(None)

    def update_message(self, message):
        if message is None:
            message = UserMessages.none
        # delete old message
        if self._message is not None:
            self._message.setParent(None)

        # if message is none show the content again
        if message == UserMessages.none:
            self._message_container.setVisible(False)
            self._content_container.setVisible(True)
            self._title_label.setVisible(True)
            return

        self._message = QtWidgets.QWidget()
        self._message.setLayout(QtWidgets.QVBoxLayout())
        self._message_container.layout().addWidget(self._message)

        message_label = QtWidgets.QLabel()
        self._message.layout().addWidget(message_label)

        buttons_container = QtWidgets.QWidget()
        buttons_container.setLayout(QtWidgets.QHBoxLayout())
        self._message.layout().addWidget(buttons_container)

        def add_button(text, result):
            button = QtWidgets.QPushButton(text)
            def callback(): return statemachine.set_user_input(result)
            button.clicked.connect(callback)
            buttons_container.layout().addWidget(button)

        if message == barbot.UserMessages.ingredient_empty:
            message_string = "Die Zutat '%s' ist leer.\n" % statemachine.current_recipe_item().ingredient.name
            message_string = message_string + "Bitte neue Flasche anschließen."
            message_label.setText(message_string)

            add_button("Cocktail abbrechen", False)
            add_button("Erneut versuchen", True)

        elif message == barbot.UserMessages.place_glas:
            message_label.setText("Bitte ein Glas auf die Plattform stellen.")

        elif message == barbot.UserMessages.mixing_done_remove_glas:
            if statemachine.was_aborted():
                message_label.setText("Cocktail abgebrochen!")
            else:
                if statemachine.current_recipe().post_instruction:
                    label = QtWidgets.QLabel("Zusätzliche Informationen:")
                    self._message.layout().addWidget(label)

                    instruction = QtWidgets.QLabel(
                        statemachine.current_recipe().post_instruction)
                    self._message.layout().addWidget(instruction)
                else:
                    text = "Der Cocktail ist fertig gemischt.\n" + \
                        "Du kannst ihn von der Platform nehmen."
                    message_label.setText(text)

        elif message == barbot.UserMessages.ask_for_straw:
            message_label.setText(
                "Möchtest du einen Strohhalm haben?")

            add_button("Ja", True)
            add_button("Nein", False)

        elif message == barbot.UserMessages.ask_for_ice:
            message_label.setText(
                "Möchtest du Eis in deinem Cocktail haben?")

            add_button("Ja", True)
            add_button("Nein", False)

        elif message == barbot.UserMessages.straws_empty:
            message_label.setText("Strohhalm konnte nicht hinzugefügt werden.")

            add_button("Egal", False)
            add_button("Erneut versuchen", True)

        elif message == barbot.UserMessages.cleaning_adapter:
            text = "Für die Reinigung muss der Reinigungsadapter angeschlossen sein.\n"
            text += "Ist der Adapter angeschlossen?"
            message_label.setText(text)

            add_button("Ja", True)
            add_button("Abbrechen", False)

        elif message == barbot.UserMessages.I2C_error:
            text = "Ein Kommunikationsfehler ist aufegtreten.\n"
            text += "Bitte überprüfe, ob alle Module richtig angeschlossen sind und versuche es erneut"
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessages.unknown_error:
            text = "Ein unbekannter Fehler ist aufgetreten.\n"
            text += "Weitere Informationen findest du im Log"
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessages.glas_removed_while_drafting:
            text = "Das Glas wurde während des Mischens entfernt!\n"
            text += "Drücke auf OK, um zum Start zurück zu fahren"
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessages.ice_empty:
            message_label.setText("Eis konnte nicht hinzugefügt werden.")

            add_button("Eis weg lassen", False)
            add_button("Erneut versuchen", True)

        elif message == barbot.UserMessages.crusher_cover_open:
            text = "Bitte den Deckel des Eiscrushers schließen!"
            message_label.setText(text)

            add_button("Eis weg lassen", False)
            add_button("Erneut versuchen", True)

        elif message == barbot.UserMessages.crusher_timeout:
            text = "Eis crushen hat zu lange gedauert, bitte überprüfe Crusher und Akku"
            message_label.setText(text)

            add_button("Eis weg lassen", False)
            add_button("Erneut versuchen", True)

        elif message == barbot.UserMessages.board_not_connected_balance:
            text = "Waage konnte nicht gefunden werden. Bitte Verbindung überprüfen."
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessages.board_not_connected_crusher:
            text = "Eis Crusher konnte nicht gefunden werden. Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessages.board_not_connected_mixer:
            text = "Mixer konnte nicht gefunden werden. Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", True)

        elif message == barbot.UserMessages.board_not_connected_straw:
            text = "Strohhalm dispenser konnte nicht gefunden werden. Bitte Verbindung überprüfen oder deaktivieren."
            message_label.setText(text)

            add_button("OK", True)

        self._message_container.setVisible(True)
        self._content_container.setVisible(False)
        self._title_label.setVisible(False)

    def set_progress(self, progress):
        for i, widget in enumerate(self.recipe_list_widgets):
            if progress is not None and i < progress:
                icon = barbotgui.qt_icon_from_file_name("done.png")
            elif progress is not None and i == progress:
                icon = barbotgui.qt_icon_from_file_name(
                    "processing.png")
            else:
                icon = barbotgui.qt_icon_from_file_name("queued.png")
            widget.setPixmap(icon.pixmap(icon.availableSizes()[0]))

    def _init_by_status(self):
        # content
        if statemachine.get_state() == statemachine.State.mixing:

            # ingredients
            recipe_items_list = QtWidgets.QWidget()
            recipe_items_list.setLayout(QtWidgets.QGridLayout())
            recipe_items_list.setProperty("class", "IngredientToDoList")
            self._content_container.layout().addWidget(recipe_items_list)
            self.recipe_list_widgets = []
            self._row_index = 0

            def add_widget(name):
                widget_item = QtWidgets.QLabel()
                self.recipe_list_widgets.append(widget_item)
                recipe_items_list.layout().addWidget(widget_item, self._row_index, 0)
                recipe_items_list.layout().addWidget(QtWidgets.QLabel(name), self._row_index, 1)
                self._row_index += 1

            for item in statemachine.current_recipe().items:
                add_widget(item.ingredient.name)

            if statemachine.add_straw:
                add_widget("Strohhalm")
            if statemachine.add_ice:
                add_widget("Eis")

            self.set_progress(0)

            # buttons
            button = QtWidgets.QPushButton("Abbrechen")
            button.clicked.connect(lambda: statemachine.abort_mixing())
            self._content_container.layout().addWidget(button)

            self._title_label.setText(
                "'%s'\nwird gemischt." % statemachine.current_recipe().name)

        elif statemachine.get_state() == statemachine.State.cleaning:
            self._title_label.setText("Reinigung")
        elif statemachine.get_state() == statemachine.State.connecting:
            self._title_label.setText("Stelle Verbindung her")
        elif statemachine.get_state() == statemachine.State.searching:
            self._title_label.setText("Suche nach BarBots in der Nähe")
        elif statemachine.get_state() == statemachine.State.cleaning_cycle:
            self._title_label.setText("Reinigung (Zyklus)")
        elif statemachine.get_state() == statemachine.State.single_ingredient:
            self._title_label.setText("Dein Nachschlag wird hinzugefügt")
        elif statemachine.get_state() == statemachine.State.startup:
            self._title_label.setText("Starte BarBot, bitte warten")
        elif statemachine.get_state() == statemachine.State.crushing:
            self._title_label.setText("Eis wird hinzugefügt")
        elif statemachine.get_state() == statemachine.State.straw:
            self._title_label.setText("Strohhalm wird hinzugefügt")
        else:
            self._title_label.setText(
                "Unknown status: %s" % statemachine.get_state())


class IdleView(View):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        from barbotgui.userviews import ListRecipes, RecipeNewOrEdit, SingleIngredient, Statistics
        self.navigation_items = [
            ["Liste", ListRecipes],
            ["Neu", RecipeNewOrEdit],
            ["Nachschlag", SingleIngredient],
            ["Statistik", Statistics],
        ]
        self.setLayout(QtWidgets.QVBoxLayout())
        barbotgui.set_no_spacing(self.layout())

        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header)

        # navigation
        self.navigation = QtWidgets.QWidget()
        self.layout().addWidget(self.navigation)
        self.navigation.setLayout(QtWidgets.QHBoxLayout())

        for text, _class in self.navigation_items:
            button = QtWidgets.QPushButton(text)
            def btn_click(checked, c=_class): return self.window.set_view(
                c(self.window))
            button.clicked.connect(btn_click)
            self.navigation.layout().addWidget(button, 1)

        # content
        content_wrapper = QtWidgets.QWidget()
        self.layout().addWidget(content_wrapper, 1)
        content_wrapper.setLayout(QtWidgets.QGridLayout())
        barbotgui.set_no_spacing(content_wrapper.layout())

        # fixed content
        self._fixed_content = QtWidgets.QWidget()
        content_wrapper.layout().addWidget(self._fixed_content)

        scroller = QtWidgets.QScrollArea()
        scroller.setProperty("class", "ContentScroller")
        scroller.setWidgetResizable(True)
        scroller.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        content_wrapper.layout().addWidget(scroller)

        QtWidgets.QScroller.grabGesture(
            scroller.viewport(), QtWidgets.QScroller.LeftMouseButtonGesture
        )

        self._content = QtWidgets.QWidget()
        self._content.setProperty("class", "IdleContent")
        scroller.setWidget(self._content)