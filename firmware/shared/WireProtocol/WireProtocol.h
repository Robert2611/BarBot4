#include "Arduino.h"
#include "Wire.h"

class WireProtocol
{
private:
public:
    static uint8_t sendFloat(float data);
    static uint8_t sendCommand(uint8_t address, uint8_t command, uint8_t *data = 0, uint8_t data_length = 0);
    static bool getBool(uint8_t address, uint8_t command, bool *result);
    static float getFloat(uint8_t address, uint8_t command, float *result);
};