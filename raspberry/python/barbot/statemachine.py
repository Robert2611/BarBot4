
import barbot
import logging
import time
from enum import Enum, auto
from . import orders
from . import ingredients
from . import ports
from . import UserMessages
from . import communication
from . import botconfig
from . import recipes


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
_weight = None
_current_recipe: recipes.Recipe = None
_current_recipe_item: recipes.RecipeItem = None
_pumps_to_clean = []
_connected_boards = []
_message: UserMessages = None
_progress = 0
add_straw = False
add_ice = False
_idle_tasks = []

# workaround for pylint, otherwise the functions are marked as not callable


def on_mixing_finished(_): return None


def on_mixing_progress_changed(_): return None


def on_state_changed(_): return None


def on_message_changed(_): return None


def was_aborted():
    return _abort_mixing


def current_recipe() -> recipes.Recipe:
    global _current_recipe
    return _current_recipe


def current_recipe_item() -> recipes.RecipeItem:
    global _current_recipe_item
    return _current_recipe_item


def set_balance_calibration(offset, cal):
    # change config
    botconfig.balance_offset = offset
    botconfig.balance_calibration = cal
    # write and reload config
    botconfig.save()
    botconfig.load()
    # send new values to mainboard
    _idle_tasks.append(lambda: communication.try_set(
        "SetBalanceOffset", int(botconfig.balance_offset)))
    _idle_tasks.append(lambda: communication.try_set(
        "SetBalanceCalibration", int(botconfig.balance_calibration)))

# main loop, runs the whole time


def run():
    global abort, _abort_mixing, _state, _get_async
    global _connected_boards, _idle_tasks
    logging.debug("State machine started" +
                  (" in demo mode" if barbot.is_demo else ""))
    while not abort:
        if _state == State.searching:
            logging.info("Search for BarBot4")
            res = barbot.communication.find_bar_bot()
            if res:
                botconfig.mac_address = res
                botconfig.save()
                set_state(State.connecting)
            # else:
            #    set_state(State.searching)
        elif _state == State.connecting:
            if not botconfig.is_mac_address_valid():
                set_state(State.searching)
            else:
                if communication.connect(botconfig.mac_address):
                    set_state(State.startup)
                else:
                    time.sleep(1)
        elif _state == State.startup:
            if not communication.is_connected:
                set_state(State.connecting)
            elif communication.read_message().type == barbot.communication.MessageTypes.STATUS:
                # check all boards that should be connected and warn if they are not
                _get_boards_connected()
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
                _set_message(UserMessages.none)
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
                if len(_idle_tasks) > 0:
                    _idle_tasks[0]()
                    _idle_tasks.pop(0)
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
    communication.send_abort()


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
    global _user_input, _abort_mixing, _current_recipe, _current_recipe_item, add_straw, add_ice
    progress = 0
    _set_mixing_progress(progress)

    if not barbot.is_demo:
        communication.try_set("PlatformLED", 3)

    # wait for the glas
    if not barbot.is_demo and communication.try_get("HasGlas") != "1":
        communication.try_set("PlatformLED", 2)
        _set_message(UserMessages.place_glas)
        _user_input = None
        # wait for glas or user abort
        if not _wait_for(lambda: (communication.try_get("HasGlas") == "1") or (_user_input is not None)):
            return
        if _user_input == False:
            return

    # wait for the user to take the hands off the glas
    time.sleep(1)
    if not barbot.is_demo:
        communication.try_set("PlatformLED", 5)
        communication.try_set("SetLED", 5)
    set_user_input(None)
    for item in _current_recipe.items:
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
        progress += 1
        _set_mixing_progress(progress)

    # add ice if it was selected and mixing was not aborted
    if add_ice and not _abort_mixing:
        if not barbot.is_demo:
            _do_crushing()
        else:
            time.sleep(1)
        progress += 1
        _set_mixing_progress(progress)

    # move to start
    if not barbot.is_demo:
        communication.try_do("Move", 0)

    # add straw if it was selected and mixing was not aborted
    if add_straw and not _abort_mixing:
        if not barbot.is_demo:
            _do_straw()
        else:
            time.sleep(1)
        progress += 1
        _set_mixing_progress(progress)

    #mising is done
    _set_message(UserMessages.mixing_done_remove_glas)
    if not barbot.is_demo:
        communication.try_set("PlatformLED", 2)
        communication.try_set("SetLED", 4)
    # show message and led for 2 seconds
    time.sleep(2)
    if not barbot.is_demo:
        communication.try_set("PlatformLED", 0)
        orders.add_order(_current_recipe)
    _set_message(UserMessages.none)
    if on_mixing_finished is not None:
        on_mixing_finished(_current_recipe)


def go_to_idle():
    _set_message(UserMessages.none)
    set_state(State.idle)
    if not barbot.is_demo:
        communication.try_set("SetLED", 3)
        # first move to what is supposed to be zero, then home
        communication.try_do("Move", 0)
        communication.try_do("Home")


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
                _set_message(UserMessages.none)
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
                _set_message(UserMessages.none)
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
                _set_message(UserMessages.none)
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


def _draft_one(item: recipes.RecipeItem):
    global _user_input, _abort_mixing
    # user aborted
    if _abort_mixing:
        return False
    if item.ingredient.type == ingredients.IngredientType.Stirr:
        communication.try_do("Mix", int(botconfig.stirring_time / 1000))
        return True
    else:
        # cl to g with density of water
        weight = int(item.amount * 10)
        port = ports.port_of_ingredient(item.ingredient)
        while True:
            result = communication.try_do("Draft", port, weight)
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
                    weight = int(result[1])
                    _set_message(UserMessages.ingredient_empty)
                    _user_input = None
                    # wait for user input
                    if not _wait_for_user_input():
                        return False
                    # remove the message
                    _set_message(UserMessages.none)
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
    _set_message(UserMessages.none)
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
    _set_message(UserMessages.none)
    _draft_one(_current_recipe_item)


def _do_straw():
    global _user_input
    # try dispensing straw until it works or user aborts
    while not communication.try_do("Straw"):
        _user_input = None
        _set_message(UserMessages.straws_empty)
        if not _wait_for_user_input():
            return
        _set_message(UserMessages.none)
        if _user_input == False:
            break

# start commands


def start_mixing(recipe: recipes.Recipe):
    global _abort_mixing, _current_recipe
    _abort_mixing = False
    _current_recipe = recipe
    set_state(State.mixing)


def start_single_ingredient(recipe_item: recipes.RecipeItem):
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


def set_async(command, parameter):
    global _set_async, _state, _weight_timeout, _set_async_parameter
    if _state != State.idle:
        return False
    _set_async = command
    _set_async_parameter = parameter
    start_time = time.time()
    while _set_async != None and time.time() < start_time + _weight_timeout:
        time.sleep(0.1)
    if _set_async != None:
        _set_async = None
        return False
    return True


def get_state():
    global _state
    return _state


def get_weight(callback):
    global _weight, _idle_tasks

    def get_and_callback():
        res = communication.try_get("GetWeight")
        if res != None:
            _weight = float(res)
        else:
            _weight = None
        callback(_weight)
    _idle_tasks.append(get_and_callback)


def _get_boards_connected():
    global _connected_boards
    input = communication.try_get("GetConnectedBoards")
    boards = int(input) if input != None else 0
    _connected_boards = [
        b for b in communication.Boards if (boards & 1 << b.value)]


def get_boards_connected(callback):
    global _connected_boards

    def get_and_callback():
        _get_boards_connected()
        callback(_connected_boards)
    _idle_tasks.append(get_and_callback)


if barbot.is_demo:
    set_state(State.connecting)
else:
    _connected_boards = [communication.Boards.balance]
    set_state(State.idle)
