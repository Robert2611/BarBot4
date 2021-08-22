import yaml
import os
from enum import Enum
from pprint import pprint
from datetime import datetime

def in_data_dir(*paths):
    script_dir = os.path.dirname(__file__)
    filepath = os.path.join(script_dir,"..","..","data", *paths)
    return filepath

class IngregientType(Enum):
    Spirit = "spirit"
    Juice = "juice"
    Sirup = "sirup"
    Other = "other"
    Stirr = "stirr"


class Ingredient(object):
    def __init__(self, Identifier:str, Name: str, Type: IngregientType, Color: int):
        self.Identifier = Identifier
        self.Name = Name
        self.Type = Type
        self.Color = Color

class RecipeItem(object):
    def __init__(self, Ingredient:Ingredient, Amount:int):
        self.Ingredient = Ingredient
        self.Amount = Amount

class Recipe(object):
    def __init__(self):
        self.Items = []
        self.Id = -1
        self.Name = "Neues Rezept"
        self.Created = datetime.now()
        self.Instruction = ""

    def Load(self, folder:str, filename:str):
        try:
            filepath = in_data_dir(folder, filename)
            with open(filepath, 'r') as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
            #first six letters are the id
            self.Id = int(filename[:6])
            # skip id + separator, do not include '.yaml'
            self.Name = filename[7:-5]
            self.Created = data["created"]
            self.Instruction = data["instruction"]
            self.Items = []
            for item_data in data["items"]:
                #all errors are handled by the try catch
                ingredient = IngredientsByIdentifier[item_data["ingredient"]]
                item = RecipeItem(ingredient, item_data["amount"])
                self.Items.append(item)
            return True
        except Exception as ex:
            print("Error: {0}".format(ex))
            return False
            
Ingredients = [
    Ingredient('rum weiss', 'Weißer Rum', IngregientType.Spirit, 0x55FFFFFF),
    Ingredient('rum braun', 'Brauner Rum', IngregientType.Spirit, 0x99D16615),
    Ingredient('vodka', 'Vodka', IngregientType.Spirit, 0x55FFFFFF),
    Ingredient('tequila', 'Tequila', IngregientType.Spirit, 0x55FFFFFF),

    Ingredient('saft zitrone', 'Zitronensaft', IngregientType.Juice, 0xAAF7EE99),
    Ingredient('saft limette', 'Limettensaft', IngregientType.Juice, 0xFF9FBF36),
    Ingredient('saft orange', 'Orangensaft', IngregientType.Juice, 0xDDFACB23),
    Ingredient('saft ananas', 'Annanassaft', IngregientType.Juice, 0xFFFAEF23),
    Ingredient('tripple sec', 'Tripple Sec', IngregientType.Sirup, 0x44FACB23),
    Ingredient('sirup kokos', 'Kokossirup', IngregientType.Sirup, 0xDDE3E1D3),
    Ingredient('sirup curacao', 'Blue Curacao', IngregientType.Sirup, 0xFF2D57E0),
    Ingredient('sirup grenadine', 'Grenadine', IngregientType.Sirup, 0xDD911111),
    Ingredient('saft cranberry', 'Cranberrysaft', IngregientType.Juice, 0x55F07373),
    Ingredient('milch', 'Milch', IngregientType.Other, 0xFFF7F7F7),
    Ingredient('saft maracuja', 'Maracujasaft', IngregientType.Juice, 0xAA0CC73),
    Ingredient('sirup zucker', 'Zuckersirup', IngregientType.Sirup, 0xDDE3E1D3),

    Ingredient('ruehren', 'Rühren', IngregientType.Sirup, 0xDDE3E1D3),
]

# for faster access
IngredientsByIdentifier = {ingredient.Identifier: ingredient for ingredient in Ingredients}

if __name__ == '__main__':
    p =  Ports()
    r = Recipe()
    success = r.Load("recipes_to_import","000058 Tequila Sunrise.yaml")
    print(success)
    pprint(r.Created)