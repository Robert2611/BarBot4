#include "WireProtocol.h"

uint8_t WireProtocol::sendFloat(float data)
{
    return Wire.write((uint8_t *)&data, sizeof(data));
}

uint8_t WireProtocol::sendCommand(uint8_t address, uint8_t command, uint8_t *data, uint8_t data_length)
{
    Wire.beginTransmission(address);
    Wire.write(command);
    for (uint8_t i = 0; i < data_length; i++)
        Wire.write(data[i]);
    return Wire.endTransmission();
}

uint8_t WireProtocol::sendCommand(uint8_t address, uint8_t command, uint8_t data)
{
    Wire.beginTransmission(address);
    Wire.write(command);
    Wire.write(data);
    return Wire.endTransmission();
}

bool WireProtocol::getBool(uint8_t address, uint8_t command, bool *result)
{
    uint8_t cmd_result = sendCommand(address, command);
    if (cmd_result == 0)
    {
        uint8_t returned = Wire.requestFrom(address, (uint8_t)1);
        if (returned != 1)
            return false;
        *result = (bool)Wire.read();
        return true;
    }
    return false;
}

bool WireProtocol::getByte(uint8_t address, uint8_t command, uint8_t *result)
{
    uint8_t cmd_result = sendCommand(address, command);
    if (cmd_result == 0)
    {
        uint8_t returned = Wire.requestFrom(address, (uint8_t)1);
        if (returned != 1)
            return false;
        *result = Wire.read();
        return true;
    }
    else
    {
        //Serial.println(cmd_result);
    }
    return false;
}

bool WireProtocol::getFloat(uint8_t address, uint8_t command, float *result)
{
    sendCommand(address, command);
    uint8_t returned = Wire.requestFrom(address, sizeof(float));
    if (returned != sizeof(float))
        return false;
    Wire.readBytes((uint8_t *)result, sizeof(float));
    return true;
}