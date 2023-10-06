from inspect import ismodule
import os
import sys
import yaml
from . import directories

_filename = directories.join(directories.data, "config.yaml")

mac_address = ""
max_speed = 200
max_accel = 300
max_cocktail_size = 30
admin_password = "0000"
pump_power = 100
balance_offset = -119.1
balance_calibration = -1040
cleaning_time = 3000
stirrer_connected = True
stirring_time = 3000
ice_crusher_connected = False
ice_amount = 100
straw_dispenser_connected = False
sugar_dispenser_connected = False
sugar_per_unit = 4


def save():
    global _filename, _fields
    values = {}
    for field in _fields:
        values[field] = getattr(sys.modules[__name__], field)
    with open(_filename, 'w') as configfile:
        yaml.dump(values, configfile)


def is_mac_address_valid():
    global mac_address
    if mac_address is None:
        return False
    return len(mac_address.strip()) == 17


def _get_fields():
    fields = []
    for name in dir(sys.modules[__name__]):
        if name.startswith("_"):
            continue
        attr = getattr(sys.modules[__name__], name)
        if callable(attr):
            continue
        if ismodule(attr):
            continue
        fields.append(name)
    return fields


_fields = _get_fields()


def load():
    global _filename, _fields
    # load config if it exists
    if os.path.isfile(_filename):
        with open(_filename, 'r') as configfile:
            data = yaml.safe_load(configfile)
        # update fields with values from
        for field in _fields:
            if field in data.keys():
                setattr(sys.modules[__name__], field, data[field])
        return True
    else:
        return False


if not load():
    # make sure to save defaults
    save()
