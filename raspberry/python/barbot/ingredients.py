from enum import Enum
from typing import List
from . import botconfig


class IngredientType(Enum):
    Spirit = "spirit"
    Juice = "juice"
    Sirup = "sirup"
    Other = "other"
    Stirr = "stirr"
    Sugar = "sugar"


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


Stir = Ingredient('ruehren', 'Rühren', IngredientType.Stirr, 0xDDE3E1D3)
Sugar = Ingredient('sugar', 'Zucker', IngredientType.Sugar, 0x55FFFFFF)

_ingredients = [
    Ingredient('rum weiss', 'Weißer Rum', IngredientType.Spirit, 0x55FFFFFF),
    Ingredient('rum braun', 'Brauner Rum', IngredientType.Spirit, 0x99D16615),
    Ingredient('vodka', 'Vodka', IngredientType.Spirit, 0x55FFFFFF),
    Ingredient('tequila', 'Tequila', IngredientType.Spirit, 0x55FFFFFF),
    Ingredient('gin', 'Gin', IngredientType.Spirit, 0x55FFFFFF),
    Ingredient('saft zitrone', 'Zitronensaft',
               IngredientType.Juice, 0xAAF7EE99),
    Ingredient('saft limette', 'Limettensaft',
               IngredientType.Juice, 0xFF9FBF36),
    Ingredient('saft orange', 'Orangensaft', IngredientType.Juice, 0xDDFACB23),
    Ingredient('saft ananas', 'Annanassaft', IngredientType.Juice, 0xFFFAEF23),
    Ingredient('tripple sec', 'Tripple Sec / Curacao',
               IngredientType.Spirit, 0x44FACB23),
    Ingredient('sirup kokos', 'Kokos Sirup', IngredientType.Sirup, 0xDDE3E1D3),
    Ingredient('sirup curacao', 'Blue Curacao Sirup',
               IngredientType.Sirup, 0xFF2D57E0),
    Ingredient('sirup grenadine', 'Grenadine Sirup',
               IngredientType.Sirup, 0xDD911111),
    Ingredient('saft cranberry', 'Cranberrysaft',
               IngredientType.Juice, 0x55F07373),
    Ingredient('milch', 'Milch', IngredientType.Other, 0xFFF7F7F7),
    Ingredient('kokosmilch', 'Kokosmilch', IngredientType.Other, 0xFFF7F7F7),
    Ingredient('sahne', 'Sahne', IngredientType.Other, 0xFFF7F7F7),
    Ingredient('sirup vanille', 'Vanille Sirup',
               IngredientType.Other, 0x99D2A615),
    Ingredient('saft maracuja', 'Maracujasaft',
               IngredientType.Juice, 0xAA0CC73),
    Ingredient('sirup zucker', 'Zuckersirup',
               IngredientType.Sirup, 0xDDE3E1D3),

    Stir,
    Sugar
]

# for faster access
_ingredientsByIdentifier = {
    ingredient.identifier: ingredient for ingredient in _ingredients}


def by_identifier(identifier: str):
    return _ingredientsByIdentifier[identifier]


def get(only_available = False, only_normal = False, only_weighed = False) -> List[Ingredient]:
    """Get list of ingredients
    
    :param only_available: If set to true, only return ingredients that are currently connected to ports
    :param only_normal: If set to true, only return ingredients that are pumped
    :param only_weighed: If set to true, only return ingredients that are added by weight    
    """
    global _ingredients
    filtered = []
    for ingredient in _ingredients:
        if only_available and not ingredient.available():
            continue
        if IngredientType.Stirr == ingredient.type:
            if True == only_normal:
                continue
            if True == only_weighed:
                continue
        if IngredientType.Sugar == ingredient.type:
            if True == only_normal:
                continue
        filtered.append(ingredient)
    return filtered

#alle
#nur verfügbare
#nur mit port
#nur gewogene