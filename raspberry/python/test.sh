#!/bin/bash
#alternative without pytest:
#python3 -m unittest discover -s test_barbot -t test

#to install pytest:
#python3 -m pip install pytest-qt
#python3 -m pip install pytest-timeout

python3 -m pytest
