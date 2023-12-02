""" All the BarBot logic
"""
import subprocess
import logging
import time
from typing import Callable, NamedTuple
from enum import Enum, auto
from . import ingredients
from . import communication
from . import config
from . import recipes

def run_command(cmd_str):
    """Run a linux command discarding all its output
    :param cmd_str: Command to be executed
    """
    subprocess.Popen([cmd_str], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)


class UserMessages(Enum):
    """Enumeration of possible messages to be shown to the user"""
    NONE = auto()
    MIXING_DONE_REMOVE_GLAS = auto()
    PLACE_GLAS = auto()
    INGREDIENT_EMPTY = auto()
    ASK_FOR_STRAW = auto()
    STRAWS_EMPTY = auto()
    CLEANING_ADAPTER = auto()
    ASK_FOR_ICE = auto()
    ICE_EMPTY = auto()
    I2C_ERROR = auto()
    UNKNOWN_ERROR = auto()
    GLAS_REMOVED_WHILE_DRAFTING = auto()
    CRUSHER_COVER_OPEN = auto()
    CRUSHER_TIMEOUT = auto()
    BOARD_NOT_CONNECTED_BALANCE = auto()
    BOARD_NOT_CONNECTED_MIXER = auto()
    BOARD_NOT_CONNECTED_STRAW = auto()
    BOARD_NOT_CONNECTED_CRUSHER = auto()
    BOARD_NOT_CONNECTED_SUGAR = auto()

class UserInput(Enum):
    """Enumeration of the possible user inputs"""
    UNDEFINED = auto()
    YES = auto()
    NO = auto()

class BarBotState(Enum):
    """Enumeration of the possible barbot states"""
    CONNECTING = auto()
    SEARCHING = auto()
    STARTUP = auto()
    IDLE = auto()
    MIXING = auto()
    CLEANING = auto()
    CLEANING_CYCLE = auto()
    SINGLE_INGREDIENT = auto()
    CRUSHING = auto()
    STRAW = auto()

# error codes (must match "shared.h")
class Error(Enum):
    """Errors returned by the esp32"""
    INGREDIENT_EMPTY = 33
    BALANCE_COMMUNICATION = 34
    I2C = 35
    STRAWS_EMPTY = 36
    GLAS_REMOVED = 37
    MIXING_FAILED = 38
    CRUSHER_COVER_OPEN = 39
    CRUSHER_TIMEOUT = 40
class _IdleTaskType(Enum):
    GET = auto()
    SET = auto()
    DO = auto()
class _IdleTask():
    """Defines a task to be executed on barbot idle"""
    def __init__(self, task_type : _IdleTaskType, callback, command: str, *parameters):
        self._task_type = task_type
        self._callback = callback
        self._parameters = parameters
        self._command = command

    def execute(self):
        """Call this in idle of barbot"""
        if self._task_type == _IdleTaskType.DO:
            result = communication.try_do(self._command, self._parameters)
        elif self._task_type == _IdleTaskType.SET:
            result = communication.try_set(self._command, self._parameters)
        elif self._task_type == _IdleTaskType.GET:
            result = communication.try_get(self._command, self._parameters)
        if self._callback is not None:
            self._callback(result)


class BarBot():
    """The main class containing the statemachine of the barbot"""
    def __init__(self, demo_mode = False):
        self._abort = False
        self._demo_mode = demo_mode
        self._user_input:UserInput = UserInput.UNDEFINED
        self._abort_mixing = False
        self._weight_timeout = 1
        self._weight = None
        self._pumps_to_clean = []
        self._connected_boards = [] if not self._demo_mode else [communication.Boards.balance]
        self._message: UserMessages = None
        self._progress = 0
        self._add_straw = False
        self._add_ice = False
        self._idle_tasks: list[_IdleTask] = []
        self._state = BarBotState.IDLE if self._demo_mode else BarBotState.CONNECTING
        self._current_recipe: recipes.Recipe = None
        self._current_recipe_item: recipes.RecipeItem = None
        # callbacks
        self.on_mixing_finished: Callable[[recipes.Recipe]] = lambda current_recipe: None
        self.on_mixing_progress_changed: Callable[[int]] = lambda progress: None
        self.on_state_changed: Callable[[BarBotState]] = lambda state: None
        self.on_message_changed: Callable[[UserMessages]] = lambda message: None

        # make sure all state functions are defined
        unknown_state = None
        for state in BarBotState:
            if not hasattr(self, self._get_state_function_name(state)):
                unknown_state = state
                break
        assert unknown_state is None, f"State function not found: {unknown_state.name}"

    @property
    def was_aborted(self):
        """Whether the mixing was aborted"""
        return self._abort_mixing

    @property
    def current_recipe(self) -> recipes.Recipe:
        """Get the recipe that is being mixed"""
        return self._current_recipe

    @property
    def current_recipe_item(self) -> recipes.RecipeItem:
        """Get the ricipe item that is being drafted"""
        return self._current_recipe_item

    @property
    def state(self):
        """Get the current state of the barbot"""
        return self._state

    def _reset_user_input(self):
        """Reset the user input to UserInput.UNDEFINED"""
        self._user_input = UserInput.UNDEFINED

    def set_balance_calibration(self, offset, cal):
        """"Save new offset and calibration for the internal balance to the config.
        Asynchronously send the new values to the esp32.
        :param offset: New offset value
        :param cal: New calibration value
        """
        # change config
        config.balance_offset = offset
        config.balance_calibration = cal
        # write and reload config
        config.save()
        config.load()
        # send new values to mainboard

        self._idle_tasks.append(
            _IdleTask(_IdleTaskType.SET, None, "SetBalanceOffset", int(config.balance_offset))
        )
        self._idle_tasks.append(
            _IdleTask(_IdleTaskType.SET, None, "SetBalanceCalibration", int(config.balance_calibration))
        )

    def reconnect(self):
        """Reinitiate the connection procedure"""
        self._set_state(BarBotState.CONNECTING)

    def _get_state_function_name(self, state: BarBotState) -> str:
        """Get the name of the barbot function to be called within the defined state.
        :param state:
        """
        return  f"_do_{str.lower(state.name)}"

    def run(self):
        """main loop, runs the whole time"""
        logging.debug("State machine started%s", " in demo mode" if self._demo_mode else "")
        while not self._abort:
            # reset abort flag
            self._abort_mixing = False
            # call self._do function
            func = getattr(self, self._get_state_function_name(self._state))
            func()
            if self._set_state not in \
                [BarBotState.STARTUP, BarBotState.IDLE, BarBotState.CONNECTING]:
                self._go_to_idle()

        if not self._demo_mode:
            communication.close()

    def _do_idle(self):
        """Perform idle task"""
        if not self._demo_mode:
            communication.read_message()
            if not communication.is_connected:
                self._set_state(BarBotState.CONNECTING)
            if len(self._idle_tasks) > 0:
                self._idle_tasks[0].execute()
                self._idle_tasks.pop(0)
        else:
            time.sleep(0.1)

    def _do_searching(self):
        """Search for a barbot in range, save its mac address and connect to it if one is found."""
        logging.info("Search for BarBot4")
        res = communication.find_bar_bot()
        if res:
            config.mac_address = res
            config.save()
            self._set_state(BarBotState.CONNECTING)

    def _do_connecting(self):
        """Connect to a barbot with the mac address defined in the config"""
        if not config.is_mac_address_valid():
            self._set_state(BarBotState.SEARCHING)
        else:
            if communication.connect(config.mac_address):
                self._set_state(BarBotState.STARTUP)
            else:
                time.sleep(1)

    def _do_startup(self):
        """Startup the barbot by setting values from the config to the esp32"""
        if not communication.is_connected:
            self._set_state(BarBotState.CONNECTING)
            return
        # wait for a status message
        if communication.read_message().type != communication.MessageTypes.STATUS:
            return
        # check all boards that should be connected and warn if they are not
        self._get_boards_connected()
        if communication.Boards.balance not in self._connected_boards:
            self._set_message(UserMessages.BOARD_NOT_CONNECTED_BALANCE)
        if config.stirrer_connected \
            and communication.Boards.mixer not in self._connected_boards:
            self._set_message(UserMessages.BOARD_NOT_CONNECTED_MIXER)
            if not self._wait_for_user_input():
                return
        if config.straw_dispenser_connected \
            and communication.Boards.straw not in self._connected_boards:
            self._set_message(UserMessages.BOARD_NOT_CONNECTED_STRAW)
            if not self._wait_for_user_input():
                return
        if config.ice_crusher_connected \
            and communication.Boards.crusher not in self._connected_boards:
            self._set_message(UserMessages.BOARD_NOT_CONNECTED_CRUSHER)
            if not self._wait_for_user_input():
                return
        if config.sugar_dispenser_connected \
            and communication.Boards.sugar not in self._connected_boards:
            self._set_message(UserMessages.BOARD_NOT_CONNECTED_SUGAR)
            if not self._wait_for_user_input():
                return
        self._set_message(UserMessages.NONE)
        communication.try_set("SetLED", 3)
        communication.try_set("SetSpeed", config.max_speed)
        communication.try_set("SetAccel", config.max_accel)
        communication.try_set("SetPumpPower", config.pump_power)
        communication.try_set("SetBalanceCalibration", int(config.balance_calibration))
        communication.try_set("SetBalanceOffset",int(config.balance_offset))
        self._set_state(BarBotState.IDLE)

    def set_user_input(self, value: UserInput):
        """Set the answer of the user to a message."""
        self._user_input = value


    def abort_mixing(self):
        """Abort an ongoing mixing process"""
        self._abort_mixing = True
        logging.warning("Mixing aborted")
        # abort can be sent synchronously
        communication.send_abort()


    def _set_state(self, state):
        self._state = state
        logging.debug("State changed to '%s'",self._state)
        if self.on_state_changed is not None:
            self.on_state_changed(state)


    def _set_mixing_progress(self, progress : int):
        self._progress = progress
        if self.on_mixing_progress_changed is not None:
            self.on_mixing_progress_changed(progress)


    def _set_message(self, message: UserMessages):
        self._message = message
        if message is None:
            logging.debug("Remove user message")
        else:
            logging.debug("Show user message: %s", message)
        if self.on_message_changed is not None:
            self.on_message_changed(message)

    @property
    def current_message(self):
        """Message to the user, None if there isn't any"""
        return self._message

    @property
    def is_busy(self):
        """Whether the barbot is executing any commands"""
        return self._state != BarBotState.IDLE

    @property
    def can_edit_database(self):
        """The database can be edited as long as the we are not using the esp32"""
        return self._state in [BarBotState.CONNECTING, BarBotState.IDLE]


    def _wait_for(self, condition : Callable[[],bool]) -> bool:
        """Wait for the condition to become true.
        Will return False when operation is aborted. 
        :param condition: Callback that is called periodically until it returns True
        :returns: True if the wait was successfull, False on abort
        """
        while not self._abort and not condition():
            time.sleep(0.1)
        return not self._abort


    def _wait_for_user_input(self):
        """Reset the user input and wait until set_user_input() was called or mixing was aborted.
        """
        self._reset_user_input()
        logging.debug("Wait for user input")
        while not self._abort and self._user_input == UserInput.UNDEFINED:
            time.sleep(0.1)
        if self._abort:
            logging.warning("Waiting aborted")
            return False
        #else
        logging.debug("User answered: %s",  self._user_input.name)
        return True



    def _go_to_idle(self):
        """Go to idle state of the barbot, reset the user message and home the hardware"""
        self._set_message(UserMessages.NONE)
        self._set_state(BarBotState.IDLE)
        if not self._demo_mode:
            communication.try_set("SetLED", 3)
            # first move to what is supposed to be zero, then home
            communication.try_do("Move", 0)
            communication.try_do("Home")

    def _draft_one(self, item: recipes.RecipeItem):
        """Draft a single ingredient.
        :param item: The recipe item to be draft"""
        # user aborted
        if self._abort_mixing:
            return False
        if item.ingredient.type == ingredients.IngredientType.STIRR:
            logging.info("Start stirring")
            communication.try_do("Mix", int(config.stirring_time / 1000))
            return True
        if item.ingredient.type == ingredients.IngredientType.SUGAR:
            # take sugar per unit from config
            weight = int(item.amount * config.sugar_per_unit)
            logging.info("Start adding %i g of '%s'", weight, item.ingredient.name)
        else:
            # cl to g
            weight = int(item.amount * item.ingredient.density * 10)
            port = ports.port_of_ingredient(item.ingredient)
            logging.info("Start adding %i g of '%s' at port %i",\
                weight, item.ingredient.name, port)
        while True:
            if item.ingredient.type == ingredients.IngredientType.SUGAR:
                success, return_parameters = communication.try_do("Sugar", weight)
            else:
                # TODO: Handle non successfull SET
                if item.ingredient.type == ingredients.IngredientType.SIRUP:
                    communication.try_set("SetPumpPower", config.pump_power_sirup)
                else:
                    communication.try_set("SetPumpPower", config.pump_power)
                success, return_parameters = communication.try_do("Draft", port, weight)
            # user aborted
            if self._abort_mixing:
                return False
            if success is True:
                # drafting successfull
                return True
            if isinstance(return_parameters, list) and len(return_parameters) >= 2:
                error_code = int(return_parameters[0])
                logging.error("Error while drafting: '%s'", error_code)
                error = Error(error_code)
                if error == Error.INGREDIENT_EMPTY:
                    # ingredient is empty
                    # safe how much is left to draft
                    weight = int(return_parameters[1])
                    self._set_message(UserMessages.INGREDIENT_EMPTY)
                    self._user_input = None
                    # wait for user input
                    if not self._wait_for_user_input():
                        return False
                    # remove the message
                    self._set_message(UserMessages.NONE)
                    if not self._user_input:
                        return False
                    # repeat the loop

                elif error == Error.GLAS_REMOVED:
                    logging.info("Glas was removed while drafting")
                    self._set_message(UserMessages.GLAS_REMOVED_WHILE_DRAFTING)
                    self._wait_for_user_input()
                    return False

                else:
                    logging.warning("Unkown error code")
                    self._set_message(UserMessages.UNKNOWN_ERROR)
                    self._wait_for_user_input()
                    return False

            else:
                # unhandled return value
                logging.error("Unhandled result while drafting: '%s'", return_parameters)
                return False

    # do commands

    def _do_mixing(self):
        """Perform mixing process with the current recipe"""
        progress = 0
        self._set_mixing_progress(progress)

        if not self._demo_mode:
            communication.try_set("PlatformLED", 3)
            # wait for the glas
            if communication.try_get("HasGlas") != "1":
                communication.try_set("PlatformLED", 2)
                self._set_message(UserMessages.PLACE_GLAS)
                self._reset_user_input()
                # wait for glas or user abort
                def glas_present_or_user_input():
                    if communication.try_get("HasGlas") == "1":
                        return True
                    # any user input was set
                    if self._user_input != UserInput.UNDEFINED:
                        return True
                    return False
                if not self._wait_for(glas_present_or_user_input):
                    return
                self._set_message(UserMessages.NONE)
                # user answered with anything
                if self._user_input != UserInput.UNDEFINED:
                    return

        # wait for the user to take the hands off the glas
        time.sleep(1)
        if not self._demo_mode:
            communication.try_set("PlatformLED", 5)
            communication.try_set("SetLED", 5)
        self._reset_user_input()
        for item in self._current_recipe.items:
            # user aborted
            if self._abort_mixing:
                break
            self._current_recipe_item = item
            if not self._demo_mode:
                # do the actual draft, exit the loop if it did not succeed
                if not self._draft_one(item):
                    break
            else:
                if self._abort_mixing:
                    logging.warning("Waiting aborted")
                    return
                time.sleep(1)
            progress += 1
            self._set_mixing_progress(progress)

        # add ice if it was selected and mixing was not aborted
        if self._add_ice and not self._abort_mixing:
            if not self._demo_mode:
                self._do_crushing()
            else:
                time.sleep(1)
            progress += 1
            self._set_mixing_progress(progress)

        # move to start
        if not self._demo_mode:
            communication.try_do("Move", 0)

        # add straw if it was selected and mixing was not aborted
        if self._add_straw and not self._abort_mixing:
            if not self._demo_mode:
                self._do_straw()
            else:
                time.sleep(1)
            progress += 1
            self._set_mixing_progress(progress)

        #mising is done
        self._set_message(UserMessages.MIXING_DONE_REMOVE_GLAS)
        if not self._demo_mode:
            communication.try_set("PlatformLED", 2)
            communication.try_set("SetLED", 4)
        # show message and led for some seconds
        time.sleep(4)
        if not self._demo_mode:
            communication.try_set("PlatformLED", 0)
            orders.add_order(self._current_recipe)
        self._set_message(UserMessages.NONE)
        if self.on_mixing_finished is not None:
            self.on_mixing_finished(self._current_recipe)

    def _do_crushing(self):
        """Perform the crushing of ice"""
        # user aborted
        if self._abort_mixing:
            return False
        # try adding ice until it works or user aborts
        ice_to_add = config.ice_amount
        while True:
            success, return_parameters = communication.try_do("Crush", ice_to_add)
            if self._abort_mixing:
                # user aborted
                return False
            if success is True:
                # crushing successfull
                return True
            if isinstance(return_parameters, list) and len(return_parameters) >= 2:
                error_code = int(return_parameters[0])
                logging.error("Error while crushing ice: '%s'", error_code)
                error = Error(error_code)
                if error == Error.INGREDIENT_EMPTY:
                    # ice is empty, save how much is left
                    ice_to_add = int(return_parameters[1])
                    self._set_message(UserMessages.ICE_EMPTY)
                    self._reset_user_input()
                    # wait for user input
                    if not self._wait_for_user_input():
                        return False
                    # remove the message
                    self._set_message(UserMessages.NONE)
                    if self._user_input != UserInput.YES:
                        return False
                    # repeat the loop

                elif error == Error.GLAS_REMOVED:
                    logging.info("Glas was removed while crushing")
                    self._set_message(UserMessages.GLAS_REMOVED_WHILE_DRAFTING)
                    self._wait_for_user_input()
                    return False

                elif error == Error.I2C:
                    self._set_message(UserMessages.I2C_ERROR)
                    # wait for user input
                    self._wait_for_user_input()
                    # a communication error will always stop the mixing process
                    return False

                elif error == Error.CRUSHER_COVER_OPEN:
                    self._set_message(UserMessages.CRUSHER_COVER_OPEN)
                    self._reset_user_input()
                    # wait for user input
                    if not self._wait_for_user_input():
                        return False
                    # remove the message
                    self._set_message(UserMessages.NONE)
                    if not self._user_input:
                        return False
                    # repeat the loop

                elif error == Error.CRUSHER_TIMEOUT:
                    self._set_message(UserMessages.CRUSHER_TIMEOUT)
                    self._user_input = None
                    # wait for user input
                    if not self._wait_for_user_input():
                        return False
                    # remove the message
                    self._set_message(UserMessages.NONE)
                    if not self._user_input:
                        return False
                    # repeat the loop

                else:
                    logging.warning("Unkown error code")
                    self._set_message(UserMessages.UNKNOWN_ERROR)
                    self._wait_for_user_input()
                    return False

            else:
                # unhandled return value
                logging.error("Unhandled result while drafting: '%s'", return_parameters)
                return False

    def _do_cleaning_cycle(self):
        self._set_message(UserMessages.CLEANING_ADAPTER)
        # ask user if the cleanig adapter is there
        self._reset_user_input()
        if not self._wait_for_user_input():
            return
        if self._user_input != UserInput.YES:
            return
        self._set_message(UserMessages.NONE)
        if self._demo_mode:
            time.sleep(2)
            return
        for pump_index in self._pumps_to_clean:
            # user aborted
            if self._abort_mixing:
                return
            communication.try_do("Clean", pump_index,
                                config.cleaning_time)

    def _do_cleaning(self):
        if self._demo_mode:
            time.sleep(2)
            return
        weight = int(self._current_recipe_item.weight)
        communication.try_do("Clean", self._current_recipe_item.port, weight)

    def _do_single_ingredient(self):
        if self._demo_mode:
            time.sleep(2)
            return
        self._set_message(UserMessages.PLACE_GLAS)
        self._reset_user_input()
        # wait for glas or user abort
        def glas_present_or_user_input():
            if communication.try_get("HasGlas") == "1":
                return True
            # any user input was set
            if self._user_input != UserInput.UNDEFINED:
                return True
            return False
        if not self._wait_for(glas_present_or_user_input):
            return
        self._set_message(UserMessages.NONE)
        # user answered with anything
        if self._user_input != UserInput.UNDEFINED:
            return
        self._draft_one(self._current_recipe_item)

    def _do_straw(self):
        """Try dispensing straw until it works or user aborts"""
        while not communication.try_do("Straw"):
            self._reset_user_input()
            self._set_message(UserMessages.STRAWS_EMPTY)
            if not self._wait_for_user_input():
                return
            self._set_message(UserMessages.NONE)
            if self._user_input != UserInput.UNDEFINED:
                break

    # start commands

    def start_mixing(self, recipe: recipes.Recipe):
        """Start mixing a recipe.
        :param recipe: The recipe that is to be mixed."""
        self._abort_mixing = False
        self._current_recipe = recipe
        self._set_state(BarBotState.MIXING)

    def start_single_ingredient(self, recipe_item: recipes.RecipeItem):
        """Start adding a single ingredient to your glas.
        :param recipe_item: The item to be added"""
        self._abort_mixing = False
        self._current_recipe_item = recipe_item
        self._set_state(BarBotState.SINGLE_INGREDIENT)

    def start_crushing(self):
        """Add ice to the glas"""
        self._abort_mixing = False
        self._set_state(BarBotState.CRUSHING)

    def start_cleaning(self, port):
        """Start cleaning a single pump.
        :param port: The port to clean"""
        self._abort_mixing = False
        self._pumps_to_clean = [port]
        self._set_state(BarBotState.CLEANING_CYCLE)

    def start_cleaning_cycle(self, pumps_to_clean:list[int]):
        """Start a cleaning cycle.
        :param pumps_to_clean: List of ports to clean successively"""
        self._abort_mixing = False
        self._pumps_to_clean = pumps_to_clean
        self._set_state(BarBotState.CLEANING_CYCLE)

    def start_straw(self):
        """Add a straw to the glas"""
        self._set_state(BarBotState.STRAW)

    def get_weight(self, callback):
        """Get the weight when the state machine is idle again.
        The callback is executed after execution.
        """
        def internal_callback(res):
            self._weight = float(res) if res is not None else None
            callback(self._weight)
        self._idle_tasks.append(
            _IdleTask(_IdleTaskType.GET, internal_callback, "GetWeight")
        )

    def _get_boards_connected(self):
        """Synchronously get the connected boards and save them to '_connected_boards'
        """
        result = communication.try_get("GetConnectedBoards")
        self._connected_boards = self._parse_connected_boards(result)

    def _parse_connected_boards(self, bit_values) -> list[communication.Boards]:
        """Parse bit values of the connected boards to list of enum"""
        boards = int(bit_values) if bit_values is not None else 0
        #convert bit field to list of enum values
        return [b for b in communication.Boards if boards & 1 << b.value]

    def get_boards_connected(self, callback):
        """Get the connected boards when the state machine is idle again.
        The callback is executed after execution.
        """
        def internal_callback(result):
            self._connected_boards = self._parse_connected_boards(result)
            callback(self._connected_boards)
        self._idle_tasks.append(
            _IdleTask(_IdleTaskType.GET, internal_callback, "GetConnectedBoards")
        )
