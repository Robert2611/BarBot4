import time
from enum import Enum
import logging
import serial
import sys

MessageTypes = Enum("MessageTypes", 'ACK NAK VAL BUSY IDLE COMM_ERROR TIMEOUT')

class ArduinoMessage():
    def __init__(self, type, parameter=None):
        self.type = type
        self.parameter = parameter


class Arduino():
    def __init__(self, port, baud, timeout):
        self.baud = baud
        self.devicename = port
        self.error = None
        self.ser = None
        self.isConnected = False
        self.timeout = timeout

    def Connect(self):
        if self.ser != None and self.ser.isOpen():
            self.ser.close()
        try:
            self.ser = serial.Serial(
                self.devicename, self.baud, timeout=self.timeout)
            # wait for Arduino to initialize
            time.sleep(1)
        except Exception as message:
            print("connection to %s failed" % (self.devicename))
            return False
        print("connection to %s successfull" % (self.devicename))
        while self.ser.in_waiting:
            self.ser.read()
        self.isConnected = True
        return True

    def Do(self, command, parameter1=None, parameter2=None, timeout=60):
        self.SendCommand(command, parameter1, parameter2)
        message = self.ReadMessage()
        if message.type == MessageTypes.NAK:
            self.error = "NAK received"
            return False
        if message.type != MessageTypes.ACK:
            self.error = "wrong answer"
            return False
        startTime = time.time()
        while True:
            if time.time()-startTime > timeout:
                self.error = "timeout"
                return False
            message = self.ReadMessage()
            if message.type == MessageTypes.BUSY:
                continue
            elif message.type == MessageTypes.IDLE:
                return True
            else:
                self.error = "wrong answer"
                return False

    def Set(self, command, parameter1=None, parameter2=None):
        self.SendCommand(command, parameter1, parameter2)
        message = self.ReadMessage()
        if message.type == MessageTypes.NAK:
            self.error = "NAK received"
            return False
        if message.type != MessageTypes.ACK:
            self.error = "wrong answer"
            return False

    def Get(self, command, parameter1=None, parameter2=None):
        self.SendCommand(command, parameter1, parameter2)
        message = self.ReadMessage()
        if message.type == MessageTypes.NAK:
            self.error = "NAK received"
            return False
        if message.type != MessageTypes.VAL:
            self.error = "wrong answer"
            return False
        return message.parameter

    def ReadMessage(self):
        if self.ser == None or not self.ser.isOpen():
            self.isConnected = False
            return ArduinoMessage(MessageTypes.COMM_ERROR, "port not open")
        try:
            b_line = bytes()
            while True:
                c = self.ser.read()
                if c == b'\n':
                    break
                elif c == b'':
                    return ArduinoMessage(MessageTypes.COMM_ERROR, "end of string")
                else:
                    b_line += c
            line = b_line.decode('utf-8')
            if not line.startswith(">"):
                return ArduinoMessage(MessageTypes.COMM_ERROR, "start sign missing")
            line = line[1:]
            line = line.replace("\r\n", "")
            token = line.split()
            for type in MessageTypes:
                if type.name == token[0]:
                    if len(token) > 1:
                        return ArduinoMessage(type, token[1])
                    else:
                        return ArduinoMessage(type)
        except Exception as e:
            print(e)
            return ArduinoMessage(MessageTypes.COMM_ERROR, e)

    def SendCommand(self, command, parameter1=None, parameter2=None):
        if self.ser != None:
            cmd = ">" + command
            if parameter1 != None:
                cmd = cmd + " " + str(parameter1)
            if parameter2 != None:
                cmd = cmd + " " + str(parameter2)
            cmd = cmd + "\n"
            self.ser.write(cmd.encode())

    def Close(self):
        self.ser.close()
