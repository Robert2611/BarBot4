import unittest
from unittest.mock import MagicMock, patch
from barbot.logic.communication import (
    ErrorType, CommunicationResult, ResponseTypes, 
    FirmwareVersion, decode_firmware_version, is_mainboard_error,
    Mainboard, MainboardConnectionBluetooth, MainboardConnectionMockup
)
from barbot.logic.communication.connection import MainboardConnection

class TestCommunicationCommon(unittest.TestCase):
    def test_firmware_version_comparison(self):
        v1 = FirmwareVersion(1, 2, 3)
        v2 = FirmwareVersion(1, 2, 4)
        v3 = FirmwareVersion(1, 3, 0)
        v4 = FirmwareVersion(2, 0, 0)
        
        self.assertTrue(v1 < v2)
        self.assertTrue(v2 < v3)
        self.assertTrue(v3 < v4)
        self.assertEqual(v1, FirmwareVersion(1, 2, 3))
        self.assertNotEqual(v1, "not a version")

    def test_decode_firmware_version(self):
        v = decode_firmware_version(10203)
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 2)
        self.assertEqual(v.patch, 3)
        self.assertEqual(str(v), "v1.2.3")

    def test_is_mainboard_error(self):
        self.assertTrue(is_mainboard_error(ErrorType.INGREDIENT_EMPTY))
        self.assertFalse(is_mainboard_error(ErrorType.NONE))
        self.assertFalse(is_mainboard_error(ErrorType.COMM_ERROR))
        self.assertFalse(is_mainboard_error(None))

    def test_communication_result(self):
        res = CommunicationResult(ErrorType.NONE, ["param1"])
        self.assertTrue(res.was_successful)
        self.assertEqual(res.return_parameters, ["param1"])

class TestMainboard(unittest.TestCase):
    def setUp(self):
        self.mock_conn = MagicMock(spec=MainboardConnection)
        self.mainboard = Mainboard(self.mock_conn)

    def test_connect_success(self):
        self.mock_conn.is_connected = True
        # Mock get("GetFirmwareVersion")
        # mainboard.get calls send_command_and_read_response
        # which calls read_non_status_message
        # which calls read_message
        
        # Simpler: patch mainboard.get
        with patch.object(Mainboard, 'get') as mock_get:
            mock_get.return_value = CommunicationResult(ErrorType.NONE, ["10203"])
            success = self.mainboard.connect("identifier")
            self.assertTrue(success)
            self.assertEqual(self.mainboard.firmware_version, FirmwareVersion(1, 2, 3))

    def test_connect_failure(self):
        self.mock_conn.is_connected = False
        success = self.mainboard.connect("identifier")
        self.assertFalse(success)

    def test_read_message_success(self):
        self.mock_conn.is_connected = True
        self.mock_conn.read_line.return_value = "ACK Command Param1 Param2"
        msg = self.mainboard.read_message()
        self.assertEqual(msg.message_type, ResponseTypes.ACK)
        self.assertEqual(msg.command, "Command")
        self.assertEqual(msg.parameters, ["Param1", "Param2"])

    def test_read_message_unknown_type(self):
        self.mock_conn.is_connected = True
        self.mock_conn.read_line.return_value = "INVALID Command"
        msg = self.mainboard.read_message()
        self.assertEqual(msg.message_type, ResponseTypes.COMM_ERROR)

    def test_read_message_wrong_format(self):
        self.mock_conn.is_connected = True
        self.mock_conn.read_line.return_value = "ACK"
        msg = self.mainboard.read_message()
        self.assertEqual(msg.message_type, ResponseTypes.COMM_ERROR)

    def test_do_command_success(self):
        # Mock send_command_and_read_response for the initial call
        # Mock read_message for the "DONE" response
        with patch.object(Mainboard, 'send_command_and_read_response') as mock_send, \
             patch.object(Mainboard, 'read_message') as mock_read:
            
            mock_send.return_value = CommunicationResult(ErrorType.NONE)
            mock_read.side_effect = [
                # First read_message for DONE
                MagicMock(message_type=ResponseTypes.DONE, command="TestCmd")
            ]
            
            res = self.mainboard.do("TestCmd")
            self.assertTrue(res.was_successful)

    def test_get_command_success(self):
        with patch.object(Mainboard, 'send_command_and_read_response') as mock_send:
            mock_send.return_value = CommunicationResult(ErrorType.NONE, ["Value"])
            res = self.mainboard.get("GetCmd")
            self.assertTrue(res.was_successful)
            self.assertEqual(res.return_parameters, ["Value"])

    def test_get_command_no_result(self):
        with patch.object(Mainboard, 'send_command_and_read_response') as mock_send:
            mock_send.return_value = CommunicationResult(ErrorType.NONE, [])
            res = self.mainboard.get("GetCmd")
            self.assertEqual(res.error, ErrorType.NO_RESULT_SENT)

    def test_do_command_retry_on_failure(self):
        with patch.object(Mainboard, 'send_command_and_read_response') as mock_send, \
             patch.object(Mainboard, 'read_message') as mock_read:
            
            # First attempt fails with a non-mainboard error (should retry)
            # Second attempt succeeds
            mock_send.side_effect = [
                CommunicationResult(ErrorType.WRONG_ANSWER),
                CommunicationResult(ErrorType.NONE)
            ]
            mock_read.return_value = MagicMock(message_type=ResponseTypes.DONE, command="TestCmd")
            
            res = self.mainboard.do("TestCmd")
            self.assertTrue(res.was_successful)
            self.assertEqual(mock_send.call_count, 2)

    def test_do_command_abort_on_mainboard_error(self):
        with patch.object(Mainboard, 'send_command_and_read_response') as mock_send:
            # Mainboard error like INGREDIENT_EMPTY should NOT retry in 'do' 
            # (the higher logic/states should handle it)
            mock_send.return_value = CommunicationResult(ErrorType.INGREDIENT_EMPTY)
            
            res = self.mainboard.do("TestCmd")
            self.assertEqual(res.error, ErrorType.INGREDIENT_EMPTY)
            self.assertEqual(mock_send.call_count, 1)

    def test_send_command_and_read_response_nak(self):
        with patch.object(Mainboard, 'send_command') as mock_send, \
             patch.object(Mainboard, 'read_non_status_message') as mock_read:
            
            mock_send.return_value = True
            mock_read.return_value = MagicMock(message_type=ResponseTypes.NAK, command="TestCmd")
            
            res = self.mainboard.send_command_and_read_response("TestCmd")
            self.assertEqual(res.error, ErrorType.NACK_RECEIVED)

    def test_send_command_and_read_response_error(self):
        with patch.object(Mainboard, 'send_command') as mock_send, \
             patch.object(Mainboard, 'read_non_status_message') as mock_read:
            
            mock_send.return_value = True
            # Simulate "ERROR INGREDIENT_EMPTY"
            mock_read.return_value = MagicMock(
                message_type=ResponseTypes.ERROR, 
                command="TestCmd",
                parameters=["INGREDIENT_EMPTY"]
            )
            
            res = self.mainboard.send_command_and_read_response("TestCmd")
            self.assertEqual(res.error, ErrorType.INGREDIENT_EMPTY)

    def test_read_non_status_message_skips_status(self):
        with patch.object(Mainboard, 'read_message') as mock_read:
            # First returns STATUS, then ACK
            mock_read.side_effect = [
                MagicMock(message_type=ResponseTypes.STATUS),
                MagicMock(message_type=ResponseTypes.ACK)
            ]
            msg = self.mainboard.read_non_status_message()
            self.assertEqual(msg.message_type, ResponseTypes.ACK)
            self.assertEqual(mock_read.call_count, 2)

    def test_send_command_success(self):
        self.mock_conn.is_connected = True
        success = self.mainboard.send_command("Test", "P1")
        self.assertTrue(success)
        self.mock_conn.send.assert_called_with("Test P1")

class TestMockup(unittest.TestCase):
    def test_mockup_flow(self):
        conn = MainboardConnectionMockup()
        conn.send("Draft 1 20")
        # First read is ACK
        line = conn.read_line()
        self.assertEqual(line, "ACK Draft")
        # Subsequent reads are STATUS or DONE
        # The mockup timing might need sleep if we don't mock time
        with patch('time.sleep'):
            line = conn.read_line()
            # It might be STATUS or DONE depending on duration_DO
            self.assertIn(line.split()[0], ["STATUS", "DONE"])

    def test_mockup_getter(self):
        conn = MainboardConnectionMockup()
        conn.set_result_for_getter("GetWeight", 100)
        conn.send("GetWeight")
        line = conn.read_line()
        self.assertEqual(line, "ACK GetWeight 100")
