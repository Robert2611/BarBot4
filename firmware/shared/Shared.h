#ifndef MIXXER_SHARED_H
#define MIXXER_SHARED_H
#include "Arduino.h"
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
#define BALANCE_LED_TYPE_FADE 3

// fastled also declares a RGB type
typedef struct
{
    uint8_t r;
    uint8_t g;
    uint8_t b;
} RGB_t;

inline RGB_t HEXStringToRGB(String HEXString)
{
    String str = "";
    if (HEXString.startsWith("#"))
        str = HEXString.substring(1);
    else
        str = HEXString;
    char charString[6 + 1];
    str.toCharArray(charString, sizeof(charString));
    unsigned long rgb = strtol(charString, NULL, 16);
    return {(byte)(rgb >> 16), (byte)(rgb >> 8 & 0xFF), (byte)(rgb & 0xFF)};
}

inline void printColor(RGB_t color)
{
    Serial.print("color: r");
    Serial.print(color.r, HEX);
    Serial.print(" g");
    Serial.print(color.g, HEX);
    Serial.print(" b");
    Serial.println(color.b, HEX);
}

inline void I2C_SEND_FLOAT(float data)
{
    Wire.write((uint8_t *)&data, sizeof(data));
}

inline void I2C_SEND_COMMAND(uint8_t address, uint8_t command, uint8_t *data = 0, uint8_t data_length = 0)
{
    Wire.beginTransmission(address);
    Wire.write(command);
    for (uint8_t i = 0; i < data_length; i++)
        Wire.write(data[i]);
    Wire.endTransmission();
}

inline bool I2C_GET_BOOL(uint8_t address, uint8_t command, bool *result)
{
    I2C_SEND_COMMAND(address, command);
    uint8_t returned = Wire.requestFrom(BALANCE_BOARD_ADDRESS, 1);
    if (returned != 1)
        return false;
    *result = (bool)Wire.read();
    return true;
}

inline float I2C_GET_FLOAT(uint8_t address, uint8_t command, float *result)
{
    I2C_SEND_COMMAND(address, command);
    uint8_t returned = Wire.requestFrom(BALANCE_BOARD_ADDRESS, sizeof(float));
    if (returned != sizeof(float))
        return false;
    Wire.readBytes((uint8_t *)result, sizeof(float));
    return true;
}
#endif