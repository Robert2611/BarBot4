#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from barbot import statemachine
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
import barbot
import barbotgui
import sys
import traceback
import threading
import psutil
from datetime import datetime
from barbot import directories
import signal

# cofigure logging
exception_file_path = directories.join(
    directories.log, datetime.now().strftime("#Exception %Y-%m-%d %H-%M-%S.txt"))
log_file_path = directories.join(
    directories.log, datetime.now().strftime("BarBot %Y-%m-%d %H-%M-%S.log"))
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
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

logging.info("<<<<<<BarBot started>>>>>>")
logging.info("--------------------------")

is_demo = "-d" in sys.argv[1:]
bot = statemachine.BarBot(demo_mode=is_demo)

# create statemachine
if not is_demo:
    bar_bot_thread = threading.Thread(target=bot.run)
    bar_bot_thread.start()

def sigint_handler(*_):
    """Close the gui on interrupt signal"""
    logging.info("SIGINT received!")
    if app is not None:
        app.quit()
signal.signal(signal.SIGINT, sigint_handler)

barbot.orders.get_parties()

# show gui and join the threads
try:
    app = QtWidgets.QApplication(sys.argv)
    form = barbotgui.MainWindow()
    form.show()
    # Let the interpreter run periodically to handle signals.
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)
    # start the qt app
    app.exec_()
    # tell the statemachine to stop
    statemachine.abort = True
    if not is_demo:
        bar_bot_thread.join()
except Exception as e:
    logging.error(traceback.format_exc())
    with open(exception_file_path, 'a') as f:
        f.write(traceback.format_exc())
        f.write('\n')
        f.write(str(psutil.virtual_memory()))

logging.info("-------------------------")
logging.info(">>>>>>BarBot closed<<<<<<")
