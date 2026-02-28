from PyQt5 import QtWidgets, QtCore
from barbot.logic import RecipeCollection, BarBot
from .base import AdminView
from ...common import InputMethod

class Settings(AdminView):
    """Edit barbot settings"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)

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
        self._add_reset_mac_button()

    def _add_reset_mac_button(self):
        reset_button = QtWidgets.QPushButton("MAC-Adresse zurücksetzen")
        reset_button.clicked.connect(self._reset_mac)
        self._content.layout().addWidget(reset_button)

    def _reset_mac(self):
        self.barbot_.config.mac_address = ""
        self.barbot_.config.save()
        self.barbot_.reconnect()
        self.show_message_trigger.emit(
            "MAC-Adresse wurde zurückgesetzt, Suche nach BarBot gestartet")

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
                edit_widget.enterEvent = lambda e, w=edit_widget: self.open_input_method_trigger.emit(w, InputMethod.NUMPAD)
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
        self.show_message_trigger.emit(
            "Einstellungen wurden gespeichert, barbot wird neu gestartet")
