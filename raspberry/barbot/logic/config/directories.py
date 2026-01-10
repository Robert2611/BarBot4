"""Directory management"""

__all__ = [
    "data_directory",
    "fixed_recipes_directory",
    "recipes_directory",
    "old_recipes_directory",
    "orders_directory",
    "log_directory",
]

import os

# Data directory
data_directory = os.path.expanduser('~/.config/barbot/')

def _create_if_not_exists(*path):
    """Make directory if it does not exist
    :param path: Path elements
    :returns: The directory"""
    folder = os.path.join("", *path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


# Create necessary directories
fixed_recipes_directory = _create_if_not_exists(data_directory, "fixed_recipes")
recipes_directory = _create_if_not_exists(data_directory, "recipes")
old_recipes_directory = _create_if_not_exists(data_directory, "old_recipes")
orders_directory = _create_if_not_exists(data_directory, "orders")
log_directory = _create_if_not_exists(data_directory, "log")
