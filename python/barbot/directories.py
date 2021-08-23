import os
_script_dir = os.path.dirname(__file__)
base = os.path.join(_script_dir, "..", "..")
data = os.path.join(base, "data")

recipes = os.path.join(base, "data", "recipes")
if not os.path.exists(recipes):
    os.mkdir(recipes)

old_recipes = os.path.join(base, "data", "old_recipes")
if not os.path.exists(old_recipes):
    os.mkdir(old_recipes)

import_recipes = os.path.join(base, "data", "import_recipes")
if not os.path.exists(import_recipes):
    os.mkdir(import_recipes)


def relative(*path):
    global base
    return os.path.join(base, *path)


def directory_exists(*path):
    global base
    relative = os.path.join(base, *path)
    return os.path.exists(relative)
