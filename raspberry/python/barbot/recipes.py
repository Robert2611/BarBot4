"""Recipes"""
import os
import logging
from typing import NamedTuple, List, Dict
from dataclasses import dataclass
from enum import Enum, auto
from datetime import datetime, timedelta
import yaml
from .config import Ingredient, IngredientType, get_ingredient_by_identifier
from .config import recipes_directory, fixed_recipes_directory
from .config import old_recipes_directory, orders_directory
from .config import BarBotConfig, PortConfiguration

PARTY_MAX_DURATION = timedelta(days=1)
PARTY_MIN_ORDER_COUNT = 5
STATISTICS_MAX_DISTANCE = timedelta(weeks=52)
ORDERS_FILENAME_PREFIX = "orders "
ORDERS_FILENAME_EXTENSION = ".yaml"
ORDERS_FILENAME_TIMEFORMAT = "%Y-%m-%d %H-%M-%S"

class RecipeSorting(Enum):
    """Type of sorting for recipes"""
    NEWEST = auto()
    #TODO: Implement sorting by makes
    MAKES = auto()

@dataclass
class RecipeFilter():
    """Describes how the recipes should be filtered"""
    show_alcoholic: bool = True
    show_non_acloholic: bool = True
    sorting: RecipeSorting = RecipeSorting.NEWEST
    only_available: bool = True
    descending: bool = False
    
@dataclass
class RecipeItem():
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
        try:
            filename = self.name + ".yaml"
            filepath = os.path.join(folder, filename)
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
            with open(filepath, 'w', encoding="utf-8") as file:
                data = yaml.dump(data, file)
            return True
        except OSError as ex:
            logging.warning("Error in recipe save: %s", ex)
            return False

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
        :param config: The barbot config to use for cheking if the recipe is available
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

class RecipeCollection():
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

    def get_filtered(self, recipe_filter: RecipeFilter, ports: PortConfiguration, config : BarBotConfig) -> List[Recipe]:
        """Get a filtered list of recpies using the given filter"""
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

def load_recipe_from_file(folder: str, filename: str) -> Recipe:
    """Load a recipe from a file
    
        :param folder: Parent folder of the file
        :param filename: Name of the file to load, should be "*.yaml"
    """
    r = Recipe()
    try:
        filepath = os.path.join(folder, filename)
        with open(filepath, 'r', encoding="utf-8") as file:
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
            ingredient = get_ingredient_by_identifier(item_data["ingredient"])
            item = RecipeItem(ingredient, item_data["amount"])
            r.items.append(item)
        return r
    except OSError as ex:
        logging.warning("Error in recipe load: %s", ex)
        return None

class OrderItem(NamedTuple):
    """Items of an order, it is like a recipe item but the ingredient is a string"""
    amount: int
    ingredient: str

class Order(NamedTuple):
    """Order of a recipe containing the recipe name and a copy of the recipe items"""
    recipe: str
    date: datetime = datetime.now()
    items: List[OrderItem] = []

def get_order_from_json(data: dict):
    """Create a Order object from serialized json data dict.
    :param data: The parsed JSON data
    :returns: A new Order with data from the JSON"""
    items = [OrderItem(line['amount'], line['ingredient']) for line in data['items']]
    return Order(data['recipe'], data['date'], items)

class PartyStatistics(NamedTuple):
    """Statistics for a party"""
    ingredients_amount: Dict[str, float]
    cocktail_count: Dict[str, int]
    cocktails_by_time: Dict[str, int]
    total_cocktails: int

class Party():
    """Class that aggregates orders by parties"""
    def __init__(self, start = datetime.now()):
        self.orders:List[Order] = []
        self.start:datetime = start

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
            yaml.dump([order], file)
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
        all_parties:List[Party] = []
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
