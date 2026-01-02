"""Port configuration management"""
from io import TextIOWrapper
import logging
import os
from typing import Dict, List

import yaml

from .directories import data_directory
from .ingredients import Ingredient, get_ingredient_by_identifier

# Port configuration
PORT_COUNT = 12

class PortConfiguration:
    """Manages the relation between the ports and the connected ingredients"""
    def __init__(self, load_on_init: bool = True):
        self._filepath = os.path.join(data_directory, 'ports.yaml')
        self._list: dict[int, Ingredient] = {i: None for i in range(PORT_COUNT)}
        # if loading failed save the default value to file
        if load_on_init and not self.load():
            logging.warning("Port configuration not found, write default.")
            self.save()

    def update(self, new_ports: Dict[int, Ingredient]):
        """Update the port list with a new port to ingredient list"""
        self._list.update(new_ports)

    def ingredient_at_port(self, port: int):
        """Get the ingredient that is connected to a given port.
        :param port: The port"""
        if port not in self._list:
            return None
        return self._list[port]

    def port_of_ingredient(self, ingredient: Ingredient):
        """Get the port where to find the given ingredient
        :param ingredient: The ingredient to look for
        :return: The index of the port of the ingredient, None if it was not found
        """
        for port, list_ingredient in self._list.items():
            if list_ingredient == ingredient:
                return port
        return None

    def save(self, output_stream: TextIOWrapper = None):
        """Save the current port configuration
        :return: True if saving was successful, False otherwise
        """
        # prepare data
        data = {}
        for port, ingredient in self._list.items():
            if ingredient is not None:
                data[port] = ingredient.identifier
            else:
                data[port] = None
        yaml_data = yaml.dump(data, None, default_flow_style=False)
        # write text
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

    def load(self, input_stream: TextIOWrapper = None):
        """Load the current port configuration
        :return: True if loading was successful, False otherwise
        """
        # load data
        result = True
        data: dict[int, str]
        try:
            if input_stream is not None:
                data = yaml.load(input_stream, Loader=yaml.FullLoader)
            else:
                with open(self._filepath, 'r', encoding="utf-8") as file:
                    data = yaml.load(file, Loader=yaml.FullLoader)
        except OSError:
            result = False
        # parse data
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
        return [i for i in self._list.values() if i is not None]
