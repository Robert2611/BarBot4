""" All the BarBot logic
"""
import subprocess
import logging
import time
from typing import Callable, List, NamedTuple
from enum import Enum, auto
from .recipes import PartyCollection,Recipe,RecipeItem
from .config import BarBotConfig, IngredientType, PortConfiguration
from .communication import Mainboard, CommunicationResult, BoardType, ResponseTypes
from .communication import ErrorType as CommError

def run_command(cmd_str):
    """Run a linux command discarding all its output
    :param cmd_str: Command to be executed
    """
    subprocess.Popen([cmd_str], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)

class UserMessageType(Enum):
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

class UserInputType(Enum):
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

class _IdleTaskType(Enum):
    GET = auto()
    SET = auto()
    DO = auto()

class _IdleTask():
    """Defines a task to be executed on barbot idle"""
    def __init__(self,task_type : _IdleTaskType, callback: Callable[[CommunicationResult], None],
                 command: str, *parameters:str):
        self._task_type = task_type
        self._callback = callback
        self._parameters = parameters
        self._command = command

    def execute(self, mainboard:Mainboard):
        """Call this in idle of barbot"""
        result = {
            _IdleTaskType.DO: mainboard.do,
            _IdleTaskType.GET: mainboard.get,
            _IdleTaskType.SET: mainboard.set
        }.get(self._task_type)(self._command, *self._parameters)
        if self._callback is not None:
            self._callback(result)

class MixingOptions(NamedTuple):
    recipe: Recipe
    add_straw: bool = False
    add_ice: bool = False

class BarBot():
    """The main class containing the statemachine of the barbot"""
    def __init__(self, config: BarBotConfig, ports: PortConfiguration, demo_mode = False):
        self._abort = False
        self._demo_mode = demo_mode
        self._user_input:UserInputType = UserInputType.UNDEFINED
        self._abort_mixing = False
        self._weight_timeout = 1
        self._weight = None
        self._pumps_to_clean = []
        self._connected_boards = [] if not self._demo_mode else [BoardType.BALANCE]
        self._message: UserMessageType = None
        self._progress = 0
        self._idle_tasks: list[_IdleTask] = []
        self._state = BarBotState.IDLE if self._demo_mode else BarBotState.CONNECTING
        self._current_mixing_options: MixingOptions = None
        self._current_recipe_item: RecipeItem = None
        self._config = config
        self._ports = ports
        self._parties = PartyCollection()
        self._mainboard = Mainboard()
        self._state_changed: bool = False
        # callbacks
        self.on_mixing_finished: Callable[[Recipe], None] = lambda current_recipe: None
        self.on_mixing_progress_changed: Callable[[int], None] = lambda progress: None
        self.on_state_changed: Callable[[BarBotState], None] = lambda state: None
        self.on_message_changed: Callable[[UserMessageType], None] = lambda message: None

        # make sure all state functions are defined
        unknown_state = None
        for state in BarBotState:
            if not hasattr(self, self._get_state_function_name(state)):
                unknown_state = state
                break
        assert unknown_state is None, f"State function not found: {unknown_state.name}"

    @property
    def parties(self) -> PartyCollection:
        """Get the parties collection"""
        return self._parties

    @property
    def config(self) -> BarBotConfig:
        """Get the config of the barbot"""
        return self._config
    
    @property
    def ports(self) -> BarBotConfig:
        """Get the port configuration of the barbot"""
        return self._ports

    @property
    def was_aborted(self) -> bool:
        """Whether the mixing was aborted"""
        return self._abort_mixing

    @property
    def current_mixing_options(self) -> MixingOptions:
        """Get the mixing options for what is being mixed"""
        return self._current_mixing_options

    @property
    def current_recipe_item(self) -> RecipeItem:
        """Get the ricipe item that is being drafted"""
        return self._current_recipe_item

    @property
    def state(self):
        """Get the current state of the barbot"""
        return self._state

    def _reset_user_input(self):
        """Reset the user input to UserInput.UNDEFINED"""
        self._user_input = UserInputType.UNDEFINED

    def set_balance_calibration(self, offset, cal):
        """"Save new offset and calibration for the internal balance to the config.
        Asynchronously send the new values to the esp32.
        :param offset: New offset value
        :param cal: New calibration value
        """
        # change config
        self._config.balance_offset = offset
        self._config.balance_calibration = cal

        # write and reload config
        self._config.save()
        self._config.load()

        # send new values to mainboard
        self._idle_tasks.append(
            _IdleTask(
                _IdleTaskType.SET,
                None,
                "SetBalanceOffset",
                int(self._config.balance_offset)
            )
        )
        self._idle_tasks.append(
            _IdleTask(
                _IdleTaskType.SET,
                None,
                "SetBalanceCalibration",
                int(self._config.balance_calibration)
            )
        )

    def reconnect(self):
        """Reinitiate the connection procedure"""
        # in demo mode there is nothing to do here
        if not self._demo_mode:
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
            if self._state_changed:
                self._state_changed = False
            # only go to idle if there was no state change in between
            elif self._state not in \
                [BarBotState.STARTUP, BarBotState.IDLE, BarBotState.CONNECTING, BarBotState.SEARCHING]:
                self._go_to_idle()

        if not self._demo_mode:
            self._mainboard.disconnect()

    def _do_idle(self):
        """Perform idle task"""
        if not self._demo_mode:
            # read status message
            self._mainboard.read_message()
            if not self._mainboard.is_connected:
                self._set_state(BarBotState.CONNECTING)
            if len(self._idle_tasks) > 0:
                self._idle_tasks[0].execute(self._mainboard)
                self._idle_tasks.pop(0)
        else:
            time.sleep(0.1)

    def _do_searching(self):
        """Search for a barbot in range, save its mac address and connect to it if one is found."""
        logging.info("Search for BarBot4")
        res = self._mainboard.find_bar_bot()
        if res:
            self._config.mac_address = res
            self._config.save()
            self._set_state(BarBotState.CONNECTING)

    def _do_connecting(self):
        """Connect to a barbot with the mac address defined in the config"""
        if not self._config.is_mac_address_valid:
            self._set_state(BarBotState.SEARCHING)
        else:
            if self._mainboard.connect(self._config.mac_address):
                self._set_state(BarBotState.STARTUP)
            else:
                time.sleep(1)

    def _do_startup(self):
        """Startup the barbot by setting values from the config to the mainboard"""
        if not self._mainboard.is_connected:
            self._set_state(BarBotState.CONNECTING)
            return
        # wait for a status message
        if self._mainboard.read_message().message_type != ResponseTypes.STATUS:
            return
        # check all boards that should be connected and warn if they are not
        self._get_boards_connected()
        if BoardType.BALANCE not in self._connected_boards:
            self._set_message(UserMessageType.BOARD_NOT_CONNECTED_BALANCE)
        if self._config.stirrer_connected \
            and BoardType.MIXER not in self._connected_boards:
            self._set_message(UserMessageType.BOARD_NOT_CONNECTED_MIXER)
            if not self._wait_for_user_input():
                return
        if self._config.straw_dispenser_connected \
            and BoardType.STRAW not in self._connected_boards:
            self._set_message(UserMessageType.BOARD_NOT_CONNECTED_STRAW)
            if not self._wait_for_user_input():
                return
        if self._config.ice_crusher_connected \
            and BoardType.CRUSHER not in self._connected_boards:
            self._set_message(UserMessageType.BOARD_NOT_CONNECTED_CRUSHER)
            if not self._wait_for_user_input():
                return
        if self._config.sugar_dispenser_connected \
            and BoardType.SUGAR not in self._connected_boards:
            self._set_message(UserMessageType.BOARD_NOT_CONNECTED_SUGAR)
            if not self._wait_for_user_input():
                return
        self._set_message(UserMessageType.NONE)
        self._mainboard.set("SetLED", 3)
        self._mainboard.set("SetSpeed", self._config.max_speed)
        self._mainboard.set("SetAccel", self._config.max_accel)
        self._mainboard.set("SetPumpPower", self._config.pump_power)
        self._mainboard.set("SetBalanceCalibration", int(self._config.balance_calibration))
        self._mainboard.set("SetBalanceOffset",int(self._config.balance_offset))
        self._set_state(BarBotState.IDLE)

    def set_user_input(self, value: UserInputType):
        """Set the answer of the user to a message."""
        self._user_input = value

    def abort_mixing(self):
        """Abort an ongoing mixing process"""
        self._abort_mixing = True
        logging.warning("Mixing aborted")
        # abort can be sent synchronously
        self._mainboard.send_abort()

    def abort(self):
        """Abort the barbot state machine"""
        self._abort_mixing = True
        self._abort = True 

    def _set_state(self, state):
        self._state = state
        logging.debug("State changed to '%s'",self._state)
        self._state_changed = True
        if self.on_state_changed is not None:
            self.on_state_changed(state)

    def _set_mixing_progress(self, progress : int):
        self._progress = progress
        if self.on_mixing_progress_changed is not None:
            self.on_mixing_progress_changed(progress)

    def _set_message(self, message: UserMessageType):
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
        while not self._abort and self._user_input == UserInputType.UNDEFINED:
            time.sleep(0.1)
        if self._abort:
            logging.warning("Waiting aborted")
            return False
        #else
        logging.debug("User answered: %s",  self._user_input.name)
        return True

    def _go_to_idle(self):
        """Go to idle state of the barbot, reset the user message and home the hardware"""
        self._set_message(UserMessageType.NONE)
        self._set_state(BarBotState.IDLE)
        #reset current values
        self._current_mixing_options = None
        self._current_recipe_item = None
        if not self._demo_mode:
            self._mainboard.set("SetLED", 3)
            # first move to what is supposed to be zero, then home
            self._mainboard.do("Move", 0)
            self._mainboard.do("Home")

    def _has_glas(self):
        result = self._mainboard.get("HasGlas")
        return result.was_successfull and result.return_parameters[0] == "1"

    def _draft_one(self, item: RecipeItem) -> bool:
        """Draft a single ingredient.
        :param item: The recipe item to be draft"""
        # user aborted
        if self._abort_mixing:
            return False
        if item.ingredient.type == IngredientType.STIRR:
            logging.info("Start stirring")
            self._mainboard.do("Mix", int(self._config.stirring_time / 1000))
            return True
        if item.ingredient.type == IngredientType.SUGAR:
            # take sugar per unit from config
            weight = int(item.amount * self._config.sugar_per_unit)
            logging.info("Start adding %i g of '%s'", weight, item.ingredient.name)
        else:
            # cl to g
            weight = int(item.amount * item.ingredient.density * 10)
            port = self._ports.port_of_ingredient(item.ingredient)
            logging.info("Start adding %i g of '%s' at port %i",\
                weight, item.ingredient.name, port)
        while True:
            if item.ingredient.type == IngredientType.SUGAR:
                result = self._mainboard.do("Sugar", weight)
            else:
                # TODO: Handle non successfull SET
                if item.ingredient.type == IngredientType.SIRUP:
                    self._mainboard.set("SetPumpPower", self._config.pump_power_sirup)
                else:
                    self._mainboard.set("SetPumpPower", self._config.pump_power)
                result = self._mainboard.do("Draft", port, weight)
            # user aborted
            if self._abort_mixing:
                return False
            if result.was_successfull is True:
                # drafting successfull
                return True
            logging.error("Error while drafting: '%s'", result.error.name)
            if result.error == CommError.INGREDIENT_EMPTY:
                # ingredient is empty
                # safe how much is left to draft
                if result.return_parameters > 0:
                    weight = int(result.return_parameters[0])
                else:
                    weight = 0
                    logging.warning("No remaining weight received")
                self._set_message(UserMessageType.INGREDIENT_EMPTY)
                self._user_input = None
                # wait for user input
                if not self._wait_for_user_input():
                    return False
                # remove the message
                self._set_message(UserMessageType.NONE)
                if not self._user_input:
                    return False
                # repeat the loop

            elif result.error == CommError.GLAS_REMOVED:
                logging.warning("Glas was removed while drafting")
                self._set_message(UserMessageType.GLAS_REMOVED_WHILE_DRAFTING)
                self._wait_for_user_input()
                return False

            else:
                logging.warning("Unexpected error code")
                self._set_message(UserMessageType.UNKNOWN_ERROR)
                self._wait_for_user_input()
                return False

    def _do_mixing(self):
        """Perform mixing process with the current recipe"""
        progress = 0
        self._set_mixing_progress(progress)

        if not self._demo_mode:
            self._set_message(UserMessageType.PLACE_GLAS)
            self._reset_user_input()
            # wait for the glas
            if not self._has_glas():
                self._mainboard.set("PlatformLED", 2)
                # wait for glas or user abort
                def glas_present_or_user_input():
                    if self._has_glas():
                        return True
                    # any user input was set
                    if self._user_input != UserInputType.UNDEFINED:
                        return True
                    return False
                if not self._wait_for(glas_present_or_user_input):
                    return
                self._set_message(UserMessageType.NONE)
                # user answered with anything
                if self._user_input != UserInputType.UNDEFINED:
                    return

        self._mainboard.set("PlatformLED", 3)
        # wait for the user to take the hands off the glas
        time.sleep(1)
        if not self._demo_mode:
            self._mainboard.set("PlatformLED", 5)
            self._mainboard.set("SetLED", 5)
        self._reset_user_input()
        for item in self._current_mixing_options.recipe.items:
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
        if self.current_mixing_options.add_ice and not self._abort_mixing:
            if not self._demo_mode:
                self._do_crushing()
            else:
                time.sleep(1)
            progress += 1
            self._set_mixing_progress(progress)

        # move to start
        if not self._demo_mode:
            self._mainboard.do("Move", 0)

        # add straw if it was selected and mixing was not aborted
        if self._current_mixing_options.add_straw and not self._abort_mixing:
            if not self._demo_mode:
                self._do_straw()
            else:
                time.sleep(1)
            progress += 1
            self._set_mixing_progress(progress)

        #mising is done
        self._set_message(UserMessageType.MIXING_DONE_REMOVE_GLAS)
        if not self._demo_mode:
            self._mainboard.set("PlatformLED", 2)
            self._mainboard.set("SetLED", 4)
        # show message and led for some seconds
        time.sleep(4)
        if not self._demo_mode:
            self._mainboard.set("PlatformLED", 0)
        self._parties.current_party.add_order(self._current_mixing_options.recipe)
        self._set_message(UserMessageType.NONE)
        if self.on_mixing_finished is not None:
            self.on_mixing_finished(self._current_mixing_options.recipe)

    def _do_crushing(self):
        """Perform the crushing of ice"""
        # user aborted
        if self._abort_mixing:
            return False
        # try adding ice until it works or user aborts
        ice_to_add = self._config.ice_amount
        while True:
            result = self._mainboard.do("Crush", ice_to_add)
            if self._abort_mixing:
                # user aborted
                return False
            if result.was_successfull:
                # crushing successfull
                return True
            logging.error("Error while drafting: '%s'", result.error.name)
            if result.error == CommError.INGREDIENT_EMPTY:
                # ice is empty, save how much is left
                if result.return_parameters > 0:
                    ice_to_add = int(result.return_parameters[0])
                else:
                    ice_to_add = 0
                    logging.warning("No remaining weight received")
                self._set_message(UserMessageType.ICE_EMPTY)
                self._reset_user_input()
                # wait for user input
                if not self._wait_for_user_input():
                    return False
                # remove the message
                self._set_message(UserMessageType.NONE)
                if self._user_input != UserInputType.YES:
                    return False
                # repeat the loop

            elif result.error == CommError.GLAS_REMOVED:
                logging.info("Glas was removed while crushing")
                self._set_message(UserMessageType.GLAS_REMOVED_WHILE_DRAFTING)
                self._wait_for_user_input()
                return False

            elif result.error == CommError.I2C:
                self._set_message(UserMessageType.I2C_ERROR)
                # wait for user input
                self._wait_for_user_input()
                # a communication error will always stop the mixing process
                return False

            elif result.error == CommError.CRUSHER_COVER_OPEN:
                self._set_message(UserMessageType.CRUSHER_COVER_OPEN)
                self._reset_user_input()
                # wait for user input
                if not self._wait_for_user_input():
                    return False
                # remove the message
                self._set_message(UserMessageType.NONE)
                if not self._user_input:
                    return False
                # repeat the loop

            elif result.error == CommError.CRUSHER_TIMEOUT:
                self._set_message(UserMessageType.CRUSHER_TIMEOUT)
                self._user_input = None
                # wait for user input
                if not self._wait_for_user_input():
                    return False
                # remove the message
                self._set_message(UserMessageType.NONE)
                if not self._user_input:
                    return False
                # repeat the loop

            else:
                logging.warning("Unkown error code")
                self._set_message(UserMessageType.UNKNOWN_ERROR)
                self._wait_for_user_input()
                return False

    def _do_cleaning_cycle(self):
        self._set_message(UserMessageType.CLEANING_ADAPTER)
        # ask user if the cleanig adapter is there
        self._reset_user_input()
        if not self._wait_for_user_input():
            return
        if self._user_input != UserInputType.YES:
            return
        self._set_message(UserMessageType.NONE)
        if self._demo_mode:
            time.sleep(2)
            return
        for pump_index in self._pumps_to_clean:
            # user aborted
            if self._abort_mixing:
                return
            self._mainboard.do("Clean", pump_index, self._config.cleaning_time)

    def _do_cleaning(self):
        if self._demo_mode:
            time.sleep(2)
            return
        weight = int(self._current_recipe_item.weight)
        self._mainboard.do("Clean", self._current_recipe_item.port, weight)

    def _do_single_ingredient(self):
        if self._demo_mode:
            time.sleep(2)
            return
        self._set_message(UserMessageType.PLACE_GLAS)
        self._reset_user_input()
        # wait for glas or user abort
        def glas_present_or_user_input():
            if self._has_glas():
                return True
            # any user input was set
            if self._user_input != UserInputType.UNDEFINED:
                return True
            return False
        if not self._wait_for(glas_present_or_user_input):
            return
        self._set_message(UserMessageType.NONE)
        # user answered with anything
        if self._user_input != UserInputType.UNDEFINED:
            return
        self._draft_one(self._current_recipe_item)

    def _do_straw(self):
        """Try dispensing straw until it works or user aborts"""
        while True:
            result = self._mainboard.do("Straw")
            if result.was_successfull:
                break
            self._reset_user_input()
            self._set_message(UserMessageType.STRAWS_EMPTY)
            if not self._wait_for_user_input():
                return
            self._set_message(UserMessageType.NONE)
            if self._user_input != UserInputType.UNDEFINED:
                break

    # start commands

    def start_mixing(self, options: MixingOptions):
        """Start mixing a recipe.
        :param options: Mixing options"""
        self._abort_mixing = False
        self._current_mixing_options = options
        self._set_state(BarBotState.MIXING)

    def start_single_ingredient(self, recipe_item: RecipeItem):
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

    def start_cleaning_cycle(self, pumps_to_clean:List[int]):
        """Start a cleaning cycle.
        :param pumps_to_clean: List of ports to clean successively"""
        self._abort_mixing = False
        self._pumps_to_clean = pumps_to_clean
        self._set_state(BarBotState.CLEANING_CYCLE)

    def start_straw(self):
        """Add a straw to the glas"""
        self._set_state(BarBotState.STRAW)

    def get_weight(self, callback:Callable[[float],None]):
        """Get the weight when the state machine is idle again.
        The callback is executed after execution.
        """
        def internal_callback(res:CommunicationResult):
            self._weight = float(res.return_parameters[0]) \
                if res.was_successfull and len(res.return_parameters) > 0 \
                else None
            callback(self._weight)
        self._idle_tasks.append(
            _IdleTask(_IdleTaskType.GET, internal_callback, "GetWeight")
        )

    def _get_boards_connected(self):
        """Synchronously get the connected boards and save them to '_connected_boards'
        """
        result = self._mainboard.get("GetConnectedBoards")
        if result.was_successfull and len(result.return_parameters) > 0:
            self._connected_boards = self._parse_connected_boards(result.return_parameters[0])

    def _parse_connected_boards(self, bit_values) -> List[BoardType]:
        """Parse bit values of the connected boards to list of enum"""
        boards = int(bit_values) if bit_values is not None else 0
        #convert bit field to list of enum values
        return [b for b in BoardType if boards & 1 << b.value]

    def get_boards_connected(self, callback):
        """Get the connected boards when the state machine is idle again.
        The callback is executed after execution.
        """
        def internal_callback(result):
            self._connected_boards = self._parse_connected_boards(result.return_parameters[0])
            callback(self._connected_boards)
        self._idle_tasks.append(
            _IdleTask(_IdleTaskType.GET, internal_callback, "GetConnectedBoards")
        )
