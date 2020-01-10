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

# setup config with default values
config = configparser.ConfigParser()
config.add_section("default")
config.set("default", "mac_address", "3C:71:BF:4C:A7:2E")
default_port = "/dev/rfcomm0" if barbotgui.is_raspberry() else "COM4"
config.set("default", "port", default_port)
config.set("default", "baud_rate", "9600")
config.set("default", "rainbow_duration", str(30 * 1000))
config.set("default", "max_speed", str(200))
config.set("default", "max_accel", str(300))
config.set("default", "max_cocktail_size", str(30))
config.set("default", "admin_password", "0000")
config.set("default", "pump_power", str(100))
config.set("default", "balance_tare", str(-119.1))
config.set("default", "balance_cal", str(-1040))
config.set("default", "cleaning_time", str(3000))
config_path = os.path.join(sys.path[0], '../bar_bot.cfg')
# load config if it exists
if os.path.isfile(config_path):
    config.read(config_path)

# search for barbot if -f is set
if "-f" in sys.argv[1:]:
    res = barbot.communication.find_bar_bot()
    if res:
        config.set("default", "mac_address", res)

# safe file again
with open(config_path, 'w') as configfile:
    config.write(configfile)

if not is_demo and barbotgui.is_raspberry():
    # connect bluetooth device
    mac = config.get("default", "mac_address")
    barbot.run_command("sudo rfcomm connect hci0 {}&".format(mac))
# create statemachine
port = config.get("default", "port")
bot = barbot.StateMachine(port, config.get("default", "baud_rate"), is_demo)
bot.on_mixing_finished = lambda rid: db.close_order(rid)
bot.rainbow_duration = config.getint("default", "rainbow_duration")
bot.max_speed = config.getint("default", "max_speed")
bot.max_accel = config.getint("default", "max_accel")
bot.pump_power = config.getint("default", "pump_power")
bot.balance_cal = -1 * config.getint("default", "balance_cal")
bot.cleaning_time = config.getint("default", "cleaning_time")
tare = config.getfloat("default", "balance_tare")
bot.balance_offset = int(tare * bot.balance_cal)
bot.start()

# show gui and join the threads
try:
    app = QtWidgets.QApplication(sys.argv)
    form = barbotgui.MainWindow(
        db, bot, config.get("default", "admin_password"))
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
