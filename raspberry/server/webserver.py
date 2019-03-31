#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import server
import os
import sys
import logging
import subprocess
import time

def getRelative(relative_path):
	dirname = sys.path[0]
	filename = os.path.join(dirname, relative_path)
	return filename

def OnRequest(action, data):
	logging.info("Request recieved: %s" % action)
	if action == "start":
		run_command([getRelative("main.py&")])
	elif action == "shutdown":
		run_command(["sudo shutdown now"])
	elif action == "reboot":
		run_command(["sudo reboot"])
	logging.info("Request finished: %s" % action)
	return {}
	
def run_command(cmd_str):
	subprocess.Popen(cmd_str, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
	
logging.basicConfig(
	level = logging.INFO,
	format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
	datefmt = '%d.%m.%y %H:%M',
	filename = 'bar_bot_server.log'
)
	
server = server.server(OnRequest, 1234)
server.start()
#start main program
run_command([getRelative("main.py&")])
time.sleep(20)
run_command(["sudo rfcomm connect hci0 20:16:04:14:60:60&"])