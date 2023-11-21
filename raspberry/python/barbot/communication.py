import time
from enum import Enum, auto
import logging
import bluetooth
from typing import List
import time

CONNECTION_TIMEOUT = 1
MAX_RETRIES = 3

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
_last_message_was_status_idle = False

def find_bar_bot():
    try:
        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        for x in nearby_devices:
            if "Bar Bot" in x[1]:
                # return address of first device with "Bar Bot" in its name
                return x[0]
    except:
        return None

def connect(mac_address: str):
    global conn, is_connected
    if conn is not None:
        conn.close()
    try:
        conn = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        conn.connect((mac_address, 1))
        conn.settimeout(CONNECTION_TIMEOUT)
        # wait for Arduino to initialize
        time.sleep(1)
        read_line()
        is_connected = True
        logging.info("Connection successfull")
    except Exception as e:
        logging.warn("Connection failed %s" % e)
        return False
    return True

def read_non_status_message() -> ProtocolMessage:
    message = read_message()
    # if a status message is recived, just ignore it, but only once!
    # it might have been in the buffer already
    if message.type == MessageTypes.STATUS:
        message = read_message()
    return message

def try_do(command, *parameters):
    """
    Send a DO command to the controller and wait for it to finish
    
    :param command: Command name
    :param parameters: Parameter for the controller command
    :returns:
        - success (bool) tells whether the command finished successfully
        - return_params (List[str]) are return parameters from controller
    """
    global error
    for _ in range(MAX_RETRIES):
        # send the command
        if not send_command(command, *parameters):
            continue
        # wait for the response
        message = read_non_status_message()
        if message.command != command:
            error = "answer for wrong command"
            continue
        elif message.type == MessageTypes.NAK:
            error = "NAK received"
            continue
        elif message.type != MessageTypes.ACK:
            error = "wrong answer"
            continue
        
        # ACK was received for the command, so wait until it finished
        while True:
            message = read_message()
            if message.command != command:
                error = "answer for wrong command"
                break
            if message.type == MessageTypes.STATUS:
                # it is still running, all good
                continue
            elif message.type == MessageTypes.DONE:
                return (True, None)
            elif message.type == MessageTypes.ERROR:
                # return the error parameters
                return (False, message.parameters)
            else:
                error = "wrong answer"
                break
    return (False, None)

def try_set(command, *parameters:str) -> bool:
    """
    Send a SET command to the controller
    
    :param command: Command name
    :param parameters: Parameter for the controller command
    :returns: Whether the command executed successfully
    """
    global error
    for _ in range(MAX_RETRIES):
        # send the command
        if not send_command(command, *parameters):
            continue
        # wait for the response
        message = read_non_status_message()
        if message.command != command:
            error = "answer for wrong command"
            continue
        if message.type == MessageTypes.NAK:
            error = "NAK received"
            continue
        if message.type != MessageTypes.ACK:
            error = "wrong answer"
            continue
        else:
            return True
    return False


def try_get(command, *parameters:str) -> str:
    """
    Send a 'GET' command to the controller
    
    :param command: Command name
    :param parameters: Parameter for the controller command
    :returns: Result of the GET command on success, None on any error
    """
    global error
    for _ in range(MAX_RETRIES):
        # send the command
        if not send_command(command, *parameters):
            continue
        # wait for the response
        message = read_non_status_message()
        if message.command != command:
            error = "answer for wrong command"
            continue
        if message.type == MessageTypes.ACK:
            if message.parameters is not None:
                return message.parameters[0]
            else:
                error = "No result sent"
                continue
        if message.type == MessageTypes.NAK:
            error = "NAK received"
            continue
    return None


def send_abort():
    send_command("ABORT")


def send_command(command, *parameters:str):
    global conn, is_connected
    if is_connected:
        cmd = command
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


def read_line():
    global conn, is_connected
    if conn == None:
        is_connected = False
        return None
    data = b''
    # make sure to read everything there is
    while True:
        char = conn.recv(1)
        data += char
        if char == b'\n':
            break
    decoded_data = data.decode('utf-8')
    return decoded_data


def read_message() -> ProtocolMessage:
    global conn, is_connected, _last_message_was_status_idle
    if conn == None:
        is_connected = False
        return ProtocolMessage(MessageTypes.COMM_ERROR, "port not open")
    try:
        line = read_line()
        line = line.replace("\n", "").replace("\r", "")
        tokens = line.split()
        # Do not repeat "STATUS IDLE" over and over again
        if tokens[0] == "STATUS" and tokens[1] == "IDLE":
            if not _last_message_was_status_idle:
                logging.debug("<" + line)
                _last_message_was_status_idle = True
        else:
            if _last_message_was_status_idle:
                _last_message_was_status_idle = False
            logging.debug("<" + line)
            
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
