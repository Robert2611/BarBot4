
import yaml
from datetime import datetime, timedelta
from . import directories
from . import ingredients
from . import recipes
import os
from typing import List

PARTY_MAX_DURATION = timedelta(days=1)
PARTY_MIN_ORDER_COUNT = 5
STATISTICS_MAX_DISTANCE = timedelta(weeks=52)
class Party:
    def __init__(self, start: datetime):
        self.orders = []
        self.start = start

_prefix = "orders "
_extension = ".yaml"
_timeformat = "%Y-%m-%d %H-%M-%S"
_filename = datetime.now().strftime(_prefix + _timeformat + _extension)
_filepath = directories.join(directories.orders, _filename)


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

def get_parties() -> List[Party]:
    global _prefix
    all_parties:List[Party] = []
    current_party = None
    for file in sorted(os.listdir(directories.orders)):
        if not file.endswith(_extension):
            continue
        if not file.startswith(_prefix):
            continue
        full_path = directories.join(directories.orders, file)
        # ignore empty files
        if os.path.getsize(full_path) == 0:
            continue
        str_datetime = file[len(_prefix):-len(_extension)]
        file_datetime = datetime.strptime(str_datetime, _timeformat)
        # ignore dates that are too long ago
        if datetime.now() - file_datetime > STATISTICS_MAX_DISTANCE:
            continue
        with open(full_path, "r") as file:
            orders_data = yaml.safe_load(file)
        # start a new party
        if current_party == None or file_datetime - current_party.start > PARTY_MAX_DURATION:
            # add the previous one if there is one
            if current_party is not None:
                all_parties.append(current_party)
            # create a new party
            current_party = Party(start=file_datetime)
        # add all orders from the file
        for order in orders_data:
            current_party.orders.append(order)
    # also add the last party
    if current_party is not None:
        all_parties.append(current_party)
    result = [p for p in all_parties if len(p.orders) >= PARTY_MIN_ORDER_COUNT]
    return result


def _increase_entry(item: dict, key, increment=1):
    if key in item.keys():
        item[key] += increment
    else:
        item[key] = increment


def get_statistics(party: Party):
    statistics = {}
    ingredients_amount = {}
    cocktail_count = {}
    cocktails_by_time = {}
    for order in party.orders:
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
            if ing.type != ingredients.IngredientType.Stirr:
                _increase_entry(ingredients_amount, ing, item["amount"])
        order["recipe"]
    statistics["ingredients_amount"] = ingredients_amount
    statistics["cocktail_count"] = cocktail_count
    statistics["cocktails_by_time"] = cocktails_by_time
    statistics["total_cocktails"] = len(party.orders)

    return statistics
