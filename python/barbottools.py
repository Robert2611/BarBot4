#!/usr/bin/env python3
from barbot import communication
import re
import os
import sys
from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import barbot.communication as com
from barbot import botconfig
import threading
import time
import logging


def get_commands():
    pattern = re.compile(
        """protocol\.add(?P<type>Do|Set|Get)Command\(\s*     #function call and type
        \"(?P<name>[^\"]*)\"                                 #string parameter aka name
        ([^\"]*if\s*\(param_c\s==\s(?P<count>\d+))?          #parameters
        """, re.DOTALL | re.VERBOSE)
    script_dir = os.path.dirname(__file__)
    with open(os.path.join(script_dir, "../firmware/mainboard/src/main.cpp"), "r") as f:
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


def get_errors():
    errors = {}
    script_dir = os.path.dirname(__file__)
    start_of_enum_found = False
    index = None
    with open(os.path.join(script_dir, "../firmware/mainboard/include/StateMachine.h"), "r") as f:
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


def print_all_commands():
    commands = get_commands()

    print("Do Commands:")
    print_commands_by_type(commands, "Do")

    print("Set Commands:")
    print_commands_by_type(commands, "Set")

    print("Get Commands:")
    print_commands_by_type(commands, "Get")


class ProtocolThread(threading.Thread):
    abort = False
    mac_address: str

    def __init__(self):
        threading.Thread.__init__(self)
        self._next_command = None

    def run_next(self, command):
        self._next_command = command

    def run(self):
        while not self.abort:
            if not communication.is_connected:
                communication.connect(self.mac_address, 2)
                if not communication.is_connected:
                    # only try connecting every 500ms
                    time.sleep(0.5)
            else:
                m = communication.read_message()
                if m is not None and self._next_command is not None:
                    if self._next_command["type"] == "Do":
                        if len(self._next_command["parameters"]) == 0:
                            communication.try_do(self._next_command["name"])
                        elif len(self._next_command["parameters"]) == 1:
                            communication.try_do(
                                self._next_command["name"], self._next_command["parameters"][0])
                        elif len(self._next_command["parameters"]) == 2:
                            communication.try_do(
                                self._next_command["name"], self._next_command["parameters"][0], self._next_command["parameters"][1])
                    elif self._next_command["type"] == "Set":
                        communication.try_set(
                            self._next_command["name"], self._next_command["parameters"][0])
                    elif self._next_command["type"] == "Get":
                        communication.try_get(
                            self._next_command["name"], self._next_command["parameters"][0])
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

    def __init__(self, protocol_thread: ProtocolThread):
        super().__init__()
        communication_thread = protocol_thread
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
        self.commands = get_commands()
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
        self.errors = get_errors()

    def send_command(self, command):
        parameters = [str(pw.value()) for pw in command["parameter_widgets"]]
        command["parameters"] = parameters if parameters is not None else None
        protocol_thread.run_next(command)

    def log_add_line(self, text):
        # only show 100 lines
        self._log_lines.append(text)
        while len(self._log_lines) > 100:
            self._log_lines.pop(0)
        text = "".join(self._log_lines)
        self.log_widget.setPlainText(text)
        scrollbar = self.log_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        if "ERROR" in text:
            re.search("ERROR\s(?P<id>\d+)\s")


if __name__ == '__main__':
    try:
        print(get_errors())
        # load mac address from config
        script_dir = os.path.dirname(__file__)
        cfg_path = os.path.join(script_dir, "../bar_bot.cfg")
        botconfig.load(cfg_path)
        # create protocol thread
        protocol_thread = ProtocolThread()
        protocol_thread.mac_address = botconfig.mac_address
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
        window = ToolsWindow(protocol_thread)
        gui_logger.qt.new_entry_signal.connect(
            lambda line: window.log_add_line(line))
        window.show()
        app.exec_()
        protocol_thread.abort = True
        protocol_thread.join()
    except KeyboardInterrupt:
        print("--> closed by user")
