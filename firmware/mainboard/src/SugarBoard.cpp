#include "SugarBoard.h"

SugarBoard::SugarBoard()
{
}

bool SugarBoard::StartDispensing()
{
    for (int i = 0; i < SUGAR_SEND_RETRIES; i++)
    {
        //was it transmitted successfully?
        if (WireProtocol::sendCommand(SUGAR_BOARD_ADDRESS, SUGAR_CMD_START_DISPENSING) == 0)
            return true;
    }
    return false;
}

bool SugarBoard::StopDispensing()
{
    for (int i = 0; i < SUGAR_SEND_RETRIES; i++)
    {
        //was it transmitted successfully?
        if (WireProtocol::sendCommand(SUGAR_BOARD_ADDRESS, SUGAR_CMD_STOP_DISPENSING) == 0)
            return true;
    }
    return false;
}

bool SugarBoard::GetError(byte *error)
{
    return WireProtocol::getByte(SUGAR_BOARD_ADDRESS, SUGAR_CMD_GET_ERROR, error);
}