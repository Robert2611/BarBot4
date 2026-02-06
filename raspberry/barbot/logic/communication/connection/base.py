import logging
from abc import ABC, abstractmethod
from typing import Optional
from ..common import RawResponse, ResponseTypes

# module logger
logger = logging.getLogger(__name__)

class MainboardConnection(ABC):
    """Abstract representation of a serial connection to the mainboard"""

    @staticmethod
    @abstractmethod
    def find_bar_bot() -> Optional[str]:
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
    def read_line(self) -> Optional[str]:
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
