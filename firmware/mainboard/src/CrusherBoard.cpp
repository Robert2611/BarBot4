#include "CrusherBoard.h"

CrusherBoard::CrusherBoard()
{
}

bool CrusherBoard::StartCrushing()
{
    for (int i = 0; i < CRUSHER_SEND_RETRIES; i++)
    {
        //was it transmitted successfully?
        if (WireProtocol::sendCommand(CRUSHER_BOARD_ADDRESS, CRUSHER_CMD_START_CRUSHING) == 0)
            return true;
    }
    return false;
}

bool CrusherBoard::StopCrushing()
{
    for (int i = 0; i < CRUSHER_SEND_RETRIES; i++)
    {
        //was it transmitted successfully?
        if (WireProtocol::sendCommand(CRUSHER_BOARD_ADDRESS, CRUSHER_CMD_STOP_CRUSHING) == 0)
            return true;
    }
    return false;
}

bool CrusherBoard::GetError(byte *error)
{
    return WireProtocol::getByte(CRUSHER_BOARD_ADDRESS, CRUSHER_CMD_GET_ERROR, error);
}