import unittest
import shutil
import os
from datetime import datetime
from barbot.config import BarBotConfig, PortConfiguration, get_ingredient_by_identifier
from barbot.recipes import load_recipe_from_file, Recipe, RecipeItem
import barbot.config

temp_path = os.path.join(os.path.dirname(__file__), ".barbot")
# make sure the temp data folder exists
os.makedirs(temp_path, exist_ok=True)

class TestPorts(unittest.TestCase):
    def setUp(self):
        barbot.config.data_directory = temp_path
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
        
    def write_test_data(self):
        """Write port config to file, they will be deserialized when ports are initialized"""
        with open(os.path.join(temp_path, "ports.yaml"), "w", encoding="utf-8") as f:
            for i, name in enumerate(self.ingredients):
                f.write(f"{i}: '{name}'\n")
    
    def test_write(self):
        
        # write data to disk
        self.write_test_data()
        
        # load
        ports = PortConfiguration()
        
        # check ports
        read_ingredients = ports.connected_ingredients
        for i, name in enumerate(self.ingredients):
            ingredient = barbot.config.get_ingredient_by_identifier(name)
            self.assertEqual(read_ingredients[i], ingredient)
            
    def test_save_load(self):

        # write data to disk
        self.write_test_data()
        
        # load the config from manually written file
        ports = PortConfiguration()
        
        # remove the config file
        os.remove(os.path.join(temp_path, "ports.yaml"))
        
        # and save it again
        ports.save()
        
        # load new config and ports
        ports_new = PortConfiguration()
            
        # check ports
        read_ingredients = ports_new.connected_ingredients
        for i, name in enumerate(self.ingredients):
            ingredient = barbot.config.get_ingredient_by_identifier(name)
            self.assertEqual(read_ingredients[i], ingredient)

class TestConfigAndPorts(unittest.TestCase):
    def setUp(self):
        # let the BarBotConfig load from that folder 
        barbot.config.data_directory = temp_path
        # shape is
        # name : (value_as_string, expected_value)
        self.config_elements = {
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

    def write_test_data(self):
        """Write config it will be deserialized when BarBotConfig is initialized"""
        with open(os.path.join(temp_path, "config.yaml"), "w", encoding="utf-8") as f:
            for name, value in self.config_elements.items():
                f.write(f"{name}: {value[0]}\n")

    def test_loading(self):
        # write data to disk
        self.write_test_data()
        
        # load the config
        config = BarBotConfig()
        
        #check config
        for name, value in self.config_elements.items():
            self.assertEqual(getattr(config, name), value[1])
        
    
    def test_save_load(self):
        # write data to disk
        self.write_test_data()
        
        # load the config
        config = BarBotConfig()
        
        # remove the config files
        os.remove(os.path.join(temp_path, "config.yaml"))
        
        # and save them again
        config.save()
        
        # load new config and ports
        config_new = BarBotConfig()
        
        #check config
        for name, value in self.config_elements.items():
            self.assertEqual(getattr(config_new, name), value[1])

class TestRecipe(unittest.TestCase):
    def setUp(self):        
        self.test_recipe = Recipe()
        self.test_recipe.name = "Test Recipe"
        self.test_recipe.created = datetime.fromisocalendar(1990, 12, 5)
        self.test_recipe.post_instruction = 'post'
        self.test_recipe.pre_instruction = 'pre'
        self.test_recipe.items = [
            RecipeItem(get_ingredient_by_identifier("saft zitrone"), 1),
            RecipeItem(get_ingredient_by_identifier("saft orange"), 2),
            RecipeItem(get_ingredient_by_identifier("saft ananas"), 3),
            RecipeItem(get_ingredient_by_identifier("sirup grenadine"), 4),
            RecipeItem(get_ingredient_by_identifier("ruehren"), 5),
            RecipeItem(get_ingredient_by_identifier("zucker"), 6)
        ]

    def write_test_data(self):
        """Write config it will be deserialized when BarBotConfig is initialized"""
        filename = os.path.join(temp_path, f"{self.test_recipe.name}.yaml")
        with open(filename, "w", encoding="utf-8") as f:
            created_str = self.test_recipe.created.strftime("YYYY-MM-DD HH:mm:ss")
            f.write(f"created: {created_str}\n")
            f.write(f"pre_instruction: {self.test_recipe.pre_instruction}\n")
            f.write(f"post_instruction: {self.test_recipe.post_instruction}\n")
            f.write(f"items:\n")
            for recipeItem in self.test_recipe.items:
                f.write(f"- amount: {recipeItem.amount}\n")
                f.write(f"  ingredient: {recipeItem.ingredient.identifier}\n")
    
    def test_loading(self):
        # write data to disk
        self.write_test_data()
        
        # load recipe
        recipe = load_recipe_from_file(temp_path, f"{self.test_recipe.name}.yaml")
        
        #check
        assert self.test_recipe.equal_to(recipe)

    def test_save_load(self):
        
        # remove previous test data
        filename = f"{self.test_recipe.name}.yaml"
        os.remove(os.path.join(temp_path, filename))

        # make sure to save the file to the right folder 
        barbot.config.recipes_directory = temp_path

        # save
        self.test_recipe.save(temp_path)
        recipe = load_recipe_from_file(temp_path, filename)

        #check
        assert self.test_recipe.equal_to(recipe)