import unittest
from unittest.mock import MagicMock, patch
from barbot.logic.core.states import (
    ConnectingState, SearchingState, StartupState, IdleState, MixingState,
    CrushingState, StrawState, CleaningCycleState, SingleIngredientState, BarBotState
)
from barbot.logic.core.common import UserInputType, UserMessageType, BarBotStateEnum, MixingOptions
from barbot.logic.config.ingredients import IngredientType
from barbot.logic.communication import Mainboard, CommunicationResult
from barbot.logic.config.barbot_config import BarBotConfig
from barbot.logic.config.port_config import PortConfiguration
from barbot.logic.core.barbot_context import BarBotContext
from barbot.logic.communication import (
    ResponseTypes, ErrorType as CommError, BoardType
)

class TestStates(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock(spec=BarBotConfig)
        self.mock_ports = MagicMock(spec=PortConfiguration)
        self.mock_mainboard = MagicMock(spec=Mainboard)
        self.mock_context = MagicMock(spec=BarBotContext)
        
        # Default behavior for context
        self.mock_context.should_abort_mixing = False
        self.mock_context.user_input = UserInputType.UNDEFINED
        self.mock_context.on_mixing_finished = MagicMock()
        self.mock_context.on_mixing_progress_changed = MagicMock()
        self.mock_context.on_message_changed = MagicMock()
        self.mock_context.parties = MagicMock()
        self.mock_context.parties.current_party = MagicMock()
        self.mock_context.connected_boards = []
        self.mock_context.current_recipe_item = MagicMock()
        
        # Global patches to speed up and avoid hangs
        self.sleep_patcher = patch('time.sleep', return_value=None)
        self.sleep_patcher.start()
        
        # Mock read_message to avoid infinite loops in _wait_for_user_input
        self.mock_mainboard.read_message.return_value = MagicMock()

    def tearDown(self):
        self.sleep_patcher.stop()

    def test_connecting_state_invalid_mac(self):
        self.mock_config.is_mac_address_valid = False
        state = ConnectingState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        next_state = state.update()
        self.assertEqual(next_state, SearchingState)

    def test_connecting_state_success(self):
        self.mock_config.is_mac_address_valid = True
        self.mock_mainboard.connect.return_value = True
        state = ConnectingState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        next_state = state.update()
        self.assertEqual(next_state, StartupState)

    def test_searching_state_found(self):
        self.mock_mainboard.find_bar_bot.return_value = "00:11:22:33:44:55"
        state = SearchingState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        next_state = state.update()
        self.assertEqual(next_state, ConnectingState)
        self.assertEqual(self.mock_config.mac_address, "00:11:22:33:44:55")

    def test_startup_state_success(self):
        self.mock_mainboard.is_connected = True
        mock_msg = MagicMock()
        mock_msg.message_type = ResponseTypes.STATUS
        self.mock_mainboard.read_message.return_value = mock_msg
        
        # All boards connected
        boards = (1 << BoardType.BALANCE.value) | (1 << BoardType.MIXER.value) | \
                 (1 << BoardType.STRAW.value) | (1 << BoardType.CRUSHER.value) | \
                 (1 << BoardType.SUGAR.value)
        
        mock_res = MagicMock(spec=CommunicationResult)
        mock_res.was_successful = True
        mock_res.return_parameters = [str(boards)]
        self.mock_mainboard.get.return_value = mock_res
        
        state = StartupState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        next_state = state.update()
        self.assertEqual(next_state, IdleState)

    def test_startup_state_board_error_retry(self):
        self.mock_mainboard.is_connected = True
        self.mock_mainboard.read_message.return_value.message_type = ResponseTypes.STATUS
        self.mock_mainboard.get.return_value = CommunicationResult(CommError.NONE, ["0"]) # No boards
        
        with patch.object(StartupState, '_wait_for_user_input', return_value=True):
            state = StartupState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
            next_state = state.update()
            # Should return None to stay in state and re-check
            self.assertIsNone(next_state)

    def test_idle_state_update(self):
        self.mock_mainboard.is_connected = True
        self.mock_mainboard.supports_is_idle_command = True
        self.mock_mainboard.get.return_value = CommunicationResult(True, ["1"])
        
        mock_task = MagicMock()
        self.mock_context.get_next_idle_task.return_value = mock_task
        
        state = IdleState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        next_state = state.update()
        self.assertIsNone(next_state)
        mock_task.execute.assert_called_once_with(self.mock_mainboard)

    @patch.object(BarBotState, '_wait_for_glass', return_value=True)
    def test_mixing_state_aborted_by_user(self, mock_wait_glass):
        recipe = MagicMock()
        recipe.items = [MagicMock()]
        options = MixingOptions(recipe=recipe)
        self.mock_context.current_mixing_options = options
        self.mock_context.should_abort_mixing = True
        
        state = MixingState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        state._finish_mixing = MagicMock()
        
        next_state = state.update()
        self.assertEqual(next_state, IdleState)
        self.assertFalse(state._finish_mixing.called)

    @patch.object(BarBotState, '_wait_for_glass', return_value=False)
    def test_crushing_state_no_glass_aborts(self, mock_wait_glass):
        state = CrushingState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        next_state = state.update()
        self.assertEqual(next_state, IdleState)

    @patch.object(BarBotState, '_wait_for_glass', return_value=True)
    @patch.object(BarBotState, '_add_ice_once', return_value=0)
    def test_crushing_state_success(self, mock_add_ice, mock_wait_glass):
        state = CrushingState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        state.on_enter()
        next_state = state.update()
        self.assertEqual(next_state, IdleState)

    @patch.object(BarBotState, '_wait_for_glass', return_value=False)
    def test_straw_state_no_glass_aborts(self, mock_wait_glass):
        state = StrawState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        next_state = state.update()
        self.assertEqual(next_state, IdleState)

    @patch.object(BarBotState, '_wait_for_glass', return_value=True)
    @patch.object(BarBotState, '_add_straw', return_value=True)
    def test_straw_state_success(self, mock_add_straw, mock_wait_glass):
        state = StrawState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        next_state = state.update()
        self.assertEqual(next_state, IdleState)

    def test_cleaning_cycle_state_confirmed(self):
        self.mock_context.pumps_to_clean = [1, 2]
        with patch.object(CleaningCycleState, '_wait_for_user_input', return_value=True):
            self.mock_context.user_input = UserInputType.YES
            state = CleaningCycleState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
            next_state = state.update()
            self.assertEqual(next_state, IdleState)
            # Should have called 'Clean' twice
            self.assertEqual(self.mock_mainboard.do.call_count, 2)

    @patch.object(BarBotState, '_wait_for_glass', return_value=True)
    @patch.object(BarBotState, '_draft_one', return_value=True)
    def test_single_ingredient_state_success(self, mock_draft, mock_wait_glass):
        state = SingleIngredientState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        next_state = state.update()
        self.assertEqual(next_state, IdleState)
        self.assertTrue(mock_draft.called)

    # Base class functionality tests
    def test_barbot_state_has_glass(self):
        state = IdleState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        self.mock_mainboard.get.return_value = CommunicationResult(CommError.NONE, ["1"])
        self.assertTrue(state._has_glas())
        
        self.mock_mainboard.get.return_value = CommunicationResult(CommError.NONE, ["0"])
        self.assertFalse(state._has_glas())

    @patch.object(BarBotState, '_has_glas', side_effect=[False, True])
    def test_wait_for_glass_success(self, mock_has_glas):
        state = IdleState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        success = state._wait_for_glass()
        self.assertTrue(success)
        self.assertEqual(mock_has_glas.call_count, 2)

    def test_draft_one_ingredient_empty(self):
        item = MagicMock()
        item.ingredient = MagicMock()
        item.ingredient.type = IngredientType.SPIRIT
        item.ingredient.name = "Any"
        item.ingredient.density = 1.0
        item.amount = 10
        self.mock_ports.port_of_ingredient.return_value = 1
        
        # Mock INGREDIENT_EMPTY error
        self.mock_mainboard.set.return_value = CommunicationResult(CommError.NONE)
        self.mock_mainboard.do.return_value = CommunicationResult(CommError.INGREDIENT_EMPTY)
        
        state = IdleState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        
        # Mock _wait_for_user_input to return True (user says they refilled)
        with patch.object(IdleState, '_wait_for_user_input', return_value=True):
            # It should retry once and then we can make it succeed
            self.mock_mainboard.do.side_effect = [
                CommunicationResult(CommError.INGREDIENT_EMPTY),
                CommunicationResult(CommError.NONE)
            ]
            self.mock_context.user_input = UserInputType.YES
            success = state._draft_one(item)
            self.assertTrue(success)
            self.assertEqual(self.mock_mainboard.do.call_count, 2)

    def test_draft_one_abort_on_empty(self):
        item = MagicMock()
        item.ingredient = MagicMock()
        item.ingredient.type = IngredientType.SPIRIT
        item.ingredient.name = "Any"
        item.ingredient.density = 1.0
        item.amount = 10
        self.mock_ports.port_of_ingredient.return_value = 1
        self.mock_mainboard.set.return_value = CommunicationResult(CommError.NONE)
        self.mock_mainboard.do.return_value = CommunicationResult(CommError.INGREDIENT_EMPTY)
        
        state = IdleState(self.mock_config, self.mock_ports, self.mock_mainboard, self.mock_context)
        
        # Mock _wait_for_user_input to return False (user aborts)
        with patch.object(IdleState, '_wait_for_user_input', return_value=False):
            success = state._draft_one(item)
            self.assertFalse(success)
