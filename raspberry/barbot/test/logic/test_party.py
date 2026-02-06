import unittest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timedelta
from barbot.logic.recipes.party import Party, PartyCollection, PartyStatistics
from barbot.logic.recipes.recipe import Recipe, RecipeItem

class TestParty(unittest.TestCase):
    @patch('barbot.logic.recipes.party.datetime')
    @patch('barbot.logic.recipes.party.open', new_callable=mock_open)
    @patch('barbot.logic.recipes.party.yaml.dump')
    def test_add_order(self, mock_yaml_dump, mock_file, mock_datetime):
        now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_datetime.strptime = datetime.strptime # Keep original strptime
        
        party = Party(start=now)
        recipe = MagicMock(spec=Recipe)
        recipe.name = "Test Cocktail"
        item = MagicMock()
        item.amount = 100
        item.ingredient = MagicMock()
        item.ingredient.identifier = "vodka"
        recipe.items = [item]
        
        party.add_order(recipe)
        
        self.assertEqual(len(party.orders), 1)
        self.assertEqual(party.orders[0].recipe, "Test Cocktail")
        self.assertTrue(mock_file.called)
        self.assertTrue(mock_yaml_dump.called)

    @patch('barbot.logic.recipes.party.get_ingredient_by_identifier')
    def test_get_statistics(self, mock_get_ingredient):
        party = Party(start=datetime(2023, 1, 1, 10, 0, 0))
        
        # Mock ingredient
        ing = MagicMock()
        ing.name = "Vodka"
        ing.type = "LIQUID" # Not STIRR
        mock_get_ingredient.return_value = ing
        
        # Add a manual order to party.orders
        order = MagicMock()
        order.recipe = "Vodka Shot"
        order.date = datetime(2023, 1, 1, 11, 0, 0)
        item = MagicMock()
        item.ingredient = "vodka"
        item.amount = 40
        order.items = [item]
        party.orders.append(order)
        
        stats = party.get_statistics()
        
        self.assertEqual(stats.total_cocktails, 1)
        self.assertEqual(stats.cocktail_count["Vodka Shot"], 1)
        self.assertEqual(stats.ingredients_amount["Vodka"], 40)

class TestPartyCollection(unittest.TestCase):
    @patch('barbot.logic.recipes.party.os.listdir')
    @patch('barbot.logic.recipes.party.os.path.getsize')
    @patch('barbot.logic.recipes.party.open', new_callable=mock_open, read_data="- recipe: Test\n  date: 2023-01-01 12:00:00\n  items: []")
    @patch('barbot.logic.recipes.party.get_order_from_json')
    def test_initialization(self, mock_get_order, mock_file, mock_getsize, mock_listdir):
        mock_listdir.return_value = ["orders 2023-01-01 12-00-00.yaml"]
        mock_getsize.return_value = 100
        mock_get_order.return_value = MagicMock()
        
        # We need to mock PARTY_MIN_ORDER_COUNT to 1 for this test to avoid complexity
        with patch('barbot.logic.recipes.party.PARTY_MIN_ORDER_COUNT', 0):
             collection = PartyCollection()
             self.assertTrue(len(collection) >= 1)
             self.assertIsNotNone(collection.current_party)
