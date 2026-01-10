"""State machine states for BarBot"""

__all__ = [
    "BarBotState",
    "ConnectingState",
    "SearchingState",
    "StartupState",
    "IdleState",
    "MixingState",
    "CrushingState",
    "StrawState",
    "CleaningCycleState",
    "CleaningState",
    "SingleIngredientState",
]


import time
import logging
from abc import ABC
from typing import List, Optional, Type

from barbot.logic.communication.communication import Mainboard
from barbot.logic.config.barbot_config import BarBotConfig
from barbot.logic.config.ingredients import IngredientType
from barbot.logic.config.port_config import PortConfiguration
from barbot.logic.recipes.recipe import RecipeItem
from barbot.logic.core.barbot_context import BarBotContext
from barbot.logic.core.common import UserInputType, UserMessageType

from ..communication import (
    BoardType,
    ResponseTypes,
    LEDMode,
    PlatformLEDMode,
    ErrorType as CommError,
)

MIN_IDLE_TIME_SEC = 0.1


class BarBotState(ABC):
    """Abstract base class for state handlers"""

    def __init__(
        self,
        config: BarBotConfig,
        ports: PortConfiguration,
        mainboard: Mainboard,
        context: BarBotContext,
    ):
        self._mainboard = mainboard
        self._config = config
        self._ports = ports
        self._context = context

    def update(self) -> Optional[Type["BarBotState"]]:
        """Execute the state's logic and return the next state or None to stay"""
        # make sure to not block too long
        time.sleep(0.1)

    def on_enter(self):
        """Actions to perform when entering the state"""

    def on_exit(self):
        """Actions to perform when exiting the state"""

    def _wait_for_user_input(self):
        """Reset the user input and wait until set_user_input() was called or mixing was aborted."""
        self._context.reset_user_input()
        logging.debug("Wait for user input")
        while (
            not self._context.should_abort_mixing
            and self._context.user_input == UserInputType.UNDEFINED
        ):
            self._mainboard.read_message()
        if self._context.should_abort_mixing:
            logging.warning("Waiting aborted")
            return False
        # else
        logging.debug("User answered: %s", self._context.user_input.name)
        return True

    def _has_glas(self):
        result = self._mainboard.get("HasGlas")
        return result.was_successful and result.return_parameters[0] == "1"

    def _wait_for_glass(self) -> bool:
        """Wait for glass to be placed"""
        # Check if glas is already present
        if self._has_glas():
            return True

        self._context.message = UserMessageType.PLACE_GLAS
        self._context.reset_user_input()
        self._mainboard.set("PlatformLED", PlatformLEDMode.BLINK.value)

        # Wait until glas is present or user input is given
        success = False
        while not self._context.should_abort_mixing:
            if self._has_glas():
                success = True
                break
            if self._context.user_input != UserInputType.UNDEFINED:
                break
            self._mainboard.read_message()

        # Clear message and reset user input
        self._context.reset_user_input()
        self._context.remove_message()

        return success

    def _draft_one(self, item: RecipeItem) -> bool:
        """Draft a single ingredient.
        :param item: The recipe item to be draft"""
        # user aborted
        if self._context.should_abort_mixing:
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
            logging.info(
                "Start adding %i g of '%s' at port %i",
                weight,
                item.ingredient.name,
                port,
            )
        while True:
            if item.ingredient.type == IngredientType.SUGAR:
                result = self._mainboard.do("Sugar", weight)
            else:
                if item.ingredient.type == IngredientType.SIRUP:
                    result = self._mainboard.set(
                        "SetPumpPower", self._config.pump_power_sirup
                    )
                else:
                    result = self._mainboard.set(
                        "SetPumpPower", self._config.pump_power
                    )
                if not result.was_successful:
                    self._context.message = UserMessageType.UNKNOWN_ERROR
                    self._wait_for_user_input()
                    return False
                result = self._mainboard.do("Draft", port, weight)
            # user aborted
            if self._context.should_abort_mixing:
                return False
            if result.was_successful is True:
                # drafting successful
                return True
            logging.error("Error while drafting: '%s'", result.error.name)
            if result.error == CommError.INGREDIENT_EMPTY:
                # ingredient is empty
                # safe how much is left to draft
                if len(result.return_parameters) > 0:
                    weight = int(result.return_parameters[0])
                else:
                    weight = 0
                    logging.warning("No remaining weight received")
                self._context.message = UserMessageType.INGREDIENT_EMPTY
                # wait for user input
                if not self._wait_for_user_input():
                    return False
                # remove the message
                self._context.remove_message()
                if self._context.user_input != UserInputType.YES:
                    return False
                # repeat the loop

            elif result.error == CommError.GLAS_REMOVED:
                logging.warning("Glas was removed while drafting")
                self._context.message = UserMessageType.GLAS_REMOVED_WHILE_DRAFTING
                self._wait_for_user_input()
                return False

            else:
                logging.warning("Unexpected error code")
                self._context.message = UserMessageType.UNKNOWN_ERROR
                self._wait_for_user_input()
                return False

    def _delay_and_keep_communicating(self, seconds):
        """Delay the state machine but keep checking the idle state to handle the communication"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            time_at_send = time.time()
            self._mainboard.get("IsIdle")
            self._mainboard.read_message()
            time_diff = time.time() - time_at_send
            if time_diff < MIN_IDLE_TIME_SEC:
                time.sleep(MIN_IDLE_TIME_SEC - time_diff)

    def _finish_mixing(self) -> Type["BarBotState"]:
        """Handle mixing completion"""
        self._context.message = UserMessageType.MIXING_DONE_REMOVE_GLAS
        self._mainboard.set("PlatformLED", PlatformLEDMode.BLINK.value)
        self._mainboard.set("SetLED", LEDMode.POSITION_WATERFALL.value)

        self._delay_and_keep_communicating(4)
        self._mainboard.set("PlatformLED", PlatformLEDMode.OFF.value)

        self._context.parties.current_party.add_order(
            self._context.current_mixing_options.recipe
        )
        self._context.remove_message()

        if self._context.on_mixing_finished is not None:
            self._context.on_mixing_finished(
                self._context.current_mixing_options.recipe
            )

        return IdleState

    def _add_ice_once(self, ice_to_add: int) -> Optional[int]:
        """Add ice using the crusher, return True if successful, False if aborted"""
        result = self._mainboard.do("Crush", ice_to_add)

        if result.was_successful:
            return 0

        return self._get_remaining_ice_amount(result)

    def _get_remaining_ice_amount(self, result) -> Optional[int]:
        """Handle errors from ice adding, return remaining ice to add or None if aborted"""
        ice_to_add = int(result.return_parameters[0]) if result.return_parameters else 0
        message_type = UserMessageType.UNKNOWN_ERROR
        requires_user_confirmation = False

        if result.error == CommError.INGREDIENT_EMPTY:
            message_type = UserMessageType.ICE_EMPTY
            requires_user_confirmation = True
        elif result.error == CommError.GLAS_REMOVED:
            message_type = UserMessageType.GLAS_REMOVED_WHILE_DRAFTING
        elif result.error == CommError.I2C:
            message_type = UserMessageType.I2C_ERROR
        elif result.error == CommError.CRUSHER_COVER_OPEN:
            message_type = UserMessageType.CRUSHER_COVER_OPEN
            requires_user_confirmation = True
        elif result.error == CommError.CRUSHER_TIMEOUT:
            message_type = UserMessageType.CRUSHER_TIMEOUT
            requires_user_confirmation = True

        self._context.message = message_type

        if not self._wait_for_user_input():
            return None

        self._context.remove_message()

        if requires_user_confirmation and self._context.user_input == UserInputType.YES:
            return ice_to_add

        return None

    def _add_straw(self) -> bool:
        """Try to add a straw, return True if successful"""
        # Try to dispense straw
        result = self._mainboard.do("Straw")
        return result.was_successful

    def _ask_for_straw_retry(self) -> bool:
        """Ask user if they want to retry adding a straw, return True if they do"""
        # Show message and wait for user input
        self._context.reset_user_input()
        self._context.message = UserMessageType.STRAWS_EMPTY
        if not self._wait_for_user_input():
            # user aborted
            return False

        # remove message
        self._context.remove_message()

        # check user input
        if self._context.user_input != UserInputType.UNDEFINED:
            return True

        return False


class ConnectingState(BarBotState):
    """Handle connecting to BarBot"""

    def update(self) -> Optional[Type["BarBotState"]]:
        """Connect to a barbot with the mac address defined in the config"""
        if not self._config.is_mac_address_valid:
            # no valid mac address, go back to searching state
            return SearchingState

        if self._mainboard.connect(self._config.mac_address):
            # connected successfully, startup
            return StartupState

        # connection failed, wait and try again
        time.sleep(1)
        return None


class SearchingState(BarBotState):
    """Handle searching for BarBot"""

    def update(self) -> Optional[Type["BarBotState"]]:
        """Search for a barbot in range, save its mac address and connect to it if one is found."""
        search_result = self._mainboard.find_bar_bot()
        if search_result:
            # found a barbot, save its mac address and go to connecting state
            self._config.mac_address = search_result
            self._config.save()
            return ConnectingState

        # no barbot found, wait and try again
        time.sleep(1)
        return None


class StartupState(BarBotState):
    """Handle BarBot startup"""

    def _parse_connected_boards(self, bit_values) -> List[BoardType]:
        """Parse bit values of the connected boards to list of enum"""
        boards = int(bit_values) if bit_values is not None else 0
        # convert bit field to list of enum values
        return [b for b in BoardType if boards & 1 << b.value]

    def _update_connected_boards_list(self):
        result = self._mainboard.get("GetConnectedBoards")
        if result.was_successful and len(result.return_parameters) > 0:
            self._context.connected_boards = self._parse_connected_boards(
                result.return_parameters[0]
            )

    def update(self) -> Optional[Type["BarBotState"]]:
        """Startup the barbot by setting values from the config to the mainboard"""
        if not self._mainboard.is_connected:
            # connection lost, go back to connecting state
            return ConnectingState

        # wait for a status message
        if self._mainboard.read_message().message_type != ResponseTypes.STATUS:
            # no status message yet, try again later
            time.sleep(1)
            return None

        # check all boards that should be connected and warn if they are not
        self._update_connected_boards_list()

        # Check each board and show appropriate messages
        board_checks = [
            (BoardType.BALANCE, UserMessageType.BOARD_NOT_CONNECTED_BALANCE),
            (
                BoardType.MIXER,
                UserMessageType.BOARD_NOT_CONNECTED_MIXER,
                self._config.stirrer_connected,
            ),
            (
                BoardType.STRAW,
                UserMessageType.BOARD_NOT_CONNECTED_STRAW,
                self._config.straw_dispenser_connected,
            ),
            (
                BoardType.CRUSHER,
                UserMessageType.BOARD_NOT_CONNECTED_CRUSHER,
                self._config.ice_crusher_connected,
            ),
            (
                BoardType.SUGAR,
                UserMessageType.BOARD_NOT_CONNECTED_SUGAR,
                self._config.sugar_dispenser_connected,
            ),
        ]

        for check in board_checks:
            board_type, message_type = check[0], check[1]
            should_check = check[2] if len(check) > 2 else True

            if should_check and board_type not in self._context.connected_boards:
                self._context.message = message_type
                if not self._wait_for_user_input():
                    return None

        self._context.remove_message()

        # Configure mainboard with config values
        self._mainboard.set("SetLED", LEDMode.RAINBOW.value)
        self._mainboard.set("SetSpeed", self._config.max_speed)
        self._mainboard.set("SetAccel", self._config.max_accel)
        self._mainboard.set("SetPumpPower", self._config.pump_power)
        self._mainboard.set(
            "SetBalanceCalibration", int(self._config.balance_calibration)
        )
        self._mainboard.set("SetBalanceOffset", int(self._config.balance_offset))

        return IdleState


class IdleState(BarBotState):
    """Handle idle state"""

    def on_enter(self):
        """Actions to perform when entering idle state"""
        self._context.abort_mixing = False
        self._context.remove_message()
        # reset current values
        self._context.current_mixing_options = None
        self._context.current_recipe_item = None
        self._mainboard.set("SetLED", LEDMode.RAINBOW.value)
        self._mainboard.set("PlatformLED", PlatformLEDMode.OFF.value)
        # move to where zero should be, if no motor steps were skipped
        self._mainboard.do("Move", 0)
        self._mainboard.do("Home")

        # reset abort mixing flag
        self._context.should_abort_mixing = False

    def update(self) -> Optional[Type["BarBotState"]]:
        """Perform idle task"""
        start_time = time.time()

        if self._mainboard.supports_is_idle_command:
            result = self._mainboard.get("IsIdle")
            if result.was_successful and len(result.return_parameters) == 1:
                if result.return_parameters[0] != "1":
                    logging.warning("'IsIdle' returned false")
            else:
                logging.warning("'IsIdle' command failed")
        else:
            self._mainboard.read_message()

        if not self._mainboard.is_connected:
            # connection lost, go back to connecting state
            return ConnectingState

        idle_task = self._context.get_next_idle_task()
        if idle_task is not None:
            idle_task.execute(self._mainboard)

        # ensure minimum idle time
        time_diff = time.time() - start_time
        if time_diff < MIN_IDLE_TIME_SEC:
            time.sleep(MIN_IDLE_TIME_SEC - time_diff)

        # stay in idle
        return None


class MixingState(BarBotState):
    """Handle mixing state"""

    def update(self) -> Optional[Type["BarBotState"]]:
        """Perform mixing process with the current recipe"""
        progress = 0
        self._context.mixing_progress = progress

        # Wait for glass
        if not self._wait_for_glass():
            # user aborted
            return IdleState

        self._mainboard.set("PlatformLED", PlatformLEDMode.ROTATE.value)
        self._delay_and_keep_communicating(1)
        self._mainboard.set("PlatformLED", PlatformLEDMode.CHASE.value)
        self._mainboard.set("SetLED", LEDMode.DRAFT_POSITION.value)
        self._context.reset_user_input()

        # Process each recipe item
        for item in self._context.current_mixing_options.recipe.items:
            if self._context.should_abort_mixing:
                break

            self._context.current_recipe_item = item
            if not self._draft_one(item):
                break

            progress += 1
            self._context.mixing_progress = progress

        # Add ice if requested
        if (
            self._context.current_mixing_options.add_ice
            and not self._context.should_abort_mixing
        ):
            ice_to_add = self._config.ice_amount
            while True:
                if self._context.should_abort_mixing:
                    break
                ice_to_add_result = self._add_ice_once(ice_to_add)
                if ice_to_add_result is None:
                    break  # user aborted
                if ice_to_add_result == 0:
                    break  # ice added completely
                ice_to_add = ice_to_add_result
                # try again
            progress += 1
            self._context.mixing_progress = progress

        # Move to start position
        self._mainboard.do("Move", 0)

        # Add straw if requested
        if (
            self._context.current_mixing_options.add_straw
            and not self._context.should_abort_mixing
        ):
            while True:
                was_successful = self._add_straw()
                if was_successful:
                    break
                if not self._ask_for_straw_retry():
                    break
                # else try again
            progress += 1
            self._context.mixing_progress = progress

        # Mixing complete
        return self._finish_mixing()


class CrushingState(BarBotState):
    """Handle ice crushing state"""

    def update(self) -> Optional[Type["BarBotState"]]:
        """Perform the crushing of ice"""
        ice_to_add = self._config.ice_amount

        while True:
            if self._context.should_abort_mixing:
                return IdleState
            ice_to_add_result = self._add_ice_once(ice_to_add)
            if ice_to_add_result is None:
                # user aborted
                return IdleState
            if ice_to_add_result == 0:
                # ice added completely
                return IdleState
            ice_to_add = ice_to_add_result
            # try again


class StrawState(BarBotState):
    """Handle straw dispensing state"""

    def update(self) -> Optional[Type["BarBotState"]]:
        """Try dispensing straw until it works or user aborts"""
        while True:
            was_successful = self._add_straw()
            if was_successful:
                return IdleState
            if not self._ask_for_straw_retry():
                return IdleState
            # try again


class CleaningCycleState(BarBotState):
    """Handle cleaning cycle state"""

    def update(self) -> Optional[Type["BarBotState"]]:
        """Perform cleaning cycle"""
        # ask user if the cleanig adapter is there
        self._context.message = UserMessageType.CLEANING_ADAPTER
        self._context.reset_user_input()

        if not self._wait_for_user_input():
            # user aborted
            return IdleState

        if self._context.user_input != UserInputType.YES:
            # user did not confirm cleaning adapter is present
            return IdleState

        self._context.remove_message()

        # perform cleaning for each pump that needs it
        for pump_index in self._context.pumps_to_clean:
            if self._context.should_abort_mixing:
                return IdleState
            self._mainboard.do("Clean", pump_index, self._config.cleaning_time)

        return IdleState


class CleaningState(BarBotState):
    """Handle cleaning cycle state"""

    def update(self) -> Optional[Type["BarBotState"]]:
        """Perform cleaning of the current recipe item"""
        item = self._context.current_recipe_item
        weight = int(item.weight)
        self._mainboard.do("Clean", item.port, weight)


class SingleIngredientState(BarBotState):
    """Handle single ingredient dispensing state"""

    def update(self) -> Optional[Type["BarBotState"]]:
        """Add a single ingredient"""
        if self._wait_for_glass():
            self._draft_one(self._context.current_recipe_item)
        return IdleState
