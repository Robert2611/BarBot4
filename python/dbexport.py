#!/usr/bin/env python3
import sqlite3 as lite
import os
import pprint
import yaml
from datetime import datetime
from barbot import directories
from barbot import recipes


def db_fetch(sql):
    con = lite.connect(directories.relative("bar_bot.sqlite"))
    con.row_factory = lite.Row
    cursor = con.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    con.close()
    return result


def get_recipe_items(id):
    sql = """
        SELECT ingredient_id, amount
        FROM recipe_items
        WHERE recipe_id = {0}
        """.format(id)
    items = []
    for row in db_fetch(sql):
        items.append({
            "ingredient": IngredientIdToIdentifier[row["ingredient_id"]],
            "amount": row["amount"]
        })
    return items


def get_recipes():
    sql = """
        SELECT  id, name, created, instruction
        FROM recipes
        WHERE successor_id IS NULL
    """
    recipes = [dict(row) for row in db_fetch(sql)]
    for recipe in recipes:
        recipe["created"] = datetime.strptime(
            recipe["created"], "%Y-%m-%d %H:%M:%S")
        recipe["items"] = get_recipe_items(recipe["id"])
    return recipes


IngredientIdToIdentifier = {
    1: 'rum weiss',
    2: 'rum braun',
    3: 'vodka',
    4: 'tequila',

    6: 'saft zitrone',
    7: 'saft limette',
    8: 'saft orange',
    9: 'saft ananas',
    10: 'tripple sec',
    11: 'sirup kokos',
    12: 'sirup curacao',
    13: 'sirup grenadine',
    14: 'saft cranberry',
    15: 'milch',
    16: 'saft maracuja',
    17: 'sirup zucker',

    255: 'ruehren'
}

for recipe in get_recipes():
    name = recipes.get_reipe_filename(recipe["id"], recipe["name"])
    # id and name are coded in the filename, remove it to avoid redundancy
    recipe.pop("id")
    recipe.pop("name")
    filename = os.path.join(directories.import_recipes, name)
    with open(filename, 'w') as outfile:
        yaml.dump(recipe, outfile, default_flow_style=False)
