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
    def _get_known_devices() -> list[str]:
        """Get a list of known (paired or seen) devices from bluetoothctl"""
        try:
            result = subprocess.run(['bluetoothctl', 'devices'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.splitlines()
        except Exception as e:
            logger.debug("Failed to get known devices: %s", e)
        return []

    @staticmethod
    def _find_bar_bot_in_device_list(devices: list[str]) -> Optional[str]:
        """Search for a 'Bar Bot' in a list of bluetoothctl device strings"""
        for line in devices:
            if "Bar Bot" in line:
                parts = line.split(maxsplit=2)
                if len(parts) >= 2:
                    mac = parts[1]
                    name = parts[2] if len(parts) > 2 else "Unknown"
                    logger.debug("Bar Bot found: %s (%s)", name, mac)
                    return mac
        return None

    @staticmethod
    def find_bar_bot() -> str:
        """Find all bluetooth devices nearby that have 'Bar Bot' in their name.
        Uses bluetoothctl for discovery.
        :returns: The mac address of the first found device that matches the name.
        """
        logger.debug("Searching for Bar Bot in known devices...")
        
        # 1. Check known devices first
        mac = MainboardConnectionBluetooth._find_bar_bot_in_device_list(
            MainboardConnectionBluetooth._get_known_devices()
        )
        if mac:
            logger.info("Bar Bot found in known devices: %s", mac)
            return mac

        # 2. If not found, trigger a short scan
        logger.info("Bar Bot not found in known devices, starting scan...")
        try:
            # Start scan
            subprocess.run(['bluetoothctl', 'scan', 'on'], timeout=2, capture_output=True)
            # wait a bit for devices to be found
            time.sleep(5)
            # Stop scan
            subprocess.run(['bluetoothctl', 'scan', 'off'], timeout=2, capture_output=True)
            
            # Check devices again after scan
            mac = MainboardConnectionBluetooth._find_bar_bot_in_device_list(
                MainboardConnectionBluetooth._get_known_devices()
            )
            if mac:
                logger.info("Bar Bot found after scan: %s", mac)
                return mac
        except Exception as e:
            logger.debug("Bluetooth scan failed: %s", e)
            
        logger.warning("No Bar Bot found in bluetooth devices after scan")
        return None

    @staticmethod
    def pair_device(mac_address: str) -> bool:
        """Pair and trust a device using bluetoothctl"""
        logger.info("Attempting to pair and trust device: %s", mac_address)
        try:
            # Note: pairing might fail if already paired, but that's okay
            subprocess.run(['bluetoothctl', 'pair', mac_address], timeout=10, capture_output=True)
            subprocess.run(['bluetoothctl', 'trust', mac_address], timeout=5, capture_output=True)
            return True
        except Exception as e:
            logger.error("Failed to pair/trust device %s: %s", mac_address, e)
            return False

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
            
            # Try to connect
            try:
                self._conn.connect((mac_address, 1))
            except (socket.error, ConnectionError) as e:
                # If connection fails, it might be because the device is not paired/trusted
                logger.info("Initial connection failed, attempting to pair: %s", e)
                if MainboardConnectionBluetooth.pair_device(mac_address):
                    # try connecting again after pairing
                    self._conn.connect((mac_address, 1))
                else:
                    raise e

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
