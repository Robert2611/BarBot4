import time
from enum import Enum, auto
import logging
import serial
import sys
import bluetooth
from bluetooth.btcommon import BluetoothError


def find_bar_bot():
    try:
        import bluetooth
        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        for x in nearby_devices:
            if "Bar Bot" in x[1]:
                # save mac address into settings
                return x[0]
    except:
        return None


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
    conn: bluetooth.BluetoothSocket = None
    error = None
    is_connected = False
    buffer: str = ""

    def __init__(self, port, baud, timeout):
        self.baud = baud
        self.devicename = port
        self.timeout = timeout

    def clear_input(self):
        # clear the input
        self.read_message()
        # if an arror accured, return false
        return self.is_connected

    def connect(self, mac_address: str):
        if self.conn is not None:
            self.conn.close()
        try:
            self.conn = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.conn.connect((mac_address, 1))
            self.conn.settimeout(self.timeout)
            # wait for Arduino to initialize
            time.sleep(1)
            self.clear_input()
            self.is_connected = True
            logging.info("connection successfull")
        except Exception as e:
            print(e)
            logging.warn("connection failed %s" % (type(e)))
            return False
        return True

    def _send_do(self, command, parameter1=None, parameter2=None):
        if not self.clear_input():
            return False
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
        if not self.clear_input():
            return False
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
        if not self.clear_input():
            return None
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

    def try_get(self, command, parameters=None):
        for _ in range(3):
            res = self._send_get(command, parameters)
            if res is not None:
                return res
        return None

    def try_set(self, command, parameters=None):
        for _ in range(3):
            if self._send_set(command, parameters):
                return True
        return False

    def try_do(self, command, parameter1=None, parameter2=None):
        for _ in range(3):
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
                self.conn.send(cmd.encode())
                return True
            except Exception:
                logging.exception("Send command failed")
        return False

    def close(self):
        if self.conn is not None:
            self.conn.close()

    def _read_existing(self):
        data = b''
        # make sure to read everything there is
        while True:
            data = self.conn.recv(1024)
            if len(data) < 1024:
                break
        return data.decode('utf-8')

    def read_message(self) -> ProtocolMessage:
        if self.conn == None:
            self.is_connected = False
            return ProtocolMessage(MessageTypes.COMM_ERROR, "port not open")
        try:
            line = ""
            # make sure we have a full line
            while True:
                line += self._read_existing()
                if "\n" in line:
                    break
            # if there is more then one message, only take the last one
            while line.count("\n") > 1:
                line = line[line.index("\n")+1:]
            line = line.replace("\n", "").replace("\r", "")
            logging.debug("<" + line)
            tokens = line.split()
            # expected format: <Type> <Command> [Parameter1] [Parameter2] ...
            # find message type
            for msg_type in MessageTypes:
                if msg_type.name == tokens[0]:
                    if len(tokens) < 2:
                        return ProtocolMessage(MessageTypes.COMM_ERROR, "wrong format")
                    elif len(tokens) == 2:
                        return ProtocolMessage(msg_type, tokens[1])
                    else:
                        return ProtocolMessage(msg_type, tokens[1], tokens[2:])
            return ProtocolMessage(MessageTypes.COMM_ERROR, "unknown type")
        except Exception as e:
            self.is_connected = False
            logging.exception("Read failed")
            return ProtocolMessage(MessageTypes.COMM_ERROR, e)
