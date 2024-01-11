"""Views to be shown for admins"""
from typing import Dict
from PyQt5 import QtWidgets, Qt, QtCore, QtGui
from barbot.communication import BoardType
from barbot.config import version as barbot_version
from barbot.recipes import Recipe
from barbot.config import PORT_COUNT
from barbotgui.core import BarBotWindow, qt_icon_from_file_name, View, Ingredient
from barbotgui.userviews import UserView

class AdminView(UserView):
    """Base class for the admin views"""
    def __init__(self, window:BarBotWindow):
        super().__init__(window)

        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

    def _add_back_button_to_fixed_content(self):
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click():
            return self.window.set_view(Overview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

class AdminLogin(AdminView):
    """Login for the admin area"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)
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
        if self._entered_password == self.barbot_.config.admin_password:
            self.window.set_view(Overview(self.window))
        self._clear_password()


class Overview(AdminView):
    """Overview over the admin views"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)

        self.admin_navigation_items = [
            ["System", System],
            ["Positionen", Ports],
            ["Einstellungen", Settings],
            ["Reinigung", Cleaning],
            ["Cocktails Löschen", RemoveRecipe],
            ["Waage kalibrieren", BalanceCalibration]
        ]

        self._add_title_to_fixed_content("Übersicht")
        self._add_admin_navigation_by_items()
        self._add_board_list()
        self._add_version_label()

        self._add_dummy_widget_to_content()

        self._start_updating_weight()

    def _start_updating_weight(self):
        # Timer for updating the current weight display
        self._update_timer = QtCore.QTimer(self)
        self._update_timer.timeout.connect(
            lambda: self.barbot_.get_weight(self._set_weight_label)
        )
        self._update_timer.start(500)

        self.barbot_.get_weight(self._set_weight_label)

    def _add_admin_navigation_by_items(self):
        self.admin_navigation = QtWidgets.QWidget()
        self.admin_navigation.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(self.admin_navigation)

        columns = 1
        column = 0
        row = 0
        for text, _class in self.admin_navigation_items:
            button = QtWidgets.QPushButton(text)
            def btn_click(_, c=_class):
                return self.window.set_view(c(self.window))
            button.clicked.connect(btn_click)
            self.admin_navigation.layout().addWidget(button, row, column)
            column += 1
            if column >= columns:
                column = 0
                row += 1

    def _add_board_list(self):
        self.boards = [
            [BoardType.BALANCE, "balance.png"],
            [BoardType.STRAW, "straw.png"],
            [BoardType.CRUSHER, "ice.png"],
            [BoardType.MIXER, "stir.png"],
            [BoardType.SUGAR, "sugar.png"]
        ]
        self._board_widgets = {}
        row = 1
        # wrapper
        wrapper = QtWidgets.QWidget()
        wrapper.setProperty("class", "Boards")
        wrapper.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(wrapper)
        for board, icon in self.boards:
            connected = board in self.barbot_.connected_boards
            # board icon
            icon = qt_icon_from_file_name(icon)
            button_board_icon = QtWidgets.QPushButton(icon, "")
            button_board_icon.setProperty("class", "IconPresenter")
            button_board_icon.setEnabled(connected)
            wrapper.layout().addWidget(button_board_icon, row, 0, 1, 1)
            # connected / disconnected icon
            icon = qt_icon_from_file_name("plug-on.png" if connected else "plug-off.png")
            button = QtWidgets.QPushButton(icon, "")
            button.setProperty("class", "IconPresenter")
            button.setEnabled(connected)
            wrapper.layout().addWidget(button, row, 1, 1, 1)

            self._board_widgets[board] = [button_board_icon, button]

            if board == BoardType.BALANCE:
                # weight label
                self._weight_label = QtWidgets.QLabel()
                wrapper.layout().addWidget(self._weight_label, row, 2, 1, 3)
            row += 1
        # dummy
        wrapper.layout().addWidget(QtWidgets.QWidget(), 0, 0)
        wrapper.layout().addWidget(QtWidgets.QWidget(), row, 0)

    def _add_version_label(self):
        version_label = QtWidgets.QLabel(f"Version: {barbot_version}")
        self._content.layout().addWidget(version_label)

    def _set_weight_label(self, weight):
        weight = weight if weight is not None else "-"
        text = f"Gewicht: {weight} g"
        try:
            # this would cause a problem if the label was allready deleted
            self._weight_label.setText(text)
        except Exception:
            pass

class Ports(AdminView):
    """Handles what is connected to the ports of the barbot"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)

        self._add_title_to_fixed_content("Positionen")
        self._add_back_button_to_fixed_content()
        self._add_list_of_ports()
        self._add_save_button()

        self._add_dummy_widget_to_content()

    def _add_list_of_ports(self):
        table = QtWidgets.QWidget()
        table.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(table)
        self._ingredient_widgets = {}
        for i in range(PORT_COUNT):
            label = QtWidgets.QLabel(f"Position {(i+1)}")
            table.layout().addWidget(label, i, 0)
            ingredient = self.barbot_.ports.ingredient_at_port(i)
            cb_port = self.window.combobox_ingredients(ingredient, only_normal=True)
            self._ingredient_widgets[i] = cb_port
            table.layout().addWidget(cb_port, i, 1)

    def _add_save_button(self):
        button = QtWidgets.QPushButton("Speichern")
        button.clicked.connect(self._save)
        self._content.layout().addWidget(button)
        self._content.layout().setAlignment(button, QtCore.Qt.AlignCenter)

    def _save(self):
        new_ports:Dict[int, Ingredient] = {}
        for port, cb in self._ingredient_widgets.items():
            new_ports[port] = cb.currentData()
        # check for duplicates
        not_none_entries = [
            ing.name
            for ing in new_ports.values()
            if ing is not None
        ]
        if len(not_none_entries) != len(set(not_none_entries)):
            self.window.show_message(
                "Jede Zutat darf nur einer\n" +\
                "Position zugewiesen werden!"
            )
            return
        # update the ports list and save it
        self.barbot_.ports.update(new_ports)
        self.barbot_.ports.save()
        self.window.show_message("Positionen wurden gespeichert.")

class BalanceCalibration(AdminView):
    """Calibrate the internal balance"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)

        self._tare_and_calibrate = False
        self._entered_weight = 0
        self.tare_weight = 0
        self.new_offset = 0

        self._add_title_to_fixed_content("Kalibrierung")
        self._add_back_button_to_fixed_content()

        # add all dialogs
        self._add_dialog_calibration_buttons()
        self._add_dialog_remove_glas()
        self._add_dialog_enter_weight()

        # show only one dialog
        self._show_dialog_calibration_buttons()

        self._add_dummy_widget_to_content()

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
        ok_button.clicked.connect(lambda: self.barbot_.get_weight(self._tare))
        row.layout().addWidget(ok_button)

        cancel_button = QtWidgets.QPushButton("Abbrechen")
        cancel_button.clicked.connect(self._show_dialog_calibration_buttons)
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
                    lambda checked, value=num: self._numpad_button_clicked(value))
                numpad.layout().addWidget(button, y, x)
        # cancel
        button = QtWidgets.QPushButton("Abbrechen")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(
            lambda checked: self._show_dialog_calibration_buttons())
        numpad.layout().addWidget(button, 3, 0)
        # zero
        button = QtWidgets.QPushButton("0")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self._numpad_button_clicked(0))
        numpad.layout().addWidget(button, 3, 1)
        # enter
        button = QtWidgets.QPushButton("OK")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self._calibrate())
        numpad.layout().addWidget(button, 3, 2)

        center_box.layout().addWidget(numpad)

    def _update_weight(self):
        self.weight_widget.setText(str(self._entered_weight))

    def _numpad_button_clicked(self, value):
        self._entered_weight = self._entered_weight * 10 + value
        self._update_weight()

    def _add_dialog_calibration_buttons(self):
        self._dialog_calibration_buttons = QtWidgets.QWidget()
        self._dialog_calibration_buttons.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(self._dialog_calibration_buttons, 1)

        # Tare
        button = QtWidgets.QPushButton("Tara")
        button.clicked.connect(self._start_tare)
        self._dialog_calibration_buttons.layout().addWidget(button)

        # Calibrate
        button = QtWidgets.QPushButton("Kalibrieren")
        button.clicked.connect(self._start_calibration)
        self._dialog_calibration_buttons.layout().addWidget(button)

    def _tare(self, tare_weight):
        self.tare_weight = tare_weight
        self.new_offset = self.barbot_.config.balance_offset + \
            self.tare_weight * self.barbot_.config.balance_calibration
        if self._tare_and_calibrate:
            # continue with calibration
            self._show_dialog_enter_weight()
        else:
            # tare only: set offset, keep calibration
            self.barbot_.set_balance_calibration(
                self.new_offset, self.barbot_.config.balance_calibration)
            self.window.show_message("Kalibrierung wurde gespeichert")
            self._show_dialog_calibration_buttons()

    def _calibrate(self):
        if self._entered_weight > 0:
            def set_calibration_and_save(weight):
                cal = (weight-self.tare_weight) * \
                    self.barbot_.config.balance_calibration/self._entered_weight
                self.barbot_.set_balance_calibration(self.new_offset, cal)
                self.window.show_message("Kalibrierung gespeichert")
            self.barbot_.get_weight(set_calibration_and_save)
        else:
            self.window.show_message("Bitte ein Gewicht eingeben")
        self._show_dialog_calibration_buttons()

    def _start_tare(self):
        self._tare_and_calibrate = False
        self._show_dialog_remove_glas()

    def _start_calibration(self):
        self._tare_and_calibrate = True
        self._show_dialog_remove_glas()

    def _show_dialog_remove_glas(self):
        self._dialog_calibration_buttons.setVisible(False)
        self._dialog_remove_glas.setVisible(True)
        self._dialog_enter_weight.setVisible(False)

    def _show_dialog_calibration_buttons(self):
        self._dialog_remove_glas.setVisible(False)
        self._dialog_calibration_buttons.setVisible(True)
        self._dialog_enter_weight.setVisible(False)

    def _show_dialog_enter_weight(self):
        self._entered_weight = 0
        self.update()
        self._dialog_remove_glas.setVisible(False)
        self._dialog_calibration_buttons.setVisible(False)
        self._dialog_enter_weight.setVisible(True)

class Cleaning(AdminView):
    """Clean the ports"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)

        self.amount = 50

        self._add_title_to_fixed_content("Reinigung")
        self._add_back_button_to_fixed_content()
        self._add_button_clean_left()
        self._add_button_clean_right()
        self._add_button_grid_for_single_ports()

        self._add_dummy_widget_to_content()

    def _add_button_clean_left(self):
        button = QtWidgets.QPushButton("Reinigen linke Hälfte")
        button.clicked.connect(self._clean_left)
        self._content.layout().addWidget(button)

    def _add_button_clean_right(self):
        button = QtWidgets.QPushButton("Reinigen rechte Hälfte")
        button.clicked.connect(self._clean_right)
        self._content.layout().addWidget(button)

    def _add_button_grid_for_single_ports(self):
        grid = QtWidgets.QWidget()
        grid.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(grid)
        for column in range(6):
            for row in range(2):
                port = row * 6 + column
                button = QtWidgets.QPushButton(str(port + 1))
                button.clicked.connect(
                    lambda _, pid=port: self._clean_single(pid))
                grid.layout().addWidget(button, row, column)

    def _clean_left(self):
        data = range(0, 6)
        self.barbot_.start_cleaning_cycle(data)

    def _clean_right(self):
        data = range(6, 12)
        self.barbot_.start_cleaning_cycle(data)

    def _clean_single(self, port):
        self.barbot_.start_cleaning(port)


class Settings(AdminView):
    """Edit barbot settings"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)

        self.entries = [
            {"name": "Max. Geschwindigkeit [mm/s]","setting": "max_speed",
                "type": int, "min": 1, "max": 1000},
            {"name": "Max. Beschleunigung [mm/s^2]", "setting": "max_accel",
                "type": int, "min": 1, "max": 1000},
            {"name": "Max Cocktail Größe [cl]", "setting": "max_cocktail_size",
                "type": int, "min": 1, "max": 50},
            {"name": "Leistung Pumpe [0..255]", "setting": "pump_power",
                "type": int, "min": 1, "max": 255},
            {"name": "Leistung Pumpe Sirup [0..255]", "setting": "pump_power_sirup",
                "type": int, "min": 1, "max": 255},
            {"name": "Dauer Reinigung [ms]", "setting": "cleaning_time",
                "type": int, "min": 1, "max": 20000},
            {"name": "Rührer verbunden", "setting": "stirrer_connected",
                "type": bool},
            {"name": "Dauer Rühren [ms]", "setting": "stirring_time",
                "type": int, "min": 1, "max": 10000},
            {"name": "Eis Crucher verbunden", "setting": "ice_crusher_connected",
                "type": bool},
            {"name": "Eis Menge [g]", "setting": "ice_amount",
                "type": int, "min": 1, "max": 300},
            {"name": "Strohhalm Dispenser verbunden", "setting": "straw_dispenser_connected",
                "type": bool},
            {"name": "Zucker Dosierer verbunden", "setting": "sugar_dispenser_connected",
                "type": bool},
            {"name": "Zucker g/Tl", "setting": "sugar_per_unit",
                "type": int, "min": 1, "max": 10},
        ]

        self._add_title_to_fixed_content("Einstellungen")
        self._add_back_button_to_fixed_content()
        self._add_form_defined_by_entries()
        self._add_save_button()

    def _add_form_defined_by_entries(self):
        form_widget = QtWidgets.QWidget()
        form_widget.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(form_widget)
        row = 0
        config = self.barbot_.config
        for entry in self.entries:
            label = QtWidgets.QLabel(entry["name"])
            if entry["type"] == int:
                edit_widget = QtWidgets.QSpinBox()
                if "min" in entry:
                    edit_widget.setMinimum(entry["min"])
                if "max" in entry:
                    edit_widget.setMaximum(entry["max"])
                edit_widget.setValue(getattr(config, entry["setting"]))
                edit_widget.enterEvent = lambda e, w=edit_widget: self.window.open_numpad(w)
                #TODO: Numpad only opens if focus is already on the element
            elif entry["type"] == bool:
                edit_widget = QtWidgets.QCheckBox()
                edit_widget.setChecked(getattr(config, entry["setting"]))
            else:
                edit_widget = QtWidgets.QLineEdit()
                edit_widget.setText(getattr(config, entry["setting"]))
            entry["widget"] = edit_widget
            form_widget.layout().addWidget(label, row, 0)
            form_widget.layout().addWidget(edit_widget, row, 1)
            row += 1

    def _add_save_button(self):
        save_button = QtWidgets.QPushButton("Speichern")
        save_button.clicked.connect(self._save)
        self._content.layout().addWidget(save_button)

    def _save(self):
        config = self.barbot_.config
        for entry in self.entries:
            if entry["type"] == int:
                setattr(config, entry["setting"], entry["widget"].value())
            elif entry["type"] == bool:
                setattr(config, entry["setting"],
                        entry["widget"].isChecked())
            else:
                setattr(config, entry["setting"], entry["widget"].text())
        self.barbot_.config.save()
        self.barbot_.reconnect()
        self.window.show_message(
            "Einstellungen wurden gespeichert, barbot wird neu gestartet")

class System(AdminView):
    """Control the whole barbot system"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)

        self._add_title_to_fixed_content("System")
        self._add_back_button_to_fixed_content()
        View.set_system_view(self._content)

class RemoveRecipe(AdminView):
    """Remove recipes"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)

        self._list = None
        self._recipe:Recipe = None

        self._add_title_to_fixed_content("Rezepte löschen")
        self._add_back_button_to_fixed_content()
        self._add_confirmation_dialog()
        self._add_recipe_list()

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
        ok_button.clicked.connect(self._remove)
        row.layout().addWidget(ok_button)

        cancel_button = QtWidgets.QPushButton("Abbrechen")
        cancel_button.clicked.connect(self._hide_confirmation)
        row.layout().addWidget(cancel_button)

    def _add_recipe_list(self):
        if self._list is not None:
            self._list.setParent(None)

        self._list = QtWidgets.QWidget()
        self._list.setLayout(QtWidgets.QVBoxLayout())
        self._content.layout().addWidget(self._list, 1)
        recipes = self.window.recipes.get_filtered(None, self.barbot_.ports, self.barbot_.config)
        for recipe in recipes:
            # box to hold the recipe
            recipe_box = QtWidgets.QWidget()
            recipe_box.setLayout(QtWidgets.QHBoxLayout())
            self._list.layout().addWidget(recipe_box)

            # title
            recipe_title = QtWidgets.QLabel(recipe.name)
            recipe_title.setProperty("class", "RecipeTitle")
            recipe_box.layout().addWidget(recipe_title, 1)

            # remove button
            icon = qt_icon_from_file_name("remove.png")
            remove_button = QtWidgets.QPushButton(icon, "")
            remove_button.clicked.connect(
                lambda _, r=recipe: self._show_confirmation(r))
            recipe_box.layout().addWidget(remove_button, 0)

    def _show_confirmation(self, recipe: Recipe):
        self._recipe = recipe
        self._list.setVisible(False)
        self._confirmation_dialog.setVisible(True)

    def _hide_confirmation(self):
        self._confirmation_dialog.setVisible(False)
        self._list.setVisible(True)

    def _remove(self):
        self.window.recipes.remove(self._recipe)
        self._hide_confirmation()
        self._add_recipe_list()
