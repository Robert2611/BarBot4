from enum import Enum, auto
from functools import total_ordering
from dataclasses import dataclass
from typing import List, NamedTuple, Optional

class ErrorType(Enum):
    """Errors that may occur during operations"""

    NONE = 0

    # generated error codes are above 100, so we don't interfere with the mainboard codes
    COMM_ERROR = 101
    SEND_FAILED = 102
    NO_RESULT_SENT = 103
    WRONG_ANSWER = 104
    NACK_RECEIVED = 105
    ANSWER_FOR_WRONG_COMMAND = 106

    # error codes of the mainboard (must match "shared.h")
    INGREDIENT_EMPTY = 33
    BALANCE_COMMUNICATION = 34
    I2C = 35
    STRAWS_EMPTY = 36
    GLAS_REMOVED = 37
    MIXING_FAILED = 38
    CRUSHER_COVER_OPEN = 39
    CRUSHER_TIMEOUT = 40
    COMMAND_ABORTED = 41
    SUGAR_DISPENSER_TIMEOUT = 42

def is_mainboard_error(error: ErrorType) -> bool:
    """Return True when an ErrorType represents a mainboard-reported error.

    Mainboard error codes are below COMM_ERROR (generated codes start at 101).
    Exclude ErrorType.NONE from being treated as a mainboard error.
    """
    return error is not None and error != ErrorType.NONE and error.value < ErrorType.COMM_ERROR.value

class BoardType(Enum):
    """board addresses must match 'shared.h'"""
    BALANCE = 0x01
    MIXER = 0x02
    STRAW = 0x03
    CRUSHER = 0x04
    SUGAR = 0x05

class LEDMode(Enum):
    """Must match LEDController.h in mainboard"""
    OFF = 0
    CONTINOUS = 1
    BLINK = 2
    RAINBOW = 3
    POSITION_WATERFALL = 4
    DRAFT_POSITION = 5

class PlatformLEDMode(Enum):
    """Must match BALANCE_LED_TYPE_<name> in 'shared.h'"""
    OFF = 0
    CONTINOUS = 1
    BLINK = 2
    ROTATE = 3
    PULSING = 4
    CHASE = 5

class ResponseTypes(Enum):
    """Types of messages that can be received from the mainboard"""
    ACK = auto()
    NAK = auto()
    DONE = auto()
    ERROR = auto()
    STATUS = auto()
    COMM_ERROR = auto()
    TIMEOUT = auto()

@total_ordering
@dataclass
class FirmwareVersion:
    """Firmware version handling"""
    major: int
    minor: int
    patch: int

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FirmwareVersion):
            return NotImplemented
        return self._to_int() == other._to_int()

    def __lt__(self, other: 'FirmwareVersion') -> bool:
        return self._to_int() < other._to_int()

    def _to_int(self) -> int:
        return self.major * 10000 + self.minor * 100 + self.patch

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

def decode_firmware_version(version: int) -> FirmwareVersion:
    """Decode a firmware version string comming from the mainboard"""
    version = int(version)
    major, version = divmod(version, 10000)
    minor, patch = divmod(version, 100)
    return FirmwareVersion(major=major, minor=minor, patch=patch)

class CommunicationResult():
    """Result of a command sent to the mainboard"""
    def __init__(self, error: ErrorType = ErrorType.NONE, return_parameters: List[str] = None):
        self.error: ErrorType = error
        self.return_parameters: List[str] = [] if return_parameters is None else return_parameters

    @property
    def was_successful(self):
        """Get whether an error code was set"""
        return self.error == ErrorType.NONE

class RawResponse(NamedTuple):
    """A raw message received from the mainboard"""
    message_type: ResponseTypes
    command: str
    parameters: List[str] = []
