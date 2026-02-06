import unittest
from unittest.mock import MagicMock, patch
from barbot.logic.recipes.recipe_collection import RecipeCollection
from barbot.logic.recipes.recipe import Recipe, RecipeFilter
from barbot.logic.config import PortConfiguration, BarBotConfig

class TestRecipeCollection(unittest.TestCase):
    def setUp(self):
        self.collection = RecipeCollection()

    @patch('barbot.logic.recipes.recipe_collection.os.listdir')
    @patch('barbot.logic.recipes.recipe_collection.load_recipe_from_file')
    def test_load(self, mock_load, mock_listdir):
        # Mock os.listdir to return some files
        mock_listdir.side_effect = lambda path: ['recipe1.yaml', 'other.txt'] if 'fixed' not in path else ['fixed1.yaml']
        
        # Mock load_recipe_from_file to return Recipe objects
        recipe1 = Recipe()
        recipe1.name = "Recipe 1"
        fixed1 = Recipe()
        fixed1.name = "Fixed 1"
        
        mock_load.side_effect = lambda folder, filename: recipe1 if filename == 'recipe1.yaml' else fixed1
        
        self.collection.load()
        
        self.assertEqual(len(self.collection._recipes), 2)
        self.assertFalse(self.collection._recipes[0].is_fixed)
        self.assertTrue(self.collection._recipes[1].is_fixed)

    def test_get_filtered_alcoholic(self):
        recipe_alc = MagicMock(spec=Recipe)
        recipe_alc.is_alcoholic = True
        recipe_alc.created = 100
        
        recipe_non_alc = MagicMock(spec=Recipe)
        recipe_non_alc.is_alcoholic = False
        recipe_non_alc.created = 200
        
        self.collection._recipes = [recipe_alc, recipe_non_alc]
        
        ports = MagicMock(spec=PortConfiguration)
        config = MagicMock(spec=BarBotConfig)
        
        # Filter only non-alcoholic
        recipe_filter = RecipeFilter(show_alcoholic=False, show_non_acloholic=True)
        filtered = self.collection.get_filtered(ports, config, recipe_filter)
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0], recipe_non_alc)

    def test_get_filtered_available(self):
        recipe_avail = MagicMock(spec=Recipe)
        recipe_avail.is_alcoholic = False
        recipe_avail.is_available.return_value = True
        recipe_avail.created = 100
        
        recipe_unavail = MagicMock(spec=Recipe)
        recipe_unavail.is_alcoholic = False
        recipe_unavail.is_available.return_value = False
        recipe_unavail.created = 200
        
        self.collection._recipes = [recipe_avail, recipe_unavail]
        
        ports = MagicMock(spec=PortConfiguration)
        config = MagicMock(spec=BarBotConfig)
        
        # Filter only available
        recipe_filter = RecipeFilter(only_available=True)
        filtered = self.collection.get_filtered(ports, config, recipe_filter)
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0], recipe_avail)

    @patch('barbot.logic.recipes.recipe_collection.os.path.isfile')
    @patch('barbot.logic.recipes.recipe_collection.os.rename')
    def test_remove(self, mock_rename, mock_isfile):
        recipe = Recipe()
        recipe.name = "Delete Me"
        self.collection._recipes = [recipe]
        
        mock_isfile.side_effect = lambda path: "Delete Me.yaml" in path
        
        self.collection.remove(recipe)
        
        self.assertEqual(len(self.collection._recipes), 0)
        self.assertTrue(mock_rename.called)

    @patch('barbot.logic.recipes.recipe.Recipe.save')
    def test_add(self, mock_save):
        recipe = Recipe()
        recipe.name = "New Recipe"
        
        self.collection.add(recipe)
        
        self.assertEqual(len(self.collection._recipes), 1)
        self.assertEqual(self.collection._recipes[0], recipe)
        self.assertTrue(mock_save.called)
