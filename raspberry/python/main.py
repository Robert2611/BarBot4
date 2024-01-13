#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import sys
import traceback
import threading
import signal
import os
from datetime import datetime
import psutil

from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer

from barbotgui import MainWindow

from barbot import BarBot, Mainboard
from barbot.recipes import RecipeCollection
from barbot.config import log_directory, BarBotConfig, PortConfiguration
from barbot.communication import MainboardConnectionBluetooth
from barbot.mockup import MaiboardConnectionMockup

# cofigure logging
exception_file_path = os.path.join(
    log_directory,
    datetime.now().strftime("#Exception %Y-%m-%d %H-%M-%S.txt")
)
log_file_path = os.path.join(
    log_directory,
    datetime.now().strftime("BarBot %Y-%m-%d %H-%M-%S.log")
)
# for some reason the logger is already configured, so we have to remove the handler
logging.getLogger().handlers.clear()
logging.basicConfig(
    filename=log_file_path,
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s\t%(message)s'
)

# log to file and stdout
if "-t" in sys.argv[1:]:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s\t%(message)s'))
    logging.getLogger().addHandler(handler)

logging.info("<<<<<<BarBot started>>>>>>")
logging.info("--------------------------")

is_demo = "-d" in sys.argv[1:]
ports = PortConfiguration()
config = BarBotConfig()
mainboard = Mainboard(MaiboardConnectionMockup() if is_demo else MainboardConnectionBluetooth())
bot = BarBot(config, ports, mainboard)
recipe_collection = RecipeCollection()
recipe_collection.load()

# create statemachine
bar_bot_thread = threading.Thread(target=bot.run)
bar_bot_thread.start()

app = None

def sigint_handler(*_):
    """Close the gui on interrupt signal"""
    logging.info("SIGINT received!")
    if app is not None:
        app.quit()
signal.signal(signal.SIGINT, sigint_handler)

# show gui and join the threads
try:
    app = QtWidgets.QApplication(sys.argv)
    form = MainWindow(bot, recipe_collection)
    form.show()
    # Let the interpreter run periodically to handle signals.
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)
    # start the qt app
    app.exec_()
    # tell the statemachine to stop
    bot.abort()
    bar_bot_thread.join()
except Exception as e:
    logging.error(traceback.format_exc())
    with open(exception_file_path, 'a', encoding="utf-8") as f:
        f.write(traceback.format_exc())
        f.write('\n')
        f.write(str(psutil.virtual_memory()))

logging.info("-------------------------")
logging.info(">>>>>>BarBot closed<<<<<<")
