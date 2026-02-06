import pytest
from unittest.mock import MagicMock, patch
from PyQt5 import QtWidgets, QtCore
from barbot.logic import BarBot, UserMessageType, BarBotStateEnum, UserInputType
from barbot.logic.recipes import RecipeCollection
from barbot.gui.view.general.busy_view import BusyView

@pytest.fixture
def mock_barbot():
    bot = MagicMock(spec=BarBot)
    bot.state = BarBotStateEnum.IDLE
    bot.current_mixing_options = None
    bot.was_aborted = False
    bot.ports = MagicMock()
    return bot

@pytest.fixture
def mock_recipes():
    return MagicMock(spec=RecipeCollection)

def test_busy_view_initial_state(qtbot, mock_barbot, mock_recipes):
    view = BusyView(mock_barbot, mock_recipes)
    qtbot.addWidget(view)
    view.show()
    
    assert view._title_label.text() != ""
    assert view._message_container.isHidden() is True
    assert view._content_container.isVisible() is True

def test_busy_view_update_message_none(qtbot, mock_barbot, mock_recipes):
    view = BusyView(mock_barbot, mock_recipes)
    qtbot.addWidget(view)
    view.show()
    
    view.update_message(None)
    assert view._message_container.isHidden() is True
    assert view._content_container.isVisible() is True

def test_busy_view_update_message_ingredient_empty(qtbot, mock_barbot, mock_recipes):
    view = BusyView(mock_barbot, mock_recipes)
    qtbot.addWidget(view)
    view.show()
    
    # Setup mock for ingredient empty message
    mock_barbot.current_recipe_item = MagicMock()
    mock_barbot.current_recipe_item.ingredient.name = "Gin"
    mock_barbot.current_recipe_item.ingredient.type = MagicMock()
    mock_barbot.ports.port_of_ingredient.return_value = 0
    
    view.update_message(UserMessageType.INGREDIENT_EMPTY)
    
    assert view._message_container.isVisible() is True
    assert "Gin" in view._message_container.findChild(QtWidgets.QLabel).text()
    
    # Check if buttons are present
    buttons = view._message_container.findChildren(QtWidgets.QPushButton)
    assert len(buttons) >= 2
    
    # Test button click
    with patch.object(mock_barbot, 'set_user_input') as mock_input:
        qtbot.mouseClick(buttons[0], QtCore.Qt.LeftButton)
        mock_input.assert_called()

def test_busy_view_status_mixing(qtbot, mock_barbot, mock_recipes):
    mock_barbot.state = BarBotStateEnum.MIXING
    mock_mixing_options = MagicMock()
    mock_mixing_options.recipe.name = "Gin Tonic"
    recipe_item = MagicMock()
    recipe_item.ingredient.name = "Gin"
    mock_mixing_options.recipe.items = [recipe_item]
    mock_mixing_options.add_straw = True
    mock_mixing_options.add_ice = True
    mock_barbot.current_mixing_options = mock_mixing_options
    
    view = BusyView(mock_barbot, mock_recipes)
    qtbot.addWidget(view)
    view.show()
    
    assert "Gin Tonic" in view._title_label.text()
    assert len(view.recipe_list_widgets) == 3 # Gin, Straw, Ice

def test_busy_view_set_progress(qtbot, mock_barbot, mock_recipes):
    mock_barbot.state = BarBotStateEnum.MIXING
    mock_mixing_options = MagicMock()
    
    class MockIngredient:
        def __init__(self, name):
            self.name = name
    
    item1 = MagicMock()
    item1.ingredient = MockIngredient("Gin")
    
    item2 = MagicMock()
    item2.ingredient = MockIngredient("Tonic")
    
    mock_mixing_options.recipe.items = [item1, item2]
    mock_mixing_options.add_straw = False
    mock_mixing_options.add_ice = False
    mock_barbot.current_mixing_options = mock_mixing_options
    
    with patch('barbot.gui.view.general.busy_view.qt_icon_from_file_name') as mock_icon_func:
        mock_icon = MagicMock()
        mock_icon.availableSizes.return_value = [QtCore.QSize(16, 16)]
        mock_icon.pixmap.return_value = QtWidgets.QWidget().grab() # Easiest way to get a QPixmap
        mock_icon_func.return_value = mock_icon
        
        view = BusyView(mock_barbot, mock_recipes)
        qtbot.addWidget(view)
        view.show()
        
        # Initial progress
        view.set_progress(0)
        assert len(view.recipe_list_widgets) == 2
        
        view.set_progress(1)
        view.set_progress(2)

def test_busy_view_various_statuses(qtbot, mock_barbot, mock_recipes):
    statuses = [
        BarBotStateEnum.CONNECTING,
        BarBotStateEnum.SEARCHING,
        BarBotStateEnum.CLEANING_CYCLE,
        BarBotStateEnum.SINGLE_INGREDIENT,
        BarBotStateEnum.STARTUP,
        BarBotStateEnum.CRUSHING,
        BarBotStateEnum.STRAW
    ]
    for status in statuses:
        mock_barbot.state = status
        view = BusyView(mock_barbot, mock_recipes)
        qtbot.addWidget(view)
        view.show()
        assert view._title_label.text() != ""

def test_busy_view_message_handling_all_variants(qtbot, mock_barbot, mock_recipes):
    view = BusyView(mock_barbot, mock_recipes)
    qtbot.addWidget(view)
    view.show()
    
    messages = [
        UserMessageType.PLACE_GLAS,
        UserMessageType.MIXING_DONE_REMOVE_GLAS,
        UserMessageType.ASK_FOR_STRAW,
        UserMessageType.ASK_FOR_ICE,
        UserMessageType.STRAWS_EMPTY,
        UserMessageType.CLEANING_ADAPTER,
        UserMessageType.I2C_ERROR,
        UserMessageType.UNKNOWN_ERROR,
        UserMessageType.GLAS_REMOVED_WHILE_DRAFTING,
        UserMessageType.ICE_EMPTY,
        UserMessageType.CRUSHER_COVER_OPEN,
        UserMessageType.CRUSHER_TIMEOUT,
        UserMessageType.BOARD_NOT_CONNECTED_BALANCE,
        UserMessageType.BOARD_NOT_CONNECTED_CRUSHER,
        UserMessageType.BOARD_NOT_CONNECTED_MIXER,
        UserMessageType.BOARD_NOT_CONNECTED_STRAW,
        UserMessageType.BOARD_NOT_CONNECTED_SUGAR
    ]
    
    for msg in messages:
        view.update_message(msg)
        assert view._message_container.isVisible() is True
        # Verify at least one button is added for messages that require input
        if msg not in [UserMessageType.MIXING_DONE_REMOVE_GLAS]:
             buttons = view._message_container.findChildren(QtWidgets.QPushButton)
             assert len(buttons) > 0
