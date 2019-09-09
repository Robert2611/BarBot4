import time
import threading
import BarBot.Communication
import sys
import os
import subprocess
import sqlite3 as lite

from enum import Enum, auto

def getAbsolutePath(relative_path):
    dirname = sys.path[0]
    filename = os.path.join(dirname, relative_path)
    return filename

def runCommand(cmd_str):
    subprocess.Popen([cmd_str], shell=True, stdin=None,
                     stdout=None, stderr=None, close_fds=True)

class State(Enum):
    CONNECTING = auto()
    STARTUP = auto()
    IDLE = auto()
    MIXING = auto()
    CLEANING = auto()
    CLEANING_CYCLE = auto()
    SINGLE_INGREDIENT = auto()

class UserMessages(Enum):
    MixingDoneRemoveGlas = auto()
    PlaceGlas = auto()
    IngredientEmpty = auto()

class StateMachine(threading.Thread):
    OnMixingFinished = None
    OnMixingProgressChanged = None
    OnStateChanged = None
    OnMessageChanged = None

    progress = None
    data = None
    abort = False
    message:UserMessages = None
    user_input = None
    rainbow_duration = 10
    max_speed = 100
    max_accel = 100
    demo = False
    protocol:BarBot.Communication.Protocol = None

    def __init__(self, port, baudrate, demo = False):
        threading.Thread.__init__(self)
        self.demo = demo
        if not demo:
            self.protocol = BarBot.Communication.Protocol(port, baudrate, 1)
            self.setState(State.CONNECTING)
        self.setState(State.IDLE)

    # main loop, runs the whole time
    def run(self):
        while not self.abort:
            if self.state == State.CONNECTING:
                if self.protocol.Connect():
                    self.setState(State.STARTUP)
                else:
                    time.sleep(1)
            elif self.state == State.STARTUP:
                if self.protocol.ReadMessage().type == BarBot.Communication.MessageTypes.STATUS:
                    self.protocol.Set("SetLED", 3)
                    self.protocol.Set("SetSpeed", self.max_speed)
                    self.protocol.Set("SetAccel", self.max_accel)
                    self.setState(State.IDLE)
            elif self.state == State.MIXING:
                self.doMixing()
                self.setState(State.IDLE)
            elif self.state == State.CLEANING:
                self.doCleaning()
                self.setState(State.IDLE)
            elif self.state == State.CLEANING_CYCLE:
                self.doCleaningCycle()
                self.setState(State.IDLE)
            elif self.state == State.SINGLE_INGREDIENT:
                self.doSingleIngredient()
                self.setState(State.IDLE)
            else:
                if not self.demo:
                    # update as long as there is data to be read
                    while self.protocol.Update():
                        pass
                    if not self.protocol.isConnected:
                        self.setState(State.CONNECTING)
                else:
                    time.sleep(0.1)
        if not self.demo:
            self.protocol.Close()

    def setUserInput(self, value:bool):
        self.user_input = value
    
    def setState(self, state):
        self.state = state
        if self.OnStateChanged is not None:
            self.OnStateChanged()
    
    def setMixingProgress(self, progress):
        self.progress = progress
        if self.OnMixingProgressChanged is not None:
            self.OnMixingProgressChanged()
    
    def setMessage(self, message:UserMessages):        
        self.message = message
        if self.OnMessageChanged is not None:
            self.OnMessageChanged()

    def isArduinoBusy(self):
        return self.state != State.IDLE

    def canManipulateDatabase(self):
        return self.state == State.CONNECTING or self.state == State.IDLE

    # do commands

    def doMixing(self):
        if self.demo:
            # self.setMessage(UserMessages.MixingDoneRemoveGlas)
            # time.sleep(2)
            # self.setMessage(None)
            # for item in self.data["recipe"]["items"]:
            #     self.data["recipe_item_index"] += 1
            #     maxProgress = len(self.data["recipe"]["items"])
            #     self.setMixingProgress(self.data["recipe_item_index"] / maxProgress)
            #     time.sleep(2)
            # return
            self.setMessage(UserMessages.IngredientEmpty)
            self.user_input = None
            # wait for user input
            while self.user_input is None:
                time.sleep(0.5)
            # remove the message
            self.setMessage(None)
            print(self.user_input)
            return
        # wait for the glas
        self.setMessage(UserMessages.PlaceGlas)
        self.protocol.Do("PlatformLED", 4)
        while self.protocol.Get("HasGlas") != "1":
            pass
        # glas is there, wait a second to let the user take away the hand
        self.protocol.Do("PlatformLED", 3)
        self.setMessage(None)
        time.sleep(1)
        self.protocol.Do("PlatformLED", 5)
        for item in self.data["recipe"]["items"]:
            # don't do anything else if user has aborted
            self.protocol.Set("SetLED", 4)
            # do the actual draft, exit the loop if it did not succeed
            if not self.draft_one(item):
                break
            self.data["recipe_item_index"] += 1
            maxProgress = len(self.data["recipe"]["items"]) - 1
            self.setMixingProgress(self.data["recipe_item_index"] / maxProgress)
        self.protocol.Do("Move", 0)
        self.setMessage(UserMessages.MixingDoneRemoveGlas)
        self.protocol.Do("PlatformLED", 2)
        self.protocol.Set("SetLED", 2)
        while self.protocol.Get("HasGlas") != "0":
            time.sleep(0.5)
        self.setMessage(None)
        self.protocol.Do("PlatformLED", 0)
        if OnMixingFinished is not None:
            self.OnMixingFinished(self.data["recipe"]["id"])
        self.protocol.Set("SetLED", 3)

    def draft_one(self, item):
        if item["port"] == 12:
            self.protocol.Do("Stir", item["amount"] * 1000)
        else:
            while True:
                weight = int(item["amount"] * item["calibration"])
                result = self.protocol.Do("Draft", item["port"], weight)
                if result == True:
                    # drafting successfull
                    return True
                elif type(result) is list and len(result) >= 2 and int(result[0]) == 12:
                    #ingredient is empty
                    # safe how much is left to draft
                    item["amount"] = int(result[1]) / item["calibration"]
                    print(UserMessages.IngredientEmpty)
                    self.setMessage(UserMessages.IngredientEmpty)
                    self.user_input = None
                    # wait for user input
                    while self.user_input is None:
                        time.sleep(0.5)
                    # remove the message
                    self.setMessage(None)
                    if not self.user_input:
                        return False
                    # repeat the loop
                else:
                    # unhandled error while drafting
                    return False

    def doCleaningCycle(self):
        if self.demo:
            time.sleep(2)
            return
        self.setMessage(UserMessages.PlaceGlas)
        while self.protocol.Get("HasGlas") != "1":
            time.sleep(0.5)
        self.setMessage(None)
        for item in self.data:
            weight = int(item["amount"] * item["calibration"])
            self.protocol.Do("Draft", item["port"], weight)
        self.protocol.Do("Move", 0)

    def doCleaning(self):
        if self.demo:
            time.sleep(2)
            return
        self.protocol.Do("Draft", self.data["port"], int(self.data["weight"]))

    def doSingleIngredient(self):
        if self.demo:
            time.sleep(2)
            return
        self.setMessage(UserMessages.PlaceGlas)
        while self.protocol.Get("HasGlas") != "1":
            time.sleep(0.5)
        self.setMessage(None)
        self.draft_one(self.data)
        self.protocol.Do("Move", 0)

    # start commands

    def startMixing(self, recipe):
        self.data = {"recipe": recipe, "recipe_item_index": 0}
        self.setState(State.MIXING)

    def startSingleIngredient(self, recipe_item):
        self.data = recipe_item
        self.setState(State.SINGLE_INGREDIENT)

    def startCleaning(self, port, weight):
        self.data = {"port": port, "weight": weight}
        self.setState(State.CLEANING)

    def startCleaningCycle(self, data):
        self.data = data
        self.setState(State.CLEANING_CYCLE)
    

class Database(object):
    con:lite.Connection
    filename:str
    isConnected:bool = False
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        if self.isConnected:
            return
        self.con = lite.connect(self.filename)
        self.con.row_factory = lite.Row
        self.cursor = self.con.cursor()
        self.isConnected = True

    def close(self):
        if(self.con is not None):
            self.con.close()
        self.con = None
        self.cursor = None
        self.isConnected = False

    def getIngredientOfPort(self):
        # only open/close if called while not connected
        wasOpen = self.isConnected
        if not wasOpen:
            self.open()
        self.cursor.execute("""
			SELECT ingredient as iid, id as port
			FROM Ports
		""")
        res = dict()
        for ingredient in self.cursor.fetchall():
            res[ingredient["port"]] = ingredient["iid"]
        if not wasOpen:
            self.close()
        return res

    def getPortAndCalibration(self, iid):
        self.open()
        self.cursor.execute("""
			SELECT p.id as port,  i.calibration AS calibration
			FROM Ports p
			JOIN Ingredients i
			ON p.ingredient = i.id
			WHERE i.id = :iid
		""", {"iid": iid})
        res = self.cursor.fetchone()
        if res == None:
            self.close()
            return None
        return dict(res)

    def getAllIngredients(self):
        self.open()
        self.cursor.execute("""
			SELECT i.id, i.name, i.type, i.calibration, p.id as port
			FROM Ingredients i
			LEFT JOIN Ports p
			ON p.ingredient = i.id
		""")
        res = dict()
        for ingredient in self.cursor.fetchall():
            res[ingredient["id"]] = dict(ingredient)
        self.close()
        return res

    def getRecipes(self):
        self.open()
        self.cursor.execute("""
			SELECT name, id
			FROM Recipes
			WHERE successor_id IS NULL
		""")
        recipes = []
        for row in self.cursor.fetchall():
            recipe = dict(row)
            self.addAllRecipeItems(recipe)
            recipes.append(recipe)
        self.close()
        return recipes

    def addAllRecipeItems(self, recipe):
        availableIngredients = self.getIngredientOfPort().values()
        self.cursor.execute("""
			SELECT ri.id, ri.amount, i.name, ri.Ingredient AS iid, i.calibration AS calibration, p.id as port
			FROM RecipeItems ri
			JOIN Ingredients i
			ON i.id = ri.Ingredient
			LEFT JOIN Ports p
			ON p.ingredient = ri.Ingredient
			WHERE ri.Recipe = :rid
		""", {"rid": recipe["id"]})
        rows = self.cursor.fetchall()
        recipe["items"] = []
        if len(rows) == 0:
            recipe["available"] = False
            return
        recipe_available = True
        for item_row in rows:
            # get all fields from the query and make a dictionary
            item = dict(item_row)
            item["available"] = item["iid"] in availableIngredients
            if not item["available"]:
                recipe_available = False
            recipe["items"].append(item)
        recipe["available"] = recipe_available

    def getRecipe(self, rid):
        self.open()
        self.cursor.execute("""
			SELECT name, id, instruction
			FROM Recipes
			WHERE successor_id IS NULL
			AND id = :rid
		""", {"rid": rid})
        res = self.cursor.fetchone()
        # does the recipe exits?
        if res == None:
            self.close()
            return None
        recipe = dict(res)
        # fetch items
        self.addAllRecipeItems(recipe)
        self.close()
        return recipe

    # returns: new recipe id
    def createOrUpdateRecipe(self, name, instruction, old_rid=-1):
        self.open()
        self.cursor.execute("""
			INSERT INTO Recipes ( name, instruction, successor_id )
			VALUES ( :name, :instruction, NULL )
		""", {"name": name, "instruction": instruction})
        self.con.commit()
        new_rid = self.cursor.lastrowid
        if(old_rid is not None and old_rid >= 0):
            # set newly created recipe as successor for current recipe
            self.cursor.execute("""
				UPDATE Recipes
				SET successor_id = :new_rid
				WHERE id = :old_rid
			""", {"old_rid": old_rid, "new_rid": new_rid})
            self.con.commit()
        self.close()
        return new_rid

    def removeRecipe(self, rid):
        self.open()
        self.cursor.execute("""
            UPDATE Recipes
            SET successor_id = -1
            WHERE id = :rid
        """, {"rid": rid})
        self.con.commit()
        self.close()
        
    def addRecipeItems(self, rid, items):
        self.open()
        for item in items:
            self.cursor.execute("""
				INSERT INTO RecipeItems ( Recipe, ingredient, amount )
				VALUES ( :rid, :ingredient, :amount )
			""", {"rid": rid, "ingredient": item["ingredient"], "amount": item["amount"]})
        self.con.commit()
        self.close()

    def recipeChanged(self, rid, name, items, instruction):
        self.open()
        self.cursor.execute("""
			SELECT name, instruction
			FROM Recipes
			WHERE id = :rid
		""", {"rid": rid})
        recipe_in_Database = self.cursor.fetchone()
        # recipe not found, so it must be different
        if recipe_in_Database == None:
            self.close()
            return True
        # name has changed
        elif recipe_in_Database["name"] != name:
            self.close()
            return True
        # instruction has changed
        elif recipe_in_Database["instruction"] != instruction and not (not recipe_in_Database["instruction"] and not instruction):
            self.close()
            return True
        self.cursor.execute("""
			SELECT id, ingredient, amount
			FROM RecipeItems
			WHERE recipe = :rid
			ORDER BY id ASC
		""", {"rid": rid})
        items_in_Database = self.cursor.fetchall()
        if len(items_in_Database) != len(items):
            print(items_in_Database)
            self.close()
            return True

        for i in range(0, len(items_in_Database)):
            if items_in_Database[i]["ingredient"] != items[i]["ingredient"] or \
                    items_in_Database[i]["amount"] != items[i]["amount"]:
                # item has changed
                self.close()
                return True
        self.close()
        return False

    def startOrder(self, rid):
        self.open()
        self.cursor.execute("""
			INSERT INTO Orders ( recipe, started, status )
			VALUES ( :rid, DATETIME('now'), 0 )
		""", {"rid": rid})
        self.con.commit()
        self.close()

    def closeOrder(self, rid):
        self.open()
        self.cursor.execute("""
			UPDATE Orders
			SET finished = DATETIME('now'), status = 1
			WHERE recipe = :rid
		""", {"rid": rid})
        self.con.commit()
        self.close()

    def clearOrders(self):
        self.open()
        self.cursor.execute("""
			UPDATE Orders
			SET status = -1
			WHERE status = 0
		""")
        self.con.commit()
        self.close()

    def setPorts(self, ports):
        self.open()
        for port, iid in ports.items():
            self.cursor.execute("""
				UPDATE Ports
				SET ingredient = :iid
				WHERE id = :port
			""", {"iid": iid, "port": port})
        self.con.commit()
        self.close()

    def setCalibration(self, port, calibration):
        self.open()
        self.cursor.execute("""
			UPDATE Ingredients
			SET calibration = :calibration
			WHERE id = (
						SELECT ingredient
						FROM Ports
						WHERE id = :port
						)
		""", {'calibration': calibration, 'port': port})
        self.con.commit()
        self.close()

    def getStrSetting(self, name):
        self.open()
        self.cursor.execute("""
			SELECT value
			FROM Settings
			WHERE name=:name
		""", {'name': name})
        res = self.cursor.fetchone()
        self.close()
        return res["value"]

    def getIntSetting(self, name):
        return int(self.getStrSetting(name))

    def getOrderedCocktailCount(self, date):
        self.open()
        self.cursor.execute("""
			SELECT r.name, r.id AS rid, COUNT(*) AS count
			FROM Orders O
			JOIN Recipes r
			ON r.id = O.recipe
			WHERE O.started >= DATETIME(:date, "+0.5 days")
			AND O.started < DATETIME(:date, "+1.5 days")
			GROUP BY r.id
			ORDER BY count DESC
		""", {'date': date})
        res = [dict(row) for row in self.cursor.fetchall()]
        return res

    def getOrderedIngredientsAmount(self, date):
        self.open()
        self.cursor.execute("""
			SELECT i.name AS ingredient, i.id AS iid, SUM(ri.amount)/100 AS liters
			FROM RecipeItems ri
			JOIN Orders o
			ON o.recipe = ri.recipe
			JOIN Ingredients i
			ON i.id = ri.ingredient
			WHERE O.started >= DATETIME(:date, "+0.5 days")
			AND O.started < DATETIME(:date, "+1.5 days")
			GROUP BY i.id
			ORDER BY liters DESC
		""", {'date': date})
        res = [dict(row) for row in self.cursor.fetchall()]
        return res

    def getOrderedCocktailsByTime(self, date):
        self.open()
        self.cursor.execute("""
			SELECT strftime('%Y-%m-%d %H',o.started) AS hour, count(*) AS count
			FROM Orders o
			WHERE O.started >= DATETIME(:date, "+0.5 days")
			AND O.started < DATETIME(:date, "+1.5 days")
			GROUP BY hour
		""", {'date': date})
        res = [dict(row) for row in self.cursor.fetchall()]
        return res

    def getParties(self):
        self.open()
        self.cursor.execute("""
			SELECT partydate, ordercount
			FROM (
				SELECT date(o.started, "-0.5 days") AS partydate,  count(o.id) as ordercount
				FROM Orders o
				GROUP BY partydate
				ORDER BY partydate DESC
			)
			WHERE ordercount > 10
		""")
        res = [dict(row) for row in self.cursor.fetchall()]
        return res
