#include "Wire.h"

#define BALANCE_BOARD_ADDRESS 0x01

#define BALANCE_CMDBALANCE_HAS_NEW_DATA 1
#define BALANCE_CMDBALANCE_GET_DATA 2
#define BALANCE_CMDBALANCE_GET_DATA_RAW 11
#define BALANCE_CMDLED_SET_COLOR_A 3
#define BALANCE_CMDLED_SET_COLOR_B 4
#define BALANCE_CMDLED_SET_TIME 5
#define BALANCE_CMDLED_SET_TYPE 6

#define BALANCE_LED_TYPE_OFF 0
#define BALANCE_LED_TYPE_CONTINOUS 1
#define BALANCE_LED_TYPE_BLINK 2
#define BALANCE_LED_TYPE_FADE 1

inline void I2C_SEND_COMMAND(byte address, byte command)
{
    Wire.beginTransmission(address);
    Wire.write(command);
    Wire.endTransmission();
}

inline bool I2C_GET_BOOL(byte address, byte command, bool *result)
{
    I2C_SEND_COMMAND(address, command);
    byte returned = Wire.requestFrom(BALANCE_BOARD_ADDRESS, 1);
    if (returned != 1)
        return false;
    *result = (bool)Wire.read();
    return true;
}

inline float I2C_GET_FLOAT(byte address, byte command, float *result)
{
    I2C_SEND_COMMAND(address, command);
    byte returned = Wire.requestFrom(BALANCE_BOARD_ADDRESS, sizeof(float));
    if (returned != sizeof(float))
        return false;
    Wire.readBytes((byte *)result, sizeof(float));
    return true;
}