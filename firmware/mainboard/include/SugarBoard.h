#ifndef SUGAR_BOARD_H
#define SUGAR_BOARD_H
#include "Shared.h"
#include "WireProtocol.h"

#define SUGAR_SEND_RETRIES 15

class SugarBoard
{
public:
    SugarBoard();
    bool StartDispensing();
    bool StopDispensing();
    bool GetError(byte *error);

private:
};
#endif