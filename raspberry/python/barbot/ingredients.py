"""Ingredients"""
from enum import Enum
from dataclasses import dataclass
from typing import NamedTuple


# density relative to that of water
DENSITY_WATER = 1
DENSITY_JUICE = DENSITY_WATER
DENSITY_SIRUP = DENSITY_WATER
DENSITY_SPIRIT = DENSITY_WATER

class IngredientType(Enum):
    """Type of the ingredient"""
    SPIRIT = "spirit"
    JUICE = "juice"
    SIRUP = "sirup"
    OTHER = "other"
    STIRR = "stirr"
    SUGAR = "sugar"

@dataclass
class Ingredient():
    """Ingredient that can be added to a recipe"""
    identifier:str
    name: str
    type: IngredientType
    color: int

    def alcoholic(self) -> bool:
        """Returns whether the ingredient contains alcohol"""
        return self.type == IngredientType.SPIRIT

    @property
    def density(self):
        """Get the density of this ingredient"""
        if self.type == IngredientType.JUICE:
            self.density = DENSITY_JUICE
        elif self.type == IngredientType.SIRUP:
            self.density = DENSITY_SIRUP
        elif self.type == IngredientType.SPIRIT:
            self.density = DENSITY_SPIRIT
        else:
            # no info, so just assume water
            self.density = DENSITY_WATER


Stir = Ingredient('ruehren',        'Rühren',               IngredientType.STIRR,   0xDDE3E1D3   )
Sugar = Ingredient('sugar',         'Zucker',               IngredientType.SUGAR,   0x55FFFFFF   )

_ingredients = [
    Ingredient('rum weiss',         'Weißer Rum',           IngredientType.SPIRIT,  0x55FFFFFF    ),
    Ingredient('rum braun',         'Brauner Rum',          IngredientType.SPIRIT,  0x99D16615    ),
    Ingredient('vodka',             'Vodka',                IngredientType.SPIRIT,  0x55FFFFFF    ),
    Ingredient('tequila',           'Tequila',              IngredientType.SPIRIT,  0x55FFFFFF    ),
    Ingredient('gin',               'Gin',                  IngredientType.SPIRIT,  0x55FFFFFF    ),
    Ingredient('saft zitrone',      'Zitronensaft',         IngredientType.JUICE,   0xAAF7EE99    ),
    Ingredient('saft limette',      'Limettensaft',         IngredientType.JUICE,   0xFF9FBF36    ),
    Ingredient('saft orange',       'Orangensaft',          IngredientType.JUICE,   0xDDFACB23    ),
    Ingredient('saft ananas',       'Annanassaft',          IngredientType.JUICE,   0xFFFAEF23    ),
    Ingredient('tripple sec',       'Tripple Sec / Curacao',IngredientType.SPIRIT,  0x44FACB23    ),
    Ingredient('sirup kokos',       'Kokos Sirup',          IngredientType.SIRUP,   0xDDE3E1D3    ),
    Ingredient('sirup curacao',     'Blue Curacao Sirup',   IngredientType.SIRUP,   0xFF2D57E0    ),
    Ingredient('sirup grenadine',   'Grenadine Sirup',      IngredientType.SIRUP,   0xDD911111    ),
    Ingredient('saft cranberry',    'Cranberrysaft',        IngredientType.JUICE,   0x55F07373    ),
    Ingredient('milch',             'Milch',                IngredientType.OTHER,   0xFFF7F7F7    ),
    Ingredient('kokosmilch',        'Kokosmilch',           IngredientType.OTHER,   0xFFF7F7F7    ),
    Ingredient('sahne',             'Sahne',                IngredientType.OTHER,   0xFFF7F7F7    ),
    Ingredient('sirup vanille',     'Vanille Sirup',        IngredientType.OTHER,   0x99D2A615    ),
    Ingredient('saft maracuja',     'Maracujasaft',         IngredientType.JUICE,   0xAA0CC73     ),
    Ingredient('sirup zucker',      'Zuckersirup',          IngredientType.SIRUP,   0xDDE3E1D3    ),
    Ingredient('sirup maracuja',    'Maracujasirup',        IngredientType.JUICE,   0xDD0CC73     ),

    Stir,
    Sugar
]

# for faster access
_ingredientsByIdentifier = {
    ingredient.identifier: ingredient
    for ingredient in _ingredients
}


def by_identifier(identifier: str):
    """Get an ingredient based on its identifier"""
    return _ingredientsByIdentifier[identifier]


def get_list(only_available = False, only_normal = False, only_weighed = False) -> list[Ingredient]:
    """Get list of ingredients
    :param only_available: If set to true,
    only return ingredients that are currently connected to ports
    :param only_normal: If set to true, only return ingredients that are pumped
    :param only_weighed: If set to true, only return ingredients that are added by weight    
    """
    filtered = []
    for ingredient in _ingredients:
        if only_available and not ingredient.available():
            continue
        if IngredientType.STIRR == ingredient.type:
            if only_normal is True:
                continue
            if only_weighed is True:
                continue
        if IngredientType.SUGAR == ingredient.type:
            if only_normal is True:
                continue
        filtered.append(ingredient)
    return filtered
