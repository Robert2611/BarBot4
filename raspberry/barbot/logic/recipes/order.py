"""Order classes and functions"""
from datetime import datetime
from typing import NamedTuple, List


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