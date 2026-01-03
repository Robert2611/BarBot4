""" All the BarBot logic
"""
import subprocess
import logging
from typing import Callable, List, NamedTuple
from enum import Enum, auto

from barbot.logic.core.barbot_interface import BarBotInterface
from barbot.logic.core.constants import UserInputType, UserMessageType
from ..recipes import PartyCollection,Recipe,RecipeItem
from ..config import BarBotConfig, PortConfiguration
from ..communication import Mainboard, CommunicationResult, BoardType
from ..communication import LEDMode, PlatformLEDMode
from .states import (
    ConnectingState, SearchingState, StartupState,
    IdleState, MixingState, CrushingState, StrawState, CleaningCycleState,
    SingleIngredientState
)

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
    """Keeps the options for a mixing process"""
    recipe: Recipe
    add_straw: bool = False
    add_ice: bool = False


def run_command(cmd_str):
    """Run a linux command discarding all its output
    :param cmd_str: Command to be executed
    """
    subprocess.Popen([cmd_str], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)

class BarBot(BarBotInterface):
    """The main class containing the statemachine of the barbot"""
    def __init__(self, config: BarBotConfig, ports: PortConfiguration, mainboard: Mainboard):
        self._abort = False
        self._user_input:UserInputType = UserInputType.UNDEFINED
        self._abort_mixing = False
        self._weight_timeout = 1
        self._weight = None
        self._pumps_to_clean = []
        self._connected_boards = []
        self._message: UserMessageType = None
        self._progress = 0
        self._idle_tasks: list[_IdleTask] = []
        self._current_mixing_options: MixingOptions = None
        self._current_recipe_item: RecipeItem = None
        self._config = config
        self._ports = ports
        self._parties = PartyCollection()
        self._mainboard = mainboard
        self._state_changed: bool = False

        # Initialize state handlers
        self._state_handlers = {
            ConnectingState: ConnectingState(config, ports, mainboard, self),
            SearchingState: SearchingState(config, ports, mainboard, self),
            StartupState: StartupState(config, ports, mainboard, self),
            IdleState: IdleState(config, ports, mainboard, self),
            MixingState: MixingState(config, ports, mainboard, self),
            CrushingState: CrushingState(config, ports, mainboard, self),
            StrawState: StrawState(config, ports, mainboard, self),
            CleaningCycleState: CleaningCycleState(config, ports, mainboard, self),
            SingleIngredientState: SingleIngredientState(config, ports, mainboard, self),
        }

        self._state = self._state_handlers[ConnectingState]

        # callbacks
        self.on_mixing_finished: Callable[[Recipe], None] = lambda current_recipe: None
        self.on_mixing_progress_changed: Callable[[int], None] = lambda progress: None
        self.on_state_changed: Callable[[type], None] = lambda state: None
        self.on_message_changed: Callable[[UserMessageType], None] = lambda message: None

    @property
    def config(self) -> BarBotConfig:
        """Get the config of the barbot"""
        return self._config

    @property
    def ports(self) -> BarBotConfig:
        """Get the port configuration of the barbot"""
        return self._ports

    # from BarBotInterface
    @property
    def was_aborted(self) -> bool:
        return self._abort_mixing

    def set_message(self, message: UserMessageType):
        return self._set_message(message)

    @property
    def user_input(self) -> UserInputType:
        return self._user_input

    def reset_user_input(self):
        self._reset_user_input()

    @property
    def parties(self) -> PartyCollection:
        """Get the parties collection"""
        return self._parties

    def set_mixing_progress(self, progress : int):
        self._set_mixing_progress(progress)

    def mixing_progress(self) -> int:
        return self._progress

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
        return self._state.__class__

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
        self._set_state(ConnectingState)

    def run(self):
        """main loop, runs the whole time"""
        logging.debug("State machine started")
        while not self._abort:
            # reset abort flag
            self._abort_mixing = False
            # call the appropriate state handler
            self._state.execute()

            if self._state_changed:
                self._state_changed = False
            # only go to idle if there was no state change in between
            elif self._state.__class__ not in [
                    StartupState,
                    IdleState,
                    ConnectingState,
                    SearchingState
                ]:
                self._go_to_idle()
        self._mainboard.disconnect()


    def set_user_input(self, value: UserInputType):
        """Set the answer of the user to a message."""
        self._user_input = value
        logging.debug("User input: %s", value.name)

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

    def _set_state_from_handler(self, state):
        """Set state from within a state handler"""
        self._set_state(state)

    def _set_state(self, state):
        self._state = self._state_handlers[state]
        logging.debug("State changed to '%s'", state.__name__)
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
        return self._state.__class__ != IdleState

    @property
    def can_edit_database(self):
        """The database can be edited as long as the we are not using the esp32"""
        return self._state.__class__ in [ConnectingState, IdleState]

    def _go_to_idle(self):
        """Go to idle state of the barbot, reset the user message and home the hardware"""
        logging.debug("Go to idle")
        self._set_message(UserMessageType.NONE)
        self._set_state(IdleState)
        #reset current values
        self._current_mixing_options = None
        self._current_recipe_item = None
        self._mainboard.set("SetLED", LEDMode.RAINBOW.value)
        self._mainboard.set("PlatformLED", PlatformLEDMode.OFF.value)
        # move to where zero should be, if no motor steps were skipped
        self._mainboard.do("Move", 0)
        self._mainboard.do("Home")

    def has_glas(self):
        result = self._mainboard.get("HasGlas")
        return result.was_successful and result.return_parameters[0] == "1"


    # start commands

    def start_mixing(self, options: MixingOptions):
        """Start mixing a recipe.
        :param options: Mixing options"""
        self._abort_mixing = False
        self._current_mixing_options = options
        self._set_state(MixingState)

    def start_single_ingredient(self, recipe_item: RecipeItem):
        """Start adding a single ingredient to your glas.
        :param recipe_item: The item to be added"""
        self._abort_mixing = False
        self._current_recipe_item = recipe_item
        self._set_state(SingleIngredientState)

    def start_crushing(self):
        """Add ice to the glas"""
        self._abort_mixing = False
        self._set_state(CrushingState)

    def start_cleaning(self, port):
        """Start cleaning a single pump.
        :param port: The port to clean"""
        self._abort_mixing = False
        self._pumps_to_clean = [port]
        self._set_state(CleaningCycleState)

    def start_cleaning_cycle(self, pumps_to_clean:List[int]):
        """Start a cleaning cycle.
        :param pumps_to_clean: List of ports to clean successively"""
        self._abort_mixing = False
        self._pumps_to_clean = pumps_to_clean
        self._set_state(CleaningCycleState)

    def start_straw(self):
        """Add a straw to the glas"""
        self._set_state(StrawState)

    def get_weight(self, callback:Callable[[float],None]):
        """Get the weight when the state machine is idle again.
        The callback is executed after execution.
        """
        def internal_callback(res:CommunicationResult):
            self._weight = float(res.return_parameters[0]) \
                if res.was_successful and len(res.return_parameters) > 0 \
                else None
            callback(self._weight)
        self._idle_tasks.append(
            _IdleTask(_IdleTaskType.GET, internal_callback, "GetWeight")
        )

    def _get_boards_connected(self):
        """Synchronously get the connected boards and save them to '_connected_boards'
        """
        result = self._mainboard.get("GetConnectedBoards")
        if result.was_successful and len(result.return_parameters) > 0:
            self._connected_boards = self._parse_connected_boards(result.return_parameters[0])

    def _parse_connected_boards(self, bit_values) -> List[BoardType]:
        """Parse bit values of the connected boards to list of enum"""
        boards = int(bit_values) if bit_values is not None else 0
        #convert bit field to list of enum values
        return [b for b in BoardType if boards & 1 << b.value]

    @property
    def connected_boards(self) -> List[BoardType]:
        """Get a list of the connected boards, it is read once on startup"""
        return self._connected_boards

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
