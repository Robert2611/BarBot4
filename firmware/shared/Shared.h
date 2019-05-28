#ifndef MIXXER_SHARED_H
#define MIXXER_SHARED_H
#include "Arduino.h"
#include "Wire.h"

#define BALANCE_BOARD_ADDRESS 0x01

#define BALANCE_CMD_HAS_NEW_DATA 1
#define BALANCE_CMD_GET_DATA 2
#define BALANCE_CMD_GET_DATA_RAW 11
#define BALANCE_CMD_SET_LED_TYPE 3

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


#endif