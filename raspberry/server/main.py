#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import statemachine
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
    result = {"action": action}

    if action == "status":
        result.update({"status": bot.action, "message": bot.message})
        if result["status"] == "mixing":
            result.update({"progress": bot.progress})
            result.update({"instruction": bot.data["recipe"]["instruction"]})
        return result

    elif action == "listrecipes":
        result.update({"recipes": db.getRecipes()})
        return result

    elif action == "getrecipe":
        id = getParameter(request_data, 'id', int)
        if id == None:
            result.update({"error": "no_id_set"})
            return result
        elif id < 0:
            result.update(
                {"recipe": None, "ingredients": db.getAllIngredients()})
            return result
        result.update({"recipe": db.getRecipe(
            id), "ingredients": db.getAllIngredients()})
        return result

    elif action == "saverecipe":
        if not bot.canManipulateDatabase():
            result.update({"error": "busy"})
            return result
        # get variables
        name = getParameter(request_data, "name")
        instruction = getParameter(request_data, "instruction")
        id = getParameter(request_data, "rid", int)
        item_amounts = request_data.get("amount[]")
        item_ids = request_data.get("id[]")
        item_ingredients = request_data.get("ingredient[]")
        # check data
        if name == None or name == "":
            result.update({"error": "name_empty"})
            return result
        if id == None:
            result.update({"error": "no_id_set"})
            return result
        if item_amounts == None or len(item_amounts) == 0 or \
                item_ids == None or len(item_ids) == 0 or \
                item_ingredients == None or len(item_ingredients) == 0 or \
                len(item_amounts) != len(item_ingredients) or \
                len(item_amounts) != len(item_ids):
            result.update({"error": "wrong_data"})
            return result
        # prepare data
        items = []
        for i in range(0, len(item_amounts)):
            ingredient = int(item_ingredients[i])
            amount = int(item_amounts[i])
            if ingredient >= 0 and amount >= 0:
                items.append({"ingredient": ingredient, "amount": amount})
        if not db.recipeChanged(id, name, items, instruction):
            result.update({"message": "nothing_changed", "recipe": db.getRecipe(
                id), "ingredients": db.getAllIngredients()})
            return result
        # update database
        new_id = db.createOrUpdateRecipe(name, instruction, id)
        db.addRecipeItems(new_id, items)
        if id < 0:
            result.update({"message": "created", "recipe": db.getRecipe(
                new_id), "ingredients": db.getAllIngredients()})
            return result
        else:
            result.update({"message": "updated", "recipe": db.getRecipe(
                new_id), "ingredients": db.getAllIngredients()})
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

    elif action == "order":
        if bot.isArduinoBusy():
            result.update({"error": "busy"})
            return result
        id = getParameter(request_data, "id", int)
        if id == None:
            result.update({"error": "no_id_set"})
            return result
        recipe = db.getRecipe(id)
        if recipe == None:
            result.update({"error": "recipe_not_found"})
            return result
        db.startOrder(recipe["id"])
        bot.startMixing(recipe)
        result.update({"message": "mixing_started"})
        return result

    elif action == "single_ingredient":
        result.update({"ports": db.getIngredientOfPort(
        ), "ingredients": db.getAllIngredients()})
        if bot.isArduinoBusy():
            result.update({"error": "busy"})
            return result
        iid = getParameter(request_data, "ingredient", int)
        amount = getParameter(request_data, "amount", int)
        if iid == None:
            # nothing to do, just return the ports and ingredients
            return result
        port_cal = db.getPortAndCalibration(iid)
        if port_cal == None:
            result.update({"error": "not_available"})
            return result
        item = port_cal
        item["amount"] = amount
        bot.startSingleIngredient(item)
        result.update({"message": "single_ingredient_started"})
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

bot = statemachine.StateMachine(OnMixingFinished, db.getStrSetting(
    "arduino_port"), db.getStrSetting("arduino_baud"))
bot.rainbow_duration = db.getIntSetting("rainbow_duration")
bot.max_speed = db.getIntSetting("max_speed")
bot.max_accel = db.getIntSetting("max_accel")
if not is_demo:
    bot.start()
else:
    bot.action = "idle"

server = server.server(OnRequest)
server.start()

print("Server started")
if is_demo:
    print("Demo mode")

try:
    if not is_demo:
        bot.join()
    server.join()
except KeyboardInterrupt:
    raise
