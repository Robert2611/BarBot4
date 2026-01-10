"""Recipe classes and functions"""

__all__ = [
    "RecipeSorting",
    "RecipeFilter",
    "RecipeItem",
    "Recipe",
    "load_recipe_from_yaml",
    "load_recipe_from_file",
]

from enum import Enum, auto
import os
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List
import yaml

from ..config import Ingredient, IngredientType, get_ingredient_by_identifier
from ..config import recipes_directory
from ..config import BarBotConfig, PortConfiguration



class RecipeSorting(Enum):
    """Type of sorting for recipes"""
    NEWEST = auto()
    # TODO: Implement sorting by makes
    MAKES = auto()

@dataclass
class RecipeFilter:
    """Describes how the recipes should be filtered"""
    show_alcoholic: bool = True
    show_non_acloholic: bool = True
    sorting: RecipeSorting = RecipeSorting.NEWEST
    only_available: bool = True
    descending: bool = False


@dataclass
class RecipeItem:
    """Single line in a recipe containing an ingredient and amount"""
    ingredient: Ingredient
    amount: int


class Recipe:
    """Definition of a recipe containing recipe items"""
    def __init__(self):
        self.items: List[RecipeItem] = []
        self.name = "Neues Rezept"
        self.created = datetime.now()
        self.pre_instruction = ""
        self.post_instruction = ""
        self.is_fixed = False

    def save(self, folder: str = recipes_directory):
        """Save the recipe to the drive"""
        # fixed recipes cannot be modified
        if self.is_fixed:
            return False
        
        # sanitize filename to prevent directory traversal
        filename = "".join(c for c in self.name if c.isalnum() or c in " ._").rstrip() + ".yaml"

        filepath = os.path.join(folder, filename)
        data = self.to_yaml()
        result = True
        try:
            with open(filepath, 'w', encoding="utf-8") as file:
                file.write(data)
        except OSError as ex:
            logging.warning("Error in recipe save: %s", ex)
            result = False
        return result

    def to_yaml(self):
        """Get the yaml representation of this recipe"""
        data = {}
        data["created"] = self.created
        data["pre_instruction"] = self.pre_instruction
        data["post_instruction"] = self.post_instruction
        data["items"] = []
        for item in self.items:
            if item.ingredient is None:
                continue
            data_item = {}
            data_item["ingredient"] = item.ingredient.identifier
            data_item["amount"] = item.amount
            data["items"].append(data_item)
        yaml_data = yaml.dump(data, None)
        return yaml_data

    def equal_to(self, recipe):
        """Determine whether this recipe has the given entries

            :param recipe: The recipe to compare this one with
            :result: True if the two recipes are equal, False otherwise
        """
        # check string attributes
        for attribute in ["name", "pre_instruction", "post_instruction"]:
            if getattr(recipe, attribute) != getattr(self, attribute):
                return False
        if len(recipe.items) != len(self.items):
            return False
        for index, self_item in enumerate(self.items):
            if self_item.ingredient != recipe.items[index].ingredient:
                return False
            # ignore the amount for stirring
            if self_item.ingredient.type == IngredientType.STIRR:
                continue
            if self_item.amount != recipe.items[index].amount:
                return False
        return True

    def is_available(self, ports: PortConfiguration, config: BarBotConfig) -> bool:
        """A recipe is available if all its ingredients are available i.e. connected to a port.
        :param config: The barbot config to use for checking if the recipe is available
        """
        for item in self.items:
            if not config.is_ingredient_available(ports, item.ingredient):
                return False
        return True

    @property
    def is_alcoholic(self) -> bool:
        """A recipe is alcoholic if at least one of its ingredients is alcoholic"""
        for item in self.items:
            if item.ingredient.alcoholic():
                return True
        return False

    def copy(self):
        """Create a new recipe that has the same content as the current one"""
        recipe = Recipe()
        recipe.name = self.name
        recipe.pre_instruction = self.pre_instruction
        recipe.post_instruction = self.post_instruction
        recipe.name = self.name
        for item in self.items:
            item_copy = RecipeItem(item.ingredient, item.amount)
            recipe.items.append(item_copy)
        return recipe


def load_recipe_from_yaml(yaml_string: str, name: str) -> Recipe:
    """Load a recipe from its yaml representation. The name is not part of the yaml,
    so it has to be provided separately"""
    # load yaml
    data = yaml.safe_load(yaml_string)

    # create recipe
    r = Recipe()
    r.created = data["created"]
    r.name = name
    if "pre_instruction" in data.keys():
        r.pre_instruction = data["pre_instruction"]
    if "post_instruction" in data.keys():
        r.post_instruction = data["post_instruction"]
    r.items = []
    for item_data in data["items"]:
        # all errors are handled by the try catch
        ingredient = get_ingredient_by_identifier(item_data["ingredient"])
        if ingredient is None:
            logging.error("Empty ingredient in recipe '%s', raw value is '%s'", name, item_data["ingredient"])
            return None
        item = RecipeItem(ingredient, item_data["amount"])
        r.items.append(item)
    return r


def load_recipe_from_file(folder: str, filename: str) -> Recipe:
    """Load a recipe from a file

        :param folder: Parent folder of the file
        :param filename: Name of the file to load, should be "*.yaml"
    """
    yaml_data = None
    try:
        filepath = os.path.join(folder, filename)
        with open(filepath, 'r', encoding="utf-8") as file:
            yaml_data = file.read()
    except OSError as ex:
        logging.warning("Error in recipe load: %s", ex)
        return None

    # do not include '.yaml'
    name = os.path.splitext(filename)[0]

    recipe = load_recipe_from_yaml(yaml_data, name)
    return recipe
