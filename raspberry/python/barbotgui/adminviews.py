from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import barbotgui
from barbotgui import IdleView
from barbot import botconfig
from barbot import statemachine
from barbot import communication
from barbot import ports
from barbot import recipes
from barbot import directories


class AdminLogin(IdleView):
    _entered_password = ""

    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        # title
        title = QtWidgets.QLabel("Admin Login")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # edit
        self.password_widget = QtWidgets.QLabel()
        self.password_widget.setProperty("class", "PasswordBox")
        self.password_widget.setText(" ")
        self._content.layout().addWidget(self.password_widget)

        # numpad
        numpad = QtWidgets.QWidget()
        numpad.setLayout(QtWidgets.QGridLayout())
        self._content.layout().setAlignment(numpad, QtCore.Qt.AlignCenter)
        for y in range(0, 3):
            for x in range(0, 3):
                num = y * 3 + x + 1
                button = QtWidgets.QPushButton(str(num))
                button.setProperty("class", "NumpadButton")
                button.clicked.connect(
                    lambda checked, value=num: self.numpad_button_clicked(value))
                numpad.layout().addWidget(button, y, x)
        # clear
        button = QtWidgets.QPushButton("Clear")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self.clear_password())
        numpad.layout().addWidget(button, 3, 0)
        # zero
        button = QtWidgets.QPushButton("0")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self.numpad_button_clicked(0))
        numpad.layout().addWidget(button, 3, 1)
        # enter
        button = QtWidgets.QPushButton("Enter")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self.check_password())
        numpad.layout().addWidget(button, 3, 2)

        self._content.layout().addWidget(numpad, 1)
        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

    def _update(self):
        self.password_widget.setText(
            "".join("*" for letter in self._entered_password))

    def numpad_button_clicked(self, value):
        self._entered_password = self._entered_password + str(value)
        self._update()

    def clear_password(self):
        self._entered_password = ""
        self._update()

    def check_password(self):
        if self._entered_password == botconfig.admin_password:
            self.window.set_view(Overview(self.window))
        self.clear_password()


class Overview(IdleView):
    _is_deleted = False

    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        # title
        title = QtWidgets.QLabel("Übersicht")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # admin navigation
        self.admin_navigation = QtWidgets.QWidget()
        self.admin_navigation.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(self.admin_navigation)

        admin_navigation_items = [
            ["System", System],
            ["Positionen", Ports],
            ["Einstellungen", Settings],
            ["Reinigung", Cleaning],
            ["Cocktails Löschen", RemoveRecipe],
            ["Waage kalibrieren", BalanceCalibration]
        ]
        columns = 1
        column = 0
        row = 0
        for text, _class in admin_navigation_items:
            button = QtWidgets.QPushButton(text)
            def btn_click(checked, c=_class): return self.window.set_view(
                c(self.window))
            button.clicked.connect(btn_click)
            self.admin_navigation.layout().addWidget(button, row, column)
            column += 1
            if column >= columns:
                column = 0
                row += 1

        self.boards = [
            [communication.Boards.balance, "balance.png"],
            [communication.Boards.straw, "straw.png"],
            [communication.Boards.crusher, "ice.png"],
            [communication.Boards.mixer, "stir.png"],
            [communication.Boards.sugar, "sugar.png"]
        ]
        self._board_widgets = {}
        row = 1
        # wrapper
        wrapper = QtWidgets.QWidget()
        wrapper.setProperty("class", "Boards")
        wrapper.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(wrapper)
        for board, icon in self.boards:
            connected = board in statemachine._connected_boards
            # board icon
            icon = barbotgui.qt_icon_from_file_name(icon)
            button_board_icon = QtWidgets.QPushButton(icon, "")
            button_board_icon.setProperty("class", "IconPresenter")
            button_board_icon.setEnabled(connected)
            wrapper.layout().addWidget(button_board_icon, row, 0, 1, 1)
            # connected / disconnected icon
            icon = barbotgui.qt_icon_from_file_name(
                "plug-on.png" if connected else "plug-off.png")
            button = QtWidgets.QPushButton(icon, "")
            button.setProperty("class", "IconPresenter")
            button.setEnabled(connected)
            wrapper.layout().addWidget(button, row, 1, 1, 1)

            self._board_widgets[board] = [button_board_icon, button]

            if board == communication.Boards.balance:
                # weight label
                self._weight_label = QtWidgets.QLabel()
                wrapper.layout().addWidget(self._weight_label, row, 2, 1, 3)
            row += 1
        # dummy
        wrapper.layout().addWidget(QtWidgets.QWidget(), 0, 0)
        wrapper.layout().addWidget(QtWidgets.QWidget(), row, 0)
        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)
        
        # title
        version_label = QtWidgets.QLabel(f"Version: {directories.version}")
        self._content.layout().addWidget(version_label)

        # Timer for updating the current weight display
        self._update_timer = QtCore.QTimer(self)
        self._update_timer.timeout.connect(
            lambda: statemachine.get_weight(self.set_weight_label))
        self._update_timer.start(500)

        statemachine.get_weight(self.set_weight_label)

    def set_weight_label(self, weight):
        weight = weight if weight is not None else "-"
        text = "Gewicht: {} g".format(weight)
        try:
            # this would cause a problem if the label was allready deleted
            self._weight_label.setText(text)
        except:
            pass

    def set_boards_enabled(self, connected_boards):
        try:
            for board, icon in self.boards:
                connected = board in connected_boards
                for widget in self._board_widgets[board]:
                    # this would cause a problem if the label was allready deleted
                    widget.setEnabled(connected)
        except:
            pass


class Ports(IdleView):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # title
        title = QtWidgets.QLabel("Positionen")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(Overview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # table
        table = QtWidgets.QWidget()
        table.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(table)
        # fill table
        self._ingredient_widgets = dict()
        for i in range(12):
            label = QtWidgets.QLabel("Position %i" % (i+1))
            table.layout().addWidget(label, i, 0)
            selectedPort = ports.List[i] if i in ports.List.keys() else 0
            cbPort = self.window.combobox_ingredients(selectedPort, only_normal=True)
            self._ingredient_widgets[i] = cbPort
            table.layout().addWidget(cbPort, i, 1)

        # save button
        button = QtWidgets.QPushButton("Speichern")
        button.clicked.connect(lambda: self._save())
        self._content.layout().addWidget(button)
        self._content.layout().setAlignment(button, QtCore.Qt.AlignCenter)

        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

    def _save(self):
        new_ports = {}
        for port, cb in self._ingredient_widgets.items():
            new_ports[port] = cb.currentData()
        # check for duplicates
        not_none_entries = [
            ing for ing in new_ports.values() if ing is not None]
        if len(not_none_entries) != len(set(not_none_entries)):
            self.window.show_message(
                "Jede Zutat darf nur einer\nPosition zugewiesen werden!")
            return
        # update the ports list and save it
        ports.List.update(new_ports)
        ports.save()
        self.window.show_message("Positionen wurden gespeichert.")


class BalanceCalibration(IdleView):
    _tare_and_calibrate = False
    _entered_weight = 0

    def __init__(self, window: barbotgui.MainWindow, portId=-1):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # title
        title = QtWidgets.QLabel("Kalibrierung")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().setAlignment(title, QtCore.Qt.AlignTop)
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(Overview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # normal buttons to be shown in the beginning
        self._add_calibration_buttons()

        # dialog to remove glas
        self._add_dialog_remove_glas()

        # dialog to enter the weight on the platform
        self._add_dialog_enter_weight()

        self._show_calibration_buttons()

        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

    def _add_dialog_remove_glas(self):
        self._dialog_remove_glas = QtWidgets.QWidget()
        self._dialog_remove_glas.setLayout(QtWidgets.QGridLayout())
        self._dialog_remove_glas.setVisible(False)
        self._content.layout().addWidget(self._dialog_remove_glas, 1)

        center_box = QtWidgets.QFrame()
        center_box.setLayout(QtWidgets.QVBoxLayout())
        self._dialog_remove_glas.layout().addWidget(
            center_box, 0, 0, QtCore.Qt.AlignCenter)

        label = QtWidgets.QLabel("Bitte alles von der Platform entfernen.")
        center_box.layout().addWidget(label)

        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        center_box.layout().addWidget(row)

        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(lambda: statemachine.get_weight(self._tare))
        row.layout().addWidget(ok_button)

        cancel_button = QtWidgets.QPushButton("Abbrechen")
        cancel_button.clicked.connect(lambda: self._show_calibration_buttons())
        row.layout().addWidget(cancel_button)

    def _add_dialog_enter_weight(self):
        self._dialog_enter_weight = QtWidgets.QWidget()
        self._dialog_enter_weight.setLayout(QtWidgets.QGridLayout())
        self._dialog_enter_weight.setVisible(False)
        self._content.layout().addWidget(self._dialog_enter_weight, 1)

        center_box = QtWidgets.QFrame()
        center_box.setLayout(QtWidgets.QVBoxLayout())
        self._dialog_enter_weight.layout().addWidget(
            center_box, 0, 0, QtCore.Qt.AlignCenter)

        label = QtWidgets.QLabel(
            "Bitte aktuelles Gewicht\nauf der Platorm angeben.")
        center_box.layout().addWidget(label)

        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        center_box.layout().addWidget(row)

        # edit
        self.weight_widget = QtWidgets.QLabel()
        center_box.layout().addWidget(self.weight_widget)

        # numpad
        numpad = QtWidgets.QWidget()
        numpad.setLayout(QtWidgets.QGridLayout())
        for y in range(0, 3):
            for x in range(0, 3):
                num = y * 3 + x + 1
                button = QtWidgets.QPushButton(str(num))
                button.setProperty("class", "NumpadButton")
                button.clicked.connect(
                    lambda checked, value=num: self.numpad_button_clicked(value))
                numpad.layout().addWidget(button, y, x)
        # cancel
        button = QtWidgets.QPushButton("Abbrechen")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(
            lambda checked: self._show_calibration_buttons())
        numpad.layout().addWidget(button, 3, 0)
        # zero
        button = QtWidgets.QPushButton("0")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self.numpad_button_clicked(0))
        numpad.layout().addWidget(button, 3, 1)
        # enter
        button = QtWidgets.QPushButton("OK")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self._calibrate())
        numpad.layout().addWidget(button, 3, 2)

        center_box.layout().addWidget(numpad)

    def _update_weight(self):
        self.weight_widget.setText(str(self._entered_weight))

    def numpad_button_clicked(self, value):
        self._entered_weight = self._entered_weight * 10 + value
        self._update_weight()

    def _add_calibration_buttons(self):
        self._calibration_buttons = QtWidgets.QWidget()
        self._calibration_buttons.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(self._calibration_buttons, 1)

        # Tare
        button = QtWidgets.QPushButton("Tara")
        button.clicked.connect(lambda: self._start_calibration(False))
        self._calibration_buttons.layout().addWidget(button)

        # Calibrate
        button = QtWidgets.QPushButton("Kalibrieren")
        button.clicked.connect(lambda: self._start_calibration(True))
        self._calibration_buttons.layout().addWidget(button)

    def _tare(self, tare_weight):
        self.tare_weight = tare_weight
        self.new_offset = botconfig.balance_offset + \
            self.tare_weight * botconfig.balance_calibration
        if self._tare_and_calibrate:
            # continue with calibration
            self._show_dialog_enter_weight()
        else:
            # tare only: set offset, keep calibration
            statemachine.set_balance_calibration(
                self.new_offset, botconfig.balance_calibration)
            self.window.show_message("Kalibrierung wurde gespeichert")
            self._show_calibration_buttons()

    def _calibrate(self):
        if self._entered_weight > 0:
            def set_calibration_and_save(weight):
                cal = (weight-self.tare_weight) * \
                    botconfig.balance_calibration/self._entered_weight
                statemachine.set_balance_calibration(self.new_offset, cal)
                self.window.show_message("Kalibrierung gespeichert")
            statemachine.get_weight(set_calibration_and_save)
        else:
            self.window.show_message("Bitte ein Gewicht eingeben")
        self._show_calibration_buttons()

    def _start_calibration(self, tare_and_calibrate):
        self._tare_and_calibrate = tare_and_calibrate
        self._show_dialog_remove_glas()

    def _show_dialog_remove_glas(self):
        self._calibration_buttons.setVisible(False)
        self._dialog_remove_glas.setVisible(True)
        self._dialog_enter_weight.setVisible(False)

    def _show_calibration_buttons(self):
        self._dialog_remove_glas.setVisible(False)
        self._calibration_buttons.setVisible(True)
        self._dialog_enter_weight.setVisible(False)

    def _show_dialog_enter_weight(self):
        self._entered_weight = 0
        self.update()
        self._dialog_remove_glas.setVisible(False)
        self._calibration_buttons.setVisible(False)
        self._dialog_enter_weight.setVisible(True)


class Cleaning(IdleView):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())
        self.amount = 50

        # title
        title = QtWidgets.QLabel("Reinigung")
        title.setProperty("class", "Headline")
        self._content.layout().setAlignment(title, QtCore.Qt.AlignTop)
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(Overview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # clean left
        button = QtWidgets.QPushButton("Reinigen linke Hälfte")
        button.clicked.connect(lambda: self._clean_left())
        self._content.layout().addWidget(button)

        # clean right
        button = QtWidgets.QPushButton("Reinigen rechte Hälfte")
        button.clicked.connect(lambda: self._clean_right())
        self._content.layout().addWidget(button)

        # grid
        grid = QtWidgets.QWidget()
        grid.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(grid)
        # fill with buttons
        for column in range(6):
            for row in range(2):
                port = row * 6 + column
                button = QtWidgets.QPushButton(str(port + 1))
                button.clicked.connect(
                    lambda checked, pid=port: self._clean_single(pid))
                grid.layout().addWidget(button, row, column)

        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

    def _clean_left(self):
        data = range(0, 6)
        statemachine.start_cleaning_cycle(data)

    def _clean_right(self):
        data = range(6, 12)
        statemachine.start_cleaning_cycle(data)

    def _clean_single(self, port):
        statemachine.start_cleaning(port)


class Settings(IdleView):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # title
        title = QtWidgets.QLabel("Einstellungen")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(Overview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        self.entries = [
            # {"name": "Mac Address", "setting": "mac_address", "type": str},
            {"name": "Max. Geschwindigkeit [mm/s]", "setting": "max_speed", "type": int, "min": 1, "max": 1000},
            {"name": "Max. Beschleunigung [mm/s^2]", "setting": "max_accel", "type": int, "min": 1, "max": 1000},
            {"name": "Max Cocktail Größe [cl]", "setting": "max_cocktail_size", "type": int, "min": 1, "max": 50},
            {"name": "Leistung Pumpe [0..255]", "setting": "pump_power", "type": int, "min": 1, "max": 255},
            {"name": "Leistung Pumpe Sirup [0..255]", "setting": "pump_power_sirup", "type": int, "min": 1, "max": 255},
            {"name": "Dauer Reinigung [ms]", "setting": "cleaning_time", "type": int, "min": 1, "max": 20000},
            {"name": "Rührer verbunden", "setting": "stirrer_connected", "type": bool},
            {"name": "Dauer Rühren [ms]", "setting": "stirring_time", "type": int, "min": 1, "max": 10000},
            {"name": "Eis Crucher verbunden", "setting": "ice_crusher_connected", "type": bool},
            {"name": "Eis Menge [g]", "setting": "ice_amount", "type": int, "min": 1, "max": 300},
            {"name": "Strohhalm Dispenser verbunden", "setting": "straw_dispenser_connected", "type": bool},
            {"name": "Zucker Dosierer verbunden", "setting": "sugar_dispenser_connected", "type": bool},
            {"name": "Zucker g/Tl", "setting": "sugar_per_unit", "type": int, "min": 1, "max": 10},
        ]
        form_widget = QtWidgets.QWidget()
        form_widget.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(form_widget)
        row = 0
        for entry in self.entries:
            label = QtWidgets.QLabel(entry["name"])
            if entry["type"] == int:
                edit_widget = QtWidgets.QSpinBox()
                if "min" in entry:
                    edit_widget.setMinimum(entry["min"])
                if "max" in entry:
                    edit_widget.setMaximum(entry["max"])
                edit_widget.setValue(getattr(botconfig, entry["setting"]))
                edit_widget.enterEvent = lambda e, w=edit_widget: self.window.open_numpad(w)
                #TODO: Numpad only opens if focus is already on the element 
            elif entry["type"] == bool:
                edit_widget = QtWidgets.QCheckBox()
                edit_widget.setChecked(getattr(botconfig, entry["setting"]))
            else:
                edit_widget = QtWidgets.QLineEdit()
                edit_widget.setText(getattr(botconfig, entry["setting"]))
            entry["widget"] = edit_widget
            form_widget.layout().addWidget(label, row, 0)
            form_widget.layout().addWidget(edit_widget, row, 1)
            row += 1

        save_button = QtWidgets.QPushButton("Speichern")
        save_button.clicked.connect(lambda: self._save())
        self._content.layout().addWidget(save_button)

    def _save(self):
        for entry in self.entries:
            if entry["type"] == int:
                setattr(botconfig, entry["setting"], entry["widget"].value())
            elif entry["type"] == bool:
                setattr(botconfig, entry["setting"],
                        entry["widget"].isChecked())
            else:
                setattr(botconfig, entry["setting"], entry["widget"].text())
        botconfig.save()
        statemachine.set_state(statemachine.State.connecting)
        self.window.show_message(
            "Einstellungen wurden gespeichert, barbot wird neu gestartet")


class System(IdleView):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # title
        title = QtWidgets.QLabel("System")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(Overview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # add actual content
        self.window.add_system_view(self._content)


class RemoveRecipe(IdleView):
    _list = None

    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # title
        title = QtWidgets.QLabel("Positionen")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().setAlignment(title, QtCore.Qt.AlignTop)
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(Overview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # confirmationDialog
        self._add_confirmation_dialog()
        # list
        self.add_list()

    def _add_confirmation_dialog(self):
        self._confirmation_dialog = QtWidgets.QWidget()
        self._confirmation_dialog.setLayout(QtWidgets.QGridLayout())
        self._confirmation_dialog.setVisible(False)
        self._content.layout().addWidget(self._confirmation_dialog, 1)

        center_box = QtWidgets.QFrame()
        center_box.setLayout(QtWidgets.QVBoxLayout())
        self._confirmation_dialog.layout().addWidget(
            center_box, 0, 0, QtCore.Qt.AlignCenter)

        label = QtWidgets.QLabel("Wirklich löschen?")
        center_box.layout().addWidget(label)

        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        center_box.layout().addWidget(row)

        ok_button = QtWidgets.QPushButton("Löschen")
        ok_button.clicked.connect(lambda: self._remove())
        row.layout().addWidget(ok_button)

        cancel_button = QtWidgets.QPushButton("Abbrechen")
        cancel_button.clicked.connect(lambda: self._hide_confirmation())
        row.layout().addWidget(cancel_button)

    def add_list(self):
        if self._list is not None:
            self._list.setParent(None)

        self._list = QtWidgets.QWidget()
        self._list.setLayout(QtWidgets.QVBoxLayout())
        self._content.layout().addWidget(self._list, 1)
        for recipe in recipes.filter(self.window.recipe_filter):
            # box to hold the recipe
            recipe_box = QtWidgets.QWidget()
            recipe_box.setLayout(QtWidgets.QHBoxLayout())
            self._list.layout().addWidget(recipe_box)

            # title
            recipe_title = QtWidgets.QLabel(recipe.name)
            recipe_title.setProperty("class", "RecipeTitle")
            recipe_box.layout().addWidget(recipe_title, 1)

            # remove button
            icon = barbotgui.qt_icon_from_file_name("remove.png")
            remove_button = QtWidgets.QPushButton(icon, "")
            remove_button.clicked.connect(
                lambda checked, r=recipe: self._show_confirmation(r))
            recipe_box.layout().addWidget(remove_button, 0)

    def _show_confirmation(self, recipe: recipes.Recipe):
        self._recipe = recipe
        self._list.setVisible(False)
        self._confirmation_dialog.setVisible(True)

    def _hide_confirmation(self):
        self._confirmation_dialog.setVisible(False)
        self._list.setVisible(True)

    def _remove(self):
        recipes.remove(self._recipe)
        self._hide_confirmation()
        self.add_list()
