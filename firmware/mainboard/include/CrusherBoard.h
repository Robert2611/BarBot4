#ifndef CRUSHER_BOARD_H
#define CRUSHER_BOARD_H
#include "Shared.h"
#include "WireProtocol.h"

#define CRUSHER_SEND_RETRIES 15

class CrusherBoard
{
public:
    CrusherBoard();
    bool StartCrushing();
    bool StopCrushing();
    bool GetError(byte *error);

private:
};
#endif