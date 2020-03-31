#include "MixerBoard.h"

MixerBoard::MixerBoard()
{
}

bool MixerBoard::IsMixing(bool *is_mixing)
{
    bool first_result;
    bool verifying = false;
    for (int i = 0; i < MIXER_SEND_RETRIES; i++)
    {
        if (WireProtocol::getBool(MIXER_BOARD_ADDRESS, MIXER_CMD_GET_IS_MIXING, is_mixing)){
            //we wait for two similar results to be sure
            if(verifying && first_result==(*is_mixing))
                return true;
            first_result = (*is_mixing);
            verifying = true;
        }
        return true;
    }
    return false;
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

bool MixerBoard::WasSuccessfull(bool *successfull)
{
    for (int i = 0; i < MIXER_SEND_RETRIES; i++)
    {
        if (WireProtocol::getBool(MIXER_BOARD_ADDRESS, MIXER_CMD_GET_SUCCESSFUL, successfull))
            return true;
    }
    return false;
}