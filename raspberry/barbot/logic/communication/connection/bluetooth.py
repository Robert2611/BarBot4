import logging
import bluetooth
from typing import Optional
from .base import MainboardConnection
from ..common import RawResponse, ResponseTypes

# module logger
logger = logging.getLogger(__name__)

CONNECTION_TIMEOUT = 1

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
            logger.debug("Bluetooth discovery failed", exc_info=True)
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
        try:
            decoded_data: str = data.decode('utf-8', errors='replace')
        except UnicodeDecodeError as e:
            logger.debug("Decoding received bytes failed: %s", e, exc_info=True)
            decoded_data = ''
        # normalize and split into lines, drop empty trailing item from split
        lines = decoded_data.replace('\r', '').split('\n')
        # remove empty strings
        non_empty = [l for l in lines if l != '']
        if len(non_empty) == 0:
            logger.debug("_read_line_unsave: no non-empty lines received: %r", repr(decoded_data))
            return ''
        if len(non_empty) > 1:
            logger.warning("read_line: More than one line in buffer! Received: '%s'", repr(decoded_data))
        # return the last non-empty line
        return non_empty[-1]

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
            return RawResponse(ResponseTypes.COMM_ERROR, str(e))

        return line

    def send(self, line : str):
        self._conn.send(f"{line}\r".encode())

    def connect(self, identifier: str = ""):
        """Connect to a bluetooth device with the given mac address.
        :param identifier: The mac address of the device to connect to."""
        mac_address = identifier
        if self._conn is not None:
            self._conn.close()
        try:
            self._conn = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self._conn.connect((mac_address, 1))
            self._conn.settimeout(CONNECTION_TIMEOUT)
            # read one line to make sure the mainboard has started (best-effort)
            try:
                _ = self.read_line()
            except (bluetooth.BluetoothError, OSError) as e:
                logger.debug("Ignored exception while priming connection: %s", e, exc_info=True)
            self._is_connected = True
            logger.info("Connection successful")
        except bluetooth.BluetoothError as e:
            logger.warning("Connection failed %s", e)
            return False
        return True

    def disconnect(self):
        """Disconnect from the mainboard by closing the bluetooth connection"""
        if self._conn is not None:
            self._conn.close()

    @property
    def is_connected(self) -> bool:
        return self._is_connected
