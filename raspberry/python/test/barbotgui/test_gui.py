# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, protected-access
import os
import time
import threading
import pytest
from pytestqt.qtbot import QtBot

from barbot import PortConfiguration, BarBotConfig, BarBot, Mainboard
from barbot.recipes import RecipeCollection
from barbot.communication import BoardType
from barbot.mockup import MaiboardConnectionMockup
from barbotgui.main_window import MainWindow
from barbotgui.userviews import ListRecipes, RecipeNewOrEdit
from barbotgui.userviews import SingleIngredient, Statistics, OrderRecipe
from barbotgui.adminviews import AdminLogin, BalanceCalibration, Overview
from barbotgui.adminviews import Ports, Cleaning, Settings, RemoveRecipe

temp_path = os.path.join(os.path.dirname(__file__), ".barbot")
# make sure the temp data folder exists
os.makedirs(temp_path, exist_ok=True)

class TestGui:
    @pytest.fixture
    def mainboard_connection_mockup(self) -> MaiboardConnectionMockup:
        result = MaiboardConnectionMockup()
        result.duration_DO = 0.5
        result.duration_SET = 0.1
        result.duration_GET = 0.1
        return result

    @pytest.fixture
    def main_window(self, qtbot : QtBot, mainboard_connection_mockup):
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
        while bot.is_busy:
            time.sleep(1)
        window = MainWindow(bot, recipe_collection)
        window.show()
        qtbot.addWidget(window)
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

    def test_admin_views(self, main_window:MainWindow, qtbot : QtBot):
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
            view_instance = view(main_window)
            main_window.set_view(view_instance)
            qtbot.wait(200)

    def test_order_recipe(self, main_window:MainWindow, qtbot : QtBot):
        qtbot.wait(200)
        # take the first recipe from the list
        recipe = main_window.recipes._recipes[0]
        main_window.set_view(OrderRecipe(main_window, recipe))
        qtbot.wait(200)

    def test_views(self, main_window:MainWindow, qtbot : QtBot):
        views = [
            ListRecipes,
            RecipeNewOrEdit,
            SingleIngredient,
            Statistics,
            RecipeNewOrEdit
        ]
        for view in views:
            main_window.set_view(view(main_window))
            qtbot.wait(200)
