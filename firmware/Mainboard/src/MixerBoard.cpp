#include "MixerBoard.h"

MixerBoard::MixerBoard()
{
    _targetPosition = MIXER_POSITION_UNDEFINED;
}

bool MixerBoard::StartMoveTop()
{
    return StartMove(MIXER_POSITION_TOP);
}

bool MixerBoard::StartMoveBottom()
{
    return StartMove(MIXER_POSITION_BOTTOM);
}

bool MixerBoard::IsAtTop()
{
    return GetPosition() == MIXER_POSITION_TOP;
}

bool MixerBoard::IsAtBottom()
{
    return GetPosition() == MIXER_POSITION_BOTTOM;
}

bool MixerBoard::StartMove(byte pos)
{
    _targetPosition = pos;
    for (int i = 0; i < MIXER_SEND_RETRIES; i++)
    {
        //was it transmitted successfully?
        if (WireProtocol::sendCommand(MIXER_BOARD_ADDRESS, MIXER_CMD_SET_TARGET_POS, (uint8_t)pos) == 0)
            return true;
    }
    return false;
}

byte MixerBoard::GetTargetPosition()
{
    return _targetPosition;
}

byte MixerBoard::GetPosition()
{
    byte pos;
    WireProtocol::getByte(MIXER_BOARD_ADDRESS, MIXER_CMD_GET_POS, &pos);
    return pos;
}

bool MixerBoard::IsMixing()
{
    return _isMixing;
}

void MixerBoard::StartMixing()
{
    _isMixing = true;
    WireProtocol::sendCommand(MIXER_BOARD_ADDRESS, MIXER_CMD_MIX_ON);
}

void MixerBoard::StopMixing()
{
    _isMixing = false;
    WireProtocol::sendCommand(MIXER_BOARD_ADDRESS, MIXER_CMD_MIX_OFF);
}