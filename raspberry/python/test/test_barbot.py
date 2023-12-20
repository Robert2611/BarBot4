import unittest
import shutil
import os
from barbot.config import BarBotConfig
import barbot.config

test_data_path = os.path.join(os.path.dirname(__file__), "data")
temp_path = os.path.join(os.path.dirname(__file__), ".barbot")
# make sure the temp data folder exists
os.makedirs(temp_path, exist_ok=True)

class TestConfig(unittest.TestCase):
    def setUp(self):
        # let the BarBotConfig load from that folder 
        barbot.config.data_directory = temp_path
        
    def test_loading(self):
        # shape is
        # name : (value_as_string, expected_value)
        config_elements = {
            "admin_password" : ('\'0123\'', '0123'),
            "balance_calibration" : ('2', 2),
            "balance_offset" : ('3', 3),
            "cleaning_time" : ('4', 4),
            "ice_amount" : ('5', 5),
            "ice_crusher_connected" : ('false', False),
            "mac_address" : ('7', 7),
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
        ingredients = [
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
        # write config and ports, they will be deserialized when BarBotConfig is initialized
        with open(os.path.join(temp_path, "config.yaml"), "w", encoding="utf-8") as f:
            for name, value in config_elements.items():
                f.write(f"{name}: {value[0]}\n")
        with open(os.path.join(temp_path, "ports.yaml"), "w", encoding="utf-8") as f:
            for i, name in enumerate(ingredients):
                f.write(f"{i}: '{name}'\n")
        
        config = BarBotConfig()
        
        #check config
        for name, value in config_elements.items():
            self.assertEqual(getattr(config, name), value[1])
        
        # check ports
        read_ingredients = config.ports.connected_ingredients
        for i, name in enumerate(ingredients):
            ingredient = barbot.config.get_ingredient_by_identifier(name)
            self.assertEqual(read_ingredients[i], ingredient)
