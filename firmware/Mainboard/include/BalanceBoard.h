#ifndef BALANCE_BOARD_H
#define BALANCE_BOARD_H
#include "Shared.h"
#include "WireProtocol.h"

class BalanceBoard
{
  public:
    BalanceBoard();
    //LED wrappers
    void LEDOff();
    void setLEDType(byte type);
    //balance data wrappers
    void setCalibration(float calibration);
    void setOffset(float offset);
    bool readData();
    float getWeight();    
  private:
    bool hasNewData();
    float raw_data;
    float calibration;
    float offset;
};
#endif