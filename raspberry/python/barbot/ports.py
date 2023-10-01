import yaml
import typing
from . import directories
from . import ingredients

Count = 12
_Filename = 'ports.yaml'
_Filepath = directories.join(directories.data, _Filename)
List: dict[int, ingredients.Ingredient]= {i: None for i in range(Count)}


def port_of_ingredient(ingredient: ingredients.Ingredient):
    global List
    for port, list_ingredient in List.items():
        if list_ingredient == ingredient:
            return port
    return None


def save():
    global _Filepath, List
    try:
        with open(_Filepath, 'w') as outfile:
            data = {}
            for port, ingredient in List.items():
                if ingredient is not None:
                    data[port] = ingredient.identifier
                else:
                    data[port] = None
            yaml.dump(data, outfile, default_flow_style=False)
            return True
    except Exception as ex:
        return False


def load():
    global _Filepath, List
    try:
        with open(_Filepath, 'r') as file:
            data:dict[int, str] = yaml.load(file, Loader=yaml.FullLoader)
            List = {}
            for port, identifier in data.items():
                if identifier is None or identifier == "":
                    List[port] = None
                else:
                    List[port] = ingredients.by_identifier(identifier)
            return True
    except:
        return False


# if loading failed save the default value to file
if not load():
    save()
