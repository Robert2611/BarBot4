import yaml
import os
import logging
from typing import List
from enum import Enum, auto
from datetime import datetime
from . import ingredients
from . import directories


class RecipeOrder(Enum):
    Newest = auto()
    Makes = auto()


class RecipeFilter(object):
    Alcoholic: bool = True
    Order: RecipeOrder = RecipeOrder.Newest
    AvailableOnly: bool = True
    DESC: bool = False


class RecipeItem(object):
    def __init__(self, Ingredient: ingredients.Ingredient, Amount: int):
        self.ingredient = Ingredient
        self.amount = Amount


class Recipe(object):
    def __init__(self):
        self.items: List[RecipeItem] = []
        self.name = "Neues Rezept"
        self.created = datetime.now()
        self.pre_instruction = ""
        self.post_instruction = ""
        self.is_fixed = False

    def save(self):
        # fixed recipes cannot be modified
        if self.is_fixed:
            return False
        try:
            filename = self.name + ".yaml"
            filepath = directories.join(directories.recipes, filename)
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
            with open(filepath, 'w') as file:
                data = yaml.dump(data, file)
            return True
        except Exception as ex:
            logging.warn("Error in recipe save: {0}".format(ex))
            return False

    def equal_to(self, recipe):
        """Determine whether this recipe has the given entries"""
        if recipe.name != self.name:
            return False
        if recipe.pre_instruction != self.pre_instruction:
            return False
        if recipe.post_instruction != self.post_instruction:
            return False
        if len(recipe.items) != len(self.items):
            return False
        for index, self_item in enumerate(self.items):
            if self_item.ingredient != recipe.items[index].ingredient:
                return False
            # ignore the amount for stirring
            if self_item.ingredient.type == ingredients.IngredientType.Stirr:
                continue
            if self_item.amount != recipe.items[index].amount:
                return False
        return True

    def available(self) -> bool:
        for item in self.items:
            if not item.ingredient.available():
                return False
        return True

    def alcoholic(self) -> bool:
        for item in self.items:
            if item.ingredient.alcoholic():
                return True
        return False

    def copy(self):
        recipe = Recipe()
        recipe.name = self.name
        recipe.pre_instruction = self.pre_instruction
        recipe.post_instruction = self.post_instruction
        recipe.name = self.name
        for item in self.items:
            item_copy = RecipeItem(item.ingredient, item.amount)
            recipe.items.append(item_copy)
        return recipe


_recipes: List[Recipe] = None


def _load_recipe_from_file(folder: str, filename: str) -> Recipe:
    r = Recipe()
    try:
        filepath = directories.join(folder, filename)
        with open(filepath, 'r') as file:
            data = yaml.safe_load(file)
        # do not include '.yaml'
        r.name = filename[:-5]
        r.created = data["created"]
        if "pre_instruction" in data.keys():
            r.pre_instruction = data["pre_instruction"]
        if "post_instruction" in data.keys():
            r.post_instruction = data["post_instruction"]
        r.items = []
        for item_data in data["items"]:
            # all errors are handled by the try catch
            ingredient = ingredients.by_identifier(item_data["ingredient"])
            item = RecipeItem(ingredient, item_data["amount"])
            r.items.append(item)
        return r
    except Exception as ex:
        logging.warn("Error in recipe load: {0}".format(ex))
        return None


def load():
    global _recipes
    _recipes = []
    # user recipes
    for file in os.listdir(directories.recipes):
        if not file.endswith(".yaml"):
            continue
        r = _load_recipe_from_file(directories.recipes, file)
        r.is_fixed = False
        _recipes.append(r)
    # fixed recipes
    for file in os.listdir(directories.fixed_recipes):
        if not file.endswith(".yaml"):
            continue
        r = _load_recipe_from_file(directories.fixed_recipes, file)
        r.is_fixed = True
        _recipes.append(r)


def filter(filter: RecipeFilter) -> List[Recipe]:
    global _recipes
    # lazy loading
    if _recipes is None:
        load()
    filtered = []
    for recipe in _recipes:
        if filter is not None:
            if recipe.alcoholic() != filter.Alcoholic:
                continue
            if filter.AvailableOnly and not recipe.available():
                continue
        filtered.append(recipe)
    desc = filter.DESC if filter is not None else False
    filtered.sort(key=lambda r: r.created, reverse=desc)
    return filtered


def remove(recipe: Recipe):
    global _recipes
    old_name = directories.join(directories.recipes, recipe.name+".yaml")
    index = 0
    # make sure file does not exist
    while True:
        index += 1
        filename = "{0}_{1:03d}.yaml".format(recipe.name, index)
        new_name = directories.join(directories.old_recipes, filename)
        if not os.path.isfile(new_name):
            break
    os.rename(old_name, new_name)
    if recipe in _recipes:
        _recipes.remove(recipe)


def add(recipe: Recipe):
    global _recipes
    recipe.save()
    _recipes.append(recipe)
