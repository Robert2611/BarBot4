import yaml
from datetime import datetime
from . import directories
from .data import Recipe
import os
from typing import Dict
_prefix = "orders "
_extension = ".yaml"
_timeformat = "%Y-%m-%d %H-%M-%S"
_filename = datetime.now().strftime(_prefix + _timeformat + _extension)
_filepath = directories.join(directories.orders, _filename)


def add_order(recipe: Recipe):
    global _filepath
    data = {}
    data["recipe"] = recipe.name
    data["date"] = datetime.now()
    data["items"] = []
    for item in recipe.items:
        data_item = {}
        data_item["amount"] = item.amount
        data_item["ingredient"] = item.ingredient.identifier if item.ingredient is not None else None
        data["items"].append(data_item)
    with open(_filepath, "a") as file:
        # append as part of list
        yaml.dump([data], file)


def list_dates() -> Dict[datetime, str]:
    global _prefix
    result = {}
    for file in os.listdir(directories.orders):
        if not file.endswith(_extension):
            continue
        if not file.startswith(_prefix):
            continue
        full_path = directories.join(directories.orders, file)
        # ignore empty files
        if os.path.getsize(full_path) == 0:
            continue
        str_datetime = file[len(_prefix):-len(_extension)]
        created = datetime.strptime(str_datetime, _timeformat)
        result[created] = full_path
    return result
