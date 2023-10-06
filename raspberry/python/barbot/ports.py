import yaml
from . import directories
from . import ingredients
from typing import Dict

Count = 12
_Filename = 'ports.yaml'
_Filepath = directories.join(directories.data, _Filename)
List: Dict[int, ingredients.Ingredient]= {i: None for i in range(Count)}


def port_of_ingredient(ingredient: ingredients.Ingredient):
    """Get the port where to find the given ingredient
    
        :param ingredient: The ingredient to look for
        :return: The index of the port of the ingredient, None if it it was not found 
    """
    global List
    for port, list_ingredient in List.items():
        if list_ingredient == ingredient:
            return port
    return None


def save():
    """ Save the current port configuration

        :return: True if saving was successfull, False otherwise
    """
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
    """ Load the current port configuration

        :return: True if loading was successfull, False otherwise
    """
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
