#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
import barbot
import barbotgui
import os
import qdarkstyle
import sys
import logging
import configparser
from datetime import datetime

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

# open database
db_filename = os.path.join(sys.path[0], '../bar_bot.sqlite')
db = barbot.Database(db_filename)
db.clear_order()

# create statemachine
config_path = os.path.join(sys.path[0], '../bar_bot.cfg')
bot = barbot.StateMachine(config_path, is_demo)
bot.on_mixing_finished = lambda rid: db.close_order(rid)
bot.start()

# show gui and join the threads
try:
    app = QtWidgets.QApplication(sys.argv)
    form = barbotgui.MainWindow(db, bot)
    form.show()
    app.exec_()
    # tell the statemachine to stop
    bot.abort = True
    if not is_demo:
        bot.join()
except KeyboardInterrupt:
    raise

logging.info("-------------------------")
logging.info(">>>>>>BarBot closed<<<<<<")
