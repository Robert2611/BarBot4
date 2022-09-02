#ifndef BAR_BOT_SHARED_H
#define BAR_BOT_SHARED_H
#include "Arduino.h"
#include "Wire.h"

#define BALANCE_BOARD_ADDRESS 0x01
#define MIXER_BOARD_ADDRESS 0x02
#define STRAW_BOARD_ADDRESS 0x03
#define CRUSHER_BOARD_ADDRESS 0x04
#define SUGAR_BOARD_ADDRESS 0x05

#define BALANCE_CMD_HAS_NEW_DATA 1
#define BALANCE_CMD_GET_DATA 2
#define BALANCE_CMD_GET_DATA_RAW 11
#define BALANCE_CMD_SET_LED_TYPE 3

#define BALANCE_LED_TYPE_OFF 0
#define BALANCE_LED_TYPE_CONTINOUS 1
#define BALANCE_LED_TYPE_BLINK 2
#define BALANCE_LED_TYPE_ROTATE 3
#define BALANCE_LED_TYPE_PULSING 4
#define BALANCE_LED_TYPE_CHASE 5

#define MIXER_CMD_START_MIXING 1
#define MIXER_CMD_GET_IS_MIXING 2
#define MIXER_CMD_GET_SUCCESSFUL 3

#define STRAW_CMD_DISPENSE 1
#define STRAW_CMD_GET_IS_DISPENSING 2
#define STRAW_CMD_GET_SUCCESSFUL 3

#define CRUSHER_CMD_START_CRUSHING 1
#define CRUSHER_CMD_STOP_CRUSHING 2
#define CRUSHER_CMD_GET_ERROR 3

#define CRUSHER_ERROR_NO_ERROR 0
#define CRUSHER_ERROR_COVER_OPEN 1
#define CRUSHER_ERROR_TIMEOUT 2

#define SUGAR_CMD_START_DISPENSING 1
#define SUGAR_CMD_STOP_DISPENSING 2
#define SUGAR_CMD_GET_ERROR 3

#define SUGAR_ERROR_NO_ERROR 0
#define SUGAR_ERROR_TIMEOUT 1

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