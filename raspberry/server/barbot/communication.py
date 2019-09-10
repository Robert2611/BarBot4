import time
from enum import Enum, auto
import logging
import serial
import sys

class MessageTypes(Enum):
    ACK = auto()
    NAK = auto()
    DONE = auto()
    ERROR = auto()
    STATUS = auto()
    COMM_ERROR = auto()
    TIMEOUT = auto()

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
        self.is_connected = False
        self.timeout = timeout

    def connect(self):
        if self.ser is not None and self.ser.isOpen():
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
        self.is_connected = True
        return True

    def send_do(self, command, parameter1, parameter2=None):
        # clear the input
        while self.has_data():
            self.read_message()
        # send the command
        if parameter2 is not None:
            self.send_command(command, [parameter1, parameter2])
        else:
            self.send_command(command, [parameter1])
        # wait for the response
        message = self.read_message()
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
            message = self.read_message()
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

    def send_set(self, command, parameter=None):
        # clear the input
        while self.has_data():
            self.read_message()
        # send the command
        self.send_command(command, [parameter])
        # wait for the response
        message = self.read_message()
        if message.command != command:
            self.error = "answer for wrong command"
            return False
        if message.type == MessageTypes.NAK:
            self.error = "NAK received"
            return False
        if message.type != MessageTypes.ACK:
            self.error = "wrong answer"
            return False

    def send_get(self, command, parameters=None):
        # clear the input
        while self.has_data():
            self.read_message()
        # send the command
        self.send_command(command, parameters)
        # wait for the response
        message = self.read_message()
        if message.command != command:
            self.error = "answer for wrong command"
            return False
        if message.type == MessageTypes.ACK:
            if message.parameters is not None:
                return message.parameters[0]
            else:
                self.error = "No result sent"
                return False
        if message.type == MessageTypes.NAK:
            self.error = "NAK received"
            return False

    def read_message(self) -> ProtocolMessage:
        if self.ser == None or not self.ser.isOpen():
            self.is_connected = False
            return ProtocolMessage(MessageTypes.COMM_ERROR, "port not open")
        try:
            b_line = bytes()
            while True:
                c = self.ser.read()
                if c == b'\n':
                    break
                elif c == b'':
                    print("EOS")
                    self.is_connected = False
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
            self.is_connected = False
            print(e)
            return ProtocolMessage(MessageTypes.COMM_ERROR, e)

    def send_command(self, command, parameters):
        if self.ser is not None:
            cmd = command
            if parameters is not None:
                for parameter in parameters:
                    cmd = cmd + " " + str(parameter)
            cmd = cmd + "\r"
            print(">" + cmd)
            self.ser.write(cmd.encode())

    def close(self):
        if self.ser is not None:
            self.ser.close()

    def has_data(self):
        return self.ser.in_waiting > 0

    def update(self):
        if self.ser == None or not self.ser.isOpen():
            self.is_connected = False
            return False
        result = self.read_message()
        return self.has_data()
