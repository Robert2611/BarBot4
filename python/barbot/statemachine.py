from barbot import UserMessages, data, communication
from enum import Enum, auto
import threading

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

on_mixing_finished = None
on_mixing_progress_changed = None
on_state_changed = None
on_message_changed = None

# error codes (must match "shared.h")
error_ingredient_empty = 33
error_balance_communication = 34
error_I2C = 35
error_straws_empty = 36
error_glas_removed = 37
error_mixing_failed = 38
error_crusher_cover_open = 39
error_crusher_timeout = 40

progress = None
abort = False
message: UserMessages = None
_user_input = None
_abort_mixing = False
weight_timeout = 1
_get_async = None
demo = False
add_straw = False
add_ice = False
current_recipe: data.Recipe = None
current_recipe_item: data.RecipeItem = None
pumps_to_clean = []
connected_boards = []
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
        self.connected_boards = [Boards.balance]
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
                # check all boards that should be connected and warn if they are not
                self.get_boards_connected(synchronous=True)
                if not Boards.balance in self.connected_boards:
                    self._set_message(
                        UserMessages.board_not_connected_balance)
                if self.config.stirrer_connected and not Boards.mixer in self.connected_boards:
                    self._set_message(
                        UserMessages.board_not_connected_mixer)
                    if not self._wait_for_user_input():
                        return
                if self.config.straw_dispenser_connected and not Boards.straw in self.connected_boards:
                    self._set_message(
                        UserMessages.board_not_connected_straw)
                    if not self._wait_for_user_input():
                        return
                if self.config.ice_crusher_connected and not Boards.crusher in self.connected_boards:
                    self._set_message(
                        UserMessages.board_not_connected_crusher)
                    if not self._wait_for_user_input():
                        return
                self._set_message(None)
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
                # get async if flag is set
                if self._get_async != None:
                    self._async_result = self.protocol.try_get(
                        self._get_async)
                    self._get_async = None
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
            return True
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
                    return False
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

            elif error_code == self.error_crusher_cover_open:
                self._set_message(UserMessages.crusher_cover_open)
                self._user_input = None
                # wait for user input
                if not self._wait_for_user_input():
                    return False
                # remove the message
                self._set_message(None)
                if not self._user_input:
                    return False
                # repeat the loop

            elif error_code == self.error_crusher_timeout:
                self._set_message(UserMessages.crusher_timeout)
                self._user_input = None
                # wait for user input
                if not self._wait_for_user_input():
                    return False
                # remove the message
                self._set_message(None)
                if not self._user_input:
                    return False
                # repeat the loop

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

def get_async(self, parameter):
    if self.state != State.idle:
        return None
    self._get_async = parameter
    start_time = time.time()
    while(self._get_async != None and time.time() < start_time + self.weight_timeout):
        time.sleep(0.1)
    if self._get_async != None:
        self._get_async = None
        return None
    return self._async_result

def get_weight(self):
    if self.get_async("GetWeight") != None:
        self.weight = float(self._async_result)
    else:
        self.weight = None
    return self.weight

def get_boards_connected(self, synchronous=False):
    if synchronous:
        # workaround: call twice so the result is really there
        self.protocol.try_get("GetConnectedBoards")
        boards = self.protocol.try_get("GetConnectedBoards")
    else:
        # workaround: call twice so the result is really there
        self.get_async("GetConnectedBoards")
        boards = self.get_async("GetConnectedBoards")
    boards = int(boards) if boards != None else 0
    self.connected_boards = [b for b in Boards if (boards & 1 << b.value)]
    return self.connected_boards
