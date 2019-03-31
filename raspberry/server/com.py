import sys
import time
import threading
import os

from threading import Thread
from arduino import Arduino
from arduino import MessageTypes

class com(Thread):
	def __init__(self, OnMixingFinishedHandler, port, baudrate):
		Thread.__init__(self)
		self.abort = False
		self.data = None
		self.OnMixingFinished = OnMixingFinishedHandler
		self.action = "connecting"
		self.arduino = Arduino(port, baudrate, 1)#'/dev/ttyAMA0'
		self.message = None
		self.progress = None
		self.settings = None

	#main loop, runs the whole time
	def run(self):
		while not self.abort:
			if self.action == "connecting":
				if self.arduino.Connect():
					self.action = "startup"
				else:
					time.sleep(1)
			elif self.action == "startup":
				if self.arduino.ReadMessage().type == MessageTypes.IDLE:
					#start the LED rainbow
					self.arduino.Set("rainbow", self.settings["rainbow_duration"])
					self.arduino.Set("maxs", self.settings["max_speed"])
					self.arduino.Set("maxa", self.settings["max_accel"])
					self.action = "idle"
			elif self.action == "mixing":
				self.doMixing()
			elif self.action == "cleaning":
				self.doCleaning()
			elif self.action == "cleaning_cycle":
				self.doCleaningCycle()
			elif self.action == "single_ingredient":
				self.doCleaningCycle();
			else:
				#elif self.action == idle:
				message = self.arduino.ReadMessage()
				if message.type != MessageTypes.IDLE:
					self.action = "connecting"
		self.arduino.Close()

	def isArduinoBusy(self):
		return self.action != "idle"

	def canManipulateDatabase(self):
		return self.action == "connecting" or self.action == "idle"

	#do commands

	def doMixing(self):
		self.message = "place_glas"
		while self.arduino.Get("GLAS") != "1":
			pass
		self.message = None
		for item in self.data["recipe"]["items"]:
			if item["port"] == 12:
				self.arduino.Do("STIR", item["amount"] * 1000)
			else:
				self.arduino.Do("DRAFT", item["port"], item["amount"] * item["calibration"])
			self.data["recipe_item_index"] += 1
			self.progress = self.data["recipe_item_index"] / len(self.data["recipe"]["items"])
		self.arduino.Do("MOVETO", 0)
		self.message = "remove_glas"
		while self.arduino.Get("GLAS") != "0":
			pass
		self.message = None
		self.OnMixingFinished(self.data["recipe"]["id"])
		self.action = "idle"

	def doCleaningCycle(self):
		self.message = "place_glas"
		while self.arduino.Get("GLAS") != "1":
			pass
		self.message = None
		for item in self.data:
			self.arduino.Do("DRAFT", item["port"], item["duration"])
		self.arduino.Do("MOVETO", 0)
		self.action = "idle"

	def doCleaning(self):
		self.arduino.Do("DRAFT", self.data["port"], self.data["duration"])
		self.action = "idle"

	#start commands

	def startMixing(self, recipe):
		self.data = {"recipe":recipe, "recipe_item_index":0}
		self.action = "mixing"

	def startSingleIngredient(self, port, duration):
		self.data = {"port":port, "duration":duration}
		self.action = "single_ingredient"

	def startCleaning(self, port, duration):
		self.data = {"port":port, "duration":duration}
		self.action = "cleaning"

	def startCleaningCycle(self, data):
		self.data = data
		self.action = "cleaning_cycle"
