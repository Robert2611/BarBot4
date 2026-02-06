import pytest
import os
import tempfile
import threading
from unittest.mock import MagicMock, patch, mock_open
from PyQt5 import QtWidgets, QtCore
from barbot.barbottools import get_commands, get_errors, ProtocolThread, GuiLogger, ToolsWindow
from barbot.logic.communication import Mainboard

@pytest.fixture
def mock_firmware_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, "src")
        include_dir = os.path.join(tmpdir, "include")
        os.makedirs(src_dir)
        os.makedirs(include_dir)
        
        main_cpp = os.path.join(src_dir, "main.cpp")
        with open(main_cpp, "w") as f:
            f.write('protocol.addDoCommand("TestDo", 1);\n')
            f.write('protocol.addSetCommand("TestSet", 1);\n')
            f.write('protocol.addGetCommand("TestGet");\n')
            
        state_machine_h = os.path.join(include_dir, "StateMachine.h")
        with open(state_machine_h, "w") as f:
            f.write("enum BarBotStatus_t {\n")
            f.write("  Error = 32,\n")
            f.write("  ErrorOne,\n")
            f.write("  ErrorTwo,\n")
            f.write("};\n")
            
        yield tmpdir

def test_get_commands(mock_firmware_dir):
    cmds = get_commands(mock_firmware_dir)
    assert len(cmds) == 3
    assert cmds[0]["name"] == "TestDo"
    assert cmds[0]["type"] == "Do"
    assert cmds[1]["name"] == "TestSet"
    assert cmds[2]["name"] == "TestGet"

def test_get_errors(mock_firmware_dir):
    errors = get_errors(mock_firmware_dir)
    assert errors[33] == "One"
    assert errors[34] == "Two"

def test_protocol_thread_logic():
    mock_mb = MagicMock(spec=Mainboard)
    mock_mb.is_connected = True
    mock_mb.read_message.return_value = MagicMock()
    
    thread = ProtocolThread(mock_mb)
    thread.run_next({"type": "Do", "name": "Mix", "parameters": ["1"]})
    
    # We can't easily run the real loop because it's infinite while not abort
    # But we can test the state transitions if we mock time.sleep to abort
    with patch("time.sleep", side_effect=[None, InterruptedError]):
        try:
            # Manually trigger the inner logic once
            thread.abort = True
            # Simulate one iteration
            thread._mainboard.is_connected = True
            thread._mainboard.read_message.return_value = MagicMock()
            # This is hard to unit test without refactoring ProtocolThread.run
            # Let's at least test the public methods
            thread.send_abort()
            mock_mb.send_abort.assert_called()
        except InterruptedError:
            pass

def test_gui_logger():
    logger = GuiLogger()
    mock_callback = MagicMock()
    logger.qt.new_entry_signal.connect(mock_callback)
    
    record = MagicMock()
    record.levelname = "INFO"
    record.msg = "Test"
    record.args = ()
    record.exc_info = None
    
    with patch.object(logger, "format", return_value="Formatted"):
        logger.emit(record)
        mock_callback.assert_called_with("Formatted\n")

def test_tools_window_initialization(qtbot, mock_firmware_dir):
    mock_thread = MagicMock()
    window = ToolsWindow(mock_thread, mock_firmware_dir)
    qtbot.addWidget(window)
    
    # Check if commands were loaded
    # get_commands returns 3 commands
    assert len(window.commands) == 3
    
    # Check for Los buttons
    buttons = window.findChildren(QtWidgets.QPushButton)
    # 3 commands -> 3 Los buttons + 1 Abort button
    assert len(buttons) >= 4
    
    # Test send_command
    with patch.object(window, "send_command") as mock_send:
        # Trigger button click
        los_button = [b for b in buttons if b.text() == "Los"][0]
        qtbot.mouseClick(los_button, QtCore.Qt.LeftButton)
        mock_send.assert_called()

def test_tools_window_log_add_line(qtbot, mock_firmware_dir):
    mock_thread = MagicMock()
    window = ToolsWindow(mock_thread, mock_firmware_dir)
    qtbot.addWidget(window)
    
    window.log_add_line("Normal log line\n")
    assert "Normal log line" in window.log_widget.toPlainText()
    
    # Test error parsing in log
    # Error index 33 is "One"
    window.log_add_line("ERROR TestCmd 33 0\n")
    assert window.errors_widget.text() == "One"
