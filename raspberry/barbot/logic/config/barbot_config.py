"""Barbot main configuration"""
from io import TextIOWrapper
import logging
import os
from typing import List

import yaml

from .directories import data_directory
from .ingredients import Ingredient, IngredientType, get_all_ingredients
from .port_config import PortConfiguration


# pylint: disable=locally-disabled, too-many-instance-attributes
class BarBotConfig:
    """Configuration for the barbot"""
    # fields
    mac_address: str = ""
    max_speed: int = 200
    max_accel: int = 300
    max_cocktail_size: int = 30
    admin_password: str = "0000"
    pump_power: int = 100
    pump_power_sirup: int = 255
    balance_offset: int = -119.1
    balance_calibration: int = -1040
    cleaning_time: int = 3000
    stirrer_connected: bool = True
    stirring_time: int = 3000
    ice_crusher_connected: bool = False
    ice_amount: int = 100
    straw_dispenser_connected: bool = False
    sugar_dispenser_connected: bool = False
    sugar_per_unit: int = 4

    def __init__(self, load_on_init: bool = True):
        self._filename = os.path.join(data_directory, "config.yaml")
        cls_annotations = BarBotConfig.__dict__.get('__annotations__', {})
        self._fields = [field for field, type in cls_annotations.items()]
        if load_on_init is True and not self.load():
            logging.warning("Config not found, write default.")
            self.save()

    def is_ingredient_available(self, ports: PortConfiguration, ingredient_: Ingredient):
        """Check if an ingredient is available at the barbot.
        :param ingredient_: The ingredient to check"""
        if ingredient_.type == IngredientType.STIRR:
            return self.stirrer_connected
        if ingredient_.type == IngredientType.SUGAR:
            return self.sugar_dispenser_connected
        return ingredient_ in ports.connected_ingredients

    def get_ingredient_list(
        self,
        ports: PortConfiguration,
        only_available=False,
        only_normal=False,
        only_weighed=False
    ) -> List[Ingredient]:
        """Get list of ingredients
        :param only_available: If set to true,
        only return ingredients that are currently connected to ports
        :param only_normal: If set to true, only return ingredients that are pumped
        :param only_weighed: If set to true, only return ingredients that are added by weight
        """
        filtered = []
        for ingredient in get_all_ingredients():
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

    def save(self, output_stream: TextIOWrapper = None):
        """Save the current config values to the hard drive"""
        # prepare data
        data = {field: getattr(self, field) for field in self._fields}
        yaml_data = yaml.dump(data, None, default_flow_style=False)
        # write text
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

    def load(self, input_stream: TextIOWrapper = None):
        """Load the config from file"""
        # load data
        result = True
        data: dict[int, str]
        try:
            if input_stream is not None:
                data = yaml.load(input_stream, Loader=yaml.FullLoader)
            else:
                with open(self._filename, 'r', encoding="utf-8") as configfile:
                    data = yaml.safe_load(configfile)
        except OSError:
            result = False

        # update config
        if result is True:
            # update fields with values from
            if data is not None:
                for field in self._fields:
                    if field in data.keys():
                        setattr(self, field, data[field])
        return result
