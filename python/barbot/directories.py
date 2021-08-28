import os
_script_dir = os.path.dirname(__file__)
base = os.path.join(_script_dir, "..", "..")


def make(*path):
    dir = os.path.join(base, *path)
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir


def make_absolute(*path):
    dir = os.path.join("", *path)
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir


data = make("data")
fixed_recipes = make_absolute(data, "fixed_recipes")
recipes = make_absolute(data, "recipes")
old_recipes = make_absolute(data, "old_recipes")
orders = make_absolute(data, "orders")
log = make_absolute(data, "log")


def join(dir, *file_or_folder):
    return os.path.join(dir, *file_or_folder)
