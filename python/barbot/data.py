from barbot import directories
import yaml
import os
from enum import Enum, auto
from datetime import datetime
from typing import List


def in_data_dir(*paths):
    script_dir = os.path.dirname(__file__)
    filepath = os.path.join(script_dir, "..", "..", "data", *paths)
    return filepath


class IngregientType(Enum):
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
    def __init__(self, Identifier: str, Name: str, Type: IngregientType, Color: int):
        self.identifier = Identifier
        self.name = Name
        self.type = Type
        self.color = Color

    def available(self):
        from barbot import ports
        return self.identifier in ports.List

    def alcoholic(self) -> bool:
        return self.type == IngregientType.Spirit


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

    def Load(self, folder: str, filename: str):
        try:
            filepath = directories.relative("data", folder, filename)
            with open(filepath, 'r') as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
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
            print("Error: {0}".format(ex))
            return False

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


Ingredients = [
    Ingredient('rum weiss', 'Weißer Rum', IngregientType.Spirit, 0x55FFFFFF),
    Ingredient('rum braun', 'Brauner Rum', IngregientType.Spirit, 0x99D16615),
    Ingredient('vodka', 'Vodka', IngregientType.Spirit, 0x55FFFFFF),
    Ingredient('tequila', 'Tequila', IngregientType.Spirit, 0x55FFFFFF),

    Ingredient('saft zitrone', 'Zitronensaft',
               IngregientType.Juice, 0xAAF7EE99),
    Ingredient('saft limette', 'Limettensaft',
               IngregientType.Juice, 0xFF9FBF36),
    Ingredient('saft orange', 'Orangensaft', IngregientType.Juice, 0xDDFACB23),
    Ingredient('saft ananas', 'Annanassaft', IngregientType.Juice, 0xFFFAEF23),
    Ingredient('tripple sec', 'Tripple Sec', IngregientType.Sirup, 0x44FACB23),
    Ingredient('sirup kokos', 'Kokossirup', IngregientType.Sirup, 0xDDE3E1D3),
    Ingredient('sirup curacao', 'Blue Curacao',
               IngregientType.Sirup, 0xFF2D57E0),
    Ingredient('sirup grenadine', 'Grenadine',
               IngregientType.Sirup, 0xDD911111),
    Ingredient('saft cranberry', 'Cranberrysaft',
               IngregientType.Juice, 0x55F07373),
    Ingredient('milch', 'Milch', IngregientType.Other, 0xFFF7F7F7),
    Ingredient('saft maracuja', 'Maracujasaft',
               IngregientType.Juice, 0xAA0CC73),
    Ingredient('sirup zucker', 'Zuckersirup',
               IngregientType.Sirup, 0xDDE3E1D3),

    Ingredient('ruehren', 'Rühren', IngregientType.Sirup, 0xDDE3E1D3),
]

# for faster access
IngredientsByIdentifier = {
    ingredient.identifier: ingredient for ingredient in Ingredients}
