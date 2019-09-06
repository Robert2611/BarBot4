#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
import BarBot
import BarBotGui
import os
import qdarkstyle
import sys

#sudo rfcomm connect hci0 20:16:04:14:60:60&

is_demo = "-d" in sys.argv[1:]

#open database
dirname = sys.path[0]
filename = os.path.join(dirname, '../bar_bot.sqlite')
db = BarBot.Database(filename)
db.clearOrders()

#create statemachine
bot = BarBot.StateMachine(db.getStrSetting("arduino_port"), db.getStrSetting("arduino_baud"), is_demo)
bot.OnMixingFinished = lambda rid: db.closeOrder(rid)
bot.rainbow_duration = db.getIntSetting("rainbow_duration")
bot.max_speed = db.getIntSetting("max_speed")
bot.max_accel = db.getIntSetting("max_accel")
bot.start()
if not is_demo:
    print("BarBot started")
else:
    print("Demo mode")

#show gui and join the threads
try:
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    form = BarBotGui.MainWindow(db, bot)
    form.show()
    app.exec_()
    # tell the statemachine to stop
    bot.abort = True
    if not is_demo:
        bot.join()
except KeyboardInterrupt:
    raise
