
import yaml
from datetime import datetime
from . import directories
from . import ingredients
from . import recipes

import os
from typing import List
_prefix = "orders "
_extension = ".yaml"
_timeformat = "%Y-%m-%d %H-%M-%S"
_filename = datetime.now().strftime(_prefix + _timeformat + _extension)
_filepath = directories.join(directories.orders, _filename)
_dates = {}


def add_order(recipe: recipes.Recipe):
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


def list_dates() -> List[datetime]:
    global _prefix, _dates
    _dates = {}
    result = []
    for file in os.listdir(directories.orders):
        if not file.endswith(_extension):
            continue
        if not file.startswith(_prefix):
            continue
        full_path = directories.join(directories.orders, file)
        # ignore empty files
        if os.path.getsize(full_path) == 0:
            continue
        # use str instead of datetime as dict key to avoid hashing problems
        str_datetime = file[len(_prefix):-len(_extension)]
        _dates[str_datetime] = full_path
        created = datetime.strptime(str_datetime, _timeformat)
        result.append(created)
    return result


def _increase_entry(item: dict, key, increment=1):
    if key in item.keys():
        item[key] += increment
    else:
        item[key] = increment


def get_statistics(date: datetime):
    global _dates
    statistics = {}
    with open(_dates[date.strftime(_timeformat)], "r") as file:
        orders_data = yaml.safe_load(file)
    ingredients_amount = {}
    cocktail_count = {}
    cocktails_by_time = {}
    for order in orders_data:
        _increase_entry(cocktail_count, order["recipe"])
        hour = datetime(
            order["date"].year,
            order["date"].month,
            order["date"].day,
            order["date"].hour,
        )
        _increase_entry(cocktails_by_time, hour)
        for item in order["items"]:
            ing = ingredients.by_identifier(item["ingredient"])
            _increase_entry(ingredients_amount, ing, item["amount"])
        order["recipe"]
    statistics["ingredients_amount"] = ingredients_amount
    statistics["cocktail_count"] = cocktail_count
    statistics["cocktails_by_time"] = cocktails_by_time
    statistics["total_cocktails"] = len(orders_data)

    return statistics
