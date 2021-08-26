import subprocess
from enum import Enum, auto

is_demo = False


def run_command(cmd_str, cmd_str2=None):
    if cmd_str2:
        subprocess.Popen([cmd_str, cmd_str2], shell=True, stdin=None,
                         stdout=None, stderr=None, close_fds=True)
    else:
        subprocess.Popen([cmd_str], shell=True, stdin=None,
                         stdout=None, stderr=None, close_fds=True)


class UserMessages(Enum):
    mixing_done_remove_glas = auto()
    place_glas = auto()
    ingredient_empty = auto()
    ask_for_straw = auto()
    straws_empty = auto()
    cleaning_adapter = auto()
    ask_for_ice = auto()
    ice_empty = auto()
    I2C_error = auto()
    unknown_error = auto()
    glas_removed_while_drafting = auto()
    crusher_cover_open = auto()
    crusher_timeout = auto()
    board_not_connected_balance = auto()
    board_not_connected_mixer = auto()
    board_not_connected_straw = auto()
    board_not_connected_crusher = auto()
