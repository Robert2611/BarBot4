#!/usr/bin/env python3
import re
import os
import sys
import threading
import time
import logging
from PyQt5 import QtWidgets, QtCore

from barbot.logic.communication import Mainboard, MainboardConnectionBluetooth

def get_commands(mainboard_firmware_path: str):
    pattern = re.compile(
        """protocol\.add(?P<type>Do|Set|Get)Command\(\s*     #function call and type
        \"(?P<name>[^\"]*)\"                                 #string parameter aka name
        ([^\"]*if\s*\(param_c\s==\s(?P<count>\d+))?          #parameters
        """, re.DOTALL | re.VERBOSE)
    with open(os.path.join(mainboard_firmware_path, "src/main.cpp"), "r", encoding="utf-8") as f:
        content = f.read()
    commands = []
    for match in pattern.finditer(content):
        command = {
            "type": match.group("type"),
            "count": int(match.group("count")) if match.group("count") is not None else 0,
            "name": match.group("name")
        }
        commands.append(command)
    return commands


def get_errors(mainboard_firmware_path: str):
    errors = {}
    start_of_enum_found = False
    index = None
    with open(os.path.join(mainboard_firmware_path, "include/StateMachine.h"), "r", encoding="utf-8") as f:
        for line in f:
            if not start_of_enum_found:
                if line.startswith("enum BarBotStatus_t"):
                    start_of_enum_found = True
            elif line.startswith("}"):
                break
            elif index is None:
                match = re.search("Error\s=\s(?P<index>\d+)", line)
                if match:
                    index = int(match.group("index"))
            else:
                match = re.search("Error(?P<name>.*),", line)
                if match:
                    index += 1
                    errors[index] = match.group("name")

    return errors


def print_commands_by_type(commands, type):
    for command in commands:
        if command["type"] == type:
            command_str = "-" + command["name"]
            if command["count"] > 0:
                for i in range(command["count"]):
                    command_str += " p{0}".format(i+1)
            print(command_str)


def print_all_commands(mainboard_firmware_path: str):
    commands = get_commands(mainboard_firmware_path)

    print("Do Commands:")
    print_commands_by_type(commands, "Do")

    print("Set Commands:")
    print_commands_by_type(commands, "Set")

    print("Get Commands:")
    print_commands_by_type(commands, "Get")


class ProtocolThread(threading.Thread):
    abort = False
    mac_address: str

    def __init__(self, mainboard: Mainboard):
        threading.Thread.__init__(self)
        self._mainboard = mainboard
        self._next_command = None

    def run_next(self, command):
        self._next_command = command

    def send_abort(self):
        self._mainboard.send_abort()

    def run(self):
        while not self.abort:
            if not self._mainboard.is_connected:
                self._mainboard.connect(self.mac_address)
                if not self._mainboard.is_connected:
                    # only try connecting every 500ms
                    time.sleep(0.5)
            else:
                m = self._mainboard.read_message()
                if m is not None and self._next_command is not None:
                    parameters = self._next_command["parameters"]
                    if self._next_command["type"] == "Do":
                        if len(parameters) == 0:
                            self._mainboard.do(self._next_command["name"])
                        elif len(parameters) == 1:
                            self._mainboard.do(
                                self._next_command["name"], parameters[0])
                        elif len(parameters) == 2:
                            self._mainboard.do(self._next_command["name"], parameters[0], parameters[1])
                    elif self._next_command["type"] == "Set":
                        self._mainboard.set(
                            self._next_command["name"], parameters[0])
                    elif self._next_command["type"] == "Get":
                        self._mainboard.get(self._next_command["name"])
                    # reset command
                    self._next_command = None


class GuiLoggerQt(QtCore.QObject):
    new_entry_signal = QtCore.pyqtSignal(str)


class GuiLogger(logging.Handler):
    qt: GuiLoggerQt = GuiLoggerQt()

    def emit(self, record):
        self.qt.new_entry_signal.emit(self.format(record)+"\n")


class ToolsWindow(QtWidgets.QMainWindow):
    _log_lines = []

    def __init__(self, protocol_thread: ProtocolThread, mainboard_firmware_path: str):
        super().__init__()
        self.protocol_thread = protocol_thread
        self.mainboard_firmware_path = mainboard_firmware_path
        self.center = QtWidgets.QWidget()
        self.setCentralWidget(self.center)
        self.center.setLayout(QtWidgets.QHBoxLayout())

        # log
        self.log_widget = QtWidgets.QPlainTextEdit()
        self.center.layout().addWidget(self.log_widget)

        # commands
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QGridLayout())
        self.center.layout().addWidget(container)
        self.commands = get_commands(mainboard_firmware_path)
        row = 0
        for command in self.commands:
            column = 0
            label = QtWidgets.QLabel(command["name"])
            container.layout().addWidget(label, row, column)
            column += 1
            command["parameter_widgets"] = []
            for _ in range(command["count"]):
                pw = QtWidgets.QSpinBox()
                pw.setMaximum(1000)
                pw.setMinimum(0)
                pw.setValue(100)
                container.layout().addWidget(pw, row, column)
                command["parameter_widgets"].append(pw)
                column += 1
            button = QtWidgets.QPushButton("Los")
            button.clicked.connect(
                lambda checked, cmd=command: self.send_command(cmd))
            container.layout().addWidget(button, row, 10)
            row += 1

        # right panel
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QGridLayout())
        self.center.layout().addWidget(container)
        # errors
        self.errors_widget = QtWidgets.QLabel("No Error")
        container.layout().addWidget(self.errors_widget)
        self.errors = get_errors(mainboard_firmware_path)
        # abort
        self.btn_abort = QtWidgets.QPushButton("Abort")
        self.btn_abort.clicked.connect(
            lambda checked: self.protocol_thread.send_abort())
        container.layout().addWidget(self.btn_abort)

    def send_command(self, command):
        parameters = [str(pw.value()) for pw in command["parameter_widgets"]]
        command["parameters"] = parameters if parameters is not None else None
        self.protocol_thread.run_next(command)

    def log_add_line(self, line):
        # only show 100 lines
        self._log_lines.append(line)
        while len(self._log_lines) > 100:
            self._log_lines.pop(0)
        text = "".join(self._log_lines)
        self.log_widget.setPlainText(text)
        scrollbar = self.log_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        if "ERROR" in line:
            m = re.search(
                "ERROR (?P<command>.+) (?P<id>\d+) (?P<parameter>-?\d+)", line)
            error_id = int(m.group("id"))
            errors = get_errors(self.mainboard_firmware_path)
            if error_id in errors.keys():
                error = errors[error_id]
            else:
                error = "Unkown error %i".format(error_id)
            self.errors_widget.setText(error)


def main():
    try:
        #TODO: first start the gui to show log messages from here on
        # check if firmware folder exists
        mainboard_firmware_path = os.path.join(os.path.dirname(__file__), "../../firmware/mainboard")
        if not os.path.exists(mainboard_firmware_path):
            print(f"Could not find mainboard firmware folder at '{mainboard_firmware_path}'")
            print("This tools must be used from within the BarBot repository")
            sys.exit(1)

        # if the mac adress is given via command line use it, otherwise search for bar_bot
        if len(sys.argv) > 1:
            mac_address = sys.argv[1]
            print(f"Using mac address from command line")
        else:
            print("No mac address given via command line, searching for bar_bot...")
            try:
                mac_address = MainboardConnectionBluetooth.find_bar_bot()
            except Exception as e:
                print(f"Error while searching for bar_bot: {e}")
                sys.exit(1)

        # create protocol thread
        print(f"Connecting to barbot with mac adress '{mac_address}'")
        mainboard_connection = MainboardConnectionBluetooth()
        mainboard = Mainboard(mainboard_connection)
        protocol_thread = ProtocolThread(mainboard)
        protocol_thread.mac_address = mac_address
        protocol_thread.start()

        app = QtWidgets.QApplication(sys.argv)
        # redirect logging to gui
        logging.basicConfig(
            filemode='a',
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        gui_logger = GuiLogger()
        logging.getLogger().addHandler(gui_logger)
        # create window
        window = ToolsWindow(protocol_thread, mainboard_firmware_path)
        gui_logger.qt.new_entry_signal.connect(window.log_add_line)
        window.show()
        app.exec_()

        protocol_thread.abort = True
        protocol_thread.join()
    except KeyboardInterrupt:
        print("--> closed by user")

if __name__ == '__main__':
    main()
