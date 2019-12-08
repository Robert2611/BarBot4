import time
import threading
import barbot.communication
import sys
import os
import subprocess
import sqlite3 as lite
import logging

from enum import Enum, auto


def run_command(cmd_str, cmd_str2=None):
    if cmd_str2:
        subprocess.Popen([cmd_str, cmd_str2], shell=True, stdin=None,
                         stdout=None, stderr=None, close_fds=True)
    else:
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
    ask_for_straw = auto()
    straws_empty = auto()


class RecipeItem(object):
    id = -1
    amount = 0
    name = ""
    iid = -1
    calibration = 0
    port = -1
    available = False


class Recipe(object):
    name = ""
    id = -1
    instruction = ""
    available = False
    items = None

    def __init__(self, name, id, instruction, available):
        self.name = name
        self.id = id
        self.instruction = instruction
        self.available = available
        self.items = []


class StateMachine(threading.Thread):
    on_mixing_finished = None
    on_mixing_progress_changed = None
    on_state_changed = None
    on_message_changed = None

    error_ingredient_empty = 33
    error_straws_empty = 36
    error_glas_removed = 37
    progress = None
    abort = False
    message: UserMessages = None
    _user_input = None
    rainbow_duration = 10
    max_speed = 100
    max_accel = 100
    max_cocktail_size = 30
    demo = False
    protocol: barbot.communication.Protocol = None
    use_straw = False
    current_recipe: barbot.Recipe = None
    current_recipe_item: RecipeItem = None

    def __init__(self, port, baudrate, demo=False):
        threading.Thread.__init__(self)
        self.demo = demo
        logging.debug("State machine started" +
                      (" in demo mode" if demo else ""))
        if not demo:
            self.protocol = barbot.communication.Protocol(port, baudrate, 1)
            self.set_state(State.connecting)
        else:
            self.set_state(State.idle)
        # workaround for pylint, otherwise the functions are marked as not callable
        self.on_mixing_finished = lambda _: None
        self.on_mixing_progress_changed = lambda: None
        self.on_state_changed = lambda: None
        self.on_message_changed = lambda: None

    # main loop, runs the whole time
    def run(self):
        while not self.abort:
            if self.state == State.connecting:
                if self.protocol.connect():
                    self.set_state(State.startup)
                else:
                    time.sleep(1)
            elif self.state == State.startup:
                if not self.protocol.is_connected:
                    self.set_state(State.connecting)
                elif self.protocol.read_message().type == barbot.communication.MessageTypes.STATUS:
                    self.protocol.try_set("SetLED", 3)
                    self.protocol.try_set("SetSpeed", self.max_speed)
                    self.protocol.try_set("SetAccel", self.max_accel)
                    self.set_state(State.idle)
            elif self.state == State.mixing:
                self._do_mixing()
                self.go_to_idle()
            elif self.state == State.cleaning:
                self._do_cleaning()
                self.go_to_idle()
            elif self.state == State.cleaning_cycle:
                self._do_cleaning_cycle()
                self.go_to_idle()
            elif self.state == State.single_ingredient:
                self._do_single_ingredient()
                self.go_to_idle()
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

    def set_user_input(self, value: bool):
        self._user_input = value

    def set_state(self, state):
        self.state = state
        logging.debug("State changed to '%s'" % self.state)
        if self.on_state_changed is not None:
            self.on_state_changed()

    def _set_mixing_progress(self, progress):
        self.progress = progress
        if self.on_mixing_progress_changed is not None:
            self.on_mixing_progress_changed()

    def _set_message(self, message: UserMessages):
        self.message = message
        if message is None:
            logging.debug("Remove user message")
        else:
            logging.debug("Show user message: %s" % self.message)
        if self.on_message_changed is not None:
            self.on_message_changed()

    def is_busy(self):
        return self.state != State.idle

    def can_edit_database(self):
        return self.state == State.connecting or self.state == State.idle

    def wait_for(self, condition):
        while not self.abort and not condition():
            time.sleep(0.1)
        return not self.abort

    def wait_for_user_input(self):
        logging.debug("Wait for user input")
        while not self.abort and self._user_input == None:
            time.sleep(0.1)
        if self.abort:
            logging.warn("Waiting aborted")
            return False
        else:
            logging.debug("User answered: %s" % self._user_input)
        return True

    # do commands

    def _do_mixing(self):
        if self.demo:
            self._set_message(UserMessages.ingredient_empty)
            self._user_input = None
            if not self.wait_for_user_input():
                return
            # remove the message
            self._set_message(None)
            logging.debug(self._user_input)
            return
        # wait for the glas
        if self.protocol.try_get("HasGlas") != "1":
            self.protocol.try_do("PlatformLED", 2)
            self._set_message(UserMessages.place_glas)
            self._user_input = None
            # wait for glas or user abort
            if not self.wait_for(lambda: (self.protocol.try_get("HasGlas") == "1") or (self._user_input == False)):
                return
            if self._user_input == False:
                return
        self.protocol.try_do("PlatformLED", 3)
        self._set_message(None)
        # ask for straw
        self._set_message(UserMessages.ask_for_straw)
        self._user_input = None
        self.protocol.try_do("PlatformLED", 4)
        if not self.wait_for_user_input():
            return
        self._set_message(None)
        self.use_straw = self._user_input
        # wait a second before actually starting the mixing
        time.sleep(1)

        self.protocol.try_do("PlatformLED", 5)
        self.protocol.try_set("SetLED", 5)

        maxProgress = max(len(self.current_recipe.items) - 1, 1)
        recipe_item_index = 0
        for item in self.current_recipe.items:
            self.current_recipe_item = item
            # do the actual draft, exit the loop if it did not succeed
            if not self._draft_one(item):
                break
            recipe_item_index += 1
            self._set_mixing_progress(recipe_item_index / maxProgress)
        self.protocol.try_do("Move", 0)
        if self.use_straw:
            # ask for straw until it works or user aborts
            while not self.protocol.try_do("Straw"):
                self._user_input = None
                self._set_message(UserMessages.straws_empty)
                if not self.wait_for_user_input():
                    return
                self._set_message(None)
                if self._user_input == False:
                    break
        self._set_message(UserMessages.mixing_done_remove_glas)
        self.protocol.try_do("PlatformLED", 2)
        self.protocol.try_set("SetLED", 4)
        self._user_input = None
        if not self.wait_for(lambda: self.protocol.try_get("HasGlas") != "1"):
            return
        self._set_message(None)
        self.protocol.try_do("PlatformLED", 0)
        if self.on_mixing_finished is not None:
            self.on_mixing_finished(self.current_recipe.id)

    def go_to_idle(self):
        self._set_message(None)
        self.protocol.try_set("SetLED", 3)
        # first move to what is supposed to be zero, then home
        self.protocol.try_do("Move", 0)
        self.protocol.try_do("Home")
        self.set_state(State.idle)

    def _draft_one(self, item: RecipeItem):
        if item.port == 12:
            self.protocol.try_do("Stir", int(item.amount * 1000))
            return True
        else:
            while True:
                weight = int(item.amount * item.calibration)
                result = self.protocol.try_do("Draft", item.port, weight)
                if result == True:
                    # drafting successfull
                    return True
                elif type(result) is list and len(result) >= 2:
                    error_code = int(result[0])
                    logging.error("Error while drafting: '%s'" % error_code)
                    if error_code == self.error_ingredient_empty:
                        # ingredient is empty
                        # safe how much is left to draft
                        item.amount = int(result[1]) / item.calibration
                        self._set_message(UserMessages.ingredient_empty)
                        self._user_input = None
                        # wait for user input
                        if not self.wait_for_user_input():
                            return
                        # remove the message
                        self._set_message(None)
                        if not self._user_input:
                            return False
                        # repeat the loop

                    elif error_code == self.error_glas_removed:
                        # TODO: Show message to user
                        logging.info("Glas was removed while drafting")
                        return False

                else:
                    # unhandled return value
                    logging.error(
                        "Unhandled result while drafting: '%s'" % result)
                    return False

    def _do_cleaning_cycle(self):
        if self.demo:
            time.sleep(2)
            return
        self._set_message(UserMessages.place_glas)
        self._user_input = None
        # wait for glas or user abort
        if not self.wait_for(lambda: self.protocol.try_get("HasGlas") != "1" or self._user_input == False):
            return
        if self._user_input == False:
            return
        self._set_message(None)
        for item in self.current_recipe:
            weight = int(item.amount * item.calibration)
            self.protocol.try_do("Draft", item.port, weight)

    def _do_cleaning(self):
        if self.demo:
            time.sleep(2)
            return
        self.protocol.try_do(
            "Draft", self.current_recipe_item.port, int(self.current_recipe_item.weight))

    def _do_single_ingredient(self):
        if self.demo:
            time.sleep(2)
            return
        self._set_message(UserMessages.place_glas)
        self._user_input = None
        # wait for glas or user abort
        if not self.wait_for(lambda: (self.protocol.try_get("HasGlas") == "1") or (self._user_input == False)):
            return
        if self._user_input == False:
            return
        self._set_message(None)
        self._draft_one(self.current_recipe_item)

    # start commands

    def start_mixing(self, recipe: barbot.Recipe):
        self.current_recipe = recipe
        self.set_state(State.mixing)

    def start_single_ingredient(self, recipe_item: RecipeItem):
        self.current_recipe_item = recipe_item
        self.set_state(State.single_ingredient)

    def start_cleaning(self, port, weight):
        self.current_recipe_item = {"port": port, "weight": weight}
        self.set_state(State.cleaning)

    def start_cleaning_cycle(self, data):
        self.current_recipe = data
        self.set_state(State.cleaning_cycle)


class RecipeOrder(Enum):
    Newest = auto()
    Makes = auto()


class RecipeFilter(object):
    Alcoholic: bool = True
    Order: RecipeOrder = RecipeOrder.Newest
    AvailableOnly: bool = True
    DESC: bool = False


class Database(object):
    con: lite.Connection
    filename: str
    _is_connected: bool = False

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
			SELECT  p.id as port, 
                    i.calibration AS calibration,
                    i.name AS name
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

    def list_ingredients(self, only_available=False):
        self.open()
        sql = """
			SELECT i.id, i.name, i.type, i.calibration, p.id as port
			FROM Ingredients i
			LEFT JOIN Ports p
			ON p.ingredient = i.id
		"""
        if only_available:
            sql = sql + "WHERE i.id in (SELECT ingredient FROM Ports)"
        self.cursor.execute(sql)
        res = dict()
        for ingredient in self.cursor.fetchall():
            res[ingredient["id"]] = dict(ingredient)
        self.close()
        return res

    def list_recipes(self, filter: RecipeFilter):
        sql = """
            SELECT  r.name AS name,
                    r.id AS id,
                    r.instruction AS instruction,
                    (
                        SELECT MIN(ri.ingredient in (SELECT ingredient FROM Ports)) > 0
                        FROM RecipeItems ri
                        WHERE ri.recipe = r.id
                    ) AS available
            FROM RecipeItems ri
            JOIN Ingredients i
            ON i.id = ri.ingredient
            JOIN Recipes r
            ON r.id == ri.recipe
            WHERE r.successor_id IS NULL
        """
        sql = sql + "GROUP BY ri.recipe\n"
        # filter alcoholic
        sql = sql + "HAVING MAX(i.type = 'spirit') = "
        if filter.Alcoholic:
            sql = sql + "1\n"
        else:
            sql = sql + "0\n"
        # available
        if filter.AvailableOnly:
            sql = sql + "AND MIN(i.id in (SELECT ingredient FROM Ports))\n"
        # ordering
        ordering = False
        if filter.Order == RecipeOrder.Newest:
            ordering = "ORDER BY id "
        if ordering:
            # sorting DESC or ASC
            if filter.DESC:
                sql = sql + ordering + "DESC\n"
            else:
                sql = sql + ordering + "ASC\n"
        self.open()
        self.cursor.execute(sql)
        recipes = []
        for row in self.cursor.fetchall():
            recipe = Recipe(row["name"], row["id"],
                            row["instruction"], row["available"])
            self._add_items_to_recipe(recipe)
            recipes.append(recipe)
        self.close()
        return recipes

    def _add_items_to_recipe(self, recipe: Recipe):
        self.cursor.execute("""
			SELECT  ri.id,
                    ri.amount,
                    i.name,
                    ri.Ingredient AS iid,
                    i.calibration AS calibration,
                    p.id as port,
                    (i.id in (SELECT ingredient FROM Ports)) AS available
			FROM RecipeItems ri
			JOIN Ingredients i
			ON i.id = ri.Ingredient
			LEFT JOIN Ports p
			ON p.ingredient = ri.Ingredient
			WHERE ri.Recipe = :rid
		""", {"rid": recipe.id})
        for row in self.cursor.fetchall():
            item = RecipeItem()
            item.id = row["id"]
            item.amount = row["amount"]
            item.name = row["name"]
            item.iid = row["iid"]
            item.calibration = row["calibration"]
            item.port = row["port"]
            item.available = row["available"]
            recipe.items.append(item)

    def recipe(self, rid):
        self.open()
        self.cursor.execute("""
			SELECT  name,
                    id,
                    instruction,
                    (
                        SELECT MIN(ri.ingredient in (SELECT ingredient FROM Ports)) > 0
                        FROM RecipeItems ri
                        WHERE ri.recipe = r.id
                    ) AS available
			FROM Recipes r
			WHERE successor_id IS NULL
			AND id = :rid
		""", {"rid": rid})
        res = self.cursor.fetchone()
        # does the recipe exits?
        if res == None:
            self.close()
            return None
        recipe = Recipe(res["name"], res["id"],
                        res["instruction"], res["available"])
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
			""", {"rid": rid, "ingredient": item.ingredient, "amount": item.amount})
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
