import os
import time
import threading
import pytest
from barbot import PortConfiguration, BarBotConfig, BarBot, Mainboard
from barbot.recipes import RecipeCollection, load_recipe_from_file
from barbot.communication import BoardType
from barbot.mockup import MaiboardConnectionMockup
from barbotgui.main_window import MainWindow
from barbotgui.userviews import ListRecipes, RecipeNewOrEdit
from barbotgui.userviews import SingleIngredient, Statistics, OrderRecipe
from barbotgui.adminviews import AdminLogin, BalanceCalibration, Overview
from barbotgui.adminviews import Ports, Cleaning, Settings, RemoveRecipe

recipes_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "recipes")
temp_path = os.path.join(os.path.dirname(__file__), ".barbot")
# make sure the temp data folder exists
os.makedirs(temp_path, exist_ok=True)

class TestGui:
    @pytest.fixture
    def mainboard_connection_mockup(self) -> MaiboardConnectionMockup:
        return MaiboardConnectionMockup()

    @pytest.fixture
    def main_window(self, qtbot, mainboard_connection_mockup):
        ports = PortConfiguration()
        config = BarBotConfig()
        mainboard = Mainboard(mainboard_connection_mockup)
        bot = BarBot(config, ports, mainboard)
        boards_encoded = 1<<BoardType.BALANCE.value | 1<<BoardType.MIXER.value
        mainboard_connection_mockup.set_result_for_getter("GetConnectedBoards", boards_encoded)
        recipe_collection = RecipeCollection()
        recipe_collection.load()
        bar_bot_thread = threading.Thread(target=bot.run)
        bar_bot_thread.start()
        window = MainWindow(bot, recipe_collection)
        window.show()
        qtbot.addWidget(window)
        while window.barbot_.is_busy:
            time.sleep(1)
        yield window
        bot.abort()
        bar_bot_thread.join(2)

    @pytest.mark.timeout(20)
    def test_single_ingredient(self, main_window, mainboard_connection_mockup):
        mainboard_connection_mockup.clear_command_history()
        view = SingleIngredient(main_window)
        main_window.set_view(view)
        view._ingredient_widget.setCurrentIndex(2)
        view._amount_widget.setCurrentIndex(3)
        view._start_button.click()
        mainboard_connection_mockup.set_result_for_getter("HasGlas", 1)
        time.sleep(2)
        while main_window.barbot_.is_busy:
            time.sleep(1)
        assert "Draft" in mainboard_connection_mockup.command_history

    def test_admin_views(self, main_window):
        admin_views = [
            AdminLogin,
            BalanceCalibration,
            Overview,
            Ports,
            Cleaning,
            Settings,
            RemoveRecipe
        ]
        for view in admin_views:
            print(f"testing: {view}")
            main_window.set_view(view(main_window))
            time.sleep(0.2)

    def test_order_recipe(self, main_window):
        # OrderRecipe needs a recipe, so we load one
        recipe = load_recipe_from_file(recipes_path, "Anti.yaml")

        if recipe is None:
            raise Exception("Could not load recipe")
        main_window.set_view(OrderRecipe(main_window, recipe))

    def test_views(self, main_window):
        views = [
            ListRecipes,
            RecipeNewOrEdit,
            SingleIngredient,
            Statistics,
            RecipeNewOrEdit
        ]
        for view in views:
            main_window.set_view(view(main_window))
            time.sleep(0.2)
