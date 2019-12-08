#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
import barbot
import barbotgui
import os
import qdarkstyle
import sys
import config
import logging


# cofigure logging
logging.basicConfig(
    filename=os.path.join(sys.path[0], '../bar_bot.log'),
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

is_demo = "-d" in sys.argv[1:]

# open database
db_filename = os.path.join(sys.path[0], '../bar_bot.sqlite')
db = barbot.Database(db_filename)
db.clear_order()

if not is_demo and barbotgui.is_raspberry():
    # connect bluetooth device
    barbot.run_command("sudo rfcomm connect hci0 %s&" % config.mac_adress)
# create statemachine
port = config.com_port_linux if barbotgui.is_raspberry() else config.com_port_windows
bot = barbot.StateMachine(port, config.baud_rate, is_demo)
bot.on_mixing_finished = lambda rid: db.close_order(rid)
bot.rainbow_duration = config.rainbow_duration
bot.max_speed = config.max_speed
bot.max_accel = config.max_accel
bot.max_cocktail_size = config.max_cocktail_size
bot.start()

# show gui and join the threads
try:
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    form = barbotgui.MainWindow(db, bot, config.admin_password)
    form.show()
    app.exec_()
    # tell the statemachine to stop
    bot.abort = True
    if not is_demo:
        bot.join()
except KeyboardInterrupt:
    raise
