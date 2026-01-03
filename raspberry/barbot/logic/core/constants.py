
from enum import Enum, auto


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
