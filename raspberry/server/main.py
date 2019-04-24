#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import com
import database
import server
import os
import sys

import logging
import json

STIR_INGREDIENT = 255

is_demo = len(sys.argv) >= 2 and sys.argv[1] == "-d"


def getParameter(request_data, index, converter=None):
    value = request_data.get(index)
    if value == None:
        return None
    elif converter != None:
        return converter(value[0])
    else:
        return value[0]


def OnRequest(action, request_data):
    if action == "status":
        return {"status": com.action, "progress": com.progress, "message": com.message}

    elif action == "listrecipes":
        return {"recipes": db.getRecipes()}

    elif action == "getrecipe":
        id = getParameter(request_data, 'id', int)
        if id == None:
            return {"error": "no_id_set"}
        elif id < 0:
            return {"recipe": None, "ingredients": db.getAllIngredients()}
        return {"recipe": db.getRecipe(id), "ingredients": db.getAllIngredients()}

    elif action == "saverecipe":
        if not com.canManipulateDatabase():
            return {"error": "busy"}
        # get variables
        name = getParameter(request_data, "name")
        id = getParameter(request_data, "rid", int)
        item_amounts = request_data.get("amount[]")
        item_ids = request_data.get("id[]")
        item_ingredients = request_data.get("ingredient[]")
        # check data
        if name == None or name == "":
            return {"error": "name_empty"}
        if id == None:
            return {"error": "no_id_set"}
        if item_amounts == None or len(item_amounts) == 0 or \
                item_ids == None or len(item_ids) == 0 or \
                item_ingredients == None or len(item_ingredients) == 0 or \
                len(item_amounts) != len(item_ingredients) or \
                len(item_amounts) != len(item_ids):
            return {"error": "wrong_data"}
        # prepare data
        items = []
        for i in range(0, len(item_amounts)):
            ingredient = int(item_ingredients[i])
            amount = int(item_amounts[i])
            if ingredient >= 0 and amount >= 0:
                items.append({"ingredient": ingredient, "amount": amount})
        if not db.recipeChanged(id, name, items):
            return {"message": "nothing_changed", "recipe": db.getRecipe(id), "ingredients": db.getAllIngredients()}
        # update database
        new_id = db.createOrUpdateRecipe(name, id)
        db.addRecipeItems(new_id, items)
        if id < 0:
            return {"message": "created", "recipe": db.getRecipe(new_id), "ingredients": db.getAllIngredients()}
        else:
            return {"message": "updated", "recipe": db.getRecipe(new_id), "ingredients": db.getAllIngredients()}

    elif action == "order":
        if com.isArduinoBusy():
            return {"error": "busy"}
        id = getParameter(request_data, "id", int)
        if id == None:
            return {"error": "no_id_set"}
        recipe = db.getRecipe(id)
        if recipe == None:
            return {"error": "recipe_not_found"}
        db.startOrder(recipe["id"])
        com.startMixing(recipe)
        return {"message": "mixing_started"}

    elif action == "single_ingredient":
        result = {"ports": db.getIngredientOfPort(), "ingredients": db.getAllIngredients()}
        if com.isArduinoBusy():
            result.update({"error": "busy"})
            return result
        iid = getParameter(request_data, "ingredient", int)
        amount = getParameter(request_data, "amount", int)
        if iid == None:
            #nothing to do, just return the ports and ingredients
            return result
        port_cal = db.getPortAndCalibration(iid)
        if port_cal == None:
            result.update({"error": "not_available"})
            return result
        com.startSingleIngredient( port_cal["port"], port_cal["calibration"] * amount)
        result.update({"error": "single_ingredient_started"})
        return result

    elif action == "admin":
        return {"ports": db.getIngredientOfPort(), "ingredients": db.getAllIngredients()}

    elif action == "setports":
        if not com.canManipulateDatabase():
            return {"error": "busy"}
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
            return {"error": "ports_not_complete"}
        db.setPorts(ports)
        return {"message": "ports_set", "ports": db.getIngredientOfPort(), "ingredients": db.getAllIngredients()}

    elif action == "setcalibration":
        if not com.canManipulateDatabase():
            return {"error": "busy"}
        port = getParameter(request_data, "port", int)
        calibration = getParameter(request_data, "calibration", int)
        if port == None or calibration == None:
            return {"error": "wrong_data"}
        db.setCalibration(port, calibration)
        return {"message": "calibration_set", "ports": db.getIngredientOfPort(), "ingredients": db.getAllIngredients()}

    elif action == "calibrate":
        if not com.canManipulateDatabase():
            return {"error": "busy"}
        port = getParameter(request_data, "port", int)
        duration = db.getIntSetting("calibrate_duration")
        com.startCleaning(port, duration)
        return {"message": "calirate_started"}

    elif action == "clean":
        if com.isArduinoBusy():
            return {"error": "busy"}
        port = getParameter(request_data, "port", int)
        duration = db.getIntSetting("clean_duration")
        com.startCleaning(port, duration)
        return {"message": "clean_started"}

    elif action == "clean_cycle_left":
        if com.isArduinoBusy():
            return {"error": "busy"}
        duration = db.getIntSetting("clean_duration") * 5
        data = []
        for port in range(0, 6):
            data.append({"port": port, "duration": duration})
        com.startCleaningCycle(data)
        return {"message": "clean_started"}

    elif action == "clean_cycle_right":
        if com.isArduinoBusy():
            return {"error": "busy"}
        duration = db.getIntSetting("clean_duration") * 5
        data = []
        for port in range(6, 12):
            data.append({"port": port, "duration": duration})
        com.startCleaningCycle(data)
        return {"message": "clean_started"}

    elif action == "statistics":
        result = {"parties": db.getPartyDates()}
        date = getParameter(request_data, "date")
        if date == None:
            date = result["parties"][0]["partydate"]
        result["total_count"] = result["parties"][0]["ordercount"]
        result["cocktail_count"] = db.getOrderedCocktailCount(date)
        result["ingredients_amount"] = db.getOrderedIngredientsAmount(date)
        result["cocktails_by_time"] = db.getOrderedCocktailsByTime(date)
        result["total_amount"] = sum([ia["liters"]
                                      for ia in result["ingredients_amount"]])
        result["date"] = date
        return result


def OnMixingFinished(rid):
    db.closeOrder(rid)

# logging.basicConfig(
#	level = logging.INFO,
#	format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
#	datefmt = '%d.%m.%y %H:%M',
#	filename = 'bar_bot.log'
#	#filename = '/home/pi/bar_bot/bar_bot.log'
# )


dirname = sys.path[0]
filename = os.path.join(dirname, '../bar_bot.sqlite')
db = database.database(filename)
db.clearOrders()

com = com.com(OnMixingFinished, db.getStrSetting(
    "arduino_port"), db.getStrSetting("arduino_baud"))
com.settings = {
    "rainbow_duration": db.getIntSetting("rainbow_duration"),
    "max_speed": db.getIntSetting("max_speed"),
    "max_accel": db.getIntSetting("max_accel")
}
if not is_demo:
    com.start()
else:
    com.action = "idle"

server = server.server(OnRequest)
server.start()

print("Server started")
if is_demo:
    print("Demo mode")

try:
    if not is_demo:
        com.join()
    server.join()
except KeyboardInterrupt:
    raise
