import os
import yaml

Count = 12
Filename = 'ports.yml'

def Save(self):
    try:
        with open(self.Filepath, 'w') as outfile:
            data = {}
            for port, ingredient in self.List.items():
                if ingredient is not None:
                    data[port] = ingredient.Identifier
                else:
                    data[port] = None
            yaml.dump(data, outfile, default_flow_style=False)
            return True
    except:
        return False

def Load(self):
    try:
        with open(self.Filepath, 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
            self.List = {}
            for port, identifier in data.items():
                if identifier is None or identifier == "":
                    self.List[port] = None
                else:
                    self.List[port] = IngredientsByIdentifier[identifier]
            return True
    except:
        return False

script_dir = os.path.dirname(__file__)
Filepath = os.path.join(script_dir, "..", "..",  "data", Filename)
success = Load()
#if loading failed initialize list with nothing connected
if not success:
    List = {i: None for i in range(Count)}
    Save()