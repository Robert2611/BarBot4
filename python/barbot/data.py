
from barbot import botconfig
import yaml
import os
from enum import Enum, auto
from datetime import datetime
from typing import List
from . import directories


class IngredientType(Enum):
    Spirit = "spirit"
    Juice = "juice"
    Sirup = "sirup"
    Other = "other"
    Stirr = "stirr"


class RecipeOrder(Enum):
    Newest = auto()
    Makes = auto()


class RecipeFilter(object):
    Alcoholic: bool = True
    Order: RecipeOrder = RecipeOrder.Newest
    AvailableOnly: bool = True
    DESC: bool = False


class Ingredient(object):
    def __init__(self, Identifier: str, Name: str, Type: IngredientType, Color: int):
        self.identifier = Identifier
        self.name = Name
        self.type = Type
        self.color = Color

    def available(self):
        from barbot import ports
        if self.type == IngredientType.Stirr:
            return botconfig.stirrer_connected
        return self in ports.List.values()

    def alcoholic(self) -> bool:
        return self.type == IngredientType.Spirit


class RecipeItem(object):
    def __init__(self, Ingredient: Ingredient, Amount: int):
        self.ingredient = Ingredient
        self.amount = Amount


class Recipe(object):
    def __init__(self):
        self.items: List[RecipeItem] = []
        self.id: int = -1
        self.name = "Neues Rezept"
        self.created = datetime.now()
        self.instruction = ""

    def load(self, folder: str, filename: str):
        global IngredientsByIdentifier
        try:
            filepath = directories.join(directories.data, folder, filename)
            with open(filepath, 'r') as file:
                data = yaml.safe_load(file)
            # first six letters are the id
            self.id = int(filename[:6])
            # skip id + separator, do not include '.yaml'
            self.name = filename[7:-5]
            self.created = data["created"]
            self.instruction = data["instruction"]
            self.items = []
            for item_data in data["items"]:
                # all errors are handled by the try catch
                ingredient = IngredientsByIdentifier[item_data["ingredient"]]
                item = RecipeItem(ingredient, item_data["amount"])
                self.items.append(item)
            return True
        except Exception as ex:
            print("Error in recipe load: {0}".format(ex))
            return False

    def save(self, folder):
        global IngredientsByIdentifier
        try:
            from . import recipes
            filename = recipes.get_recipe_filename(self.id, self.name)
            filepath = directories.relative("data", folder, filename)
            data = {}
            data["created"] = self.created
            data["instruction"] = self.instruction
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
            print("Error in recipe save: {0}".format(ex))
            return False

    def equal_to(self, recipe):
        """Determine whether this recipe has the given entries"""
        if recipe.name != self.name:
            return False
        if recipe.instruction != self.instruction:
            return False
        if len(recipe.items) != len(self.items):
            return False
        for index, self_item in enumerate(self.items):
            if self_item.ingredient != recipe.items[index].ingredient:
                return False
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
        recipe.instruction = self.instruction
        recipe.name = self.name
        for item in self.items:
            item_copy = RecipeItem(item.ingredient, item.amount)
            recipe.items.append(item_copy)
        return recipe


Ingredients = [
    Ingredient('rum weiss', 'Weißer Rum', IngredientType.Spirit, 0x55FFFFFF),
    Ingredient('rum braun', 'Brauner Rum', IngredientType.Spirit, 0x99D16615),
    Ingredient('vodka', 'Vodka', IngredientType.Spirit, 0x55FFFFFF),
    Ingredient('tequila', 'Tequila', IngredientType.Spirit, 0x55FFFFFF),

    Ingredient('saft zitrone', 'Zitronensaft',
               IngredientType.Juice, 0xAAF7EE99),
    Ingredient('saft limette', 'Limettensaft',
               IngredientType.Juice, 0xFF9FBF36),
    Ingredient('saft orange', 'Orangensaft', IngredientType.Juice, 0xDDFACB23),
    Ingredient('saft ananas', 'Annanassaft', IngredientType.Juice, 0xFFFAEF23),
    Ingredient('tripple sec', 'Tripple Sec',
               IngredientType.Spirit, 0x44FACB23),
    Ingredient('sirup kokos', 'Kokossirup', IngredientType.Sirup, 0xDDE3E1D3),
    Ingredient('sirup curacao', 'Blue Curacao',
               IngredientType.Sirup, 0xFF2D57E0),
    Ingredient('sirup grenadine', 'Grenadine',
               IngredientType.Sirup, 0xDD911111),
    Ingredient('saft cranberry', 'Cranberrysaft',
               IngredientType.Juice, 0x55F07373),
    Ingredient('milch', 'Milch', IngredientType.Other, 0xFFF7F7F7),
    Ingredient('saft maracuja', 'Maracujasaft',
               IngredientType.Juice, 0xAA0CC73),
    Ingredient('sirup zucker', 'Zuckersirup',
               IngredientType.Sirup, 0xDDE3E1D3),

    Ingredient('ruehren', 'Rühren', IngredientType.Stirr, 0xDDE3E1D3),
]


def get_ingredients(only_available=False, special_ingredients=True) -> List[Ingredient]:
    global Ingredients
    filtered = []
    for ingredient in Ingredients:
        if only_available and not ingredient.available():
            continue
        if not special_ingredients and ingredient.type == IngredientType.Stirr:
            continue
        filtered.append(ingredient)
    return filtered


# for faster access
IngredientsByIdentifier = {
    ingredient.identifier: ingredient for ingredient in Ingredients}
