import sys
import time
import threading
import os

from threading import Thread
import Protocol

from enum import Enum, auto

class State(Enum):
    CONNECTING = auto()
    STARTUP = auto()
    IDLE = auto()
    MIXING = auto()
    CLEANING = auto()
    CLEANING_CYCLE = auto()
    SINGLE_INGREDIENT = auto()


class StateMachine(Thread):
    OnMixingFinished = None
    OnMixingProgressChanged = None
    OnStateChanged = None

    def __init__(self, port, baudrate):
        Thread.__init__(self)
        self.abort = False
        self.data = None
        self.setState(State.CONNECTING)
        self.protocol = Protocol.Protocol(port, baudrate, 1)
        self.message = None
        self.progress = None
        self.rainbow_duration = 10
        self.max_speed = 100
        self.max_accel = 100
        self.user_input = None

    # main loop, runs the whole time
    def run(self):
        while not self.abort:
            if self.state == State.CONNECTING:
                if self.protocol.Connect():
                    self.setState(State.STARTUP)
                else:
                    time.sleep(1)
            elif self.state == State.STARTUP:
                if self.protocol.ReadMessage().type == Protocol.MessageTypes.STATUS:
                    self.protocol.Set("SetLED", 3)
                    self.protocol.Set("SetSpeed", self.max_speed)
                    self.protocol.Set("SetAccel", self.max_accel)
                    self.setState(State.IDLE)
            elif self.state == State.MIXING:
                self.doMixing()
            elif self.state == State.CLEANING:
                self.doCleaning()
            elif self.state == State.CLEANING_CYCLE:
                self.doCleaningCycle()
            elif self.state == State.SINGLE_INGREDIENT:
                self.doSingleIngredient()
            else:
                # update as long as there is data to be read
                while self.protocol.Update():
                    pass
                if not self.protocol.isConnected:
                    self.setState(State.CONNECTING)
        self.protocol.Close()
    
    def setState(self, state):
        self.state = state
        if self.OnStateChanged != None:
            self.OnStateChanged()

    def isArduinoBusy(self):
        return self.state != State.IDLE

    def canManipulateDatabase(self):
        return self.state == State.CONNECTING or self.state == State.IDLE

    # do commands

    def doMixing(self):
        # wait for the glas
        self.message = "place_glas"
        self.protocol.Do("PlatformLED", 4)
        while self.protocol.Get("HasGlas") != "1":
            pass
        # glas is there, wait a second to let the user take away the hand
        self.protocol.Do("PlatformLED", 3)
        self.message = None
        time.sleep(1)
        self.protocol.Do("PlatformLED", 5)
        for item in self.data["recipe"]["items"]:
            # don't do anything else if user has aborted
            self.protocol.Set("SetLED", 4)
            # do the actual draft and exit the loop if it did not succeed
            if not self.draft_one(item):
                break
            self.data["recipe_item_index"] += 1
            self.progress = self.data["recipe_item_index"] / \
                len(self.data["recipe"]["items"])
            if self.OnMixingProgressChanged != None:
                self.OnMixingProgressChanged(self.progress)
        self.protocol.Do("Move", 0)
        self.message = "mixing_done_remove_glas"
        self.protocol.Do("PlatformLED", 2)
        self.protocol.Set("SetLED", 2)
        while self.protocol.Get("HasGlas") != "0":
            time.sleep(0.5)
        self.message = None
        self.protocol.Do("PlatformLED", 0)
        if OnMixingFinished != None:
            self.OnMixingFinished(self.data["recipe"]["id"])
        self.protocol.Set("SetLED", 3)
        self.setState(State.IDLE)

    def draft_one(self, item):
        if item["port"] == 12:
            self.protocol.Do("Stir", item["amount"] * 1000)
        else:
            while True:
                result = self.protocol.Do("Draft", item["port"], int(
                    item["amount"] * item["calibration"]))
                if result == True:
                    # drafting successfull
                    return True
                elif type(result) is list and len(result) >= 2 and int(result[0]) == 12:
                    #ingredient is empty
                    # safe how much is left to draft
                    item["amount"] = int(result[1]) / item["calibration"]
                    print("ingredient_empty")
                    self.message = "ingredient_empty"
                    self.user_input = None
                    # wait for user input
                    while self.user_input == None:
                        time.sleep(0.5)
                    # remove the message again
                    self.message = None
                    if self.user_input == False:
                        return False
                    # repeat the loop
                else:
                    # unhandled error while drafting
                    return False

    def doCleaningCycle(self):
        self.message = "place_glas"
        while self.protocol.Get("HasGlas") != "1":
            time.sleep(0.5)
        self.message = None
        for item in self.data:
            self.protocol.Do("Draft", item["port"], item["duration"])
        self.protocol.Do("Move", 0)
        self.setState(State.IDLE)

    def doCleaning(self):
        self.protocol.Do("Pump", self.data["port"], self.data["duration"])
        self.setState(State.IDLE)

    def doSingleIngredient(self):
        self.message = "place_glas"
        while self.protocol.Get("HasGlas") != "1":
            time.sleep(0.5)
        self.message = None
        self.draft_one(self.data)
        self.protocol.Do("Move", 0)
        self.setState(State.IDLE)

    # start commands

    def startMixing(self, recipe):
        self.data = {"recipe": recipe, "recipe_item_index": 0}
        self.setState(State.MIXING)

    def startSingleIngredient(self, recipe_item):
        self.data = recipe_item
        self.setState(State.SINGLE_INGREDIENT)

    def startCleaning(self, port, duration):
        self.data = {"port": port, "duration": duration}
        self.setState(State.CLEANING)

    def startCleaningCycle(self, data):
        self.data = data
        self.setState(State.CLEANING_CYCLE)
