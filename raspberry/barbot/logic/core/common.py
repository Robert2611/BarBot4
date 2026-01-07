from enum import Enum, auto
import subprocess
from typing import NamedTuple
from barbot.logic.recipes.recipe import Recipe


def run_command(cmd_str):
    """Run a linux command discarding all its output
    :param cmd_str: Command to be executed
    """
    subprocess.Popen(
        [cmd_str], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True
    )


class MixingOptions(NamedTuple):
    """Keeps the options for a mixing process"""

    recipe: Recipe
    add_straw: bool = False
    add_ice: bool = False


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


class BarBotStateEnum(Enum):
    """Enumeration of BarBot state classes"""

    CONNECTING = auto()
    SEARCHING = auto()
    STARTUP = auto()
    IDLE = auto()
    MIXING = auto()
    CRUSHING = auto()
    STRAW = auto()
    CLEANING_CYCLE = auto()
    CLEANING = auto()
    SINGLE_INGREDIENT = auto()
