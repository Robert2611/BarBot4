import configparser
import os

config = configparser.ConfigParser()


def set_value(name: str, value):
    config.set("default", name, str(value))


def __get_str(name):
    return config.get("default", name)


def __get_int(name):
    return config.getint("default", name)


def __get_float(name):
    return config.getfloat("default", name)


def __get_bool(name):
    return config.getboolean("default", name)


def save():
    # safe file again
    with open(_Filename, 'w') as configfile:
        config.write(configfile)


def is_mac_address_valid():
    return len(mac_address.strip()) == 17


def load(Filename):
    _Filename = Filename
    # load config if it exists
    if os.path.isfile(_Filename):
        config.read(_Filename)
        apply()
        return True
    else:
        return False


def apply():
    global mac_address
    mac_address = __get_str("mac_address")
    global max_speed
    max_speed = __get_int("max_speed")
    global max_accel
    max_accel = __get_int("max_accel")
    global max_cocktail_size
    max_cocktail_size = __get_int("max_cocktail_size")
    global admin_password
    admin_password = __get_str("admin_password")
    global pump_power
    pump_power = __get_int("pump_power")
    global balance_offset
    balance_offset = __get_float("balance_offset")
    global balance_calibration
    balance_calibration = __get_float("balance_calibration")
    global cleaning_time
    cleaning_time = __get_int("cleaning_time")
    global stirrer_connected
    stirrer_connected = __get_bool("stirrer_connected")
    global stirring_time
    stirring_time = __get_int("stirring_time")
    global ice_crusher_connected
    ice_crusher_connected = __get_bool("ice_crusher_connected")
    global ice_amount
    ice_amount = __get_int("ice_amount")
    global straw_dispenser_connected
    straw_dispenser_connected = __get_bool(
        "straw_dispenser_connected")


_Filename = None

# setup config with default values
config.add_section("default")
set_value("mac_address", "")
set_value("max_speed", 200)
set_value("max_accel", 300)
set_value("max_cocktail_size", 30)
set_value("admin_password", "0000")
set_value("pump_power", 100)
set_value("balance_offset", -119.1)
set_value("balance_calibration", -1040)
set_value("cleaning_time", 3000)
set_value("stirrer_connected", True)
set_value("stirring_time", 3000)
set_value("ice_crusher_connected", False)
set_value("ice_amount", 100)
set_value("straw_dispenser_connected", False)
apply()
