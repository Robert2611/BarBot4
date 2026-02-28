import logging
import socket
import subprocess
import time
from typing import Optional
from .base import MainboardConnection
from ..common import RawResponse, ResponseTypes

# module logger
logger = logging.getLogger(__name__)

CONNECTION_TIMEOUT = 1

class MainboardConnectionBluetooth(MainboardConnection):
    """Implementation of the MaimboardConnection using native bluetooth sockets"""
    def __init__(self):
        self._conn : socket.socket = None
        self._is_connected = False

    @staticmethod
    def find_bar_bot() -> str:
        """Find all bluetooth devices nearby that have 'Bar Bot' in their name.
        Uses bluetoothctl for discovery to avoid the legacy PyBluez dependency.
        :returns: The mac address of the first found device that matches the name.
        """
        logger.debug("Searching for Bar Bot...")
        try:
            # Run bluetoothctl devices to get a list of paired/seen devices
            result = subprocess.run(['bluetoothctl', 'devices'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    logger.debug("Bluetooth device: %s", line)
                    # Format: Device XX:XX:XX:XX:XX:XX Name
                    if "Bar Bot" in line:
                        parts = line.split(maxsplit=2)
                        if len(parts) >= 2:
                            mac = parts[1]
                            name = parts[2] if len(parts) > 2 else "Unknown"
                            logger.info("Bar Bot found: %s (%s)", name, mac)
                            return mac
            else:
                logger.warning("bluetoothctl devices returned with code %s", result.returncode)
        except Exception as e:
            logger.debug("Bluetooth discovery failed using bluetoothctl: %s", e)
        logger.warning("No Bar Bot found in bluetooth devices")
        return None

    def _read_line_unsave(self):
        data = b''
        # make sure to read everything there is
        while True:
            # read up to 1024 bytes
            received = self._conn.recv(1024)
            if not received:
                raise ConnectionError("Connection closed by peer")
            data += received
            # we received a new line character
            if data[-1:] == b'\n':
                break
            # arbitrary limit to prevent infinite loops on corrupted data
            if len(data) > 4096:
                logger.warning("read_line: Buffer overflow, more than 4096 bytes read!")
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
        except (socket.error, ConnectionError) as e:
            self._is_connected = False
            logger.error("Read failed with error: %s", e)
            return None

        return line

    def send(self, line : str):
        if self._conn:
            self._conn.sendall(f"{line}\r\n".encode())

    def connect(self, identifier: str = ""):
        """Connect to a bluetooth device with the given mac address.
        :param identifier: The mac address of the device to connect to."""
        mac_address = identifier
        if self._conn is not None:
            self._conn.close()
        try:
            # Create a native Bluetooth RFCOMM socket
            self._conn = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self._conn.settimeout(5) # Set a generous timeout for connection
            self._conn.connect((mac_address, 1))
            self._conn.settimeout(CONNECTION_TIMEOUT)
            
            # read one line to make sure the mainboard has started (best-effort)
            try:
                _ = self.read_line()
            except Exception as e:
                logger.debug("Ignored exception while priming connection: %s", e)
            
            self._is_connected = True
            logger.info("Connection successful to %s", mac_address)
        except (socket.error, ConnectionError) as e:
            logger.warning("Connection failed to %s: %s", mac_address, e)
            self._is_connected = False
            self._conn = None
            return False
        return True

    def disconnect(self):
        """Disconnect from the mainboard by closing the bluetooth connection"""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected
