import yaml
import os
from typing import List
from .data import Recipe
from .data import RecipeFilter
from . import directories

_sequence_filename = directories.join(directories.data, "sequence.yaml")
_recipes: List[Recipe] = None


def load():
    global _recipes
    _recipes = []
    for file in os.listdir(directories.recipes):
        if not file.endswith(".yaml"):
            continue
        r = Recipe()
        r.load(directories.recipes, file)
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
    recipe.save(directories.recipes)
    _recipes.append(recipe)
