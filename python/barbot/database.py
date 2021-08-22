
class Database(object):
    con: lite.Connection
    filename: str
    _is_connected: bool = False

    def __init__(self, filename):
        self.filename = filename

    def open(self):
        if self._is_connected:
            return
        self.con = lite.connect(self.filename)
        self.con.row_factory = lite.Row
        self.cursor = self.con.cursor()
        self._is_connected = True

    def close(self):
        if(self.con is not None):
            self.con.close()
        self.con = None
        self.cursor = None
        self._is_connected = False

    def ingredient_of_port(self):
        # only open/close if called while not connected
        wasOpen = self._is_connected
        if not wasOpen:
            self.open()
        self.cursor.execute("""
			SELECT ingredient_id, id as port
			FROM ports
		""")
        res = dict()
        for ingredient in self.cursor.fetchall():
            res[ingredient["port"]] = ingredient["ingredient_id"]
        if not wasOpen:
            self.close()
        return res

    def port_and_calibration(self, ingredient_id):
        self.open()
        self.cursor.execute("""
			SELECT  p.id as port, 
                    i.calibration AS calibration,
                    i.name AS name
			FROM ports p
			JOIN ingredients i
			ON p.ingredient_id = i.id
			WHERE i.id = :ingredient_id
		""", {"ingredient_id": ingredient_id})
        res = self.cursor.fetchone()
        if res == None:
            self.close()
            return None
        return dict(res)

    def list_ingredients(self, only_available=False, special_ingredients=True):
        self.open()
        sql = """
			SELECT i.id, i.name, i.type, i.calibration, p.id as port, i.color
			FROM ingredients i
			LEFT JOIN ports p
			ON p.ingredient_id = i.id
		"""
        if only_available:
            sql += "WHERE i.id in (SELECT ingredient_id FROM ports)"
        if not special_ingredients:
            sql += " AND " if only_available else "WHERE "
            sql += "i.type<>'special'"

        self.cursor.execute(sql)
        res = dict()
        for ingredient in self.cursor.fetchall():
            res[ingredient["id"]] = dict(ingredient)
        self.close()
        return res

    def list_recipes(self, filter: RecipeFilter):
        sql = """
            SELECT  r.name AS name,
                    r.id AS id,
                    r.instruction AS instruction,
                    (
                        SELECT MIN(ri.ingredient_id in (SELECT ingredient_id FROM ports)) > 0
                        FROM recipe_items ri
                        WHERE ri.recipe_id = r.id
                    ) AS available
            FROM recipe_items ri
            JOIN ingredients i
            ON i.id = ri.ingredient_id
            JOIN recipes r
            ON r.id == ri.recipe_id
            WHERE r.successor_id IS NULL
        """
        sql = sql + "GROUP BY ri.recipe_id\n"
        # filter alcoholic
        sql = sql + "HAVING MAX(i.type = 'spirit') = "
        if filter.Alcoholic:
            sql = sql + "1\n"
        else:
            sql = sql + "0\n"
        # available
        if filter.AvailableOnly:
            sql = sql + "AND MIN(i.id in (SELECT ingredient_id FROM ports))\n"
        # ordering
        ordering = False
        if filter.Order == RecipeOrder.Newest:
            ordering = "ORDER BY id "
        if ordering:
            # sorting DESC or ASC
            if filter.DESC:
                sql = sql + ordering + "DESC\n"
            else:
                sql = sql + ordering + "ASC\n"
        self.open()
        self.cursor.execute(sql)
        recipes = []
        for row in self.cursor.fetchall():
            recipe = Recipe(row["name"], row["id"],
                            row["instruction"], row["available"])
            self._add_items_to_recipe(recipe)
            recipes.append(recipe)
        self.close()
        return recipes

    def _add_items_to_recipe(self, recipe: Recipe):
        self.cursor.execute("""
			SELECT  ri.id,
                    ri.amount,
                    i.name,
                    i.color,
                    ri.ingredient_id,
                    i.calibration AS calibration,
                    p.id as port,
                    (i.id in (SELECT ingredient_id FROM ports)) AS available
			FROM recipe_items ri
			JOIN ingredients i
			ON i.id = ri.ingredient_id
			LEFT JOIN ports p
			ON p.ingredient_id = ri.ingredient_id
			WHERE ri.recipe_id = :rid
		""", {"rid": recipe.id})
        for row in self.cursor.fetchall():
            item = RecipeItem()
            item.id = row["id"]
            item.amount = row["amount"]
            item.name = row["name"]
            item.ingredient_id = row["ingredient_id"]
            item.calibration = row["calibration"]
            item.port = row["port"]
            item.available = row["available"]
            item.color = row["color"]
            recipe.items.append(item)

    def recipe(self, rid):
        self.open()
        self.cursor.execute("""
			SELECT  name,
                    id,
                    instruction,
                    (
                        SELECT MIN(ri.ingredient_id in (SELECT ingredient_id FROM ports)) > 0
                        FROM recipe_items ri
                        WHERE ri.recipe_id = r.id
                    ) AS available
			FROM recipes r
			WHERE successor_id IS NULL
			AND id = :rid
		""", {"rid": rid})
        res = self.cursor.fetchone()
        # does the recipe exits?
        if res == None:
            self.close()
            return None
        recipe = Recipe(res["name"], res["id"],
                        res["instruction"], res["available"])
        # fetch items
        self._add_items_to_recipe(recipe)
        self.close()
        return recipe

    # returns: new recipe id
    def create_or_update_recipe(self, name, instruction, old_rid=-1):
        self.open()
        self.cursor.execute("""
			INSERT INTO recipes ( name, instruction, successor_id )
			VALUES ( :name, :instruction, NULL )
		""", {"name": name, "instruction": instruction})
        self.con.commit()
        new_rid = self.cursor.lastrowid
        if(old_rid is not None and old_rid >= 0):
            # set newly created recipe as successor for current recipe
            self.cursor.execute("""
				UPDATE recipes
				SET successor_id = :new_rid
				WHERE id = :old_rid
			""", {"old_rid": old_rid, "new_rid": new_rid})
            self.con.commit()
        self.close()
        return new_rid

    def remove_recipe(self, rid):
        self.open()
        self.cursor.execute("""
            UPDATE recipes
            SET successor_id = -1
            WHERE id = :rid
        """, {"rid": rid})
        self.con.commit()
        self.close()

    def _insert_recipe_items(self, rid, items):
        self.open()
        for item in items:
            self.cursor.execute("""
				INSERT INTO recipe_items ( recipe_id, ingredient_id, amount )
				VALUES ( :rid, :ingredient_id, :amount )
			""", {"rid": rid, "ingredient_id": item.ingredient_id, "amount": item.amount})
        self.con.commit()
        self.close()

    def has_recipe_changed(self, rid, name, items, instruction):
        self.open()
        self.cursor.execute("""
			SELECT name, instruction
			FROM recipes
			WHERE id = :rid
		""", {"rid": rid})
        recipe_in_Database = self.cursor.fetchone()
        # recipe not found, so it must be different
        if recipe_in_Database == None:
            self.close()
            return True
        # name has changed
        elif recipe_in_Database["name"] != name:
            self.close()
            return True
        # instruction has changed
        elif recipe_in_Database["instruction"] != instruction and not (not recipe_in_Database["instruction"] and not instruction):
            self.close()
            return True
        self.cursor.execute("""
			SELECT id, ingredient_id, amount
			FROM recipe_items
			WHERE recipe_id = :rid
			ORDER BY id ASC
		""", {"rid": rid})
        items_in_Database = self.cursor.fetchall()
        if len(items_in_Database) != len(items):
            self.close()
            return True

        for i in range(0, len(items_in_Database)):
            if items_in_Database[i]["ingredient_id"] != items[i].ingredient_id or \
                    items_in_Database[i]["amount"] != items[i].amount:
                # item has changed
                self.close()
                return True
        self.close()
        return False

    def start_order(self, rid):
        self.open()
        self.cursor.execute("""
			INSERT INTO orders ( recipe_id, started, status )
			VALUES ( :rid, DATETIME('now'), 0 )
		""", {"rid": rid})
        self.con.commit()
        self.close()

    def close_order(self, rid):
        self.open()
        self.cursor.execute("""
			UPDATE orders
			SET finished = DATETIME('now'), status = 1
			WHERE recipe_id = :rid
		""", {"rid": rid})
        self.con.commit()
        self.close()

    def clear_order(self):
        self.open()
        self.cursor.execute("""
			UPDATE orders
			SET status = -1
			WHERE status = 0
		""")
        self.con.commit()
        self.close()

    def update_ports(self, ports):
        self.open()
        for port, ingredient_id in ports.items():
            self.cursor.execute("""
				UPDATE ports
				SET ingredient_id = :ingredient_id
				WHERE id = :port
			""", {"ingredient_id": ingredient_id, "port": port})
        self.con.commit()
        self.close()

    def update_calibration(self, port, calibration):
        self.open()
        self.cursor.execute("""
			UPDATE ingredients
			SET calibration = :calibration
			WHERE id = (
						SELECT ingredient_id
						FROM ports
						WHERE id = :port
						)
		""", {'calibration': calibration, 'port': port})
        self.con.commit()
        self.close()

    def ordered_cocktails_count(self, date):
        self.open()
        self.cursor.execute("""
			SELECT r.name, r.id AS rid, COUNT(*) AS count
			FROM orders O
			JOIN recipes r
			ON r.id = O.recipe_id
			WHERE O.started >= DATETIME(:date, "+0.5 days")
			AND O.started < DATETIME(:date, "+1.5 days")
			GROUP BY r.id
			ORDER BY count DESC
		""", {'date': date})
        res = [dict(row) for row in self.cursor.fetchall()]
        return res

    def ordered_ingredients_amount(self, date):
        self.open()
        self.cursor.execute("""
			SELECT i.name AS ingredient, i.id AS ingredient_id, SUM(ri.amount)/100 AS liters
			FROM recipe_items ri
			JOIN orders o
			ON o.recipe_id = ri.recipe_id
			JOIN ingredients i
			ON i.id = ri.ingredient_id
			WHERE O.started >= DATETIME(:date, "+0.5 days")
			AND O.started < DATETIME(:date, "+1.5 days")
			GROUP BY i.id
			ORDER BY liters DESC
		""", {'date': date})
        res = [dict(row) for row in self.cursor.fetchall()]
        return res

    def ordered_cocktails_by_time(self, date):
        self.open()
        self.cursor.execute("""
			SELECT strftime('%Y-%m-%d %H',o.started) AS hour, count(*) AS count
			FROM orders o
			WHERE O.started >= DATETIME(:date, "+0.5 days")
			AND O.started < DATETIME(:date, "+1.5 days")
			GROUP BY hour
		""", {'date': date})
        res = [dict(row) for row in self.cursor.fetchall()]
        return res

    def list_parties(self):
        self.open()
        self.cursor.execute("""
			SELECT partydate, ordercount
			FROM (
				SELECT date(o.started, "-0.5 days") AS partydate,  count(o.id) as ordercount
				FROM orders o
				GROUP BY partydate
				ORDER BY partydate DESC
			)
			WHERE ordercount > 10
		""")
        res = [dict(row) for row in self.cursor.fetchall()]
        return res
