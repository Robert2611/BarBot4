import os
import time
import threading
import pytest
from barbot import PortConfiguration, BarBotConfig, BarBot
from barbot.recipes import RecipeCollection, load_recipe_from_file
from barbot.communication import BoardType
import barbotgui.userviews
from barbotgui.userviews import ListRecipes, RecipeNewOrEdit, SingleIngredient, Statistics, OrderRecipe
from barbotgui.adminviews import AdminLogin, BalanceCalibration, Overview, Ports, Cleaning, Settings, RemoveRecipe
from barbot.mockup import MaiboardConnectionMockup

recipes_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "recipes")
temp_path = os.path.join(os.path.dirname(__file__), ".barbot")
# make sure the temp data folder exists
os.makedirs(temp_path, exist_ok=True)

def test_gui(main_window):
    assert main_window._current_view.is_idle_view
    assert isinstance(main_window._current_view, ListRecipes)

@pytest.fixture
def mainboard_connection_mockup() -> MaiboardConnectionMockup:
    return MaiboardConnectionMockup()

@pytest.fixture
def main_window(qtbot, mainboard_connection_mockup):
    ports = PortConfiguration()
    config = BarBotConfig()
    bot = BarBot(config, ports)
    # inject mockup for communication
    bot._mainboard._connection = mainboard_connection_mockup
    mainboard_connection_mockup.set_result_for_getter("GetConnectedBoards", 1<<BoardType.BALANCE.value | 1<<BoardType.MIXER.value)
    recipe_collection = RecipeCollection()
    recipe_collection.load()
    bar_bot_thread = threading.Thread(target=bot.run)
    bar_bot_thread.start()
    window = barbotgui.MainWindow(bot, recipe_collection)
    window.show()
    qtbot.addWidget(window)
    yield window
    bot.abort()
    bar_bot_thread.join(2)

@pytest.mark.timeout(20)
def test_single_ingredient(main_window, mainboard_connection_mockup):
    while main_window.barbot_.is_busy:
        time.sleep(1)
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

def test_views(main_window):
    #create all views
    views = [ListRecipes, RecipeNewOrEdit, SingleIngredient, Statistics, RecipeNewOrEdit]
    for view in views:
        main_window.set_view(view(main_window))

    # OrderRecipe needs a recipe, so we load one

    recipe = load_recipe_from_file(recipes_path, "Anti.yaml")
    if recipe is None:
        raise Exception("Could not load recipe")
    main_window.set_view(OrderRecipe(main_window, recipe))

    #create all admin views
    admin_views = [AdminLogin, BalanceCalibration, Overview, Ports, Cleaning, Settings, RemoveRecipe]
    for view in admin_views:
        main_window.set_view(view(main_window))