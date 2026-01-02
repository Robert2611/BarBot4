"""Party classes and statistics"""
import os
from datetime import datetime, timedelta
from typing import NamedTuple, List, Dict
import yaml

from ..config import IngredientType, get_ingredient_by_identifier, orders_directory

from .order import Order, OrderItem, get_order_from_json
from .recipe import Recipe

PARTY_MAX_DURATION = timedelta(days=1)
PARTY_MIN_ORDER_COUNT = 5
STATISTICS_MAX_DISTANCE = timedelta(weeks=52)
ORDERS_FILENAME_PREFIX = "orders "
ORDERS_FILENAME_EXTENSION = ".yaml"
ORDERS_FILENAME_TIMEFORMAT = "%Y-%m-%d %H-%M-%S"

class PartyStatistics(NamedTuple):
    """Statistics for a party"""
    ingredients_amount: Dict[str, float]
    cocktail_count: Dict[str, int]
    cocktails_by_time: Dict[str, int]
    total_cocktails: int


class Party:
    """Class that aggregates orders by parties"""
    def __init__(self, start=datetime.now()):
        self.orders: List[Order] = []
        self.start: datetime = start

    def add_order(self, recipe: Recipe):
        """Add a new order to the list and save it"""
        order = Order(recipe.name)
        for item in recipe.items:
            ingredient = item.ingredient.identifier if item.ingredient is not None else None
            order_item = OrderItem(item.amount, ingredient)
            order.items.append(order_item)
        _filename = datetime.now().strftime(
            ORDERS_FILENAME_PREFIX + ORDERS_FILENAME_TIMEFORMAT + ORDERS_FILENAME_EXTENSION
        )
        _filepath = os.path.join(orders_directory, _filename)
        with open(_filepath, "a", encoding="utf-8") as file:
            # append as part of list
            data = {
                "recipe": order.recipe,
                "date": order.date,
                "items": [
                    {
                        "amount": item.amount,
                        "ingredient": item.ingredient
                    }
                    for item in order.items
                ]
            }
            yaml.dump([data], file)
        self.orders.append(order)

    def get_statistics(self) -> PartyStatistics:
        """Calculate statistics for this party"""
        ingredients_amount = {}
        cocktail_count = {}
        cocktails_by_time = {}

        def _increase_entry(item: dict, key, increment=1):
            if key in item.keys():
                item[key] += increment
            else:
                item[key] = increment

        for order in self.orders:
            _increase_entry(cocktail_count, order.recipe)
            hour = datetime(order.date.year, order.date.month, order.date.day, order.date.hour)
            _increase_entry(cocktails_by_time, hour)
            for item in order.items:
                ing = get_ingredient_by_identifier(item.ingredient)
                if ing.type != IngredientType.STIRR:
                    _increase_entry(ingredients_amount, ing.name, item.amount)
        return PartyStatistics(
            ingredients_amount,
            cocktail_count,
            cocktails_by_time,
            len(self.orders)
        )


class PartyCollection(List[Party]):
    """Collection holding all parties that themselves hold the orders"""
    def __init__(self):
        all_parties = self._get_parties()
        for party in all_parties:
            if len(party.orders) >= PARTY_MIN_ORDER_COUNT:
                self.append(party)
        self._current_party = None
        if len(self) > 0 and datetime.now() - self[-1].start <= PARTY_MAX_DURATION:
            self._current_party = self[-1]
        else:
            self._current_party = Party()
            self.append(self._current_party)

    @property
    def current_party(self):
        """Get the currently ongoing party"""
        return self._current_party

    @staticmethod
    def _get_parties():
        all_parties: List[Party] = []
        current_party = None
        for file in sorted(os.listdir(orders_directory)):
            if not file.endswith(ORDERS_FILENAME_EXTENSION):
                continue
            if not file.startswith(ORDERS_FILENAME_PREFIX):
                continue
            full_path = os.path.join(orders_directory, file)
            # ignore empty files
            if os.path.getsize(full_path) == 0:
                continue
            str_datetime = file[len(ORDERS_FILENAME_PREFIX):-len(ORDERS_FILENAME_EXTENSION)]
            file_datetime = datetime.strptime(str_datetime, ORDERS_FILENAME_TIMEFORMAT)
            # ignore dates that are too long ago
            if datetime.now() - file_datetime > STATISTICS_MAX_DISTANCE:
                continue
            with open(full_path, "r", encoding="utf-8") as file:
                orders_data = yaml.safe_load(file)
            # start a new party
            if current_party is None \
                    or file_datetime - current_party.start > PARTY_MAX_DURATION:
                # add the previous one if there is one
                if current_party is not None:
                    all_parties.append(current_party)
                # create a new party
                current_party = Party(start=file_datetime)
            # add all orders from the file
            for order in orders_data:
                current_party.orders.append(get_order_from_json(order))
        # also add the last party
        if current_party is not None:
            all_parties.append(current_party)
        return all_parties
