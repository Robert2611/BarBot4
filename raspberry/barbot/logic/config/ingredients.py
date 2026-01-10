"""Barbot ingredients configuration"""

__all__ = [
    "IngredientType",
    "Ingredient",
    "Stir",
    "Sugar",
    "get_ingredient_by_identifier",
    "get_all_ingredients",
]

from dataclasses import dataclass
from enum import Enum
from typing import List

# Density constants relative to water
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
class Ingredient:
    """Ingredient that can be added to a recipe"""
    identifier: str
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
            return DENSITY_JUICE
        if self.type == IngredientType.SIRUP:
            return DENSITY_SIRUP
        if self.type == IngredientType.SPIRIT:
            return DENSITY_SPIRIT
        # no info, so just assume water
        return DENSITY_WATER


# Predefined ingredients
Stir = Ingredient('ruehren', 'Rühren', IngredientType.STIRR, 0xDDE3E1D3)
Sugar = Ingredient('zucker', 'Zucker', IngredientType.SUGAR, 0x55FFFFFF)

_ingredients = [
    Ingredient('rum weiss', 'Weißer Rum', IngredientType.SPIRIT, 0x55FFFFFF),
    Ingredient('rum braun', 'Brauner Rum', IngredientType.SPIRIT, 0x99D16615),
    Ingredient('vodka', 'Vodka', IngredientType.SPIRIT, 0x55FFFFFF),
    Ingredient('tequila', 'Tequila', IngredientType.SPIRIT, 0x55FFFFFF),
    Ingredient('gin', 'Gin', IngredientType.SPIRIT, 0x55FFFFFF),
    Ingredient('saft zitrone', 'Zitronensaft', IngredientType.JUICE, 0xAAF7EE99),
    Ingredient('saft limette', 'Limettensaft', IngredientType.JUICE, 0xFF9FBF36),
    Ingredient('saft orange', 'Orangensaft', IngredientType.JUICE, 0xDDFACB23),
    Ingredient('saft ananas', 'Annanassaft', IngredientType.JUICE, 0xFFFAEF23),
    Ingredient('tripple sec', 'Tripple Sec / Curacao', IngredientType.SPIRIT, 0x44FACB23),
    Ingredient('sirup kokos', 'Kokos Sirup', IngredientType.SIRUP, 0xDDE3E1D3),
    Ingredient('sirup curacao', 'Blue Curacao Sirup', IngredientType.SIRUP, 0xFF2D57E0),
    Ingredient('sirup grenadine', 'Grenadine Sirup', IngredientType.SIRUP, 0xDD911111),
    Ingredient('saft cranberry', 'Cranberrysaft', IngredientType.JUICE, 0x55F07373),
    Ingredient('milch', 'Milch', IngredientType.OTHER, 0xFFF7F7F7),
    Ingredient('kokosmilch', 'Kokosmilch', IngredientType.OTHER, 0xFFF7F7F7),
    Ingredient('sahne', 'Sahne', IngredientType.OTHER, 0xFFF7F7F7),
    Ingredient('sirup vanille', 'Vanille Sirup', IngredientType.OTHER, 0x99D2A615),
    Ingredient('saft maracuja', 'Maracujasaft', IngredientType.JUICE, 0xAA0CC73),
    Ingredient('sirup zucker', 'Zuckersirup', IngredientType.SIRUP, 0xDDE3E1D3),
    Ingredient('sirup maracuja', 'Maracujasirup', IngredientType.SIRUP, 0xDD0CC73),
    Ingredient('sirup pfirsich', 'Pfirsichsirup', IngredientType.SIRUP, 0xDD0CC73),
    Ingredient('pfirsich likoer', 'Pfirsichlikör', IngredientType.SPIRIT, 0x44FAAB23),
    Ingredient('sirup mandel', 'Mandel Sirup', IngredientType.SIRUP, 0xDDE3E1D3),
    Stir,
    Sugar
]


def get_ingredient_by_identifier(identifier: str):
    """Get an ingredient based on its identifier"""
    for ingredient in _ingredients:
        if identifier == ingredient.identifier:
            return ingredient
    return None


def get_all_ingredients() -> List[Ingredient]:
    """Get all predefined ingredients"""
    return _ingredients.copy()
