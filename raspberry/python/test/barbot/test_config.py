# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, protected-access
from io import StringIO, TextIOWrapper
import unittest
from barbot.config import BarBotConfig

class TestConfig(unittest.TestCase):
    def setUp(self):
        # shape is
        # name : (value_as_string, expected_value)
        self.config_elements = {
            "admin_password" : ('\'0123\'', '0123'),
            "balance_calibration" : ('2', 2),
            "balance_offset" : ('3', 3),
            "cleaning_time" : ('4', 4),
            "ice_amount" : ('5', 5),
            "ice_crusher_connected" : ('false', False),
            "mac_address" : ('00:80:41:ae:fd:7e', '00:80:41:ae:fd:7e'),
            "max_accel" : ('8', 8),
            "max_cocktail_size" : ('9', 9),
            "max_speed" : ('10', 10),
            "pump_power" : ('11', 11),
            "pump_power_sirup" : ('12', 12),
            "stirrer_connected" : ('false', False),
            "stirring_time" : ('14', 14),
            "straw_dispenser_connected" : ('true', True),
            "sugar_dispenser_connected" : ('true', True),
            "sugar_per_unit" : ('17', 17),
        }

    def get_test_data_yaml_stream(self) -> TextIOWrapper:
        """Write config it will be deserialized when BarBotConfig is initialized"""
        result = ""
        for name, value in self.config_elements.items():
            result += f"{name}: {value[0]}\n"
        return StringIO(result)

    def test_load_config_from_yaml(self):
        # load test data
        config = BarBotConfig(load_on_init=False)
        config.load(self.get_test_data_yaml_stream())

        #check config
        for name, value in self.config_elements.items():
            self.assertEqual(getattr(config, name), value[1])

    def test_save_config_and_load_it_again(self):
        # load test data
        config = BarBotConfig(load_on_init=False)
        config.load(self.get_test_data_yaml_stream())

        # save it to stream
        saved_config_yaml_stream = StringIO()
        config.save(output_stream=saved_config_yaml_stream)
        saved_config_yaml = saved_config_yaml_stream.getvalue()

        # load saved data back
        config_new = BarBotConfig(load_on_init=False)
        config_new.load(input_stream=StringIO(saved_config_yaml))

        #check config
        for name, value in self.config_elements.items():
            self.assertEqual(getattr(config_new, name), value[1])
