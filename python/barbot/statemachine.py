
import barbot
from barbot import UserMessages, data, communication, botconfig
import logging
import time
from enum import Enum, auto
import threading
from barbot.data import IngregientType


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


# error codes (must match "shared.h")
class Error(Enum):
    ingredient_empty = 33
    balance_communication = 34
    I2C = 35
    straws_empty = 36
    glas_removed = 37
    mixing_failed = 38
    crusher_cover_open = 39
    crusher_timeout = 40


abort = False
_user_input = None
_abort_mixing = False
_weight_timeout = 1
_get_async = None
_weight = None
_current_recipe: data.Recipe = None
_current_recipe_item: data.RecipeItem = None
_pumps_to_clean = []
_connected_boards = []
_bt_timeout = 1
_async_result = None
_message: UserMessages = None
_progress = 0

# workaround for pylint, otherwise the functions are marked as not callable


def on_mixing_finished(_): return None


def on_mixing_progress_changed(_): return None


def on_state_changed(_): return None


def on_message_changed(_): return None


def set_balance_calibration(offset, cal):
    # change config
    botconfig.set_value("balance_offset", offset)
    botconfig.set_value("balance_calibration", cal)
    # write and reload config
    botconfig.save()
    botconfig.load()
    # send new values to mainboard
    communication.try_set("SetBalanceOffset",
                          int(botconfig.balance_offset))
    communication.try_set("SetBalanceCalibration",
                          int(botconfig.balance_calibration))

# main loop, runs the whole time


def run():
    global abort, _abort_mixing, _state, _get_async, _bt_timeout, connected_boards, _async_result
    logging.debug("State machine started" +
                  (" in demo mode" if barbot.is_demo else ""))
    while not abort:
        if _state == State.searching:
            logging.info("Search for BarBot4")
            res = barbot.communication.find_bar_bot()
            if res:
                botconfig.set_value("mac_address", res)
                botconfig.save()
                botconfig.apply()
                set_state(State.connecting)
            # else:
            #    set_state(State.searching)
        elif _state == State.connecting:
            if not botconfig.is_mac_address_valid():
                set_state(State.searching)
            else:
                if communication.connect(botconfig.mac_address, _bt_timeout):
                    set_state(State.startup)
                else:
                    time.sleep(1)
        elif _state == State.startup:
            if not communication.is_connected:
                set_state(State.connecting)
            elif communication.read_message().type == barbot.communication.MessageTypes.STATUS:
                # check all boards that should be connected and warn if they are not
                get_boards_connected(synchronous=True)
                if not communication.Boards.balance in _connected_boards:
                    _set_message(UserMessages.board_not_connected_balance)
                if botconfig.stirrer_connected and not communication.Boards.mixer in _connected_boards:
                    _set_message(UserMessages.board_not_connected_mixer)
                    if not _wait_for_user_input():
                        return
                if botconfig.straw_dispenser_connected and not communication.Boards.straw in _connected_boards:
                    _set_message(UserMessages.board_not_connected_straw)
                    if not _wait_for_user_input():
                        return
                if botconfig.ice_crusher_connected and not communication.Boards.crusher in _connected_boards:
                    _set_message(UserMessages.board_not_connected_crusher)
                    if not _wait_for_user_input():
                        return
                _set_message(None)
                communication.try_set("SetLED", 3)
                communication.try_set("SetSpeed", botconfig.max_speed)
                communication.try_set("SetAccel", botconfig.max_accel)
                communication.try_set("SetPumpPower", botconfig.pump_power)
                communication.try_set("SetBalanceCalibration", int(
                    botconfig.balance_calibration))
                communication.try_set("SetBalanceOffset",
                                      int(botconfig.balance_offset))
                set_state(State.idle)
        elif _state == State.mixing:
            _do_mixing()
            _abort_mixing = False
            go_to_idle()
        elif _state == State.cleaning_cycle:
            _do_cleaning_cycle()
            go_to_idle()
        elif _state == State.single_ingredient:
            _do_single_ingredient()
            go_to_idle()
        elif _state == State.crushing:
            _do_crushing()
            go_to_idle()
        elif _state == State.straw:
            _do_straw()
            go_to_idle()
        else:
            if not barbot.is_demo:
                communication.read_message()
                if not communication.is_connected:
                    set_state(State.connecting)
                # get async if flag is set
                if _get_async != None:
                    _async_result = communication.try_get(_get_async)
                    _get_async = None
            else:
                time.sleep(0.1)
    if not barbot.is_demo:
        communication.close()


def set_user_input(value: bool):
    global _user_input
    _user_input = value


def abort_mixing():
    global _abort_mixing
    _abort_mixing = True


def set_state(state):
    global _state
    _state = state
    logging.debug("State changed to '%s'" % _state)
    if on_state_changed is not None:
        on_state_changed(state)


def _set_mixing_progress(progress):
    global _progress
    _progress = progress
    if on_mixing_progress_changed is not None:
        on_mixing_progress_changed(progress)


def _set_message(message: UserMessages):
    global _message
    _message = message
    if message is None:
        logging.debug("Remove user message")
    else:
        logging.debug("Show user message: %s" % message)
    if on_message_changed is not None:
        on_message_changed(message)


def current_message():
    global _message
    return _message


def is_busy():
    global _state
    return _state != State.idle


def can_edit_database():
    global _state
    return _state == State.connecting or _state == State.idle


def _wait_for(condition):
    global abort
    while not abort and not condition():
        time.sleep(0.1)
    return not abort


def _wait_for_user_input():
    global abort, _user_input
    _user_input = None
    logging.debug("Wait for user input")
    while not abort and _user_input == None:
        time.sleep(0.1)
    if abort:
        logging.warn("Waiting aborted")
        return False
    else:
        logging.debug("User answered: %s" % _user_input)
    return True

# do commands


def _do_mixing():
    global _user_input, _abort_mixing, _current_recipe, _current_recipe_item
    _set_mixing_progress(0)
    # wait for the glas
    if not barbot.is_demo and communication.try_get("HasGlas") != "1":
        communication.try_do("PlatformLED", 2)
        _set_message(UserMessages.place_glas)
        _user_input = None
        # wait for glas or user abort
        if not _wait_for(lambda: (communication.try_get("HasGlas") == "1") or (_user_input is not None)):
            return
        if _user_input == False:
            return

    if not barbot.is_demo:
        communication.try_do("PlatformLED", 3)
    _set_message(None)
    # ask for ice if module is connected
    if botconfig.ice_crusher_connected:
        _set_message(UserMessages.ask_for_ice)
        if not barbot.is_demo:
            communication.try_do("PlatformLED", 4)
        if not _wait_for_user_input():
            return
        _set_message(None)
        add_ice = _user_input
    else:
        add_ice = False
    # ask for straw if module is connected
    if botconfig.straw_dispenser_connected:
        _set_message(UserMessages.ask_for_straw)
        if not barbot.is_demo:
            communication.try_do("PlatformLED", 4)
        if not _wait_for_user_input():
            return
        _set_message(None)
        add_straw = _user_input
    else:
        add_straw = False
    # wait a second before actually starting the mixing
    time.sleep(1)
    if not barbot.is_demo:
        communication.try_do("PlatformLED", 5)
        communication.try_set("SetLED", 5)
    set_user_input(None)
    for index, item in enumerate(_current_recipe.items):
        _set_mixing_progress(index)
        # user aborted
        if _abort_mixing:
            break
        _current_recipe_item = item
        if not barbot.is_demo:
            # do the actual draft, exit the loop if it did not succeed
            if not _draft_one(item):
                break
        else:
            if _abort_mixing:
                logging.warn("Waiting aborted")
                return
            time.sleep(1)
    progress = len(_current_recipe.items)

    # add ice if desired and mixing was not aborted
    if add_ice and not _abort_mixing:
        _set_mixing_progress(progress)
        if not barbot.is_demo:
            _do_crushing()
        else:
            time.sleep(1)
    if not barbot.is_demo:
        communication.try_do("Move", 0)
    progress += 1

    # add straw if desired and mixing was not aborted
    if add_straw and not _abort_mixing:
        if not barbot.is_demo:
            _do_straw()
        else:
            time.sleep(1)
        _set_mixing_progress(progress)

    if not barbot.is_demo:
        _set_message(UserMessages.mixing_done_remove_glas)
        communication.try_do("PlatformLED", 2)
        communication.try_set("SetLED", 4)
        _user_input = None
        if not _wait_for(lambda: communication.try_get("HasGlas") != "1"):
            return
        _set_message(None)
        communication.try_do("PlatformLED", 0)
        if on_mixing_finished is not None:
            on_mixing_finished(_current_recipe.id)


def go_to_idle(self):
    _set_message(None)
    if not barbot.is_demo:
        communication.try_set("SetLED", 3)
        # first move to what is supposed to be zero, then home
        communication.try_do("Move", 0)
        communication.try_do("Home")
    set_state(State.idle)


def _do_crushing():
    global _user_input, _abort_mixing
    # user aborted
    if _abort_mixing:
        return False
    # try adding ice until it works or user aborts
    ice_to_add = botconfig.ice_amount
    while True:
        result = communication.try_do("Crush", ice_to_add)
        # user aborted
        if _abort_mixing:
            return False
        if result == True:
            # crushing successfull
            return True
        elif type(result) is list and len(result) >= 2:
            error_code = int(result[0])
            logging.error("Error while crushing ice: '%s'" % error_code)
            error = Error(error_code)
            if error == Error.ingredient_empty:
                # ice is empty, save how much is left
                ice_to_add = int(result[1])
                _set_message(UserMessages.ice_empty)
                _user_input = None
                # wait for user input
                if not _wait_for_user_input():
                    return False
                # remove the message
                _set_message(None)
                if not _user_input:
                    return False
                # repeat the loop

            elif error == Error.glas_removed:
                logging.info("Glas was removed while crushing")
                _set_message(
                    UserMessages.glas_removed_while_drafting)
                _wait_for_user_input()
                return False

            elif error == Error.I2C:
                _set_message(UserMessages.I2C_error)
                # wait for user input
                _wait_for_user_input()
                # a communication error will always stop the mixing process
                return False

            elif error == Error.crusher_cover_open:
                _set_message(UserMessages.crusher_cover_open)
                _user_input = None
                # wait for user input
                if not _wait_for_user_input():
                    return False
                # remove the message
                _set_message(None)
                if not _user_input:
                    return False
                # repeat the loop

            elif error == Error.crusher_timeout:
                _set_message(UserMessages.crusher_timeout)
                _user_input = None
                # wait for user input
                if not _wait_for_user_input():
                    return False
                # remove the message
                _set_message(None)
                if not _user_input:
                    return False
                # repeat the loop

            else:
                logging.warning("Unkown error code")
                _set_message(UserMessages.unknown_error)
                _wait_for_user_input()
                return False

        else:
            # unhandled return value
            logging.error(
                "Unhandled result while drafting: '%s'" % result)
            return False


def _draft_one(item: data.RecipeItem):
    global _user_input, _abort_mixing
    # user aborted
    if _abort_mixing:
        return False
    if item.Ingredient.Type == IngregientType.Stirr:
        communication.try_do("Mix", botconfig.stirring_time)
        return True
    else:
        while True:
            weight = int(item.amount * item.calibration)
            result = communication.try_do("Draft", item.port, weight)
            # user aborted
            if _abort_mixing:
                return False
            if result == True:
                # drafting successfull
                return True
            elif type(result) is list and len(result) >= 2:
                error_code = int(result[0])
                logging.error("Error while drafting: '%s'" % error_code)
                error = Error(error_code)
                if error == Error.ingredient_empty:
                    # ingredient is empty
                    # safe how much is left to draft
                    item.amount = int(result[1]) / item.calibration
                    _set_message(UserMessages.ingredient_empty)
                    _user_input = None
                    # wait for user input
                    if not _wait_for_user_input():
                        return False
                    # remove the message
                    _set_message(None)
                    if not _user_input:
                        return False
                    # repeat the loop

                elif error == Error.glas_removed:
                    logging.info("Glas was removed while drafting")
                    _set_message(
                        UserMessages.glas_removed_while_drafting)
                    _wait_for_user_input()
                    return False

                else:
                    logging.warning("Unkown error code")
                    _set_message(UserMessages.unknown_error)
                    _wait_for_user_input()
                    return False

            else:
                # unhandled return value
                logging.error(
                    "Unhandled result while drafting: '%s'" % result)
                return False


def _do_cleaning_cycle():
    global _user_input, _pumps_to_clean
    _set_message(UserMessages.cleaning_adapter)
    # ask user if the cleanig adapter is there
    _user_input = None
    if not _wait_for(lambda: (_user_input is not None)):
        return
    if _user_input == False:
        return
    _set_message(None)
    if barbot.is_demo:
        time.sleep(2)
        return
    for pump_index in _pumps_to_clean:
        communication.try_do("Clean", pump_index,
                             botconfig.cleaning_time)


def _do_cleaning():
    global _current_recipe_item
    if barbot.is_demo:
        time.sleep(2)
        return
    weight = int(_current_recipe_item.weight)
    communication.try_do("Clean", _current_recipe_item.port, weight)


def _do_single_ingredient():
    global _user_input, _current_recipe_item
    if barbot.is_demo:
        time.sleep(2)
        return
    _set_message(UserMessages.place_glas)
    _user_input = None
    # wait for glas or user abort
    if not _wait_for(lambda: (communication.try_get("HasGlas") == "1") or (_user_input is not None)):
        return
    if _user_input == False:
        return
    _set_message(None)
    _draft_one(_current_recipe_item)


def _do_straw():
    global _user_input
    # try dispensing straw until it works or user aborts
    while not communication.try_do("Straw"):
        _user_input = None
        _set_message(UserMessages.straws_empty)
        if not _wait_for_user_input():
            return
        _set_message(None)
        if _user_input == False:
            break

# start commands


def start_mixing(recipe: data.Recipe):
    global _abort_mixing, _current_recipe
    _abort_mixing = False
    _current_recipe = recipe
    set_state(State.mixing)


def start_single_ingredient(recipe_item: data.RecipeItem):
    global _abort_mixing, _current_recipe_item
    _abort_mixing = False
    _current_recipe_item = recipe_item
    set_state(State.single_ingredient)


def start_crushing():
    global _abort_mixing
    _abort_mixing = False
    set_state(State.crushing)


def start_cleaning(port):
    global _abort_mixing, _pumps_to_clean
    _abort_mixing = False
    _pumps_to_clean = [port]
    set_state(State.cleaning_cycle)


def start_cleaning_cycle(pumps_to_clean):
    global _abort_mixing, _pumps_to_clean
    _abort_mixing = False
    _pumps_to_clean = pumps_to_clean
    set_state(State.cleaning_cycle)


def start_straw():
    set_state(State.straw)


def get_async(parameter):
    global _get_async, _state, _weight_timeout, _async_result
    if _state != State.idle:
        return None
    _get_async = parameter
    start_time = time.time()
    while(_get_async != None and time.time() < start_time + _weight_timeout):
        time.sleep(0.1)
    if _get_async != None:
        _get_async = None
        return None
    return _async_result


def get_state():
    global _state
    return _state


def get_weight():
    global _weight, _async_result
    if get_async("GetWeight") != None:
        _weight = float(_async_result)
    else:
        _weight = None
    return _weight


def get_boards_connected(synchronous=False):
    global _connected_boards
    if synchronous:
        boards = communication.try_get("GetConnectedBoards")
    else:
        get_async("GetConnectedBoards")
        boards = get_async("GetConnectedBoards")
    boards = int(boards) if boards != None else 0
    _connected_boards = [
        b for b in communication.Boards if (boards & 1 << b.value)]
    return _connected_boards


if barbot.is_demo:
    set_state(State.connecting)
else:
    _connected_boards = [communication.Boards.balance]
    set_state(State.idle)
