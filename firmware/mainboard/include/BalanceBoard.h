#ifndef BALANCE_BOARD_H
#define BALANCE_BOARD_H
#include "Shared.h"
#include "WireProtocol.h"

//if it takes longer than DRAFT_TIMEOUT_MILLIS to receive a new value an error is thrown
//the update time of the balance is 80Hz
#define BALANCE_DATA_TIMEOUT 1000

#define BALANCE_SEND_RETRIES 3

enum BalanceUpdateResult_t
{
  Balance_CommunicationError,
  Balance_NoData,
  Balance_DataRead,
  Balance_Timeout
};

class BalanceBoard
{
public:
  BalanceBoard();
  //LED wrappers
  bool LEDOff();
  bool setLEDType(byte type);
  //balance data wrappers
  void setCalibration(float calibration);
  void setOffset(float offset);
  BalanceUpdateResult_t update();
  float getWeight();

private:
  bool hasNewData(bool *has_data);
  float raw_data;
  float calibration;
  float offset;
  int retries;
  unsigned long last_check_millis;
  unsigned long last_data_millis;
};
#endif