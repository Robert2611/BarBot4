"""Barbot configuration """
from io import TextIOWrapper
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Union

import yaml

data_directory = os.path.expanduser('~/.barbot/')
__version_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),"../../version.txt")
PORT_COUNT = 12


# density relative to that of water
DENSITY_WATER = 1
DENSITY_JUICE = DENSITY_WATER
DENSITY_SIRUP = DENSITY_WATER
DENSITY_SPIRIT = DENSITY_WATER

class IngredientType(Enum):
    """Type of the ingredient"""
    SPIRIT = "spirit"
    JUICE = "juice"
    SIRUP = "sirup"
    OTHER = "other"
    STIRR = "stirr"
    SUGAR = "sugar"

@dataclass
class Ingredient():
    """Ingredient that can be added to a recipe"""
    identifier:str
    name: str
    type: IngredientType
    color: int

    def alcoholic(self) -> bool:
        """Returns whether the ingredient contains alcohol"""
        return self.type == IngredientType.SPIRIT

    @property
    def density(self):
        """Get the density of this ingredient"""
        if self.type == IngredientType.JUICE:
            return DENSITY_JUICE
        elif self.type == IngredientType.SIRUP:
            return DENSITY_SIRUP
        elif self.type == IngredientType.SPIRIT:
            return DENSITY_SPIRIT
        else:
            # no info, so just assume water
            return DENSITY_WATER


Stir = Ingredient('ruehren',        'Rühren',               IngredientType.STIRR,   0xDDE3E1D3   )
Sugar = Ingredient('zucker',         'Zucker',               IngredientType.SUGAR,   0x55FFFFFF   )

_ingredients = [
    Ingredient('rum weiss',         'Weißer Rum',           IngredientType.SPIRIT,  0x55FFFFFF    ),
    Ingredient('rum braun',         'Brauner Rum',          IngredientType.SPIRIT,  0x99D16615    ),
    Ingredient('vodka',             'Vodka',                IngredientType.SPIRIT,  0x55FFFFFF    ),
    Ingredient('tequila',           'Tequila',              IngredientType.SPIRIT,  0x55FFFFFF    ),
    Ingredient('gin',               'Gin',                  IngredientType.SPIRIT,  0x55FFFFFF    ),
    Ingredient('saft zitrone',      'Zitronensaft',         IngredientType.JUICE,   0xAAF7EE99    ),
    Ingredient('saft limette',      'Limettensaft',         IngredientType.JUICE,   0xFF9FBF36    ),
    Ingredient('saft orange',       'Orangensaft',          IngredientType.JUICE,   0xDDFACB23    ),
    Ingredient('saft ananas',       'Annanassaft',          IngredientType.JUICE,   0xFFFAEF23    ),
    Ingredient('tripple sec',       'Tripple Sec / Curacao',IngredientType.SPIRIT,  0x44FACB23    ),
    Ingredient('sirup kokos',       'Kokos Sirup',          IngredientType.SIRUP,   0xDDE3E1D3    ),
    Ingredient('sirup curacao',     'Blue Curacao Sirup',   IngredientType.SIRUP,   0xFF2D57E0    ),
    Ingredient('sirup grenadine',   'Grenadine Sirup',      IngredientType.SIRUP,   0xDD911111    ),
    Ingredient('saft cranberry',    'Cranberrysaft',        IngredientType.JUICE,   0x55F07373    ),
    Ingredient('milch',             'Milch',                IngredientType.OTHER,   0xFFF7F7F7    ),
    Ingredient('kokosmilch',        'Kokosmilch',           IngredientType.OTHER,   0xFFF7F7F7    ),
    Ingredient('sahne',             'Sahne',                IngredientType.OTHER,   0xFFF7F7F7    ),
    Ingredient('sirup vanille',     'Vanille Sirup',        IngredientType.OTHER,   0x99D2A615    ),
    Ingredient('saft maracuja',     'Maracujasaft',         IngredientType.JUICE,   0xAA0CC73     ),
    Ingredient('sirup zucker',      'Zuckersirup',          IngredientType.SIRUP,   0xDDE3E1D3    ),
    Ingredient('sirup maracuja',    'Maracujasirup',        IngredientType.SIRUP,   0xDD0CC73     ),
    Ingredient('sirup pfirsich',    'Pfirsichsirup',        IngredientType.SIRUP,   0xDD0CC73     ),
    Ingredient('pfirsich likoer',   'Pfirsichlikör',        IngredientType.SPIRIT,  0x44FAAB23    ),
    Ingredient('sirup mandel',      'Mandel Sirup',         IngredientType.SIRUP,   0xDDE3E1D3    ),

    Stir,
    Sugar
]

def get_ingredient_by_identifier(identifier: str):
    """Get an ingredient based on its identifier"""
    for ingredient in _ingredients:
        if identifier == ingredient.identifier:
            return ingredient
    return None

class PortConfiguration:
    """Manages the relation between the ports and the connected ingredients"""
    def __init__(self, load_on_init : bool = True):
        self._filepath = os.path.join(data_directory, 'ports.yaml')
        self._list: dict[int, Ingredient]= {i: None for i in range(PORT_COUNT)}
        # if loading failed save the default value to file
        if load_on_init and not self.load():
            logging.warning("Port configuration not fould, write default.")
            self.save()

    def update(self, new_ports:Dict[int, Ingredient]):
        """Update the port list with a new port to  ingredient list"""
        self._list.update(new_ports)

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

    def save(self, output_stream : TextIOWrapper = None):
        """ Save the current port configuration
        :return: True if saving was successfull, False otherwise
        """
        #prepare data
        data = {}
        for port, ingredient in self._list.items():
            if ingredient is not None:
                data[port] = ingredient.identifier
            else:
                data[port] = None
        yaml_data = yaml.dump(data, None, default_flow_style=False)
        #write text
        result = True
        try:
            if output_stream is not None:
                output_stream.write(yaml_data)
            else:
                with open(self._filepath, 'w', encoding="utf-8") as file:
                    file.write(yaml_data)
        except OSError:
            result = False
        return result

    def load(self, input_stream : TextIOWrapper = None):
        """ Load the current port configuration
        :return: True if loading was successfull, False otherwise
        """
        #load data
        result = True
        data : dict[int, str]
        try:
            if input_stream is not None:
                data = yaml.load(input_stream, Loader=yaml.FullLoader)
            else:
                with open(self._filepath, 'r', encoding="utf-8") as file:
                    data = yaml.load(file, Loader=yaml.FullLoader)
        except OSError:
            result = False
        #parse data
        if result is True:
            self._list = {}
            for port, identifier in data.items():
                if identifier is None or identifier == "":
                    self._list[port] = None
                else:
                    self._list[port] = get_ingredient_by_identifier(identifier)
        return result

    @property
    def connected_ingredients(self) -> List[Ingredient]:
        """Get a list of all connected ingredients"""
        return [ i for i in self._list.values() if i is not None ]

# pylint: disable=locally-disabled, too-many-instance-attributes
class BarBotConfig:
    """Configuration for the barbot"""
    # fields
    mac_address:str = ""
    max_speed:int = 200
    max_accel:int = 300
    max_cocktail_size:int = 30
    admin_password:str = "0000"
    pump_power:int = 100
    pump_power_sirup:int = 255
    balance_offset:int = -119.1
    balance_calibration:int = -1040
    cleaning_time:int = 3000
    stirrer_connected:bool = True
    stirring_time:int = 3000
    ice_crusher_connected:bool = False
    ice_amount:int = 100
    straw_dispenser_connected:bool = False
    sugar_dispenser_connected:bool = False
    sugar_per_unit:int = 4

    def __init__(self, load_on_init : bool = True):
        self._filename = os.path.join(data_directory, "config.yaml")
        cls_annotations = BarBotConfig.__dict__.get('__annotations__', {})
        self._fields = [field for field, type in cls_annotations.items()]
        if load_on_init is True and not self.load():
            logging.warning("Config not fould, write default.")
            self.save()

    def is_ingredient_available(self, ports: PortConfiguration, ingredient_:Ingredient):
        """Check if an ingredient is available at the barbot.
        :param ingredient_: The ingredient to check"""
        if ingredient_.type == IngredientType.STIRR:
            return self.stirrer_connected
        if ingredient_.type == IngredientType.SUGAR:
            return self.sugar_dispenser_connected
        return ingredient_ in ports.connected_ingredients

    def get_ingredient_list(self, ports: PortConfiguration, only_available = False, only_normal = False, only_weighed = False) -> List[Ingredient]:
        """Get list of ingredients
        :param only_available: If set to true,
        only return ingredients that are currently connected to ports
        :param only_normal: If set to true, only return ingredients that are pumped
        :param only_weighed: If set to true, only return ingredients that are added by weight    
        """
        filtered = []
        for ingredient in _ingredients:
            if only_available and not self.is_ingredient_available(ports, ingredient):
                continue
            if IngredientType.STIRR == ingredient.type:
                if only_normal is True:
                    continue
                if only_weighed is True:
                    continue
            if IngredientType.SUGAR == ingredient.type:
                if only_normal is True:
                    continue
            filtered.append(ingredient)
        return filtered

    def save(self, output_stream : TextIOWrapper = None):
        """Save the current config values to the hard drive"""
        #prepare data
        data = { field : getattr(self, field) for field in self._fields }
        yaml_data = yaml.dump(data, None, default_flow_style=False)
        #write text
        result = True
        try:
            if output_stream is not None:
                output_stream.write(yaml_data)
            else:
                with open(self._filename, 'w', encoding="utf-8") as file:
                    file.write(yaml_data)
        except OSError:
            result = False
        return result

    @property
    def is_mac_address_valid(self):
        """Get whether the mac address has the correct structure"""
        if self.mac_address is None:
            return False
        return len(self.mac_address.strip()) == 17

    def load(self, input_stream : TextIOWrapper = None):
        """Load the config from file"""
        #load data
        result = True
        data : dict[int, str]
        try:
            if input_stream is not None:
                data = yaml.load(input_stream, Loader=yaml.FullLoader)
            else:
                with open(self._filename, 'r', encoding="utf-8") as configfile:
                    data = yaml.safe_load(configfile)
        except OSError:
            result = False

        #update config
        if result is True:
            # update fields with values from
            if data is not None:
                for field in self._fields:
                    if field in data.keys():
                        setattr(self, field, data[field])
        return result


def _get_version():
    """Get version from 'version.txt'"""
    if not os.path.exists(__version_file):
        return None
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
