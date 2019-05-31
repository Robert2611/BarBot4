import time
from enum import Enum
import logging
import serial
import sys

MessageTypes = Enum(
    "MessageTypes", 'ACK NAK DONE ERROR STATUS COMM_ERROR TIMEOUT')


class ProtocolMessage():
    def __init__(self, type, command, parameters=None):
        self.type = type
        self.command = command
        self.parameters = parameters


class Protocol():
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
        except Exception:
            print("connection to %s failed" % (self.devicename))
            return False
        print("connection to %s successfull" % (self.devicename))
        while self.ser.in_waiting:
            self.ser.read()
        self.isConnected = True
        return True

    def Do(self, command, parameter1, parameter2=None):
        # clear the input
        while self.HasData():
            self.ReadMessage()
        # send the command
        if parameter2 != None:
            self.SendCommand(command, [parameter1, parameter2])
        else:
            self.SendCommand(command, [parameter1])
        # wait for the response
        message = self.ReadMessage()
        if message.command != command:
            self.error = "answer for wrong command"
            return False
        if message.type == MessageTypes.NAK:
            self.error = "NAK received"
            return False
        if message.type != MessageTypes.ACK:
            self.error = "wrong answer"
            return False
        while True:
            message = self.ReadMessage()
            if message.command != command:
                self.error = "answer for wrong command"
                return False
            if message.type == MessageTypes.STATUS:
                # it is still running, all good
                continue
            elif message.type == MessageTypes.DONE:
                return True
            elif message.type == MessageTypes.ERROR:
                # return the error parameters
                return message.parameters
            else:
                self.error = "wrong answer"
                return False

    def Set(self, command, parameter=None):
        # clear the input
        while self.HasData():
            self.ReadMessage()
        # send the command
        self.SendCommand(command, [parameter])
        # wait for the response
        message = self.ReadMessage()
        if message.command != command:
            self.error = "answer for wrong command"
            return False
        if message.type == MessageTypes.NAK:
            self.error = "NAK received"
            return False
        if message.type != MessageTypes.ACK:
            self.error = "wrong answer"
            return False

    def Get(self, command, parameters=None):
        # clear the input
        while self.HasData():
            self.ReadMessage()
        # send the command
        self.SendCommand(command, parameters)
        # wait for the response
        message = self.ReadMessage()
        if message.command != command:
            self.error = "answer for wrong command"
            return False
        if message.type == MessageTypes.ACK:
            if message.parameters != None:
                return message.parameters[0]
            else:
                self.error = "No result sent"
                return False
        if message.type == MessageTypes.NAK:
            self.error = "NAK received"
            return False

    def ReadMessage(self):
        if self.ser == None or not self.ser.isOpen():
            self.isConnected = False
            return ProtocolMessage(MessageTypes.COMM_ERROR, "port not open")
        try:
            b_line = bytes()
            while True:
                c = self.ser.read()
                if c == b'\n':
                    break
                elif c == b'':
                    print("EOS")
                    self.isConnected = False
                    return ProtocolMessage(MessageTypes.COMM_ERROR, "end of string")
                else:
                    b_line += c
            line = b_line.decode('utf-8')
            line = line.replace("\n", "")
            line = line.replace("\r", "")
            print("<" + line)
            tokens = line.split()
            # expected format: <Type> <Command> [Parameter1] [Parameter2] ...
            # find message type
            for type in MessageTypes:
                if type.name == tokens[0]:
                    if len(tokens) < 2:
                        return ProtocolMessage(MessageTypes.COMM_ERROR, "wrong format")
                    elif len(tokens) == 2:
                        return ProtocolMessage(type, tokens[1])
                    else:
                        return ProtocolMessage(type, tokens[1], tokens[2:])
            return ProtocolMessage(MessageTypes.COMM_ERROR, "unknown type")
        except Exception as e:
            self.isConnected = False
            print(e)
            return ProtocolMessage(MessageTypes.COMM_ERROR, e)

    def SendCommand(self, command, parameters):
        if self.ser != None:
            cmd = command
            if parameters != None:
                for parameter in parameters:
                    cmd = cmd + " " + str(parameter)
            cmd = cmd + "\r"
            print(">" + cmd)
            self.ser.write(cmd.encode())

    def Close(self):
        self.ser.close()

    def HasData(self):
        return self.ser.in_waiting > 0

    def Update(self):
        if self.ser == None or not self.ser.isOpen():
            self.isConnected = False
            return False
        result = self.ReadMessage()
        return self.HasData()
