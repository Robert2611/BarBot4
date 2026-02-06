import logging
import bluetooth
from .common import (
    ErrorType, CommunicationResult, RawResponse, ResponseTypes, 
    FirmwareVersion, decode_firmware_version, is_mainboard_error
)
from .connection import MainboardConnection

MAX_RETRIES = 3

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
        if response.was_successful and len(response.return_parameters) > 0:
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
        if result.was_successful and message.command != command:
            result.error = ErrorType.ANSWER_FOR_WRONG_COMMAND
        if result.was_successful and message.message_type == ResponseTypes.NAK:
            result.error = ErrorType.NACK_RECEIVED
        if result.was_successful and message.message_type != ResponseTypes.ACK:
            result.error = ErrorType.WRONG_ANSWER
        if result.was_successful and message.message_type == ResponseTypes.COMM_ERROR:
            result.error = ErrorType.COMM_ERROR
        if result.was_successful and message.message_type == ResponseTypes.ERROR:
            # first parameter is the error type
            try:
                result.error = ErrorType[message.parameters[0]]
            except (KeyError, IndexError):
                 result.error = ErrorType.WRONG_ANSWER
            result.return_parameters = message.parameters[1:]
        if result.was_successful and message.message_type == ResponseTypes.ACK:
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
            while result.was_successful:
                message = self.read_message()
                if result.was_successful and message.command != command:
                    result.error = ErrorType.ANSWER_FOR_WRONG_COMMAND
                if result.was_successful and message.message_type == ResponseTypes.ERROR:
                    try:
                        result.error = ErrorType(int(message.parameters[0]))
                    except (ValueError, IndexError):
                        result.error = ErrorType.WRONG_ANSWER
                    result.return_parameters = message.parameters[1:]
                if result.was_successful:
                    if message.message_type == ResponseTypes.DONE:
                        break
                    if message.message_type != ResponseTypes.STATUS:
                        result.error = ErrorType.WRONG_ANSWER
            if result.was_successful or is_mainboard_error(result.error):
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
        :returns: Whether the command executed successfuly
        """
        retries_left = MAX_RETRIES
        # make sure to always run the loop once
        while retries_left > 0:
            result = self.send_command_and_read_response(command, *parameters)
            if result.was_successful:
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
            if result.was_successful:
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
        if line == "" or line is None:
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
