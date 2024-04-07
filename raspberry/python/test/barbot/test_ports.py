# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, protected-access
from io import StringIO, TextIOWrapper
import unittest
from barbot.config import PortConfiguration, get_ingredient_by_identifier

class TestPorts(unittest.TestCase):
    def setUp(self):
        self.ingredients = [
            'rum weiss',
            'rum braun',
            'vodka',
            'tequila',
            'gin',
            'saft zitrone',
            'saft limette',
            'saft orange',
            'saft ananas',
            'tripple sec',
            'sirup kokos',
            'sirup curacao',
            'sirup grenadine',
            'saft cranberry',
            'milch',
        ]

    def get_test_data_yaml_stream(self) -> TextIOWrapper:
        """Write port config to file, they will be deserialized when ports are initialized"""
        result = ""
        for i, name in enumerate(self.ingredients):
            result += f"{i}: '{name}'\n"
        return StringIO(result)

    def test_load_ports_from_yaml(self):
        ports = PortConfiguration(load_on_init=False)
        ports.load(input_stream=self.get_test_data_yaml_stream())

        # check ports
        read_ingredients = ports.connected_ingredients
        for i, name in enumerate(self.ingredients):
            ingredient = get_ingredient_by_identifier(name)
            self.assertEqual(read_ingredients[i], ingredient)

    def test_save_ports_and_load_them_again(self):
        # load test data
        ports = PortConfiguration(load_on_init=False)
        ports.load(input_stream=self.get_test_data_yaml_stream())

        # save it to stream
        saved_ports_yaml_stream = StringIO()
        ports.save(output_stream=saved_ports_yaml_stream)
        saved_ports_yaml = saved_ports_yaml_stream.getvalue()

        # load saved data back
        ports_new = PortConfiguration(load_on_init=False)
        ports_new.load(input_stream=StringIO(saved_ports_yaml))

        # check ports
        read_ingredients = ports_new.connected_ingredients
        for i, name in enumerate(self.ingredients):
            ingredient = get_ingredient_by_identifier(name)
            self.assertEqual(read_ingredients[i], ingredient)
