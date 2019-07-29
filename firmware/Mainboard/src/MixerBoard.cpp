#include "MixerBoard.h"

MixerBoard::MixerBoard()
{
    _targetPosition = MIXER_POSITION_UNDEFINED;
}

void MixerBoard::StartMoveTop()
{
    StartMove(MIXER_POSITION_TOP);
}

void MixerBoard::StartMoveBottom()
{
    StartMove(MIXER_POSITION_BOTTOM);
}

bool MixerBoard::IsAtTop()
{
    return GetPosition() == MIXER_POSITION_TOP;
}

bool MixerBoard::IsAtBottom()
{
    return GetPosition() == MIXER_POSITION_BOTTOM;
}

void MixerBoard::StartMove(byte pos)
{
    _targetPosition = pos;
    WireProtocol::sendCommand(MIXER_BOARD_ADDRESS, MIXER_CMD_SET_TARGET_POS, (uint8_t)pos);
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