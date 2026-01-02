#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import traceback
import threading
import signal
import os
from datetime import datetime
from types import TracebackType
import psutil

from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer

from .gui import MainWindow

from .logic import BarBot, Mainboard
from .logic.recipes import RecipeCollection
from .logic.config import log_directory, BarBotConfig, PortConfiguration
from .logic.communication import MainboardConnectionBluetooth
from .logic.mockup import MainboardConnectionMockup


def setup_logging(enable_log_to_stdout: bool):
    exception_file_path = os.path.join(
        log_directory,
        datetime.now().strftime("#Exception %Y-%m-%d %H-%M-%S.txt")
    )
    log_file_path = os.path.join(
        log_directory,
        datetime.now().strftime("BarBot %Y-%m-%d %H-%M-%S.log")
    )
    logging.getLogger().handlers.clear()
    logging.basicConfig(
        filename=log_file_path,
        filemode='w',
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s\t%(message)s'
    )
    if enable_log_to_stdout:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s\t%(message)s'))
        logging.getLogger().addHandler(handler)
    return log_file_path, exception_file_path

def handle_exception_factory(exception_file_path):
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        with open(exception_file_path, 'a', encoding="utf-8") as f:
            traceback_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            f.write("\n".join(traceback_lines))
            f.write('\n')
            f.write(str(psutil.virtual_memory()))
    return handle_exception

def create_barbot(is_demo):
    ports = PortConfiguration()
    config = BarBotConfig()
    mainboard = Mainboard(MainboardConnectionMockup() if is_demo else MainboardConnectionBluetooth())
    bot = BarBot(config, ports, mainboard)
    return bot

def start_statemachine(bot):
    bar_bot_thread = threading.Thread(target=bot.run)
    bar_bot_thread.start()
    return bar_bot_thread

def setup_sigint(app):
    def sigint_handler(*_):
        logging.info("SIGINT received!")
        if app is not None:
            app.quit()
    signal.signal(signal.SIGINT, sigint_handler)

def run(is_demo: bool, enable_log_to_stdout: bool):
    _, exception_file_path = setup_logging(enable_log_to_stdout)
    logging.info("<<<<<<BarBot started>>>>>>")
    logging.info("--------------------------")

    bot = create_barbot(is_demo)
    bar_bot_thread = start_statemachine(bot)

    recipe_collection = RecipeCollection()
    recipe_collection.load()

    sys.excepthook = handle_exception_factory(exception_file_path)

    app = QtWidgets.QApplication(sys.argv)
    setup_sigint(app)
    form = MainWindow(bot, recipe_collection)
    form.show()
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)
    app.exec_()
    bot.abort()
    bar_bot_thread.join()

    logging.info("-------------------------")
    logging.info(">>>>>>BarBot closed<<<<<<")

def main():
    parser = argparse.ArgumentParser(description="BarBot")
    parser.add_argument('--demo', action='store_true', help='Run in demo mode')
    parser.add_argument('--log', action='store_true', help='Enable logging to stdout')
    args = parser.parse_args()

    is_demo = args.demo
    enable_log_to_stdout = args.log

    # Override based on script name for backward compatibility with console scripts
    script_name = os.path.basename(sys.argv[0])
    if 'barbot-demo' in script_name:
        is_demo = True
        enable_log_to_stdout = True
    elif 'barbot-with-log' in script_name:
        enable_log_to_stdout = True

    run(is_demo=is_demo, enable_log_to_stdout=enable_log_to_stdout)

if __name__ == "__main__":
    main()
