#include "StrawBoard.h"

StrawBoard::StrawBoard()
{
}

bool StrawBoard::StartDispense()
{
    for (int i = 0; i < STRAW_SEND_RETRIES; i++)
    {
        // was it transmitted successfuly?
        if (WireProtocol::sendCommand(STRAW_BOARD_ADDRESS, STRAW_CMD_DISPENSE) == 0)
            return true;
    }
    return false;
}

bool StrawBoard::IsDispensing(bool *dispensing)
{
    return WireProtocol::getBool(STRAW_BOARD_ADDRESS, STRAW_CMD_GET_IS_DISPENSING, dispensing);
}

bool StrawBoard::Wassuccessful(bool *successful)
{
    return WireProtocol::getBool(STRAW_BOARD_ADDRESS, STRAW_CMD_GET_SUCCESSFUL, successful);
}
