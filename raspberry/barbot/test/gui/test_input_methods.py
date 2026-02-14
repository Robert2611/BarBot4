import pytest
from unittest.mock import MagicMock, patch, mock_open
from PyQt5 import QtWidgets, QtCore
from barbot.gui.core import MainWindow, InputMethod
from barbot.gui.controls import Keyboard, Numpad, ListSelector, SelectorButton
from barbot.logic import BarBot, BarBotStateEnum
from barbot.logic.recipes import RecipeCollection

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

@pytest.fixture
def main_window(qtbot, mock_barbot, mock_recipes):
    # Patch styling and file loading
    with patch('barbot.gui.core.css_path', return_value='/tmp'), \
         patch('builtins.open', mock_open(read_data="* { color: black; }")), \
         patch('barbot.gui.core.MainWindow.show'), \
         patch('barbot.gui.core.is_raspberry', return_value=False):
        
        # Patch views to avoid complex dependencies but still allow MainWindow to work
        from barbot.gui.view.base import View
        class MockView(View):
            switch_view_trigger = QtCore.pyqtSignal(object)
            show_message_trigger = QtCore.pyqtSignal(str)
            open_input_method_trigger = QtCore.pyqtSignal(object, InputMethod)
            close_keyboard_trigger = QtCore.pyqtSignal()
            def __init__(self, *args, **kwargs):
                QtWidgets.QWidget.__init__(self)
                self._is_idle_view = True
            @property
            def is_idle_view(self):
                return self._is_idle_view
            @property
            def barbot_(self):
                return mock_barbot
            @property
            def recipes(self):
                return mock_recipes
        
        with patch('barbot.gui.view.user.ListRecipes', return_value=MockView()), \
             patch('barbot.gui.view.general.BusyView', return_value=MockView()):
            window = MainWindow(mock_barbot, mock_recipes)
            qtbot.addWidget(window)
            return window

def test_keyboard_integration_flow(qtbot, main_window):
    target = QtWidgets.QLineEdit()
    qtbot.addWidget(target)
    
    # Simulate signal from a view
    main_window._current_view.open_input_method_trigger.emit(target, InputMethod.KEYBOARD)
    
    # Check if keyboard is shown
    keyboard = main_window._keyboard
    assert isinstance(keyboard, Keyboard)
    assert keyboard.isVisible()
    
    # Find a letter button (e.g., 'q')
    buttons = keyboard.findChildren(QtWidgets.QPushButton)
    q_button = next(b for b in buttons if b.text() == 'q')
    
    # Click it
    qtbot.mouseClick(q_button, QtCore.Qt.LeftButton)
    
    # Verify target update
    assert target.text() == "q"
    
    # Close it
    main_window.close_keyboard()
    assert main_window._keyboard is None

def test_numpad_integration_flow(qtbot, main_window):
    target = QtWidgets.QSpinBox()
    target.setRange(0, 100)
    qtbot.addWidget(target)
    
    # Simulate signal
    main_window._current_view.open_input_method_trigger.emit(target, InputMethod.NUMPAD)
    
    # Check if numpad is shown
    numpad = main_window._keyboard
    assert isinstance(numpad, Numpad)
    assert numpad.isVisible()
    
    # Find buttons
    buttons = numpad.findChildren(QtWidgets.QPushButton)
    btn_1 = next(b for b in buttons if b.text() == '1')
    btn_ok = next(b for b in buttons if b.text() == 'Ok')
    
    # Enter '1'
    qtbot.mouseClick(btn_1, QtCore.Qt.LeftButton)
    assert numpad._value_label.text() == "1"
    
    # Click Ok
    qtbot.mouseClick(btn_ok, QtCore.Qt.LeftButton)
    
    # Verify target update
    assert target.value() == 1
    # MainWindow doesn't automatically clear _keyboard when widget closes itself
    main_window.close_keyboard()
    assert main_window._keyboard is None

def test_list_selector_integration_flow(qtbot, main_window):
    items = [("Option A", "A"), ("Option B", "B")]
    target = SelectorButton("Select", lambda: items)
    qtbot.addWidget(target)
    
    # Connect signal like base.py does
    target.request_selection_trigger.connect(main_window._current_view.open_input_method_trigger)
    
    # Click the button to trigger
    qtbot.mouseClick(target, QtCore.Qt.LeftButton)
    
    # Check if list selector is shown
    selector = main_window._keyboard
    assert isinstance(selector, ListSelector)
    assert selector.isVisible()
    
    # Find "Option B" button
    buttons = selector.findChildren(QtWidgets.QPushButton)
    btn_b = next(b for b in buttons if b.text() == "Option B")
    
    # Click it
    qtbot.mouseClick(btn_b, QtCore.Qt.LeftButton)
    
    # Verify target update (SelectorButton text changes on selection)
    assert target.text() == "Option B"
    main_window.close_keyboard()
    assert main_window._keyboard is None

def test_overlay_closes_on_outside_click(qtbot, main_window):
    target = QtWidgets.QLineEdit()
    main_window.open_keyboard(target)
    assert main_window._keyboard is not None
    
    # Click on the central widget (outside the keyboard)
    qtbot.mouseClick(main_window.center, QtCore.Qt.LeftButton)
    
    # Verify keyboard closed
    assert main_window._keyboard is None
