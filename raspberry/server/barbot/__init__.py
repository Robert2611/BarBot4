import time
import threading
import barbot.communication
import sys
import os
import subprocess
import sqlite3 as lite

from enum import Enum, auto

def run_command(cmd_str):
    subprocess.Popen([cmd_str], shell=True, stdin=None,
                     stdout=None, stderr=None, close_fds=True)

class State(Enum):
    connecting = auto()
    startup = auto()
    idle = auto()
    mixing = auto()
    cleaning = auto()
    cleaning_cycle = auto()
    single_ingredient = auto()

class UserMessages(Enum):
    mixing_done_remove_glas = auto()
    place_glas = auto()
    ingredient_empty = auto()

class StateMachine(threading.Thread):
    on_mixing_finished = None
    on_mixing_progress_changed = None
    on_state_changed = None
    on_message_changed = None

    progress = None
    data = None
    abort = False
    message:UserMessages = None
    _user_input = None
    rainbow_duration = 10
    max_speed = 100
    max_accel = 100
    demo = False
    protocol:barbot.communication.Protocol = None

    def __init__(self, port, baudrate, demo = False):
        threading.Thread.__init__(self)
        self.demo = demo
        if not demo:
            self.protocol = barbot.communication.Protocol(port, baudrate, 1)
            self.set_state(State.connecting)
        self.set_state(State.idle)

    # main loop, runs the whole time
    def run(self):
        while not self.abort:
            if self.state == State.connecting:
                if self.protocol.connect():
                    self.set_state(State.startup)
                else:
                    time.sleep(1)
            elif self.state == State.startup:
                if self.protocol.read_message().type == barbot.communication.MessageTypes.STATUS:
                    self.protocol.try_set("SetLED", 3)
                    self.protocol.try_set("SetSpeed", self.max_speed)
                    self.protocol.try_set("SetAccel", self.max_accel)
                    self.set_state(State.idle)
            elif self.state == State.mixing:
                self._do_mixing()
                self.set_state(State.idle)
            elif self.state == State.cleaning:
                self._do_cleaning()
                self.set_state(State.idle)
            elif self.state == State.cleaning_cycle:
                self._do_cleaning_cycle()
                self.set_state(State.idle)
            elif self.state == State.single_ingredient:
                self._do_single_ingredient()
                self.set_state(State.idle)
            else:
                if not self.demo:
                    # update as long as there is data to be read
                    while self.protocol.update():
                        pass
                    if not self.protocol.is_connected:
                        self.set_state(State.connecting)
                else:
                    time.sleep(0.1)
        if not self.demo:
            self.protocol.close()

    def set_user_input(self, value:bool):
        self._user_input = value
    
    def set_state(self, state):
        self.state = state
        if self.on_state_changed is not None:
            self.on_state_changed()
    
    def _set_mixing_progress(self, progress):
        self.progress = progress
        if self.on_mixing_progress_changed is not None:
            self.on_mixing_progress_changed()
    
    def _set_message(self, message:UserMessages):        
        self.message = message
        if self.on_message_changed is not None:
            self.on_message_changed()

    def is_busy(self):
        return self.state != State.idle

    def can_edit_database(self):
        return self.state == State.connecting or self.state == State.idle

    # do commands

    def _do_mixing(self):
        if self.demo:
            # self._set_message(UserMessages.mixing_done_remove_glas)
            # time.sleep(2)
            # self._set_message(None)
            # for item in self.data["recipe"]["items"]:
            #     self.data["recipe_item_index"] += 1
            #     maxProgress = len(self.data["recipe"]["items"])
            #     self._set_mixing_progress(self.data["recipe_item_index"] / maxProgress)
            #     time.sleep(2)
            # return
            self._set_message(UserMessages.ingredient_empty)
            self.user_input = None
            # wait for user input
            while self.user_input is None:
                time.sleep(0.5)
            # remove the message
            self._set_message(None)
            print(self.user_input)
            return
        # wait for the glas
        self._set_message(UserMessages.place_glas)
        self.protocol.try_do("PlatformLED", 4)
        while self.protocol.try_get("HasGlas") != "1":
            pass
        # glas is there, wait a second to let the user take away the hand
        self.protocol.try_do("PlatformLED", 3)
        self._set_message(None)
        time.sleep(1)
        self.protocol.try_do("PlatformLED", 5)
        for item in self.data["recipe"]["items"]:
            # don't do anything else if user has aborted
            self.protocol.try_set("SetLED", 4)
            # do the actual draft, exit the loop if it did not succeed
            if not self._draft_one(item):
                break
            self.data["recipe_item_index"] += 1
            maxProgress = len(self.data["recipe"]["items"]) - 1
            self._set_mixing_progress(self.data["recipe_item_index"] / maxProgress)
        self.protocol.try_do("Move", 0)
        self._set_message(UserMessages.mixing_done_remove_glas)
        self.protocol.try_do("PlatformLED", 2)
        self.protocol.try_set("SetLED", 2)
        while self.protocol.try_get("HasGlas") != "0":
            time.sleep(0.5)
        self._set_message(None)
        self.protocol.try_do("PlatformLED", 0)
        if on_mixing_finished is not None:
            self.on_mixing_finished(self.data["recipe"]["id"])
        self.protocol.try_set("SetLED", 3)

    def _draft_one(self, item):
        if item["port"] == 12:
            self.protocol.try_do("Stir", item["amount"] * 1000)
        else:
            while True:
                weight = int(item["amount"] * item["calibration"])
                result = self.protocol.try_do("Draft", item["port"], weight)
                if result == True:
                    # drafting successfull
                    return True
                elif type(result) is list and len(result) >= 2 and int(result[0]) == 12:
                    #ingredient is empty
                    # safe how much is left to draft
                    item["amount"] = int(result[1]) / item["calibration"]
                    print(UserMessages.ingredient_empty)
                    self._set_message(UserMessages.ingredient_empty)
                    self.user_input = None
                    # wait for user input
                    while self.user_input is None:
                        time.sleep(0.5)
                    # remove the message
                    self._set_message(None)
                    if not self.user_input:
                        return False
                    # repeat the loop
                else:
                    # unhandled error while drafting
                    return False

    def _do_cleaning_cycle(self):
        if self.demo:
            time.sleep(2)
            return
        self._set_message(UserMessages.place_glas)
        while self.protocol.try_get("HasGlas") != "1":
            time.sleep(0.5)
        self._set_message(None)
        for item in self.data:
            weight = int(item["amount"] * item["calibration"])
            self.protocol.try_do("Draft", item["port"], weight)
        self.protocol.try_do("Move", 0)

    def _do_cleaning(self):
        if self.demo:
            time.sleep(2)
            return
        self.protocol.try_do("Draft", self.data["port"], int(self.data["weight"]))

    def _do_single_ingredient(self):
        if self.demo:
            time.sleep(2)
            return
        self._set_message(UserMessages.place_glas)
        while self.protocol.try_get("HasGlas") != "1":
            time.sleep(0.5)
        self._set_message(None)
        self._draft_one(self.data)
        self.protocol.try_do("Move", 0)

    # start commands

    def start_mixing(self, recipe):
        self.data = {"recipe": recipe, "recipe_item_index": 0}
        self.set_state(State.mixing)

    def start_single_ingredient(self, recipe_item):
        self.data = recipe_item
        self.set_state(State.single_ingredient)

    def start_cleaning(self, port, weight):
        self.data = {"port": port, "weight": weight}
        self.set_state(State.cleaning)

    def start_cleaning_cycle(self, data):
        self.data = data
        self.set_state(State.cleaning_cycle)
    

class Database(object):
    con:lite.Connection
    filename:str
    _is_connected:bool = False
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        if self._is_connected:
            return
        self.con = lite.connect(self.filename)
        self.con.row_factory = lite.Row
        self.cursor = self.con.cursor()
        self._is_connected = True

    def close(self):
        if(self.con is not None):
            self.con.close()
        self.con = None
        self.cursor = None
        self._is_connected = False

    def ingredient_of_port(self):
        # only open/close if called while not connected
        wasOpen = self._is_connected
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

    def port_and_calibration(self, iid):
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

    def list_ingredients(self):
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

    def list_recipes(self):
        self.open()
        self.cursor.execute("""
			SELECT name, id
			FROM Recipes
			WHERE successor_id IS NULL
		""")
        recipes = []
        for row in self.cursor.fetchall():
            recipe = dict(row)
            self._add_items_to_recipe(recipe)
            recipes.append(recipe)
        self.close()
        return recipes

    def _add_items_to_recipe(self, recipe):
        availableIngredients = self.ingredient_of_port().values()
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

    def recipe(self, rid):
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
        self._add_items_to_recipe(recipe)
        self.close()
        return recipe

    # returns: new recipe id
    def create_or_update_recipe(self, name, instruction, old_rid=-1):
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

    def remove_recipe(self, rid):
        self.open()
        self.cursor.execute("""
            UPDATE Recipes
            SET successor_id = -1
            WHERE id = :rid
        """, {"rid": rid})
        self.con.commit()
        self.close()
        
    def _insert_recipe_items(self, rid, items):
        self.open()
        for item in items:
            self.cursor.execute("""
				INSERT INTO RecipeItems ( Recipe, ingredient, amount )
				VALUES ( :rid, :ingredient, :amount )
			""", {"rid": rid, "ingredient": item["ingredient"], "amount": item["amount"]})
        self.con.commit()
        self.close()

    def has_recipe_changed(self, rid, name, items, instruction):
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

    def start_order(self, rid):
        self.open()
        self.cursor.execute("""
			INSERT INTO Orders ( recipe, started, status )
			VALUES ( :rid, DATETIME('now'), 0 )
		""", {"rid": rid})
        self.con.commit()
        self.close()

    def close_order(self, rid):
        self.open()
        self.cursor.execute("""
			UPDATE Orders
			SET finished = DATETIME('now'), status = 1
			WHERE recipe = :rid
		""", {"rid": rid})
        self.con.commit()
        self.close()

    def clear_order(self):
        self.open()
        self.cursor.execute("""
			UPDATE Orders
			SET status = -1
			WHERE status = 0
		""")
        self.con.commit()
        self.close()

    def update_ports(self, ports):
        self.open()
        for port, iid in ports.items():
            self.cursor.execute("""
				UPDATE Ports
				SET ingredient = :iid
				WHERE id = :port
			""", {"iid": iid, "port": port})
        self.con.commit()
        self.close()

    def update_calibration(self, port, calibration):
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

    def ordered_cocktails_count(self, date):
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

    def ordered_ingredients_amount(self, date):
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

    def ordered_cocktails_by_time(self, date):
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

    def list_parties(self):
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
