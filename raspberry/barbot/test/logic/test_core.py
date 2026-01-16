# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, protected-access
import unittest
from unittest.mock import MagicMock, patch
from barbot.logic.core import BarBot, BarBotContext, IdleTask, IdleTaskType
from barbot.logic.core.common import (
    UserInputType,
    UserMessageType,
    MixingOptions,
)
from barbot.logic.core.states import (
    ConnectingState,
    SearchingState,
    StartupState,
    IdleState,
)
from barbot.logic.communication import LEDMode, PlatformLEDMode


class TestBarBotContext(unittest.TestCase):
    def setUp(self):
        self.context = BarBotContext()

    def test_initial_values(self):
        self.assertFalse(self.context.should_stop_statemachine)
        self.assertFalse(self.context.should_abort_mixing)
        self.assertEqual(self.context.user_input, UserInputType.UNDEFINED)
        self.assertEqual(self.context.weight_timeout, 1)
        self.assertIsNone(self.context.weight)
        self.assertEqual(self.context.pumps_to_clean, [])
        self.assertEqual(self.context.connected_boards, [])
        self.assertIsNone(self.context._message)
        self.assertEqual(self.context._progress, 0)
        self.assertEqual(self.context.idle_tasks, [])
        self.assertIsNone(self.context.current_mixing_options)
        self.assertIsNone(self.context.current_recipe_item)
        self.assertIsInstance(self.context.parties, object)  # PartyCollection
        self.assertFalse(self.context.state_changed)
        self.assertTrue(self.context.should_reconnect)

    def test_get_next_idle_task(self):
        task = IdleTask(IdleTaskType.DO, None, "test")
        self.context.idle_tasks.append(task)
        self.assertEqual(self.context.get_next_idle_task(), task)
        self.assertEqual(self.context.idle_tasks, [])

    def test_reset_user_input(self):
        self.context.user_input = UserInputType.YES
        self.context.reset_user_input()
        self.assertEqual(self.context.user_input, UserInputType.UNDEFINED)

    def test_mixing_progress_property(self):
        callback_called = False

        def callback(progress):
            nonlocal callback_called
            callback_called = True
            self.assertEqual(progress, 50)

        self.context.on_mixing_progress_changed = callback
        self.context.mixing_progress = 50
        self.assertEqual(self.context._progress, 50)
        self.assertTrue(callback_called)

    def test_message_property(self):
        callback_called = False

        def callback(message):
            nonlocal callback_called
            callback_called = True
            self.assertEqual(message, UserMessageType.PLACE_GLAS)

        self.context.on_message_changed = callback
        self.context.message = UserMessageType.PLACE_GLAS
        self.assertEqual(self.context._message, UserMessageType.PLACE_GLAS)
        self.assertTrue(callback_called)

    def test_remove_message(self):
        self.context.message = UserMessageType.PLACE_GLAS
        self.context.remove_message()
        self.assertEqual(self.context._message, UserMessageType.NONE)


class TestIdleTask(unittest.TestCase):
    def setUp(self):
        self.mainboard = MagicMock()
        self.callback = MagicMock()

    def test_idle_task_do(self):
        task = IdleTask(IdleTaskType.DO, self.callback, "command", "param1", "param2")
        self.mainboard.do.return_value = "result"
        task.execute(self.mainboard)
        self.mainboard.do.assert_called_once_with("command", "param1", "param2")
        self.callback.assert_called_once_with("result")

    def test_idle_task_get(self):
        task = IdleTask(IdleTaskType.GET, self.callback, "command", "param1")
        self.mainboard.get.return_value = "result"
        task.execute(self.mainboard)
        self.mainboard.get.assert_called_once_with("command", "param1")
        self.callback.assert_called_once_with("result")

    def test_idle_task_set(self):
        task = IdleTask(IdleTaskType.SET, self.callback, "command", "param1")
        self.mainboard.set.return_value = "result"
        task.execute(self.mainboard)
        self.mainboard.set.assert_called_once_with("command", "param1")
        self.callback.assert_called_once_with("result")


class TestBarBot(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.ports = MagicMock()
        self.mainboard = MagicMock()
        self.barbot = BarBot(self.config, self.ports, self.mainboard)

    def test_initial_state(self):
        self.assertIsInstance(self.barbot._context, BarBotContext)
        self.assertIsNone(self.barbot._next_state_by_class)
        self.assertFalse(self.barbot._is_transitioning)

    def test_config_property(self):
        self.assertEqual(self.barbot.config, self.config)

    def test_ports_property(self):
        self.assertEqual(self.barbot.ports, self.ports)

    def test_was_aborted(self):
        self.assertFalse(self.barbot.was_aborted)

    def test_mixing_progress(self):
        self.barbot._context._progress = 50
        self.assertEqual(self.barbot.mixing_progress, 50)

    def test_current_mixing_options(self):
        options = MixingOptions(MagicMock())
        self.barbot._context.current_mixing_options = options
        self.assertEqual(self.barbot.current_mixing_options, options)

    def test_current_recipe_item(self):
        item = MagicMock()
        self.barbot._context.current_recipe_item = item
        self.assertEqual(self.barbot.current_recipe_item, item)

    def test_set_balance_calibration(self):
        self.barbot.set_balance_calibration(10, 20)
        self.assertEqual(self.config.balance_offset, 10)
        self.assertEqual(self.config.balance_calibration, 20)
        # Check idle tasks added
        self.assertEqual(len(self.barbot._context.idle_tasks), 2)
        task1 = self.barbot._context.idle_tasks[0]
        self.assertEqual(task1._command, "SetBalanceOffset")
        task2 = self.barbot._context.idle_tasks[1]
        self.assertEqual(task2._command, "SetBalanceCalibration")

    def test_reconnect(self):
        self.barbot.reconnect()
        self.assertTrue(self.barbot._should_reconnect)


class TestStates(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.ports = MagicMock()
        self.mainboard = MagicMock()
        self.context = MagicMock()

    def test_connecting_state_on_enter(self):
        state = ConnectingState(self.config, self.ports, self.mainboard, self.context)
        state.on_enter()
        # on_enter does nothing, so no calls
        self.mainboard.do.assert_not_called()

    def test_connecting_state_update_invalid_mac(self):
        self.config.is_mac_address_valid = False
        state = ConnectingState(self.config, self.ports, self.mainboard, self.context)
        next_state = state.update()
        self.assertEqual(next_state, SearchingState)

    def test_connecting_state_update_connect_success(self):
        self.config.is_mac_address_valid = True
        self.mainboard.connect.return_value = True
        state = ConnectingState(self.config, self.ports, self.mainboard, self.context)
        next_state = state.update()
        self.assertEqual(next_state, StartupState)
        self.mainboard.connect.assert_called_once_with(self.config.mac_address)

    @patch("time.sleep")
    def test_connecting_state_update_connect_fail(self, mock_sleep):
        self.config.is_mac_address_valid = True
        self.mainboard.connect.return_value = False
        state = ConnectingState(self.config, self.ports, self.mainboard, self.context)
        next_state = state.update()
        self.assertIsNone(next_state)
        mock_sleep.assert_called_once_with(1)

    def test_idle_state_on_enter(self):
        state = IdleState(self.config, self.ports, self.mainboard, self.context)
        state.on_enter()
        self.mainboard.set.assert_any_call("SetLED", LEDMode.RAINBOW.value)
        self.mainboard.set.assert_any_call("PlatformLED", PlatformLEDMode.OFF.value)
        self.mainboard.do.assert_any_call("Move", 0)
        self.mainboard.do.assert_any_call("Home")
        self.assertFalse(self.context.should_abort_mixing)
        self.assertIsNone(self.context.current_mixing_options)
        self.assertIsNone(self.context.current_recipe_item)


if __name__ == "__main__":
    unittest.main()
