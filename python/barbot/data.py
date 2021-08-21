import yaml
import os
from enum import Enum


class IngregientType(Enum):
    Spirit = 0
    Juice = 1
    Sirup = 2
    Other = 3
    Stirr = 255
    Empty = 256


class Ingredient(object):
    def __init__(self, Id: int, Name: str, Type: IngregientType, Color: int):
        self.Id = Id
        self.Name = Name
        self.Type = Type
        self.Color = Color


class Ports(object):
    Count = 12
    Filename = 'ports.yml'

    def __init__(self):
        script_dir = os.path.dirname(__file__)
        self.Filepath = os.path.join(
            script_dir, "..", "..",  "data", self.Filename)
        self.List = {i: IngredientsById[-1] for i in range(self.Count)}

    def Write(self):
        with open(self.Filepath, 'w') as outfile:
            data = {port: ingredient.Id for port,
                    ingredient in self.List.items()}
            yaml.dump(data, outfile, default_flow_style=False)

    def Read(self):
        with open(self.Filepath, 'r') as outfile:
            data = yaml.load(self.Filepath)
        self.List = {port: IngredientsById[id] for port, id in data.items()}


Ingredients = [
    Ingredient(-1, 'Leer', IngregientType.Empty, 0x00000000),
    Ingredient(1, 'Weißer Rum', IngregientType.Spirit, 0x55FFFFFF),
    Ingredient(2, 'Brauner Rum', IngregientType.Spirit, 0x99D16615),
    Ingredient(3, 'Vodka', IngregientType.Spirit, 0x55FFFFFF),
    Ingredient(4, 'Tequila', IngregientType.Spirit, 0x55FFFFFF),

    Ingredient(6, 'Zitronensaft', IngregientType.Juice, 0xAAF7EE99),
    Ingredient(7, 'Limettensaft', IngregientType.Juice, 0xFF9FBF36),
    Ingredient(8, 'Orangensaft', IngregientType.Juice, 0xDDFACB23),
    Ingredient(9, 'Annanassaft', IngregientType.Juice, 0xFFFAEF23),
    Ingredient(10, 'Tripple Sec', IngregientType.Sirup, 0x44FACB23),
    Ingredient(11, 'Kokossirup', IngregientType.Sirup, 0xDDE3E1D3),
    Ingredient(12, 'Blue Curacao', IngregientType.Sirup, 0xFF2D57E0),
    Ingredient(13, 'Grenadine', IngregientType.Sirup, 0xDD911111),
    Ingredient(14, 'Cranberrysaft', IngregientType.Juice, 0x55F07373),
    Ingredient(15, 'Milch', IngregientType.Other, 0xFFF7F7F7),
    Ingredient(16, 'Maracujasaft', IngregientType.Juice, 0xAA0CC73),
    Ingredient(17, 'Zuckersirup', IngregientType.Sirup, 0xDDE3E1D3),

    Ingredient(255, 'Rühren', IngregientType.Sirup, 0xDDE3E1D3),
]

# for faster access
IngredientsById = {ingredient.Id: ingredient for ingredient in Ingredients}

p = Ports()
p.Read()
print(p.List)
