#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMainWindow, QApplication
import Statemachine
import Database
import BarBotMainWindow
import os
import qdarkstyle
import sys
import logging
import json

#sudo rfcomm connect hci0 20:16:04:14:60:60&

is_demo = "-d" in sys.argv[1:]

def getParameter(request_data, index, converter=None):
    value = request_data.get(index)
    if value == None:
        return None
    elif converter != None:
        return converter(value[0])
    else:
        return value[0]


def OnRequest(action, request_data):
    result = {"action": action}

    if action == "status":
        result.update({"status": bot.action, "message": bot.message})
        if result["status"] == "mixing":
            result.update({"progress": bot.progress})
            result.update({"instruction": bot.data["recipe"]["instruction"]})
        return result

    elif action == "remove_recipe":
        if not bot.canManipulateDatabase():
            result.update({"error": "busy"})
            return result
        id = getParameter(request_data, 'id', int)        
        if id == None:
            result.update({"recipes": db.getRecipes()})
            result.update({"error": "no_id_set"})
            return result
        elif id < 0:
            return result
        db.removeRecipe(id)
        result.update({"message": "recipe_removed"})
        result.update({"recipes": db.getRecipes()})
        return result

    elif action == "admin":
        result.update({"ports": db.getIngredientOfPort()})
        result.update({"ingredients": db.getAllIngredients()})
        result.update({"recipes": db.getRecipes()})
        return result

    elif action == "setports":
        if not bot.canManipulateDatabase():
            result.update({"error": "busy"})
            return result
        db_ports = db.getIngredientOfPort()
        ports = dict()
        portsOK = True
        for port in db_ports.keys():
            if port >= 12:
                continue
            param = getParameter(request_data, "port_" + str(port), int)
            if(param == None):
                portsOK = False
            else:
                ports[port] = param
        if not portsOK:
            result.update({"error": "ports_not_complete"})
            return result
        db.setPorts(ports)
        result.update({"message": "ports_set", "ports": db.getIngredientOfPort(
        ), "ingredients": db.getAllIngredients()})
        return result

    elif action == "setcalibration":
        if not bot.canManipulateDatabase():
            result.update({"error": "busy"})
            return result
        port = getParameter(request_data, "port", int)
        calibration = getParameter(request_data, "calibration", int)
        if port == None or calibration == None:
            result.update({"error": "wrong_data"})
            return result
        db.setCalibration(port, calibration)
        result.update({"message": "calibration_set", "ports": db.getIngredientOfPort(
        ), "ingredients": db.getAllIngredients()})
        return result

    elif action == "calibrate":
        if not bot.canManipulateDatabase():
            result.update({"error": "busy"})
            return result
        port = getParameter(request_data, "port", int)
        duration = db.getIntSetting("calibrate_duration")
        bot.startCleaning(port, duration)
        result.update({"message": "calirate_started"})
        return result

    elif action == "clean":
        if bot.isArduinoBusy():
            result.update({"error": "busy"})
            return result
        port = getParameter(request_data, "port", int)
        duration = db.getIntSetting("clean_duration")
        bot.startCleaning(port, duration)
        result.update({"message": "clean_started"})
        return result

    elif action == "clean_cycle_left":
        if bot.isArduinoBusy():
            result.update({"error": "busy"})
            return result
        duration = db.getIntSetting("clean_duration") * 5
        data = []
        for port in range(0, 6):
            data.append({"port": port, "duration": duration})
        bot.startCleaningCycle(data)
        result.update({"message": "clean_started"})
        return result

    elif action == "clean_cycle_right":
        if bot.isArduinoBusy():
            result.update({"error": "busy"})
            return result
        duration = db.getIntSetting("clean_duration") * 5
        data = []
        for port in range(6, 12):
            data.append({"port": port, "duration": duration})
        bot.startCleaningCycle(data)
        result.update({"message": "clean_started"})
        return result

    elif action == "statistics":
        result.update({"parties": db.getPartyDates()})
        date = getParameter(request_data, "date")
        if date == None:
            date = result["parties"][0]["partydate"]
        result["total_count"] = result["parties"][0]["ordercount"]
        result["cocktail_count"] = db.getOrderedCocktailCount(date)
        result["ingredients_amount"] = db.getOrderedIngredientsAmount(date)
        result["cocktails_by_time"] = db.getOrderedCocktailsByTime(date)
        result["total_amount"] = sum([ia["liters"] for ia in result["ingredients_amount"]])
        result["date"] = date
        return result
    
    elif action == "user_input":
        user_input = getParameter(request_data, "user_input")
        bot.user_input = user_input == "true"       
        return result


dirname = sys.path[0]
filename = os.path.join(dirname, '../bar_bot.sqlite')
db = Database.Database(filename)
db.clearOrders()

bot = Statemachine.StateMachine(db.getStrSetting("arduino_port"), db.getStrSetting("arduino_baud"))
bot.OnMixingFinished = lambda rid: db.closeOrder(rid)
bot.rainbow_duration = db.getIntSetting("rainbow_duration")
bot.max_speed = db.getIntSetting("max_speed")
bot.max_accel = db.getIntSetting("max_accel")
if not is_demo:
    bot.start()
    print("Com started")
else:
    bot.setState(Statemachine.State.IDLE)
    print("Demo mode")

try:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    form = BarBotMainWindow.BarBotMainWindow(db, bot)
    form.show()
    app.exec_()
    if not is_demo:
        bot.join()
except KeyboardInterrupt:
    raise
