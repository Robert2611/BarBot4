#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3 as lite


class database(object):
    def __init__(self, filename):
        self.filename = filename
        self.con = None
        self.isConnected = False

    def open(self):
        if self.isConnected:
            return
        self.con = lite.connect(self.filename)
        self.con.row_factory = lite.Row
        self.cursor = self.con.cursor()
        self.isConnected = True

    def close(self):
        if(self.con != None):
            self.con.close()
        self.con = None
        self.cursor = None
        self.isConnected = False

    def getIngredientOfPort(self):
        # only open/close if called while not connected
        wasOpen = self.isConnected
        if not wasOpen:
            self.open()
        self.cursor.execute("""
			SELECT ingredient as iid, id as port
			FROM Ports
		""")
        res = dict()
        for ingredient in self.cursor.fetchall():
            res[ingredient["port"]] = ingredient["iid"]
        if not wasOpen:
            self.close()
        return res

    def getPortAndCalibration(self, iid):
        self.open()
        self.cursor.execute("""
			SELECT p.id as port,  i.calibration AS calibration
			FROM Ports p
			JOIN Ingredients i
			ON p.ingredient = i.id
			WHERE i.id = :iid
		""", {"iid": iid})
        res = self.cursor.fetchone()
        if res == None:
            self.close()
            return None
        return dict(res)

    def getAllIngredients(self):
        self.open()
        self.cursor.execute("""
			SELECT i.id, i.name, i.type, i.calibration, p.id as port
			FROM Ingredients i
			LEFT JOIN Ports p
			ON p.ingredient = i.id
		""")
        res = dict()
        for ingredient in self.cursor.fetchall():
            res[ingredient["id"]] = dict(ingredient)
        self.close()
        return res

    def getRecipes(self):
        self.open()
        self.cursor.execute("""
			SELECT name, id
			FROM Recipes
			WHERE successor_id IS NULL
		""")
        recipes = []
        for row in self.cursor.fetchall():
            recipe = dict(row)
            self.addAllRecipeItems(recipe)
            recipes.append(recipe)
        self.close()
        return recipes

    def addAllRecipeItems(self, recipe):
        availableIngredients = self.getIngredientOfPort().values()
        self.cursor.execute("""
			SELECT ri.id, ri.amount, i.name, ri.Ingredient AS iid, i.calibration AS calibration, p.id as port
			FROM RecipeItems ri
			JOIN Ingredients i
			ON i.id = ri.Ingredient
			LEFT JOIN Ports p
			ON p.ingredient = ri.Ingredient
			WHERE ri.Recipe = :rid
		""", {"rid": recipe["id"]})
        rows = self.cursor.fetchall()
        recipe["items"] = []
        if len(rows) == 0:
            recipe["available"] = False
            return
        recipe_available = True
        for item_row in rows:
            # get all fields from the query and make a dictionary
            item = dict(item_row)
            item["available"] = item["iid"] in availableIngredients
            if not item["available"]:
                recipe_available = False
            recipe["items"].append(item)
        recipe["available"] = recipe_available

    def getRecipe(self, rid):
        self.open()
        self.cursor.execute("""
			SELECT name, id, instruction
			FROM Recipes
			WHERE successor_id IS NULL
			AND id = :rid
		""", {"rid": rid})
        res = self.cursor.fetchone()
        # does the recipe exits?
        if res == None:
            self.close()
            return None
        recipe = dict(res)
        # fetch items
        self.addAllRecipeItems(recipe)
        self.close()
        return recipe

    # returns: new recipe id
    def createOrUpdateRecipe(self, name, instruction, old_rid=-1):
        self.open()
        self.cursor.execute("""
			INSERT INTO Recipes ( name, instruction, successor_id )
			VALUES ( :name, :instruction, NULL )
		""", {"name": name, "instruction" : instruction})
        self.con.commit()
        new_rid = self.cursor.lastrowid
        if(old_rid >= 0):
            # set newly created recipe as successor for current recipe
            self.cursor.execute("""
				UPDATE Recipes
				SET successor_id = :new_rid
				WHERE id = :old_rid
			""", {"old_rid": old_rid, "new_rid": new_rid})
            self.con.commit()
        self.close()
        return new_rid

    def addRecipeItems(self, rid, items):
        self.open()
        for item in items:
            self.cursor.execute("""
				INSERT INTO RecipeItems ( Recipe, ingredient, amount )
				VALUES ( :rid, :ingredient, :amount )
			""", {"rid": rid, "ingredient": item["ingredient"], "amount": item["amount"]})
        self.con.commit()
        self.close()

    def recipeChanged(self, rid, name, items, instruction):
        self.open()
        self.cursor.execute("""
			SELECT name, instruction
			FROM Recipes
			WHERE id = :rid
		""", {"rid": rid})
        recipe_in_database = self.cursor.fetchone()
        # recipe not found, so it must be different
        if recipe_in_database == None:
            self.close()
            return True
        # name has changed
        elif recipe_in_database["name"] != name:
            self.close()
            return True
        #instruction has changed
        elif recipe_in_database["instruction"] != instruction:
            self.close()
            return True
        self.cursor.execute("""
			SELECT id, ingredient, amount
			FROM RecipeItems
			WHERE recipe = :rid
			ORDER BY id ASC
		""", {"rid": rid})
        items_in_database = self.cursor.fetchall()
        if len(items_in_database) != len(items):
            self.close()
            return True

        for i in range(0, len(items_in_database)):
            if items_in_database[i]["ingredient"] != items[i]["ingredient"] or \
                    items_in_database[i]["amount"] != items[i]["amount"]:
                # item has changed
                self.close()
                return True
        self.close()
        return False

    def startOrder(self, rid):
        self.open()
        self.cursor.execute("""
			INSERT INTO Orders ( recipe, started, status )
			VALUES ( :rid, DATETIME('now'), 0 )
		""", {"rid": rid})
        self.con.commit()
        self.close()

    def closeOrder(self, rid):
        self.open()
        self.cursor.execute("""
			UPDATE Orders
			SET finished = DATETIME('now'), status = 1
			WHERE recipe = :rid
		""", {"rid": rid})
        self.con.commit()
        self.close()

    def clearOrders(self):
        self.open()
        self.cursor.execute("""
			UPDATE Orders
			SET status = -1
			WHERE status = 0
		""")
        self.con.commit()
        self.close()

    def setPorts(self, ports):
        self.open()
        for port, iid in ports.items():
            self.cursor.execute("""
				UPDATE Ports
				SET ingredient = :iid
				WHERE id = :port
			""", {"iid": iid, "port": port})
        self.con.commit()
        self.close()

    def setCalibration(self, port, calibration):
        self.open()
        self.cursor.execute("""
			UPDATE Ingredients
			SET calibration = :calibration
			WHERE id = (
						SELECT ingredient
						FROM Ports
						WHERE id = :port
						)
		""", {'calibration': calibration, 'port': port})
        self.con.commit()
        self.close()

    def getStrSetting(self, name):
        self.open()
        self.cursor.execute("""
			SELECT value
			FROM Settings
			WHERE name=:name
		""", {'name': name})
        res = self.cursor.fetchone()
        self.close()
        return res["value"]

    def getIntSetting(self, name):
        return int(self.getStrSetting(name))

    def getOrderedCocktailCount(self, date):
        self.open()
        self.cursor.execute("""
			SELECT r.name, r.id AS rid, COUNT(*) AS count
			FROM Orders O
			JOIN Recipes r
			ON r.id = O.recipe
			WHERE O.started >= DATETIME(:date, "+0.5 days")
			AND O.started < DATETIME(:date, "+1.5 days")
			GROUP BY r.id
			ORDER BY count DESC
		""", {'date': date})
        res = [dict(row) for row in self.cursor.fetchall()]
        return res

    def getOrderedIngredientsAmount(self, date):
        self.open()
        self.cursor.execute("""
			SELECT i.name AS ingredient, i.id AS iid, SUM(ri.amount)/100 AS liters
			FROM RecipeItems ri
			JOIN Orders o
			ON o.recipe = ri.recipe
			JOIN Ingredients i
			ON i.id = ri.ingredient
			WHERE O.started >= DATETIME(:date, "+0.5 days")
			AND O.started < DATETIME(:date, "+1.5 days")
			GROUP BY i.id
			ORDER BY liters DESC
		""", {'date': date})
        res = [dict(row) for row in self.cursor.fetchall()]
        return res

    def getOrderedCocktailsByTime(self, date):
        self.open()
        self.cursor.execute("""
			SELECT strftime('%Y-%m-%d %H',o.started) AS hour, count(*) AS count
			FROM Orders o
			WHERE O.started >= DATETIME(:date, "+0.5 days")
			AND O.started < DATETIME(:date, "+1.5 days")
			GROUP BY hour
		""", {'date': date})
        res = [dict(row) for row in self.cursor.fetchall()]
        return res

    def getPartyDates(self):
        self.open()
        self.cursor.execute("""
			SELECT partydate, ordercount
			FROM (
				SELECT date(o.started, "-0.5 days") AS partydate,  count(o.id) as ordercount
				FROM Orders o
				GROUP BY partydate
				ORDER BY partydate DESC
			)
			WHERE ordercount > 10
		""")
        res = [dict(row) for row in self.cursor.fetchall()]
        return res
