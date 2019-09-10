#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
import barbot
import barbotgui
import os
import qdarkstyle
import sys
import config

#sudo rfcomm connect hci0 20:16:04:14:60:60&

is_demo = "-d" in sys.argv[1:]

#open database
dirname = sys.path[0]
filename = os.path.join(dirname, '../bar_bot.sqlite')
db = barbot.Database(filename)
db.clear_order()

#create statemachine
bot = barbot.StateMachine(config.com_port, config.baud_rate, is_demo)
bot.on_mixing_finished = lambda rid: db.close_order(rid)
bot.rainbow_duration = config.rainbow_duration
bot.max_speed = config.max_speed
bot.max_accel = config.max_accel
bot.start()
if not is_demo:
    print("barbot started")
else:
    print("Demo mode")

#show gui and join the threads
try:
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    form = barbotgui.MainWindow(db, bot)
    form.show()
    app.exec_()
    # tell the statemachine to stop
    bot.abort = True
    if not is_demo:
        bot.join()
except KeyboardInterrupt:
    raise
