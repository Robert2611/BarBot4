#include "MixerBoard.h"

MixerBoard::MixerBoard()
{
}

bool MixerBoard::IsMixing(bool* is_mixing)
{
	return WireProtocol::getBool(MIXER_BOARD_ADDRESS, MIXER_CMD_GET_IS_MIXING, is_mixing);
}

bool MixerBoard::StartMixing(byte seconds)
{
    for (int i = 0; i < MIXER_SEND_RETRIES; i++)
    {
        //was it transmitted successfully?
        if (WireProtocol::sendCommand(MIXER_BOARD_ADDRESS, MIXER_CMD_START_MIXING, seconds) == 0)
            return true;
    }
    return false;
}

bool MixerBoard::WasSuccessfull(bool* successfull)
{    
	return WireProtocol::getBool(MIXER_BOARD_ADDRESS, MIXER_CMD_GET_SUCCESSFUL, successfull);
}