import time
from enum import Enum, auto
import logging
import bluetooth

timeout = 1

class Boards(Enum):
    # board addresses must match "shared.h"
    balance = 0x01
    mixer = 0x02
    straw = 0x03
    crusher = 0x04
    sugar = 0x05


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


conn: bluetooth.BluetoothSocket = None
error = None
is_connected = False
buffer: str = ""


def find_bar_bot():
    try:
        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        for x in nearby_devices:
            if "Bar Bot" in x[1]:
                # return address of first device with "Bar Bot" in its name
                return x[0]
    except:
        return None


def clear_input() -> bool:
    global is_connected
    # clear the input
    read_message()
    # if an error accured, return false
    return is_connected


def connect(mac_address: str):
    global conn, is_connected
    if conn is not None:
        conn.close()
    try:
        conn = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        conn.connect((mac_address, 1))
        conn.settimeout(timeout)
        # wait for Arduino to initialize
        time.sleep(1)
        clear_input()
        is_connected = True
        logging.info("Connection successfull")
    except Exception as e:
        logging.warn("Connection failed %s" % e)
        return False
    return True


def _send_do(command, parameter1=None, parameter2=None):
    global error
    if not clear_input():
        return False
    # send the command
    if parameter1 is not None and parameter2 is not None:
        send_command(command, [parameter1, parameter2])
    elif parameter1 is not None:
        send_command(command, [parameter1])
    else:
        send_command(command)
    # wait for the response
    message = read_message()
    if message.command != command:
        error = "answer for wrong command"
        return False
    if message.type == MessageTypes.NAK:
        error = "NAK received"
        return False
    if message.type != MessageTypes.ACK:
        error = "wrong answer"
        return False
    while True:
        message = read_message()
        if message.command != command:
            error = "answer for wrong command"
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
            error = "wrong answer"
            return False


def _send_set(command, parameter=None):
    global error
    if not clear_input():
        return False
    # send the command
    send_command(command, [parameter])
    # wait for the response
    message = read_message()
    if message.command != command:
        error = "answer for wrong command"
        return False
    if message.type == MessageTypes.NAK:
        error = "NAK received"
        return False
    if message.type != MessageTypes.ACK:
        error = "wrong answer"
        return False
    return True


def _send_get(command, parameters=None):
    global error
    if not clear_input():
        return None
    # send the command
    send_command(command, parameters)
    # wait for the response
    message = read_message()
    if message.command != command:
        error = "answer for wrong command"
        return None
    if message.type == MessageTypes.ACK:
        if message.parameters is not None:
            return message.parameters[0]
        else:
            error = "No result sent"
            return None
    if message.type == MessageTypes.NAK:
        error = "NAK received"
        return None
    return None


def send_abort():
    send_command("ABORT")


def try_get(command, parameters=None):
    for _ in range(3):
        res = _send_get(command, parameters)
        if res is not None:
            return res
    return None


def try_set(command, parameters=None):
    for _ in range(3):
        if _send_set(command, parameters):
            return True
    return False


def try_do(command, parameter1=None, parameter2=None):
    for _ in range(3):
        res = _send_do(command, parameter1, parameter2)
        if res:
            return res
    return False


def send_command(command, parameters=None):
    global conn, is_connected
    if is_connected:
        cmd = command
        if parameters is not None:
            for parameter in parameters:
                cmd = cmd + " " + str(parameter)
        cmd = cmd + "\r"
        logging.debug(">" + cmd)
        try:
            conn.send(cmd.encode())
            return True
        except Exception:
            logging.exception("Send command failed")
    return False


def close():
    global conn
    if conn is not None:
        conn.close()


def _read_existing():
    global conn
    data = b''
    # make sure to read everything there is
    while True:
        data = conn.recv(1024)
        if len(data) < 1024:
            break
    return data.decode('utf-8')


def read_message() -> ProtocolMessage:
    global conn, is_connected
    if conn == None:
        is_connected = False
        return ProtocolMessage(MessageTypes.COMM_ERROR, "port not open")
    try:
        line = ""
        # make sure we have a full line
        while True:
            line += _read_existing()
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
        if len(tokens) > 0:
            for msg_type in MessageTypes:
                if msg_type.name == tokens[0]:
                    if len(tokens) < 2:
                        return ProtocolMessage(MessageTypes.COMM_ERROR, "wrong format")
                    elif len(tokens) == 2:
                        return ProtocolMessage(msg_type, tokens[1])
                    else:
                        return ProtocolMessage(msg_type, tokens[1], tokens[2:])
        return ProtocolMessage(MessageTypes.COMM_ERROR, "unknown type")
    except bluetooth.btcommon.BluetoothError as e:
        is_connected = False
        logging.error(f"Read failed with BluetoothError:{e.args}")
        return ProtocolMessage(MessageTypes.COMM_ERROR, e)
    except Exception as e:
        is_connected = False
        logging.exception("Read failed")
        return ProtocolMessage(MessageTypes.COMM_ERROR, e)
