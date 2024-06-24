"""Mockups for testing and demo"""
import time
from barbot.communication import MainboardConnection

class MaiboardConnectionMockup(MainboardConnection):
    """Mockup class for MainboardConnection.
    It executes delays instead of actual communication.
    The result of a GET command can be set.
    """
    def __init__(self):
        self._last_line_sent = None
        self._current_command = None
        self._last_received_time = None
        self._current_command_type = None
        self._command_history = []
        self._was_ack_sent = False
        self._getter_results = {}
        self.duration_DO = 0.5
        self.duration_SET = 0.1
        self.duration_GET = 0.1
        self.time_since_last_command_sent = 0
        self.commands = {
            "Delay": ["DO", 1],
            "Draft": ["DO", 2],
            "Crush": ["DO", 1],
            "Sugar": ["DO", 1],
            "Mix": ["DO", 1],
            "Clean": ["DO", 2],
            "Straw": ["DO", 0],
            "Home": ["DO", 0],
            "Move": ["DO", 1],

            "PlatformLED": ["SET", 1],
            "SetSpeed": ["SET", 1],
            "SetAccel": ["SET", 1],
            "SetBalanceCalibration": ["SET", 1],
            "SetBalanceOffset": ["SET", 1],
            "SetPumpPower": ["SET", 1],
            "SetLED": ["SET", 1],

            "IsIdle": ["GET", 0],
            "GetFirmwareVersion": ["GET", 0],
            "GetWeight": ["GET", 0],
            "HasGlas": ["GET", 0],
            "GetConnectedBoards": ["GET", 0],
        }

    @property
    def command_history(self):
        """List of commands that have been sent"""
        return self._command_history

    def clear_command_history(self):
        """Clear the list of commands that have been sent"""
        self._command_history = []

    def set_result_for_getter(self, getter_command: str, value:int):
        """Set the result that the next call of a get command should return"""
        self._getter_results[getter_command] = int(value)


    @staticmethod
    def find_bar_bot() -> str:
        """Returns an identifier that can be used by the connect() method"""
        return "mainboard_mockup"

    def connect(self, identifier: str = "") -> bool:
        """Connect, return true if successfull"""
        return self.is_connected

    def disconnect(self):
        pass

    def read_line(self) -> str:
        if self._current_command is None:
            return "STATUS IDLE"
        if self._last_received_time is not None:
            self.time_since_last_command_sent = time.time() - self._last_received_time
        if self._current_command_type == "DO":
            return self._handle_DO_command()
        elif self._current_command_type == "GET":
            return self._handle_GET_command()
        else:
            return self._handle_SET_command()

    def _handle_DO_command(self):
        time_left_for_command = self.duration_DO - self.time_since_last_command_sent
        time_left_for_command = max(0, time_left_for_command)
        if not self._was_ack_sent:
            self._was_ack_sent = True
            return f"ACK {self._current_command}"
        if time_left_for_command > 0.3:
            time.sleep(0.3)
            return f"STATUS {self._current_command}"
        time.sleep(time_left_for_command)
        result = f"DONE {self._current_command}"
        self._current_command = None
        return result

    def _handle_GET_command(self):
        if self.time_since_last_command_sent < self.duration_GET:
            time.sleep(self.duration_GET - self.time_since_last_command_sent)
        result = self._getter_results[self._current_command] \
                    if self._current_command in self._getter_results \
                    else 0
        result = f"ACK {self._current_command} {result}"
        self._current_command = None
        return result

    def _handle_SET_command(self):
        if self.time_since_last_command_sent < self.duration_SET:
            time.sleep(self.duration_SET - self.time_since_last_command_sent)
        result = f"ACK {self._current_command}"
        self._current_command = None
        return result

    @property
    def is_connected(self) -> bool:
        return True

    def send(self, line:str):
        self._last_line_sent = line
        line_items = line.split(" ")
        self._current_command = line_items[0]
        self._last_received_time = time.time()
        assert self._current_command in self.commands
        self._command_history.append(self._current_command)
        self._current_command_type, expected_parameter_count = self.commands[self._current_command]
        assert len(line_items) == expected_parameter_count + 1
        self._was_ack_sent = False
