import time
import threading
import barbot.communication
import sys
import os
import subprocess
import sqlite3 as lite
import logging
import configparser

from enum import Enum, auto

ingredient_id_stirring = 255


def run_command(cmd_str, cmd_str2=None):
    if cmd_str2:
        subprocess.Popen([cmd_str, cmd_str2], shell=True, stdin=None,
                         stdout=None, stderr=None, close_fds=True)
    else:
        subprocess.Popen([cmd_str], shell=True, stdin=None,
                         stdout=None, stderr=None, close_fds=True)


class State(Enum):
    connecting = auto()
    searching = auto()
    startup = auto()
    idle = auto()
    mixing = auto()
    cleaning = auto()
    cleaning_cycle = auto()
    single_ingredient = auto()
    crushing = auto()
    straw = auto()
    stirring = auto()


class UserMessages(Enum):
    mixing_done_remove_glas = auto()
    place_glas = auto()
    ingredient_empty = auto()
    ask_for_straw = auto()
    straws_empty = auto()
    cleaning_adapter = auto()
    ask_for_ice = auto()
    ice_empty = auto()
    I2C_error = auto()
    unknown_error = auto()
    glas_removed_while_drafting = auto()


class RecipeItem(object):
    id = -1
    amount = 0
    name = ""
    ingredient_id = -1
    calibration = 0
    port = -1
    available = False
    color = "#00000000"

    def isStirringItem(self):
        return self.ingredient_id == ingredient_id_stirring


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


class BarBotConfig(object):
    def __init__(self, filename):
        self.filename = filename
        # always create default config first to make sure all fields exist
        self._create()
        # now load or create config file from default
        if os.path.isfile(self.filename):
            self.config.read(self.filename)
        # write file content to fields of object
        self.apply()
        # write file again to make sure also new attributes are saved
        self.save()

    def _create(self):
        # setup config with default values
        self.config = configparser.ConfigParser()
        self.config.add_section("default")
        self.set_value("mac_address", "")
        self.set_value("rainbow_duration", 30 * 1000)
        self.set_value("max_speed", 200)
        self.set_value("max_accel", 300)
        self.set_value("max_cocktail_size", 30)
        self.set_value("admin_password", "0000")
        self.set_value("pump_power", 100)
        self.set_value("balance_offset", -119.1)
        self.set_value("balance_calibration", -1040)
        self.set_value("cleaning_time", 3000)
        self.set_value("stirrer_connected", True)
        self.set_value("stirring_time", 3000)
        self.set_value("ice_crusher_connected", False)
        self.set_value("ice_amount", 100)
        self.set_value("straw_dispenser_connected", False)

    def apply(self):
        self.mac_address = self.__get_str("mac_address")
        self.rainbow_duration = self.__get_int("rainbow_duration")
        self.max_speed = self.__get_int("max_speed")
        self.max_accel = self.__get_int("max_accel")
        self.max_cocktail_size = self.__get_int("max_cocktail_size")
        self.admin_password = self.__get_str("admin_password")
        self.pump_power = self.__get_int("pump_power")
        self.balance_offset = self.__get_float("balance_offset")
        self.balance_calibration = self.__get_float("balance_calibration")
        self.cleaning_time = self.__get_int("cleaning_time")
        self.stirrer_connected = self.__get_bool("stirrer_connected")
        self.stirring_time = self.__get_int("stirring_time")
        self.ice_crusher_connected = self.__get_bool("ice_crusher_connected")
        self.ice_amount = self.__get_int("ice_amount")
        self.straw_dispenser_connected = self.__get_bool(
            "straw_dispenser_connected")

    def set_value(self, name: str, value):
        self.config.set("default", name, str(value))

    def __get_str(self, name):
        return self.config.get("default", name)

    def __get_int(self, name):
        return self.config.getint("default", name)

    def __get_float(self, name):
        return self.config.getfloat("default", name)

    def __get_bool(self, name):
        return self.config.getboolean("default", name)

    def save(self):
        # safe file again
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)

    def load(self):
        # load config if it exists
        if os.path.isfile(self.filename):
            self.config.read(self.filename)
            self.apply()
            return True
        else:
            return False


class StateMachine(threading.Thread):
    on_mixing_finished = None
    on_mixing_progress_changed = None
    on_state_changed = None
    on_message_changed = None

    error_ingredient_empty = 33
    error_balance_communication = 34
    error_I2C = 35
    error_straws_empty = 36
    error_glas_removed = 37
    error_mixing_failed = 38

    progress = None
    abort = False
    message: UserMessages = None
    _user_input = None
    _abort_mixing = False
    weight_timeout = 0.5
    _get_weight_at_next_idle = False
    demo = False
    protocol: barbot.communication.Protocol = None
    add_straw = False
    add_ice = False
    current_recipe: barbot.Recipe = None
    current_recipe_item: RecipeItem = None
    pumps_to_clean = []
    bt_timeout = 1

    def __init__(self, config_path, demo=False):
        threading.Thread.__init__(self)
        self.demo = demo

        self.config = BarBotConfig(config_path)

        # workaround for pylint, otherwise the functions are marked as not callable
        self.on_mixing_finished = lambda _: None
        self.on_mixing_progress_changed = lambda: None
        self.on_state_changed = lambda: None
        self.on_message_changed = lambda: None

        if not self.demo:
            self.protocol = barbot.communication.Protocol()
            self.set_state(State.connecting)
        else:
            self.set_state(State.idle)

    def is_mac_address_valid(self):
        return len(self.config.mac_address.strip()) == 17

    def set_balance_calibration(self, offset, cal):
        # change config
        self.config.set_value("balance_offset", offset)
        self.config.set_value("balance_calibration", cal)
        # write and reload config
        self.config.save()
        self.config.load()
        # send new values to mainboard
        self.protocol.try_set("SetBalanceOffset",
                              int(self.config.balance_offset))
        self.protocol.try_set("SetBalanceCalibration",
                              int(self.config.balance_calibration))

    # main loop, runs the whole time
    def run(self):
        logging.debug("State machine started" +
                      (" in demo mode" if self.demo else ""))
        while not self.abort:
            if self.state == State.searching:
                logging.info("Search for BarBot4")
                res = barbot.communication.find_bar_bot()
                if res:
                    self.config.set_value("mac_address", res)
                    self.config.save()
                    self.config.apply()
                    self.set_state(State.connecting)
                # else:
                #    self.set_state(State.searching)
            elif self.state == State.connecting:
                if not self.is_mac_address_valid():
                    self.set_state(State.searching)
                else:
                    if self.protocol.connect(self.config.mac_address, self.bt_timeout):
                        self.set_state(State.startup)
                    else:
                        time.sleep(1)
            elif self.state == State.startup:
                if not self.protocol.is_connected:
                    self.set_state(State.connecting)
                elif self.protocol.read_message().type == barbot.communication.MessageTypes.STATUS:
                    p = self.protocol
                    p.try_set("SetLED", 3)
                    p.try_set("SetSpeed", self.config.max_speed)
                    p.try_set("SetAccel", self.config.max_accel)
                    p.try_set("SetPumpPower", self.config.pump_power)
                    p.try_set("SetBalanceCalibration",
                              int(self.config.balance_calibration))
                    p.try_set("SetBalanceOffset", int(
                        self.config.balance_offset))
                    self.set_state(State.idle)
            elif self.state == State.mixing:
                self._do_mixing()
                self._abort_mixing = False
                self.go_to_idle()
            elif self.state == State.cleaning_cycle:
                self._do_cleaning_cycle()
                self.go_to_idle()
            elif self.state == State.single_ingredient:
                self._do_single_ingredient()
                self.go_to_idle()
            elif self.state == State.crushing:
                self._do_crushing()
                self.go_to_idle()
            elif self.state == State.straw:
                self._do_straw()
                self.go_to_idle()
            else:
                if not self.demo:
                    self.protocol.read_message()
                    if not self.protocol.is_connected:
                        self.set_state(State.connecting)
                    # get weight if flag is set
                    if self._get_weight_at_next_idle:
                        self.weight = float(self.protocol.try_get("GetWeight"))
                        self._get_weight_at_next_idle = False
                else:
                    time.sleep(0.1)
        if not self.demo:
            self.protocol.close()

    def set_user_input(self, value: bool):
        self._user_input = value

    def abort_mixing(self):
        self._abort_mixing = True

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

    def _wait_for(self, condition):
        while not self.abort and not condition():
            time.sleep(0.1)
        return not self.abort

    def _wait_for_user_input(self):
        self._user_input = None
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
        self._set_mixing_progress(0)
        # wait for the glas
        if not self.demo and self.protocol.try_get("HasGlas") != "1":
            self.protocol.try_do("PlatformLED", 2)
            self._set_message(UserMessages.place_glas)
            self._user_input = None
            # wait for glas or user abort
            if not self._wait_for(lambda: (self.protocol.try_get("HasGlas") == "1") or (self._user_input is not None)):
                return
            if self._user_input == False:
                return

        if not self.demo:
            self.protocol.try_do("PlatformLED", 3)
        self._set_message(None)
        # ask for ice if module is connected
        if self.config.ice_crusher_connected:
            self._set_message(UserMessages.ask_for_ice)
            if not self.demo:
                self.protocol.try_do("PlatformLED", 4)
            if not self._wait_for_user_input():
                return
            self._set_message(None)
            self.add_ice = self._user_input
        else:
            self.add_ice = False
        # ask for straw if module is connected
        if self.config.straw_dispenser_connected:
            self._set_message(UserMessages.ask_for_straw)
            if not self.demo:
                self.protocol.try_do("PlatformLED", 4)
            if not self._wait_for_user_input():
                return
            self._set_message(None)
            self.add_straw = self._user_input
        else:
            self.add_straw = False
        # wait a second before actually starting the mixing
        time.sleep(1)
        if not self.demo:
            self.protocol.try_do("PlatformLED", 5)
            self.protocol.try_set("SetLED", 5)
        self.set_user_input(None)
        for index, item in enumerate(self.current_recipe.items):
            self._set_mixing_progress(index)
            # user aborted
            if self._abort_mixing:
                break
            self.current_recipe_item = item
            if not self.demo:
                # do the actual draft, exit the loop if it did not succeed
                if not self._draft_one(item):
                    break
            else:
                if self._abort_mixing:
                    logging.warn("Waiting aborted")
                    return
                time.sleep(1)
        progress = len(self.current_recipe.items)

        # add ice if desired and mixing was not aborted
        if self.add_ice and not self._abort_mixing:
            self._set_mixing_progress(progress)
            if not self.demo:
                self._do_crushing()
            else:
                time.sleep(1)
        if not self.demo:
            self.protocol.try_do("Move", 0)
        progress += 1

        # add straw if desired and mixing was not aborted
        if self.add_straw and not self._abort_mixing:
            if not self.demo:
                self._do_straw()
            else:
                time.sleep(1)
            self._set_mixing_progress(progress)

        if not self.demo:
            self._set_message(UserMessages.mixing_done_remove_glas)
            self.protocol.try_do("PlatformLED", 2)
            self.protocol.try_set("SetLED", 4)
            self._user_input = None
            if not self._wait_for(lambda: self.protocol.try_get("HasGlas") != "1"):
                return
            self._set_message(None)
            self.protocol.try_do("PlatformLED", 0)
            if self.on_mixing_finished is not None:
                self.on_mixing_finished(self.current_recipe.id)

    def go_to_idle(self):
        self._set_message(None)
        if self.protocol:
            self.protocol.try_set("SetLED", 3)
            # first move to what is supposed to be zero, then home
            self.protocol.try_do("Move", 0)
            self.protocol.try_do("Home")
        self.set_state(State.idle)

    def _do_crushing(self):
        # user aborted
        if self._abort_mixing:
            return False
        # try adding ice until it works or user aborts
        ice_to_add = self.config.ice_amount
        while True:
            result = self.protocol.try_do("Crush", ice_to_add)
            # user aborted
            if self._abort_mixing:
                return False
            if result == True:
                # crushing successfull
                return
            elif type(result) is list and len(result) >= 2:
                error_code = int(result[0])
                logging.error("Error while crushing ice: '%s'" % error_code)
                if error_code == self.error_ingredient_empty:
                    # ice is empty, save how much is left
                    ice_to_add = int(result[1])
                    self._set_message(UserMessages.ice_empty)
                    self._user_input = None
                    # wait for user input
                    if not self._wait_for_user_input():
                        return
                    # remove the message
                    self._set_message(None)
                    if not self._user_input:
                        return False
                    # repeat the loop

                elif error_code == self.error_glas_removed:
                    logging.info("Glas was removed while crushing")
                    self._set_message(
                        UserMessages.glas_removed_while_drafting)
                    self._wait_for_user_input()
                    return False

                elif error_code == self.error_I2C:
                    self._set_message(UserMessages.I2C_error)
                    # wait for user input
                    self._wait_for_user_input()
                    # a communication error will always stop the mixing process
                    return False

                else:
                    logging.warning("Unkown error code")
                    self._set_message(UserMessages.unknown_error)
                    self._wait_for_user_input()
                    return False

            else:
                # unhandled return value
                logging.error(
                    "Unhandled result while drafting: '%s'" % result)
                return False

    def _draft_one(self, item: RecipeItem):
        # user aborted
        if self._abort_mixing:
            return False
        if item.isStirringItem():
            self.protocol.try_do("Mix", self.config.stirring_time)
            return True
        else:
            while True:
                weight = int(item.amount * item.calibration)
                result = self.protocol.try_do("Draft", item.port, weight)
                # user aborted
                if self._abort_mixing:
                    return False
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
                        if not self._wait_for_user_input():
                            return False
                        # remove the message
                        self._set_message(None)
                        if not self._user_input:
                            return False
                        # repeat the loop

                    elif error_code == self.error_glas_removed:
                        logging.info("Glas was removed while drafting")
                        self._set_message(
                            UserMessages.glas_removed_while_drafting)
                        self._wait_for_user_input()
                        return False

                    else:
                        logging.warning("Unkown error code")
                        self._set_message(UserMessages.unknown_error)
                        self._wait_for_user_input()
                        return False

                else:
                    # unhandled return value
                    logging.error(
                        "Unhandled result while drafting: '%s'" % result)
                    return False

    def _do_cleaning_cycle(self):
        self._set_message(UserMessages.cleaning_adapter)
        # ask user if the cleanig adapter is there
        self._user_input = None
        if not self._wait_for(lambda: (self._user_input is not None)):
            return
        if self._user_input == False:
            return
        self._set_message(None)
        if self.demo:
            time.sleep(2)
            return
        for pump_index in self.pumps_to_clean:
            self.protocol.try_do("Clean", pump_index,
                                 self.config.cleaning_time)

    def _do_cleaning(self):
        if self.demo:
            time.sleep(2)
            return
        weight = int(self.current_recipe_item.weight)
        self.protocol.try_do("Clean", self.current_recipe_item.port, weight)

    def _do_single_ingredient(self):
        if self.demo:
            time.sleep(2)
            return
        self._set_message(UserMessages.place_glas)
        self._user_input = None
        # wait for glas or user abort
        if not self._wait_for(lambda: (self.protocol.try_get("HasGlas") == "1") or (self._user_input is not None)):
            return
        if self._user_input == False:
            return
        self._set_message(None)
        self._draft_one(self.current_recipe_item)

    def _do_straw(self):
        # try dispensing straw until it works or user aborts
        while not self.protocol.try_do("Straw"):
            self._user_input = None
            self._set_message(UserMessages.straws_empty)
            if not self._wait_for_user_input():
                return
            self._set_message(None)
            if self._user_input == False:
                break

    # start commands

    def start_mixing(self, recipe: barbot.Recipe):
        self._abort_mixing = False
        self.current_recipe = recipe
        self.set_state(State.mixing)

    def start_single_ingredient(self, recipe_item: RecipeItem):
        self._abort_mixing = False
        self.current_recipe_item = recipe_item
        self.set_state(State.single_ingredient)

    def start_crushing(self):
        self._abort_mixing = False
        self.set_state(State.crushing)

    def start_cleaning(self, port):
        self._abort_mixing = False
        self.pumps_to_clean = [port]
        self.set_state(State.cleaning_cycle)

    def start_cleaning_cycle(self, _pumps_to_clean):
        self._abort_mixing = False
        self.pumps_to_clean = _pumps_to_clean
        self.set_state(State.cleaning_cycle)

    def start_straw(self):
        self.set_state(State.straw)

    def get_weight(self):
        if self.state != State.idle:
            return None
        self._get_weight_at_next_idle = True
        start_time = time.time()
        while(self._get_weight_at_next_idle and time.time() < start_time + self.weight_timeout):
            time.sleep(0.01)
        if self._get_weight_at_next_idle:
            self._get_weight_at_next_idle = False
            return None
        return self.weight


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
			SELECT ingredient_id, id as port
			FROM ports
		""")
        res = dict()
        for ingredient in self.cursor.fetchall():
            res[ingredient["port"]] = ingredient["ingredient_id"]
        if not wasOpen:
            self.close()
        return res

    def port_and_calibration(self, ingredient_id):
        self.open()
        self.cursor.execute("""
			SELECT  p.id as port, 
                    i.calibration AS calibration,
                    i.name AS name
			FROM ports p
			JOIN ingredients i
			ON p.ingredient_id = i.id
			WHERE i.id = :ingredient_id
		""", {"ingredient_id": ingredient_id})
        res = self.cursor.fetchone()
        if res == None:
            self.close()
            return None
        return dict(res)

    def list_ingredients(self, only_available=False, special_ingredients=True):
        self.open()
        sql = """
			SELECT i.id, i.name, i.type, i.calibration, p.id as port, i.color
			FROM ingredients i
			LEFT JOIN ports p
			ON p.ingredient_id = i.id
		"""
        if only_available:
            sql += "WHERE i.id in (SELECT ingredient_id FROM ports)"
        if not special_ingredients:
            sql += " AND " if only_available else "WHERE "
            sql += "i.type<>'special'"

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
                        SELECT MIN(ri.ingredient_id in (SELECT ingredient_id FROM ports)) > 0
                        FROM recipe_items ri
                        WHERE ri.recipe_id = r.id
                    ) AS available
            FROM recipe_items ri
            JOIN ingredients i
            ON i.id = ri.ingredient_id
            JOIN recipes r
            ON r.id == ri.recipe_id
            WHERE r.successor_id IS NULL
        """
        sql = sql + "GROUP BY ri.recipe_id\n"
        # filter alcoholic
        sql = sql + "HAVING MAX(i.type = 'spirit') = "
        if filter.Alcoholic:
            sql = sql + "1\n"
        else:
            sql = sql + "0\n"
        # available
        if filter.AvailableOnly:
            sql = sql + "AND MIN(i.id in (SELECT ingredient_id FROM ports))\n"
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
                    i.color,
                    ri.ingredient_id,
                    i.calibration AS calibration,
                    p.id as port,
                    (i.id in (SELECT ingredient_id FROM ports)) AS available
			FROM recipe_items ri
			JOIN ingredients i
			ON i.id = ri.ingredient_id
			LEFT JOIN ports p
			ON p.ingredient_id = ri.ingredient_id
			WHERE ri.recipe_id = :rid
		""", {"rid": recipe.id})
        for row in self.cursor.fetchall():
            item = RecipeItem()
            item.id = row["id"]
            item.amount = row["amount"]
            item.name = row["name"]
            item.ingredient_id = row["ingredient_id"]
            item.calibration = row["calibration"]
            item.port = row["port"]
            item.available = row["available"]
            item.color = row["color"]
            recipe.items.append(item)

    def recipe(self, rid):
        self.open()
        self.cursor.execute("""
			SELECT  name,
                    id,
                    instruction,
                    (
                        SELECT MIN(ri.ingredient_id in (SELECT ingredient_id FROM ports)) > 0
                        FROM recipe_items ri
                        WHERE ri.recipe_id = r.id
                    ) AS available
			FROM recipes r
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
			INSERT INTO recipes ( name, instruction, successor_id )
			VALUES ( :name, :instruction, NULL )
		""", {"name": name, "instruction": instruction})
        self.con.commit()
        new_rid = self.cursor.lastrowid
        if(old_rid is not None and old_rid >= 0):
            # set newly created recipe as successor for current recipe
            self.cursor.execute("""
				UPDATE recipes
				SET successor_id = :new_rid
				WHERE id = :old_rid
			""", {"old_rid": old_rid, "new_rid": new_rid})
            self.con.commit()
        self.close()
        return new_rid

    def remove_recipe(self, rid):
        self.open()
        self.cursor.execute("""
            UPDATE recipes
            SET successor_id = -1
            WHERE id = :rid
        """, {"rid": rid})
        self.con.commit()
        self.close()

    def _insert_recipe_items(self, rid, items):
        self.open()
        for item in items:
            self.cursor.execute("""
				INSERT INTO recipe_items ( recipe_id, ingredient_id, amount )
				VALUES ( :rid, :ingredient_id, :amount )
			""", {"rid": rid, "ingredient_id": item.ingredient_id, "amount": item.amount})
        self.con.commit()
        self.close()

    def has_recipe_changed(self, rid, name, items, instruction):
        self.open()
        self.cursor.execute("""
			SELECT name, instruction
			FROM recipes
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
			SELECT id, ingredient_id, amount
			FROM recipe_items
			WHERE recipe_id = :rid
			ORDER BY id ASC
		""", {"rid": rid})
        items_in_Database = self.cursor.fetchall()
        if len(items_in_Database) != len(items):
            self.close()
            return True

        for i in range(0, len(items_in_Database)):
            if items_in_Database[i]["ingredient_id"] != items[i].ingredient_id or \
                    items_in_Database[i]["amount"] != items[i].amount:
                # item has changed
                self.close()
                return True
        self.close()
        return False

    def start_order(self, rid):
        self.open()
        self.cursor.execute("""
			INSERT INTO orders ( recipe_id, started, status )
			VALUES ( :rid, DATETIME('now'), 0 )
		""", {"rid": rid})
        self.con.commit()
        self.close()

    def close_order(self, rid):
        self.open()
        self.cursor.execute("""
			UPDATE orders
			SET finished = DATETIME('now'), status = 1
			WHERE recipe_id = :rid
		""", {"rid": rid})
        self.con.commit()
        self.close()

    def clear_order(self):
        self.open()
        self.cursor.execute("""
			UPDATE orders
			SET status = -1
			WHERE status = 0
		""")
        self.con.commit()
        self.close()

    def update_ports(self, ports):
        self.open()
        for port, ingredient_id in ports.items():
            self.cursor.execute("""
				UPDATE ports
				SET ingredient_id = :ingredient_id
				WHERE id = :port
			""", {"ingredient_id": ingredient_id, "port": port})
        self.con.commit()
        self.close()

    def update_calibration(self, port, calibration):
        self.open()
        self.cursor.execute("""
			UPDATE ingredients
			SET calibration = :calibration
			WHERE id = (
						SELECT ingredient_id
						FROM ports
						WHERE id = :port
						)
		""", {'calibration': calibration, 'port': port})
        self.con.commit()
        self.close()

    def ordered_cocktails_count(self, date):
        self.open()
        self.cursor.execute("""
			SELECT r.name, r.id AS rid, COUNT(*) AS count
			FROM orders O
			JOIN recipes r
			ON r.id = O.recipe_id
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
			SELECT i.name AS ingredient, i.id AS ingredient_id, SUM(ri.amount)/100 AS liters
			FROM recipe_items ri
			JOIN orders o
			ON o.recipe_id = ri.recipe_id
			JOIN ingredients i
			ON i.id = ri.ingredient_id
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
			FROM orders o
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
				FROM orders o
				GROUP BY partydate
				ORDER BY partydate DESC
			)
			WHERE ordercount > 10
		""")
        res = [dict(row) for row in self.cursor.fetchall()]
        return res
