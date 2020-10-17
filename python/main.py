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

# cofigure logging
logging.basicConfig(
    filename=os.path.join(sys.path[0], '../bar_bot.log'),
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

if not is_demo and barbotgui.is_raspberry():
    # search for barbot if no valid mac address is set
    if bot.is_mac_address_valid():
        bot.find_bar_bot()
    # connect bluetooth device
    barbot.run_command("sudo rfcomm connect hci0 {}&".format(bot.mac_address))

bot.connect()
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
