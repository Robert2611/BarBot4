#ifndef MIXER_BOARD_H
#define MIXER_BOARD_H
#include "Shared.h"
#include "WireProtocol.h"

#define MIXER_SEND_RETRIES 15

class MixerBoard
{
public:
  MixerBoard();
  bool IsMixing(bool *mixing);
  bool StartMixing(byte seconds);
  bool WasSuccessfull(bool* successfull);

private:

};
#endif