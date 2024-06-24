# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, protected-access
import unittest
from datetime import datetime
from barbot.config import get_ingredient_by_identifier
from barbot.recipes import load_recipe_from_yaml, Recipe, RecipeItem

class TestRecipe(unittest.TestCase):
    def setUp(self):
        self.test_recipe = Recipe()
        self.test_recipe.name = "Test Recipe"
        self.test_recipe.created = datetime(1990, 12, 5)
        self.test_recipe.post_instruction = 'post'
        self.test_recipe.pre_instruction = 'pre'
        self.test_recipe.items = [
            RecipeItem(get_ingredient_by_identifier("saft zitrone"), 1), # type: ignore
            RecipeItem(get_ingredient_by_identifier("saft orange"), 2), # type: ignore
            RecipeItem(get_ingredient_by_identifier("saft ananas"), 3), # type: ignore
            RecipeItem(get_ingredient_by_identifier("sirup grenadine"), 4), # type: ignore
            RecipeItem(get_ingredient_by_identifier("ruehren"), 5), # type: ignore
            RecipeItem(get_ingredient_by_identifier("zucker"), 6) # type: ignore
        ]

    def get_test_data_yaml(self):
        data = ""
        created_str = self.test_recipe.created.strftime("YYYY-MM-DD HH:mm:ss")
        data += f"created: {created_str}\n"
        data += f"pre_instruction: {self.test_recipe.pre_instruction}\n"
        data += f"post_instruction: {self.test_recipe.post_instruction}\n"
        data += "items:\n"
        for recipe_item in self.test_recipe.items:
            data += f"- amount: {recipe_item.amount}\n"
            data += f"  ingredient: {recipe_item.ingredient.identifier}\n"
        return data

    def test_load_recipe_from_yaml(self):
        #load test data
        data = self.get_test_data_yaml()
        recipe = load_recipe_from_yaml(data, self.test_recipe.name)

        #check
        assert self.test_recipe.equal_to(recipe)

    def test_save_recipe_and_load_it_again(self):
        # save the recipe
        data = self.test_recipe.to_yaml()
        # load test data
        recipe = load_recipe_from_yaml(data, self.test_recipe.name)
        assert self.test_recipe.equal_to(recipe)
