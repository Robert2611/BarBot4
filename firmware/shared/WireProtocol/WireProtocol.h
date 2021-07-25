#ifndef WIRE_PROTOCOL_H
#define WIRE_PROTOCOL_H
#include "Arduino.h"
#include "Wire.h"

#define WIREPROTOCOL_CMD_PING 254
#define WIREPROTOCOL_MAX_BOARDS 8

class WireProtocol
{
private:
public:
    static uint8_t sendFloat(float data);
    static uint8_t sendCommand(uint8_t address, uint8_t command, uint8_t *data = 0, uint8_t data_length = 0);
    static uint8_t sendCommand(uint8_t address, uint8_t command, uint8_t data);
    static bool getBool(uint8_t address, uint8_t command, bool *result);
    static bool getFloat(uint8_t address, uint8_t command, float *result);
    static bool getByte(uint8_t address, uint8_t command, uint8_t *result);
    static void blinkAddress(byte address, byte pin);
    static bool ping(uint8_t address);
};
#endif