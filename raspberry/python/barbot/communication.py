"""This module handles the communication between the barbot and the mainboard"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import NamedTuple, List
from enum import Enum, auto
from functools import total_ordering
import logging
import bluetooth

CONNECTION_TIMEOUT = 1
MAX_RETRIES = 3

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

def is_mainboard_error(error:ErrorType):
    return error.value < ErrorType.COMM_ERROR.value

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

    def __eq__(self, other):
        return self._to_int() == other._to_int()

    def __ge__(self, other):
        return self._to_int() > other._to_int()

    def _to_int(self):
        return self.major * 10000 + self.minor * 100 + self.patch

    def __str__(self):
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
    def was_successfull(self):
        """Get whether an error code was set"""
        return self.error == ErrorType.NONE

class RawResponse(NamedTuple):
    """A raw message received from the mainboard"""
    message_type: ResponseTypes
    command: str
    parameters: List[str] = []

class MainboardConnection(ABC):
    """Abstract representation of a serial connection to the mainboard"""

    @staticmethod
    @abstractmethod
    def find_bar_bot() -> str:
        """Returns an identifier that can be used by the connect() method"""
        return ""

    @abstractmethod
    def connect(self, identifier: str = "") -> bool:
        """Establish connection to the mainboard"""
        return self.is_connected

    @abstractmethod
    def disconnect(self):
        """Close the mainboard connection"""

    @abstractmethod
    def read_line(self) -> str:
        """Read a single line from the mainboard"""
        return ""

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the mainboard connected and ready to communicate"""
        return False

    @abstractmethod
    def send(self, line:str):
        """Send a line to the minboard"""

class MainboardConnectionBluetooth(MainboardConnection):
    """Implementation of the MaimboardConnection using bluetooth"""
    def __init__(self):
        self._conn : bluetooth.BluetoothSocket = None
        self._is_connected = False

    @staticmethod
    def find_bar_bot() -> str:
        """Find all bluetooth devices nearby that have 'Bar Bot' in their name.
        :returns: The mac address of the first found device that matches the name.
        """
        try:
            nearby_devices = bluetooth.discover_devices(lookup_names=True)
            for x in nearby_devices:
                if "Bar Bot" in x[1]:
                    # return address of first device with "Bar Bot" in its name
                    return x[0]
        except bluetooth.BluetoothError:
            pass
        return None

    def _read_line_unsave(self):
        data = b''
        # make sure to read everything there is
        while True:
            # read up to 1024 bytes
            received = self._conn.recv(1024)
            data += received
            # we actually received 1024 bytes
            if len(received) == 1024:
                logging.warning("read_line: More than 1024 bytes read!")
                # make shure to all bytes in the pipeline
                continue
            # we received a new line character
            if data[-1:] == b'\n':
                break
        decoded_data:str = data.decode('utf-8')
        # only take the last part of the message
        lines = decoded_data.replace('\r','').split('\n')
        if len(lines) > 2:
            logging.warning("read_line: More than one line in buffer! Received: '%s'", repr(decoded_data))
        return lines[-2]

    def read_line(self) -> str:
        """Read the last line that was received on the manboard connection.
        This command is blocking!
        :returns: The last line received. None, if the mainboard is not connected."""
        if self._conn is None:
            self._is_connected = False
            return None
        try:
            line = self._read_line_unsave()
        except bluetooth.btcommon.BluetoothError as e:
            self._is_connected = False
            logging.error("Read failed with BluetoothError:%s", e.args)
            return RawResponse(ResponseTypes.COMM_ERROR, e)

        return line

    def send(self, line : str):
        self._conn.send(f"{line}\r".encode())

    def connect(self, identifier: str = ""):
        """Connect to a bluetooth device with the given mac address.
        :param mac_address: The mac address of the device to connect to."""
        mac_address = identifier
        if self._conn is not None:
            self._conn.close()
        try:
            self._conn = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self._conn.connect((mac_address, 1))
            self._conn.settimeout(CONNECTION_TIMEOUT)
            # read one line to make sure the mainboard has started
            self.read_line()
            self._is_connected = True
            logging.info("Connection successfull")
        except bluetooth.BluetoothError as e:
            logging.warning("Connection failed %s", e)
            return False
        return True

    def disconnect(self):
        """Disconnect from the mainboard by closing the bluetooth connection"""
        if self._conn is not None:
            self._conn.close()

    @property
    def is_connected(self) -> bool:
        return self._is_connected

class Mainboard:
    """Class representing the mainboard of the barbot, it is used to handle the communication"""
    def __init__(self, connection: MainboardConnection):
        self._connection = connection
        self._error = None
        self._buffer: str = ""
        self._last_message_was_status_idle = False
        self._firmware_version: FirmwareVersion = FirmwareVersion(0, 0, 0)

    @property
    def is_connected(self):
        """Get wether the mainboard is connected and ready"""
        return self._connection.is_connected

    @property
    def firmware_version(self):
        """Get the firmware version, only valid after connecting!"""
        return self._firmware_version

    @property
    def supports_is_idle_command(self):
        """Get whether the mainboard supports the command 'IsIdle'"""
        return self.firmware_version is not None \
                and self.firmware_version >= FirmwareVersion(4, 4, 0)

    def read_non_status_message(self) -> RawResponse:
        """Read a response message.
        If a status message is read instead, discard it and continue listening"""
        message = self.read_message()
        # if a status message is recived, just ignore it, but only once!
        # it might have been in the buffer already
        if message.message_type == ResponseTypes.STATUS:
            logging.info("Status message discarded")
            message = self.read_message()
        return message

    def connect(self, identifier: str):
        """Connect to the mainboard"""
        self._connection.connect(identifier)
        if not self._connection.is_connected:
            return False
        # read firmware version
        response = self.get("GetFirmwareVersion")
        if response.was_successfull and len(response.return_parameters) > 0:
            self._firmware_version = decode_firmware_version(int(response.return_parameters[0]))
            logging.info("Firmware version is: %s", self._firmware_version)
        else:
            self._firmware_version = FirmwareVersion(0, 0, 0)
            logging.warning("Could not read firmware version, probably legacy")
        return self._connection.is_connected

    def disconnect(self):
        """Disconnect from the mainboard"""
        self._connection.disconnect()

    def find_bar_bot(self):
        """Find available mainboards, get the first one """
        return self._connection.find_bar_bot()

    def send_command_and_read_response(self, command, *parameters:str) -> CommunicationResult:
        """Send a command and read back its response from the mainboard.
        
        :param command: Command name
        :param parameters: Parameter for the controller command
        :returns: CommunicationResult
        """
        if not self.send_command(command, *parameters):
            return CommunicationResult(error=ErrorType.SEND_FAILED)
        # wait for the response
        message = self.read_non_status_message()

        result = CommunicationResult()
        # check if the result is for the command we sent and it is an ACK
        if result.was_successfull and message.command != command:
            result.error = ErrorType.ANSWER_FOR_WRONG_COMMAND
        if result.was_successfull and message.message_type == ResponseTypes.NAK:
            result.error = ErrorType.NACK_RECEIVED
        if result.was_successfull and message.message_type != ResponseTypes.ACK:
            result.error = ErrorType.WRONG_ANSWER
        if result.was_successfull and message.message_type == ResponseTypes.COMM_ERROR:
            result.error = ErrorType.COMM_ERROR
        if result.was_successfull and message.message_type == ResponseTypes.ERROR:
            # first parameter is the error type
            result.error = ErrorType[message.parameters[0]]
            result.return_parameters = message.parameters[1:]
        if result.was_successfull and message.message_type == ResponseTypes.ACK:
            # an ack can include more info
            result.return_parameters = message.parameters
        return result

    def do(self, command, *parameters:str) -> CommunicationResult:
        """
        Send a DO command to the controller and wait for it to finish
        
        :param command: Command name
        :param parameters: Parameter for the controller command
        :returns: CommunicationResult
        """
        retries_left = MAX_RETRIES
        # make sure to always run the loop once
        while retries_left > 0:
            result = self.send_command_and_read_response(command, *parameters)

            # ACK was received for the command, so wait until it finished
            while result.was_successfull:
                message = self.read_message()
                if result.was_successfull and message.command != command:
                    result.error = ErrorType.ANSWER_FOR_WRONG_COMMAND
                if result.was_successfull and message.message_type == ResponseTypes.ERROR:
                    result.error = ErrorType(int(message.parameters[0]))
                    result.return_parameters = message.parameters[1:]
                if result.was_successfull:
                    if message.message_type == ResponseTypes.DONE:
                        break
                    if message.message_type != ResponseTypes.STATUS:
                        result.error = ErrorType.WRONG_ANSWER
            if result.was_successfull or is_mainboard_error(result.error):
                # at success, exit the loop
                break
            logging.warning("try_do with '%s', failed attempt: %s", command, result.error.name)
            retries_left -= 1

        # at success or when no retries are left
        # if it failed, the last error is still in the result variable
        return result

    def set(self, command, *parameters:str) -> CommunicationResult:
        """
        Send a SET command to the controller
        
        :param command: Command name
        :param parameters: Parameter for the controller command
        :returns: Whether the command executed successfully
        """
        retries_left = MAX_RETRIES
        # make sure to always run the loop once
        while retries_left > 0:
            result = self.send_command_and_read_response(command, *parameters)
            if result.was_successfull:
                # at success, exit the loop
                break
            logging.warning("try_set with '%s', failed attempt: %s", command, result.error.name)
            retries_left -= 1

        # at success or when no retries are left
        # if it failed, the last error is still in the result variable
        return result

    def get(self, command, *parameters:str) -> CommunicationResult:
        """
        Send a GET command to the controller
        
        :param command: Command name
        :param parameters: Parameter for the controller command
        :returns: CommunicationResult containing the returned value on success
        """
        retries_left = MAX_RETRIES
        # make sure to always run the loop once
        while retries_left > 0:
            result = self.send_command_and_read_response(command, *parameters)
            if result.was_successfull:
                # at success, first check if we actually received a value
                if len(result.return_parameters) == 0:
                    result.error = ErrorType.NO_RESULT_SENT
                else:
                    break
            logging.warning("try_get with '%s', failed attempt: %s", command, result.error.name)
            retries_left -= 1

        # at success or when no retries are left
        # if it failed, the last error is still in the result variable
        return result

    def send_abort(self):
        """Send a command to abort the currently running command"""
        self.send_command("ABORT")

    def send_command(self, command, *parameters:str):
        """Send a command to the mainboard.
        This will not wait for any response."""
        if self.is_connected:
            line = command
            for p in parameters:
                line += " " + str(p)
            if command != "IsIdle":
                logging.debug("-> '%s'", line)
            try:
                self._connection.send(line)
                return True
            except bluetooth.BluetoothError:
                logging.exception("Send command failed")
        return False

    def read_message(self) -> RawResponse:
        """Read a response message from the mainboard.
        :returns: Response object containing information about the response or errors """
        if not self.is_connected:
            return RawResponse(ResponseTypes.COMM_ERROR, "port not open")
        line = self._connection.read_line()
        if line == "":
            return RawResponse(ResponseTypes.COMM_ERROR, "empty line read")
        tokens = line.split()
        # Do not repeat status messages over and over again
        is_idle_message = self._is_status_message(tokens) or self._is_is_idle_message(tokens)
        do_logging = not is_idle_message or not self._last_message_was_status_idle
        if do_logging:
            logging.debug("<- '%s'", line)
        self._last_message_was_status_idle = is_idle_message

        # expected format: <Type> <Command> [Parameter1] [Parameter2] ...
        # find message type
        if len(tokens) > 0:
            for msg_type in ResponseTypes:
                if msg_type.name != tokens[0]:
                    continue
                if len(tokens) < 2:
                    return RawResponse(ResponseTypes.COMM_ERROR, "wrong format")
                return RawResponse(ResponseTypes[tokens[0]], tokens[1], tokens[2:])
        return RawResponse(ResponseTypes.COMM_ERROR, "unknown type")

    def _is_status_message(self, tokens):
        return tokens == ["STATUS", "IDLE"]

    def _is_is_idle_message(self, tokens):
        return tokens == ["ACK", "IsIdle", "1"]
