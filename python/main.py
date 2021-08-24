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
from barbot import botconfig

# cofigure logging
log_path = os.path.join(sys.path[0], "../log/")
if not os.path.exists(log_path):
    os.makedirs(log_path)
logging.basicConfig(
    filename=os.path.join(
        log_path, datetime.now().strftime("BarBot %Y-%m-%d %H-%M-%S.log")),
    filemode='a',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.info("<<<<<<BarBot started>>>>>>")
logging.info("--------------------------")

is_demo = "-d" in sys.argv[1:]

# create statemachine
if not is_demo:
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
    if not is_demo:
        bar_bot_thread.join()
except KeyboardInterrupt:
    raise

logging.info("-------------------------")
logging.info(">>>>>>BarBot closed<<<<<<")
