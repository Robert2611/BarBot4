#ifndef STRAW_BOARD_H
#define STRAW_BOARD_H
#include "Shared.h"
#include "WireProtocol.h"

#define STRAW_SEND_RETRIES 15

class StrawBoard
{
public:
  StrawBoard();
  bool StartDispense();
  bool IsDispensing(bool* dispensing);
  bool WasSuccessfull(bool* successfull);

private:

};
#endif