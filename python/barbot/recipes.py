from barbot.data import Recipe
from barbot.data import RecipeFilter
from barbot import directories
import yaml
import os
from typing import List

_sequence_filename = directories.relative("data", "sequence.yaml")
_recipes: List[Recipe] = None


def load():
    global _recipes
    _recipes = []
    for file in os.listdir(directories.recipes):
        if not file.endswith(".yaml"):
            continue
        r = Recipe()
        r.Load(directories.recipes, file)
        _recipes.append(r)


def filter(filter: RecipeFilter) -> List[Recipe]:
    global _recipes
    # lazy loading
    if _recipes is None:
        load()
    filtered = []
    for recipe in _recipes:
        if recipe.alcoholic() != filter.Alcoholic:
            continue
        if filter.AvailableOnly and not recipe.available():
            continue
        filtered.append(recipe)
    filtered.sort(key=lambda r: r.id, reverse=filter.DESC)
    return filtered


def get_next_id() -> int:
    global _sequence_filename, _sequence
    with open(_sequence_filename, "r") as file:
        data = yaml.safe_load(file)
    return data["recipe"]


def generate_new_id() -> int:
    global _sequence_filename
    with open(_sequence_filename, "r+") as file:
        data = yaml.safe_load(file)
        sequence = data["recipe"]
        sequence += 1
        data["recipe"] = sequence
        file.seek(0)
        yaml.dump(data, file)
    # return the new id
    return sequence


def get_reipe_filename(id: int, name: str) -> str:
    return"{0:06d} {1}.yaml".format(id, name)


def import_from_directory():
    for file in os.listdir(directories.import_recipes):
        if not file.endswith(".yaml"):
            continue
        name = file[7:-5]
        id = generate_new_id()
        old_name = os.path.join(directories.import_recipes, file)
        new_name = os.path.join(
            directories.recipes, get_reipe_filename(id, name))
        os.rename(old_name, new_name)


# import what is in the import directory
import_from_directory()
