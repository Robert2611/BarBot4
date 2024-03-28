#!/bin/bash
#alternative without pytest:
#python3 -m unittest discover -s test_barbot -t test

#to install pytest:
#python3 -m pip install pytest-qt
#python3 -m pip install pytest-timeout

# make sure to execute in the test folder
SCRIPT_FILE="$0"
SCRIPT_FOLDER=$(dirname "$SCRIPT_FILE")
cd "$SCRIPT_FOLDER"
python3 -m pytest test/test_barbot.py -v
python3 -m pytest test/test_gui.py -v