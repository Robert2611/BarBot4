import sys
import time
import threading
import os

from threading import Thread
from protocol import Protocol
from protocol import MessageTypes


class StateMachine(Thread):
    def __init__(self, OnMixingFinishedHandler, port, baudrate):
        Thread.__init__(self)
        self.abort = False
        self.data = None
        self.OnMixingFinished = OnMixingFinishedHandler
        self.action = "connecting"
        self.protocol = Protocol(port, baudrate, 1)  # '/dev/ttyAMA0'
        self.message = None
        self.progress = None
        self.rainbow_duration = 10
        self.max_speed = 100
        self.max_accel = 100

    # main loop, runs the whole time
    def run(self):
        while not self.abort:
            if self.action == "connecting":
                if self.protocol.Connect():
                    self.action = "startup"
                else:
                    time.sleep(1)
            elif self.action == "startup":
                if self.protocol.ReadMessage().type == MessageTypes.STATUS:
                    # start the LED rainbow
                    self.protocol.Set("SetRBDuration", self.rainbow_duration)
                    self.protocol.Set("SetSpeed", self.max_speed)
                    self.protocol.Set("SetAccel", self.max_accel)
                    self.action = "idle"
            elif self.action == "mixing":
                self.doMixing()
            elif self.action == "cleaning":
                self.doCleaning()
            elif self.action == "cleaning_cycle":
                self.doCleaningCycle()
            elif self.action == "single_ingredient":
                self.doSingleIngredient()
            else:
                # elif self.action == idle:
                #update as long as there is data to be read
                while True:
                    if not self.protocol.Update():
                        break
                if not self.protocol.isConnected:
                    self.action = "connecting"
        self.protocol.Close()

    def isArduinoBusy(self):
        return self.action != "idle"

    def canManipulateDatabase(self):
        return self.action == "connecting" or self.action == "idle"

    # do commands

    def doMixing(self):
        self.message = "place_glas"
        while self.protocol.Get("HasGlas") != "1":
            pass
        self.message = None
        for item in self.data["recipe"]["items"]:
            if item["port"] == 12:
                self.protocol.Do("Stir", item["amount"] * 1000)
            else:
                self.protocol.Do("Draft", item["port"], item["amount"] * item["calibration"])
            self.data["recipe_item_index"] += 1
            self.progress = self.data["recipe_item_index"] / \
                len(self.data["recipe"]["items"])
        self.protocol.Do("Move", 0)
        self.message = "mixing_done_remove_glas"
        while self.protocol.Get("HasGlas") != "0":
            pass
        self.message = None
        self.OnMixingFinished(self.data["recipe"]["id"])
        self.action = "idle"

    def doCleaningCycle(self):
        self.message = "place_glas"
        while self.protocol.Get("HasGlas") != "1":
            pass
        self.message = None
        for item in self.data:
            self.protocol.Do("Draft", item["port"], item["duration"])
        self.protocol.Do("Move", 0)
        self.action = "idle"

    def doCleaning(self):
        self.protocol.Do("Pump", self.data["port"], self.data["duration"])
        self.action = "idle"

    def doSingleIngredient(self):
        self.message = "place_glas"
        while self.protocol.Get("HasGlas") != "1":
            pass
        self.message = None
        self.protocol.Do("Draft", self.data["port"], self.data["amount"] * self.data["calibration"])
        self.protocol.Do("Move", 0)
        self.action = "idle"

    # start commands

    def startMixing(self, recipe):
        self.data = {"recipe": recipe, "recipe_item_index": 0}
        self.action = "mixing"

    def startSingleIngredient(self, recipe_item):
        self.data = recipe_item
        self.action = "single_ingredient"

    def startCleaning(self, port, duration):
        self.data = {"port": port, "duration": duration}
        self.action = "cleaning"

    def startCleaningCycle(self, data):
        self.data = data
        self.action = "cleaning_cycle"
