# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring, protected-access
import unittest
from unittest.mock import MagicMock
from barbot.communication import decode_firmware_version, FirmwareVersion, Mainboard
from barbot.mockup import MaiboardConnectionMockup

class TestCommunication(unittest.TestCase):
    def test_firmware_version_decoding(self):
        assert FirmwareVersion(0, 0, 0) == decode_firmware_version(0)
        assert FirmwareVersion(1, 2, 3) == decode_firmware_version(10203)
        assert FirmwareVersion(99, 99, 99) == decode_firmware_version(999999)
        self.assertRaises(Exception, decode_firmware_version, "something")

    def test_firmware_version_comparison(self):
        assert FirmwareVersion(2, 0, 0) == FirmwareVersion(2, 0, 0)
        assert FirmwareVersion(2, 0, 0) > FirmwareVersion(1, 0, 0)
        assert FirmwareVersion(2, 0, 0) >= FirmwareVersion(1, 1, 1)
        assert FirmwareVersion(2, 0, 0) >= FirmwareVersion(1, 3, 3)
        assert FirmwareVersion(1, 1, 1) < FirmwareVersion(2, 0, 0)
        assert FirmwareVersion(1, 5, 5) < FirmwareVersion(2, 0, 0)
        assert FirmwareVersion(1, 5, 5) < FirmwareVersion(1, 6, 0)
        assert FirmwareVersion(1, 5, 5) <= FirmwareVersion(1, 5, 6)
        assert FirmwareVersion(0, 0, 0) <= FirmwareVersion(4, 0, 0)

    def test_mainboard_commands(self):
        connection_mockup = MaiboardConnectionMockup()
        connection_mockup.duration_DO = 0.01
        connection_mockup.duration_SET = 0.01
        connection_mockup.duration_GET = 0.01
        mainboard = Mainboard(connection_mockup)
        for command_name, command_data in connection_mockup.commands.items():
            command_type, parameter_count = command_data
            fake_parameters = ["0" for _ in range(parameter_count)]
            if command_type == "DO":
                result = mainboard.do(command_name, *fake_parameters)
            elif command_type == "SET":
                result = mainboard.set(command_name, *fake_parameters)
            else:
                result = mainboard.set(command_name, *fake_parameters)
            assert result.was_successfull
            if command_type == "GET":
                assert len(result.return_parameters) == 1

    def test_mainboard_command_do(self):
        command = "TESTCOMMAND"
        params = ["1", "2", "3"]
        attrs = {
            "read_line.side_effect" : [
                f"ACK {command}",
                f"STATUS {command}",
                f"STATUS {command}",
                f"DONE {command}"
                ],
            "is_connected" : True
        }
        connection_mockup = MagicMock()
        connection_mockup.configure_mock(**attrs)
        mainboard = Mainboard(connection_mockup)

        result = mainboard.do(command, *params)
        assert result.was_successfull
        connection_mockup.send.assert_called_once_with(f"{command} {' '.join(params)}")

    def test_mainboard_command_get(self):
        command = "TESTCOMMAND"
        params = ["testparam", "2", "3"]
        return_value = 4
        attrs = {
            "read_line.side_effect" : [
                f"ACK {command} {return_value}",
                f"NAK {command}",
                ],
            "is_connected" : True
        }
        connection_mockup = MagicMock()
        connection_mockup.configure_mock(**attrs)
        mainboard = Mainboard(connection_mockup)

        #normal response
        result = mainboard.set(command, *params)
        assert result.was_successfull
        assert result.return_parameters == [str(return_value)]
        connection_mockup.send.assert_called_once_with(f"{command} {' '.join(params)}")


    def test_mainboard_command_set(self):
        command = "TESTCOMMAND"
        params = ["testparam", "2", "3"]
        attrs = {
            "read_line.side_effect" : [
                f"ACK {command}"
                ],
            "is_connected" : True
        }
        connection_mockup = MagicMock()
        connection_mockup.configure_mock(**attrs)
        mainboard = Mainboard(connection_mockup)

        result = mainboard.set(command, *params)
        assert result.was_successfull
        connection_mockup.send.assert_called_once_with(f"{command} {' '.join(params)}")
