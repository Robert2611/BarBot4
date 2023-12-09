"""This module handles the communication between the barbot and the mainboard"""
import time
from dataclasses import dataclass
from typing import NamedTuple
from enum import Enum, auto
import logging
import bluetooth

CONNECTION_TIMEOUT = 1
MAX_RETRIES = 3

class ErrorType(Enum):
    """Errors that may occur during operations"""

    NONE = 0

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

class BoardType(Enum):
    """board addresses must match 'shared.h'"""
    BALANCE = 0x01
    MIXER = 0x02
    STRAW = 0x03
    CRUSHER = 0x04
    SUGAR = 0x05

class ResponseTypes(Enum):
    """Types of messages that can be received from the mainboard"""
    ACK = auto()
    NAK = auto()
    DONE = auto()
    ERROR = auto()
    STATUS = auto()
    COMM_ERROR = auto()
    TIMEOUT = auto()


@dataclass
class CommunicationResult():
    """Result of a command sent to the mainboard"""
    error: ErrorType = ErrorType.NONE
    return_parameters: list[str] = []
    @property
    def was_successfull(self):
        """Get whether an error code was set"""
        return self.error == ErrorType.NONE

@dataclass
class RawResponse(NamedTuple):
    """A raw message received from the mainboard"""
    message_type: ResponseTypes
    command: str
    parameters: list[str] = []

class Mainboard:
    """Class representing the mainboard of the barbot, it is used to handle the communication"""
    def __init__(self):
        self._conn: bluetooth.BluetoothSocket = None
        self._error = None
        self._is_connected = False
        self._buffer: str = ""
        self._last_message_was_status_idle = False

    @property
    def is_connected(self):
        """Get wether the mainboard is connected via bluetooth"""
        return self._is_connected

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

    def connect(self, mac_address: str):
        """Connect to a bluetooth device with the given mac address.
        :param mac_address: The mac address of the device to connect to."""
        if self._conn is not None:
            self._conn.close()
        try:
            self._conn = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self._conn.connect((mac_address, 1))
            self._conn.settimeout(CONNECTION_TIMEOUT)
            # wait for Arduino to initialize
            time.sleep(1)
            self._read_line()
            self._is_connected = True
            logging.info("Connection successfull")
        except bluetooth.BluetoothError as e:
            logging.warning("Connection failed %s", e)
            return False
        return True

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
            result.error = message.parameters[0]
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
            result = self.send_command_and_read_response(command, parameters)

            # ACK was received for the command, so wait until it finished
            while result.was_successfull:
                message = self.read_message()
                if result.was_successfull and message.command != command:
                    result.error = ErrorType.ANSWER_FOR_WRONG_COMMAND
                if result.was_successfull and message.message_type == ResponseTypes.ERROR:
                    result.error = message.parameters[0]
                    result.return_parameters = message.parameters[1:]
                if result.was_successfull:
                    if message.message_type == ResponseTypes.DONE:
                        break
                    if message.message_type != ResponseTypes.STATUS:
                        result.error = ErrorType.WRONG_ANSWER
            if result.was_successfull:
                # at success, exit the loop
                break
            logging.warning("try_do, failed attempt: %s", result.error.name)
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
            result = self.send_command_and_read_response(command, parameters)
            if result.was_successfull:
                # at success, exit the loop
                break
            logging.warning("try_do, failed attempt: %s", result.error.name)
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
            result = self.send_command_and_read_response(command, parameters)
            if result.was_successfull:
                # at success, first check if we actually received a value
                if len(result.return_parameters) == 0:
                    result.error = ErrorType.NO_RESULT_SENT
                else:
                    break
            logging.warning("try_do, failed attempt: %s", result.error.name)
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
        if self._is_connected:
            cmd = command
            for parameter in parameters:
                cmd = cmd + " " + str(parameter)
            cmd = cmd + "\r"
            logging.debug(">%s", cmd)
            try:
                self._conn.send(cmd.encode())
                return True
            except bluetooth.BluetoothError:
                logging.exception("Send command failed")
        return False

    def disconnect(self):
        """Disconnect from the mainboard by closing the bluetooth connection"""
        if self._conn is not None:
            self._conn.close()

    def _read_line(self):
        """Read the last line that was received on the manboard connection.
        This command is blocking!
        :returns: The last line received. None, if the mainboard is not connected."""
        if self._conn is None:
            self._is_connected = False
            return None
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
        decoded_data = data.decode('utf-8')
        # only take the last part of the message
        lines = decoded_data.split('\n')
        if len(lines) > 2:
            logging.warning("read_line: More than one line in buffer!")
        return lines[-2]

    def read_message(self) -> RawResponse:
        """Read a response message from the mainboard.
        :returns: Response object containing information about the response or errors """
        if self._conn is None:
            self._is_connected = False
            return RawResponse(ResponseTypes.COMM_ERROR, "port not open")
        try:
            line = self._read_line()
            tokens = line.split()
            # Do not repeat "STATUS IDLE" over and over again
            if len(tokens) >= 2 and tokens[0] == "STATUS" and tokens[1] == "IDLE":
                if not self._last_message_was_status_idle:
                    logging.debug("<%s", line)
                    self._last_message_was_status_idle = True
            else:
                if self._last_message_was_status_idle:
                    self._last_message_was_status_idle = False
                logging.debug("<%s", line)

            # expected format: <Type> <Command> [Parameter1] [Parameter2] ...
            # find message type
            if len(tokens) > 0:
                for msg_type in ResponseTypes:
                    if msg_type.name != tokens[0]:
                        continue
                    if len(tokens) < 2:
                        return RawResponse(ResponseTypes.COMM_ERROR, "wrong format")
                    return RawResponse(tokens[0], tokens[1], tokens[2:])
            return RawResponse(ResponseTypes.COMM_ERROR, "unknown type")
        except bluetooth.btcommon.BluetoothError as e:
            self._is_connected = False
            logging.error("Read failed with BluetoothError:%s", e.args)
            return RawResponse(ResponseTypes.COMM_ERROR, e)
