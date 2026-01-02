"""Recipe collection management"""
import os
from typing import List

from ..config import fixed_recipes_directory, recipes_directory, old_recipes_directory
from ..config import BarBotConfig, PortConfiguration
from .recipe import Recipe, RecipeFilter, load_recipe_from_file


class RecipeCollection:
    """Collection holding all recipes"""
    def __init__(self):
        self._recipes: List[Recipe] = []

    def load(self):
        """Load all recipes in the recipes folder and the fixed_recipes folder """
        self._recipes.clear()
        # user recipes
        for file in os.listdir(recipes_directory):
            if not file.endswith(".yaml"):
                continue
            r = load_recipe_from_file(recipes_directory, file)
            if r is not None:
                r.is_fixed = False
                self._recipes.append(r)
        # fixed recipes
        for file in os.listdir(fixed_recipes_directory):
            if not file.endswith(".yaml"):
                continue
            r = load_recipe_from_file(fixed_recipes_directory, file)
            if r is not None:
                r.is_fixed = True
                self._recipes.append(r)

    def get_filtered(self, recipe_filter: RecipeFilter, ports: PortConfiguration, config: BarBotConfig) -> List[Recipe]:
        """Get a filtered list of recipes using the given filter"""
        # lazy loading
        if self._recipes is None:
            self.load()
        filtered = []
        for recipe in self._recipes:
            if recipe_filter is not None:
                is_alcoholic = recipe.is_alcoholic
                if is_alcoholic and not recipe_filter.show_alcoholic:
                    continue
                if not is_alcoholic and not recipe_filter.show_non_acloholic:
                    continue
                if recipe_filter.only_available and not recipe.is_available(ports, config):
                    continue
            filtered.append(recipe)
        desc = recipe_filter.descending if recipe_filter is not None else False
        filtered.sort(key=lambda r: r.created, reverse=desc)
        return filtered

    def remove(self, recipe: Recipe):
        """Remove a recipe from the collection.
        The removed recipe will not be displayed anymore
        but the file will be backed up in the old_recipes folder.
        :param recipe: The recipe to remove"""
        old_name = os.path.join(recipes_directory, f"{recipe.name}.yaml")
        if os.path.isfile(old_name):
            index = 0
            # make sure file does not exist
            while True:
                index += 1
                filename = f"{recipe.name}_{index:03d}.yaml"
                new_name = os.path.join(old_recipes_directory, filename)
                if not os.path.isfile(new_name):
                    break
            os.rename(old_name, new_name)
        if recipe in self._recipes:
            self._recipes.remove(recipe)

    def add(self, recipe: Recipe):
        """Add a new recipe to the list and save it.
        :param recipe: The recipe to add"""
        recipe.save()
        self._recipes.append(recipe)
