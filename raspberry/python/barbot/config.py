"""Barbot configuration """
import os
import sys
import yaml
from .ingredients import Ingredient
from .ingredients import by_identifier as ingredient_by_identifier

data_directory = os.path.expanduser('~/.barbot/')
__version_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),"../../version.txt")
PORT_COUNT = 12

# pylint: disable=locally-disabled, too-many-instance-attributes
class BarBotConfig:
    """Configuration for the barbot"""
    def __init__(self):
        self._filename = os.path.join(data_directory, "config.yaml")

        self.mac_address = ""
        self.max_speed = 200
        self.max_accel = 300
        self.max_cocktail_size = 30
        self.admin_password = "0000"
        self.pump_power = 100
        self.pump_power_sirup = 255
        self.balance_offset = -119.1
        self.balance_calibration = -1040
        self.cleaning_time = 3000
        self.stirrer_connected = True
        self.stirring_time = 3000
        self.ice_crusher_connected = False
        self.ice_amount = 100
        self.straw_dispenser_connected = False
        self.sugar_dispenser_connected = False
        self.sugar_per_unit = 4

        self.ports = PortConfiguration()

        # all public attribute
        self._fields = [
            name for name in dir(self)
            if not name.startswith('_')
            # exclude complex types
            and name not in ["ports"]
        ]

        if not self.load():
            self.save()

    def save(self):
        """Save the current config values to the hard drive"""
        values = { field : getattr(self, field) for field in self._fields }
        with open(self._filename, 'w', encoding="utf-8") as configfile:
            yaml.dump(values, configfile)

    @property
    def is_mac_address_valid(self):
        """Get whether the mac address has the correct structure"""
        if self.mac_address is None:
            return False
        return len(self.mac_address.strip()) == 17

    def load(self):
        """Load the config from file"""
        # load config if it exists
        if not os.path.isfile(self._filename):
            return False
        with open(self._filename, 'r', encoding="utf-8") as configfile:
            data = yaml.safe_load(configfile)
        # update fields with values from
        for field in self._fields:
            if field in data.keys():
                setattr(sys.modules[__name__], field, data[field])
        return True

class PortConfiguration:
    """Manages the relation between the ports and the connected ingredients"""
    def __init__(self):
        self._filepath = os.path.join(data_directory, 'ports.yaml')
        self._list: dict[int, Ingredient]= {i: None for i in range(PORT_COUNT)}
        # if loading failed save the default value to file
        if not self.load():
            self.save()

    def ingredient_at_port(self, port:int):
        """Get the ingredient that is connected to a given port.
        :param port: The port"""
        if port not in self._list:
            return None
        return self._list[port]

    def port_of_ingredient(self, ingredient: Ingredient):
        """Get the port where to find the given ingredient
        :param ingredient: The ingredient to look for
        :return: The index of the port of the ingredient, None if it it was not found 
        """
        for port, list_ingredient in self._list.items():
            if list_ingredient == ingredient:
                return port
        return None


    def save(self):
        """ Save the current port configuration
        :return: True if saving was successfull, False otherwise
        """
        try:
            with open(self._filepath, 'w', encoding="utf-8") as outfile:
                data = {}
                for port, ingredient in self._list.items():
                    if ingredient is not None:
                        data[port] = ingredient.identifier
                    else:
                        data[port] = None
                yaml.dump(data, outfile, default_flow_style=False)
                return True
        except OSError:
            return False

    def load(self):
        """ Load the current port configuration
        :return: True if loading was successfull, False otherwise
        """
        try:
            with open(self._filepath, 'r', encoding="utf-8") as file:
                data:dict[int, str] = yaml.load(file, Loader=yaml.FullLoader)
                self._list = {}
                for port, identifier in data.items():
                    if identifier is None or identifier == "":
                        self._list[port] = None
                    else:
                        self._list[port] = ingredient_by_identifier(identifier)
                return True
        except OSError:
            return False

    @property
    def available_ingredients(self) -> set[Ingredient]:
        """Get a list of all connected ingredients"""
        return set(self._list.values())

def _get_version():
    """Get version from 'version.txt'"""
    try:
        with open(__version_file, "r", encoding="utf-8") as f:
            result = f.read()
    except OSError:
        result = None
    return result

version = _get_version()

def _create_if_not_exists(*path):
    """Make directory if it does not exist
    :param path: Path elements
    :returns: The directory"""
    folder = os.path.join("", *path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder
fixed_recipes_directory = _create_if_not_exists(data_directory, "fixed_recipes")
recipes_directory = _create_if_not_exists(data_directory, "recipes")
old_recipes_directory = _create_if_not_exists(data_directory, "old_recipes")
orders_directory = _create_if_not_exists(data_directory, "orders")
log_directory = _create_if_not_exists(data_directory, "log")
