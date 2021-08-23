import os
import yaml
from barbot import directories
from barbot.data import IngredientsByIdentifier

Count = 12
_Filename = 'ports.yml'
_Filepath = directories.relative("data", _Filename)
List = {i: None for i in range(Count)}


def save():
    global _Filepath, List
    try:
        with open(_Filepath, 'w') as outfile:
            data = {}
            for port, ingredient in List.items():
                if ingredient is not None:
                    data[port] = ingredient.Identifier
                else:
                    data[port] = None
            yaml.dump(data, outfile, default_flow_style=False)
            return True
    except:
        return False


def load():
    global _Filepath, List
    try:
        with open(_Filepath, 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
            List = {}
            for port, identifier in data.items():
                if identifier is None or identifier == "":
                    List[port] = None
                else:
                    List[port] = IngredientsByIdentifier[identifier]
            return True
    except:
        return False


# if loading failed save the default value to file
if not load():
    save()
