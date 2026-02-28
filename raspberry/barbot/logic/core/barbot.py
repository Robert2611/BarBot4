"""All the BarBot logic"""

__all__ = ["BarBot"]


import logging
from typing import Callable, List, Optional, Type

from barbot.logic.core.common import (
    BarBotStateEnum,
    MixingOptions,
    UserInputType,
    UserMessageType,
)
from barbot.logic.recipes.recipe import Recipe

from ..communication import BoardType, CommunicationResult, Mainboard
from ..config import BarBotConfig, PortConfiguration
from ..recipes import PartyCollection, RecipeItem
from .barbot_context import BarBotContext
from .states import (
    BarBotState,
    CleaningCycleState,
    ConnectingState,
    CrushingState,
    IdleState,
    MixingState,
    SearchingState,
    SingleIngredientState,
    StartupState,
    StrawState,
)
from .idle_task import IdleTask, IdleTaskType


class BarBot:
    """The main class containing the statemachine of the barbot"""

    def __init__(
        self, config: BarBotConfig, ports: PortConfiguration, mainboard: Mainboard
    ):
        self._config = config
        self._ports = ports
        self._mainboard = mainboard
        self._should_reconnect: bool = False
        self._context = BarBotContext()
        self._next_state_by_class: Optional[Type["BarBotState"]] = None
        self._is_transitioning: bool = False

        # Initialize state handlers
        BBSE = BarBotStateEnum
        self._state_classes_by_type: dict[BarBotStateEnum, Type["BarBotState"]] = {
            BBSE.CONNECTING: ConnectingState,
            BBSE.SEARCHING: SearchingState,
            BBSE.STARTUP: StartupState,
            BBSE.IDLE: IdleState,
            BBSE.MIXING: MixingState,
            BBSE.CRUSHING: CrushingState,
            BBSE.STRAW: StrawState,
            BBSE.CLEANING_CYCLE: CleaningCycleState,
            BBSE.SINGLE_INGREDIENT: SingleIngredientState,
        }

        # initial state
        self._state_instance: BarBotState = self._create_state(
            self._state_classes_by_type[BarBotStateEnum.CONNECTING]
        )

        self.on_state_changed: Callable[[BarBotStateEnum], None] = lambda state: None

    def _set_next_state_by_class(self, state: Type["BarBotState"]):
        """Set the next state to transition to.
        :param state: The state type to transition to"""
        logging.debug("Next state set to %s", state.__name__)
        self._next_state_by_class = state

    def _set_next_state_by_enum(self, state: BarBotStateEnum):
        """Set the next state to transition to.
        :param state: The state enum to transition to"""
        self._set_next_state_by_class(self._state_classes_by_type[state])

    def _create_state(self, state: Type["BarBotState"]) -> "BarBotState":
        """Create a new state instance of the given state type.
        :param state: The state type to create
        :return: The created state instance"""
        return state(self._config, self._ports, self._mainboard, self._context)

    # forward on_mixing_finished callback
    @property
    def on_mixing_finished(self) -> Callable[[Recipe], None]:
        """Callback when mixing is finished"""
        return self._context.on_mixing_finished

    @on_mixing_finished.setter
    def on_mixing_finished(self, callback: Callable[[Recipe], None]):
        """Set the callback when mixing is finished"""
        self._context.on_mixing_finished = callback

    # forward on_mixing_progress_changed callback
    @property
    def on_mixing_progress_changed(self) -> Callable[[int], None]:
        """Callback when mixing progress changes"""
        return self._context.on_mixing_progress_changed

    @on_mixing_progress_changed.setter
    def on_mixing_progress_changed(self, callback: Callable[[int], None]):
        """Set the callback when mixing progress changes"""
        self._context.on_mixing_progress_changed = callback

    # forward on_message_changed callback
    @property
    def on_message_changed(self) -> Callable[[UserMessageType], None]:
        """Callback when message changes"""
        return self._context.on_message_changed

    @on_message_changed.setter
    def on_message_changed(self, callback: Callable[[UserMessageType], None]):
        """Set the callback when message changes"""
        self._context.on_message_changed = callback

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
        """Check if the mixing process was aborted"""
        return self._context.should_abort_mixing

    @property
    def parties(self) -> PartyCollection:
        """Get the parties collection"""
        return self._context.parties

    @property
    def mixing_progress(self) -> int:
        """Get the current mixing progress as index of total steps"""
        return self._context.mixing_progress

    @property
    def current_mixing_options(self) -> MixingOptions:
        """Get the mixing options for what is being mixed"""
        return self._context.current_mixing_options

    @property
    def current_recipe_item(self) -> RecipeItem:
        """Get the recipe item that is being drafted"""
        return self._context.current_recipe_item

    def set_balance_calibration(self, offset, cal):
        """ "Save new offset and calibration for the internal balance to the config.
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
        self._context.idle_tasks.append(
            IdleTask(
                IdleTaskType.SET,
                None,
                "SetBalanceOffset",
                int(self._config.balance_offset),
            )
        )
        self._context.idle_tasks.append(
            IdleTask(
                IdleTaskType.SET,
                None,
                "SetBalanceCalibration",
                int(self._config.balance_calibration),
            )
        )

    def reconnect(self):
        """Reinitiate the connection procedure"""
        self._should_reconnect = True
        logging.debug("Reconnection requested")

    def _transition_to_state(self, state: Type["BarBotState"]):
        """Transition to the given state type immediately.
        :param state: The state type to transition to"""
        self._is_transitioning = True
        self._state_instance.on_exit()
        self._state_instance = self._create_state(state)
        self._state_instance.on_enter()
        self._is_transitioning = False

        # callback for state change with the new states enum representation
        if self.on_state_changed is not None:
            for state_enum, state_class in self._state_classes_by_type.items():
                if isinstance(self._state_instance, state_class):
                    self.on_state_changed(state_enum)
                    break

    def run(self):
        """main loop, runs the whole time"""
        logging.debug("State machine started")
        self._state_instance.on_enter()
        while not self._context.should_stop_statemachine:
            # call the appropriate state handler
            next_state = self._state_instance.update()
            if next_state is not None:
                self._set_next_state_by_class(next_state)
                logging.debug("State requested transition to %s", next_state.__name__)

            elif self._should_reconnect:
                # handle reconnection request
                self._should_reconnect = False
                self._set_next_state_by_class(ConnectingState)
                logging.debug("State requested reconnection to ConnectingState")

            if self._next_state_by_class is not None:
                logging.debug(
                    "Transitioning from %s to %s",
                    self._state_instance.__class__.__name__,
                    self._next_state_by_class.__name__,
                )
                self._transition_to_state(self._next_state_by_class)
                self._next_state_by_class = None

                logging.debug(
                    "Now in %s",
                    self._state_instance.__class__.__name__,
                )

        logging.debug("State machine stopped")
        self._mainboard.disconnect()

    def set_user_input(self, value: UserInputType):
        """Set the answer of the user to a message."""
        self._context.user_input = value
        logging.debug("User input: %s", value.name)

    def abort_mixing(self):
        """Abort an ongoing mixing process"""
        self._context.should_abort_mixing = True
        logging.warning("Mixing aborted")
        # send the abort command to the mainboard synchronously to directly stop mixing
        self._mainboard.send_abort()

    def abort(self):
        """Abort the barbot state machine"""
        self._context.should_stop_statemachine = True
        self._context.should_abort_mixing = True

    @property
    def current_message(self):
        """Message to the user, None if there isn't any"""
        return self._context.message

    @property
    def state(self) -> BarBotStateEnum:
        """Get the enum representation of the current state"""
        for state_enum, state_instance in self._state_classes_by_type.items():
            if isinstance(self._state_instance, state_instance):
                return state_enum
        return None

    @property
    def is_busy(self):
        """Whether the barbot is executing any commands"""
        return self.state != BarBotStateEnum.IDLE or self._is_transitioning

    @property
    def can_edit_database(self):
        """The database can be edited as long as the we are not using the esp32"""
        return self.state in [
            BarBotStateEnum.CONNECTING,
            BarBotStateEnum.IDLE,
        ]

    @property
    def connected_boards(self) -> List[BoardType]:
        """Get a list of the connected boards, it is read once on startup"""
        return self._context.connected_boards

    # start commands
    def start_mixing(self, options: MixingOptions):
        """Start mixing a recipe.
        :param options: Mixing options"""
        if self.is_busy:
            logging.warning("Cannot start mixing while busy")
            return
        self._context.current_mixing_options = options
        self._set_next_state_by_enum(BarBotStateEnum.MIXING)

    def start_single_ingredient(self, recipe_item: RecipeItem):
        """Start adding a single ingredient to your glas.
        :param recipe_item: The item to be added"""
        if self.is_busy:
            logging.warning("Cannot start single ingredient while busy")
            return
        self._context.current_recipe_item = recipe_item
        self._set_next_state_by_enum(BarBotStateEnum.SINGLE_INGREDIENT)

    def start_crushing(self):
        """Add ice to the glas"""
        if self.is_busy:
            logging.warning("Cannot start crushing while busy")
            return
        self._set_next_state_by_enum(BarBotStateEnum.CRUSHING)

    def start_cleaning(self, port: int):
        """Start cleaning a single pump.
        :param port: The port to clean"""
        if self.is_busy:
            logging.warning("Cannot start cleaning while busy")
            return
        self._context.pumps_to_clean = [port]

        self._set_next_state_by_enum(BarBotStateEnum.CLEANING_CYCLE)

    def start_cleaning_cycle(self, pumps_to_clean: List[int]):
        """Start a cleaning cycle.
        :param pumps_to_clean: List of ports to clean successively"""
        if self.is_busy:
            logging.warning("Cannot start cleaning cycle while busy")
            return
        self._context.pumps_to_clean = pumps_to_clean
        self._set_next_state_by_enum(BarBotStateEnum.CLEANING_CYCLE)

    def start_straw(self):
        """Add a straw to the glas"""
        if self.is_busy:
            logging.warning("Cannot start adding straw while busy")
            return
        self._set_next_state_by_enum(BarBotStateEnum.STRAW)

    def get_weight(self, callback: Callable[[float], None]):
        """Get the weight when the state machine is idle again.
        The callback is executed after execution.
        """

        def internal_callback(res: CommunicationResult):
            self._context.weight = (
                float(res.return_parameters[0])
                if res.was_successful and len(res.return_parameters) > 0
                else None
            )
            callback(self._context.weight)

        self._context.idle_tasks.append(
            IdleTask(IdleTaskType.GET, internal_callback, "GetWeight")
        )
