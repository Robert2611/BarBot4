from PyQt5 import QtWidgets, QtCore
from barbot.logic import RecipeCollection, BarBot
from .base import AdminView

class BalanceCalibration(AdminView):
    """Calibrate the internal balance"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)

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
            self.show_message_trigger.emit("Kalibrierung wurde gespeichert")
            self._show_dialog_calibration_buttons()

    def _calibrate(self):
        if self._entered_weight > 0:
            def set_calibration_and_save(weight):
                cal = (weight-self.tare_weight) * \
                    self.barbot_.config.balance_calibration/self._entered_weight
                self.barbot_.set_balance_calibration(self.new_offset, cal)
                self.show_message_trigger.emit("Kalibrierung gespeichert")
            self.barbot_.get_weight(set_calibration_and_save)
        else:
            self.show_message_trigger.emit("Bitte ein Gewicht eingeben")
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
