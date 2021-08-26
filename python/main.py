#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from barbot import statemachine
from PyQt5 import QtWidgets
import barbot
import barbotgui
import sys
import threading
from datetime import datetime
from barbot import directories

# cofigure logging
log_file = datetime.now().strftime("BarBot %Y-%m-%d %H-%M-%S.log")
log_file_path = directories.join(directories.log, log_file)
# for some reason the logger is already configured, so we have to remove the handler
logging.getLogger().handlers.clear()
logging.basicConfig(
    filename=log_file_path,
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s\t%(message)s'
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
