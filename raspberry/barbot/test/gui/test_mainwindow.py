import pytest
from unittest.mock import MagicMock, patch, mock_open
from PyQt5 import QtWidgets, QtCore
from barbot.logic import BarBot, UserMessageType, BarBotStateEnum
from barbot.logic.recipes import RecipeCollection
from barbot.gui.main_window import MainWindow
from barbot.gui.common import InputMethod

@pytest.fixture
def mock_barbot():
    bot = MagicMock(spec=BarBot)
    bot.state = BarBotStateEnum.IDLE
    bot.is_busy = False
    bot.on_state_changed = None
    bot.on_message_changed = None
    bot.on_mixing_progress_changed = None
    return bot

@pytest.fixture
def mock_recipes():
    return MagicMock(spec=RecipeCollection)

from barbot.gui.view.base import View

class MockView(View):
    # Signals must be class attributes
    switch_view_trigger = QtCore.pyqtSignal(object)
    show_message_trigger = QtCore.pyqtSignal(str)
    open_input_method_trigger = QtCore.pyqtSignal(object, InputMethod)
    close_keyboard_trigger = QtCore.pyqtSignal()
    
    def __init__(self, bb=None, rs=None, is_idle=True):
        # We don't call super here to avoid needing real barbot/recipes if we don't want to
        # but inheriting from QWidget (via View) is essential for addWidget
        QtWidgets.QWidget.__init__(self)
        self._is_idle_view = is_idle

@pytest.fixture
def main_window(qtbot, mock_barbot, mock_recipes):
    # Patch styling and file loading
    with patch('barbot.gui.main_window.css_path', return_value='/tmp'), \
         patch('builtins.open', mock_open(read_data="* { color: black; }")), \
         patch('barbot.gui.main_window.MainWindow.show'), \
         patch('barbot.gui.main_window.is_raspberry', return_value=False):
        
        with patch('barbot.gui.view.user.ListRecipes', return_value=MockView(mock_barbot, mock_recipes)), \
             patch('barbot.gui.view.general.BusyView', return_value=MockView(mock_barbot, mock_recipes, is_idle=False)):
            window = MainWindow(mock_barbot, mock_recipes)
            qtbot.addWidget(window)
            return window

def test_mainwindow_initial_view(main_window):
    assert main_window._current_view is not None
    assert isinstance(main_window._current_view, MockView)

def test_mainwindow_set_view(main_window):
    view = MockView()
    main_window.set_view(view)
    assert main_window._current_view == view

def test_mainwindow_show_message_splash(qtbot, main_window):
    with patch('PyQt5.QtWidgets.QLabel.show') as mock_show:
        main_window._show_message_splash("Test Message")
        mock_show.assert_called()

def test_mainwindow_open_keyboard(main_window):
    target = QtWidgets.QLineEdit()
    with patch('barbot.gui.main_window.Keyboard') as mock_keyboard_class:
        main_window.open_keyboard(target)
        mock_keyboard_class.assert_called_with(target, main_window.styles, main_window)
        assert main_window._keyboard == mock_keyboard_class.return_value

def test_mainwindow_open_numpad(main_window):
    target = QtWidgets.QSpinBox()
    with patch('barbot.gui.main_window.Numpad') as mock_numpad_class:
        main_window.open_numpad(target)
        mock_numpad_class.assert_called_with(target, main_window.styles, main_window)
        assert main_window._keyboard == mock_numpad_class.return_value

def test_mainwindow_open_list_selector(main_window):
    target = MagicMock()
    target.get_items.return_value = [("Item 1", 1)]
    with patch('barbot.gui.main_window.ListSelector') as mock_list_selector_class:
        main_window.open_list_selector(target)
        mock_list_selector_class.assert_called_with(target.get_items.return_value, main_window.styles, main_window)
        assert main_window._keyboard == mock_list_selector_class.return_value
        # Check signal connection
        mock_list_selector_class.return_value.on_item_selected.connect.assert_called_with(target.handle_selection)

def test_mainwindow_close_keyboard(main_window):
    main_window._keyboard = MagicMock()
    # close_keyboard calls close() which is a QWidget method. 
    # If we use MagicMock, it works, but let's be safe.
    main_window.close_keyboard()
    assert main_window._keyboard is None

def test_mainwindow_update_view_busy(main_window, mock_barbot):
    mock_barbot.is_busy = True
    with patch('barbot.gui.view.general.BusyView', return_value=MockView(is_idle=False)):
        main_window.update_view()
        assert isinstance(main_window._current_view, MockView)
        assert main_window._current_view.is_idle_view is False

def test_mainwindow_header_clicked_admin_login(main_window, mock_barbot):
    main_window.header_clicked(None)
    assert main_window._admin_button_active is True
    
    mock_barbot.is_busy = False
    with patch('barbot.gui.view.admin.AdminLogin', return_value=MockView()):
        main_window.header_clicked(None)
        assert isinstance(main_window._current_view, MockView)
