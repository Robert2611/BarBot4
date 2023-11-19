import os
data = os.path.expanduser('~/.barbot/')

def make(*path):
    global base
    dir = os.path.join(base, *path)
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def make_absolute(*path):
    dir = os.path.join("", *path)
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def join(dir, *file_or_folder):
    return os.path.join(dir, *file_or_folder)


fixed_recipes = make_absolute(data, "fixed_recipes")
recipes = make_absolute(data, "recipes")
old_recipes = make_absolute(data, "old_recipes")
orders = make_absolute(data, "orders")
log = make_absolute(data, "log")

# Get version from "version.txt"
__version_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),"../../version.txt")
try:
    with open(__version_file, "r") as f:
        version = f.read()
except Exception:
    version = None