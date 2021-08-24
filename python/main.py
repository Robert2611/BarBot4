#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from barbot import statemachine
from PyQt5 import QtWidgets
import barbot
import barbotgui
import os
import sys
import logging
import threading
from datetime import datetime
from barbot import orders, recipes
from barbot import directories
from pprint import pprint

# cofigure logging
log_file = datetime.now().strftime("BarBot %Y-%m-%d %H-%M-%S.log")
log_file_path = directories.join(directories.log, log_file)
logging.basicConfig(
    filename=log_file_path,
    filemode='a',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.info("<<<<<<BarBot started>>>>>>")
logging.info("--------------------------")

barbot.is_demo = "-d" in sys.argv[1:]

# create statemachine
if not barbot.is_demo:
    bar_bot_thread = threading.Thread(target=statemachine.run)
    bar_bot_thread.start()

# show gui and join the threads
try:
    app = QtWidgets.QApplication(sys.argv)
    form = barbotgui.MainWindow()
    form.show()
    app.exec_()
    # tell the statemachine to stop
    statemachine.abort = True
    if not barbot.is_demo:
        bar_bot_thread.join()
except KeyboardInterrupt:
    raise

logging.info("-------------------------")
logging.info(">>>>>>BarBot closed<<<<<<")
