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
    ser: serial.Serial = None
    error = None
    is_connected = False

    def __init__(self, port, baud, timeout):
        self.baud = baud
        self.devicename = port
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
            logging.warn("connection to %s failed" % (self.devicename))
            return False
        logging.info("connection to %s successfull" % (self.devicename))
        while self.ser.in_waiting:
            self.ser.read()
        self.is_connected = True
        return True

    def _send_do(self, command, parameter1=None, parameter2=None):
        # clear the input
        while self.has_data():
            self.read_message()
        # send the command
        if parameter1 is not None and parameter2 is not None:
            self.send_command(command, [parameter1, parameter2])
        elif parameter1 is not None:
            self.send_command(command, [parameter1])
        else:
            self.send_command(command)
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

    def _send_set(self, command, parameter=None):
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
        return True

    def _send_get(self, command, parameters=None):
        # clear the input
        while self.has_data():
            self.read_message()
        # send the command
        self.send_command(command, parameters)
        # wait for the response
        message = self.read_message()
        if message.command != command:
            self.error = "answer for wrong command"
            return None
        if message.type == MessageTypes.ACK:
            if message.parameters is not None:
                return message.parameters[0]
            else:
                self.error = "No result sent"
                return None
        if message.type == MessageTypes.NAK:
            self.error = "NAK received"
            return None
        return None

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
                    logging.warn("Read returned empty byte")
                    self.is_connected = False
                    return ProtocolMessage(MessageTypes.COMM_ERROR, "end of string")
                else:
                    b_line += c
            line = b_line.decode('utf-8')
            line = line.replace("\n", "")
            line = line.replace("\r", "")
            logging.debug("<" + line)
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
            logging.exception("Read failed")
            return ProtocolMessage(MessageTypes.COMM_ERROR, e)

    def try_get(self, command, parameters=None):
        for i in range(3):
            res = self._send_get(command, parameters)
            if res is not None:
                return res
        return None

    def try_set(self, command, parameters=None):
        for i in range(3):
            if self._send_set(command, parameters):
                return True
        return False

    def try_do(self, command, parameter1=None, parameter2=None):
        for i in range(3):
            res = self._send_do(command, parameter1, parameter2)
            if res:
                return res
        return False

    def send_command(self, command, parameters=None):
        if self.is_connected:
            cmd = command
            if parameters is not None:
                for parameter in parameters:
                    cmd = cmd + " " + str(parameter)
            cmd = cmd + "\r"
            logging.debug(">" + cmd)
            try:
                if self.ser.write(cmd.encode()) > 0:
                    return True
            except Exception:
                logging.exception("Send command failed")
        return False

    def close(self):
        if self.ser is not None:
            self.ser.close()

    def has_data(self):
        if self.ser == None or not self.ser.isOpen():
            self.is_connected = False
            return False
        try:
            res = self.ser.in_waiting > 0
            return res
        except Exception:
            logging.exception("Receiving data count failed")
        return False

    def update(self):
        if self.ser == None or not self.ser.isOpen():
            self.is_connected = False
            return False
        self.read_message()
        return self.has_data()
