from typing import Dict
from PyQt5 import QtWidgets, QtCore
from barbot.logic import RecipeCollection, BarBot
from barbot.logic.config import PORT_COUNT, Ingredient
from .base import AdminView

class Ports(AdminView):
    """Handles what is connected to the ports of the barbot"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)

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
            cb_port = self.combobox_ingredients(ingredient, only_normal=True)
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
            self.show_message_trigger.emit(
                "Jede Zutat darf nur einer\n" +\
                "Position zugewiesen werden!"
            )
            return
        # update the ports list and save it
        self.barbot_.ports.update(new_ports)
        self.barbot_.ports.save()
        self.show_message_trigger.emit("Positionen wurden gespeichert.")
