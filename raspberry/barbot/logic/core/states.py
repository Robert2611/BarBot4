"""State machine states for BarBot"""
import time
import logging
from abc import ABC, abstractmethod

from barbot.logic.communication.communication import Mainboard
from barbot.logic.config.barbot_config import BarBotConfig
from barbot.logic.config.ingredients import IngredientType
from barbot.logic.config.port_config import PortConfiguration
from barbot.logic.core.constants import UserInputType, UserMessageType
from barbot.logic.recipes.recipe import RecipeItem

from ..communication import BoardType, ResponseTypes, LEDMode, PlatformLEDMode, ErrorType as CommError
from .barbot_interface import BarBotInterface

MIN_IDLE_TIME_SEC = 0.1

class BarBotState(ABC):
    """Abstract base class for state handlers"""

    def __init__(
        self,
        config: BarBotConfig,
        ports: PortConfiguration,
        mainboard: Mainboard,
        barbot_interface: BarBotInterface,
    ):
        self._mainboard = mainboard
        self._config = config
        self._ports = ports
        self._barbot_interface = barbot_interface

    @abstractmethod
    def execute(self) -> None:
        """Execute the state's logic"""

    def can_transition_to_idle(self) -> bool:
        """Check if this state can transition to idle"""
        return False

    def _wait_for_glass(self) -> bool:
        """Wait for glass to be placed"""
        # Check if glas is already present
        if self._barbot_interface.has_glas():
            return True

        self._barbot_interface.set_message(UserMessageType.PLACE_GLAS)
        self._barbot_interface.reset_user_input()
        self._mainboard.set("PlatformLED", PlatformLEDMode.BLINK.value)

        # Wait until glas is present or user input is given
        success = False
        while not self._barbot_interface.was_aborted:
            if self._barbot_interface.has_glas():
                success = True
                break
            if self._barbot_interface.user_input != UserInputType.UNDEFINED:
                break
            self._mainboard.read_message()

        # Clear message and reset user input
        self._barbot_interface.reset_user_input()
        self._barbot_interface.set_message(UserMessageType.NONE)

        return success

    def _draft_one(self, item: RecipeItem) -> bool:
        """Draft a single ingredient.
        :param item: The recipe item to be draft"""
        # user aborted
        if self._barbot_interface.was_aborted:
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
                if item.ingredient.type == IngredientType.SIRUP:
                    result = self._mainboard.set("SetPumpPower", self._config.pump_power_sirup)
                else:
                    result = self._mainboard.set("SetPumpPower", self._config.pump_power)
                if not result.was_successful:
                    self._barbot_interface.set_message(UserMessageType.UNKNOWN_ERROR)
                    self._barbot_interface.wait_foruser_input()
                    return False
                result = self._mainboard.do("Draft", port, weight)
            # user aborted
            if self._barbot_interface.was_aborted:
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
                self._barbot_interface.set_message(UserMessageType.INGREDIENT_EMPTY)
                # wait for user input
                if not self._barbot_interface.wait_foruser_input():
                    return False
                # remove the message
                self._barbot_interface.set_message(UserMessageType.NONE)
                if self._barbot_interface.user_input != UserInputType.YES:
                    return False
                # repeat the loop

            elif result.error == CommError.GLAS_REMOVED:
                logging.warning("Glas was removed while drafting")
                self._barbot_interface.set_message(UserMessageType.GLAS_REMOVED_WHILE_DRAFTING)
                self._barbot_interface.wait_foruser_input()
                return False

            else:
                logging.warning("Unexpected error code")
                self._barbot_interface.set_message(UserMessageType.UNKNOWN_ERROR)
                self._barbot_interface.wait_foruser_input()
                return False

    def _delay_and_keep_communicating(self, seconds):
        """Delay the state machine but keep checking the idle state to handle the communication"""
        start_time = time.time()
        while time.time() - start_time > seconds:
            time_at_send = time.time()
            self._mainboard.get("IsIdle")
            self._mainboard.read_message()
            time_diff = time.time() - time_at_send
            if time_diff < MIN_IDLE_TIME_SEC:
                time.sleep(MIN_IDLE_TIME_SEC - time_diff)

    def _finish_mixing(self):
        """Handle mixing completion"""
        self._barbot_interface.set_message(UserMessageType.MIXING_DONE_REMOVE_GLAS)
        self._mainboard.set("PlatformLED", PlatformLEDMode.BLINK.value)
        self._mainboard.set("SetLED", LEDMode.POSITION_WATERFALL.value)

        self._delay_and_keep_communicating(4)
        self._mainboard.set("PlatformLED", PlatformLEDMode.OFF.value)

        self._barbot_interface.parties.current_party.add_order(self._barbot_interface.current_mixing_options.recipe)
        self._barbot_interface.set_message(UserMessageType.NONE)

        if self._barbot_interface.on_mixing_finished is not None:
            self._barbot_interface.on_mixing_finished(self._barbot_interface.current_mixing_options.recipe)

        self._barbot_interface._go_to_idle()


class ConnectingState(BarBotState):
    """Handle connecting to BarBot"""

    def execute(self) -> None:
        """Connect to a barbot with the mac address defined in the config"""
        if not self._config.is_mac_address_valid:
            self._barbot_interface._set_state_from_handler(SearchingState)
        elif self._mainboard.connect(self._config.mac_address):
            self._barbot_interface._set_state_from_handler(StartupState)
        else:
            time.sleep(1)

    def can_transition_to_idle(self) -> bool:
        return True


class SearchingState(BarBotState):
    """Handle searching for BarBot"""

    def execute(self) -> None:
        """Search for a barbot in range, save its mac address and connect to it if one is found."""
        res = self._mainboard.find_bar_bot()
        if res:
            self._config.mac_address = res
            self._config.save()
            self._barbot_interface._set_state_from_handler(ConnectingState)
        else:
            time.sleep(1)

    def can_transition_to_idle(self) -> bool:
        return True


class StartupState(BarBotState):
    """Handle BarBot startup"""

    def execute(self) -> None:
        """Startup the barbot by setting values from the config to the mainboard"""
        if not self._mainboard.is_connected:
            self._barbot_interface._set_state_from_handler(ConnectingState)
            return

        # wait for a status message
        if self._mainboard.read_message().message_type != ResponseTypes.STATUS:
            return

        # check all boards that should be connected and warn if they are not
        self._barbot_interface._get_boards_connected()

        # Check each board and show appropriate messages
        board_checks = [
            (BoardType.BALANCE, UserMessageType.BOARD_NOT_CONNECTED_BALANCE),
            (BoardType.MIXER, UserMessageType.BOARD_NOT_CONNECTED_MIXER, self._config.stirrer_connected),
            (BoardType.STRAW, UserMessageType.BOARD_NOT_CONNECTED_STRAW, self._config.straw_dispenser_connected),
            (BoardType.CRUSHER, UserMessageType.BOARD_NOT_CONNECTED_CRUSHER, self._config.ice_crusher_connected),
            (BoardType.SUGAR, UserMessageType.BOARD_NOT_CONNECTED_SUGAR, self._config.sugar_dispenser_connected),
        ]

        for check in board_checks:
            board_type, message_type = check[0], check[1]
            should_check = check[2] if len(check) > 2 else True

            if should_check and board_type not in self._barbot_interface._connected_boards:
                self._barbot_interface.set_message(message_type)
                if not self._barbot_interface.wait_foruser_input():
                    return

        self._barbot_interface.set_message(UserMessageType.NONE)

        # Configure mainboard with config values
        self._mainboard.set("SetLED", LEDMode.RAINBOW.value)
        self._mainboard.set("SetSpeed", self._config.max_speed)
        self._mainboard.set("SetAccel", self._config.max_accel)
        self._mainboard.set("SetPumpPower", self._config.pump_power)
        self._mainboard.set("SetBalanceCalibration", int(self._config.balance_calibration))
        self._mainboard.set("SetBalanceOffset", int(self._config.balance_offset))

        self._barbot_interface._set_state_from_handler(IdleState)

    def can_transition_to_idle(self) -> bool:
        return True


class IdleState(BarBotState):
    """Handle idle state"""

    def execute(self) -> None:
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

        time_diff = time.time() - start_time
        if time_diff < MIN_IDLE_TIME_SEC:
            time.sleep(MIN_IDLE_TIME_SEC - time_diff)

        if not self._mainboard.is_connected:
            self._barbot_interface._set_state_from_handler(ConnectingState)

        if self._barbot_interface._idle_tasks:
            self._barbot_interface._idle_tasks[0].execute(self._mainboard)
            self._barbot_interface._idle_tasks.pop(0)

    def can_transition_to_idle(self) -> bool:
        return True


class MixingState(BarBotState):
    """Handle mixing state"""

    def execute(self) -> None:
        """Perform mixing process with the current recipe"""
        progress = 0
        self._barbot_interface.set_mixing_progress(progress)

        # Wait for glass
        if not self._wait_for_glass():
            return

        self._mainboard.set("PlatformLED", PlatformLEDMode.ROTATE.value)
        self._delay_and_keep_communicating(1)
        self._mainboard.set("PlatformLED", PlatformLEDMode.CHASE.value)
        self._mainboard.set("SetLED", LEDMode.DRAFT_POSITION.value)
        self._barbot_interface.reset_user_input()

        # Process each recipe item
        for item in self._barbot_interface.current_mixing_options.recipe.items:
            if self._barbot_interface.was_aborted:
                break

            self._barbot_interface.current_recipe_item = item
            if not self._draft_one(item):
                break

            progress += 1
            self._barbot_interface.set_mixing_progress(progress)

        # Add ice if requested
        if self._barbot_interface.current_mixing_options.add_ice and not self._barbot_interface.was_aborted:
            self._barbot_interface._set_state_from_handler(CrushingState)
            return

        # Move to start position
        self._mainboard.do("Move", 0)

        # Add straw if requested
        if self._barbot_interface.current_mixing_options.add_straw and not self._barbot_interface.was_aborted:
            self._barbot_interface._set_state_from_handler(StrawState)
            return

        # Mixing complete
        self._finish_mixing()


class CrushingState(BarBotState):
    """Handle ice crushing state"""

    def execute(self) -> None:
        """Perform the crushing of ice"""
        if self._barbot_interface.was_aborted:
            self._barbot_interface._go_to_idle()
            return

        ice_to_add = self._config.ice_amount

        while True:
            result = self._mainboard.do("Crush", ice_to_add)

            if self._barbot_interface.was_aborted:
                self._barbot_interface._go_to_idle()
                return

            if result.was_successful:
                self._continue_mixing()
                return

            if not self._handle_crushing_error(result, ice_to_add):
                self._barbot_interface._go_to_idle()
                return

    def _handle_crushing_error(self, result, ice_to_add) -> bool:
        """Handle crushing errors, return True to continue, False to abort"""
        if result.error == CommError.INGREDIENT_EMPTY:
            ice_to_add = int(result.return_parameters[0]) if result.return_parameters else 0
            self._barbot_interface.set_message(UserMessageType.ICE_EMPTY)
            if not self._barbot_interface.wait_foruser_input():
                return False
            self._barbot_interface.set_message(UserMessageType.NONE)
            return self._barbot_interface.user_input == UserInputType.YES

        elif result.error == CommError.GLAS_REMOVED:
            self._barbot_interface.set_message(UserMessageType.GLAS_REMOVED_WHILE_DRAFTING)
            self._barbot_interface.wait_foruser_input()
            return False

        elif result.error == CommError.I2C:
            self._barbot_interface.set_message(UserMessageType.I2C_ERROR)
            self._barbot_interface.wait_foruser_input()
            return False

        elif result.error == CommError.CRUSHER_COVER_OPEN:
            self._barbot_interface.set_message(UserMessageType.CRUSHER_COVER_OPEN)
            if not self._barbot_interface.wait_foruser_input():
                return False
            self._barbot_interface.set_message(UserMessageType.NONE)
            return self._barbot_interface.user_input == UserInputType.YES

        elif result.error == CommError.CRUSHER_TIMEOUT:
            self._barbot_interface.set_message(UserMessageType.CRUSHER_TIMEOUT)
            if not self._barbot_interface.wait_foruser_input():
                return False
            self._barbot_interface.set_message(UserMessageType.NONE)
            return self._barbot_interface.user_input == UserInputType.YES

        else:
            self._barbot_interface.set_message(UserMessageType.UNKNOWN_ERROR)
            self._barbot_interface.wait_foruser_input()
            return False

    def _continue_mixing(self):
        """Continue with the next step in mixing"""
        self._barbot_interface.set_mixing_progress(self._barbot_interface.mixing_progress + 1)

        # Move to start and add straw if requested
        self._mainboard.do("Move", 0)
        if self._barbot_interface.current_mixing_options.add_straw and not self._barbot_interface.was_aborted:
            self._barbot_interface._set_state_from_handler(StrawState)
        else:
            self._finish_mixing()




class StrawState(BarBotState):
    """Handle straw dispensing state"""

    def execute(self) -> None:
        """Try dispensing straw until it works or user aborts"""
        while True:
            result = self._mainboard.do("Straw")
            if result.was_successful:
                self._finish_mixing()
                return

            self._barbot_interface.reset_user_input()
            self._barbot_interface.set_message(UserMessageType.STRAWS_EMPTY)

            if not self._barbot_interface.wait_foruser_input():
                self._barbot_interface._go_to_idle()
                return

            self._barbot_interface.set_message(UserMessageType.NONE)
            if self._barbot_interface.user_input != UserInputType.UNDEFINED:
                self._finish_mixing()
                return

class CleaningCycleState(BarBotState):
    """Handle cleaning cycle state"""

    def execute(self) -> None:
        """Perform cleaning cycle"""
        self._barbot_interface.set_message(UserMessageType.CLEANING_ADAPTER)
        self._barbot_interface.reset_user_input()

        if not self._barbot_interface.wait_foruser_input():
            self._barbot_interface._go_to_idle()
            return

        if self._barbot_interface.user_input != UserInputType.YES:
            self._barbot_interface._go_to_idle()
            return

        self._barbot_interface.set_message(UserMessageType.NONE)

        for pump_index in self._barbot_interface._pumps_to_clean:
            if self._barbot_interface.was_aborted:
                self._barbot_interface._go_to_idle()
                return
            self._mainboard.do("Clean", pump_index, self._config.cleaning_time)

        self._barbot_interface._go_to_idle()


class SingleIngredientState(BarBotState):
    """Handle single ingredient dispensing state"""

    def execute(self) -> None:
        """Add a single ingredient"""
        if not self._wait_for_glass():
            self._barbot_interface._go_to_idle()
            return

        self._draft_one(self._barbot_interface.current_recipe_item)
        self._barbot_interface._go_to_idle()