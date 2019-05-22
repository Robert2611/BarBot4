#ifndef BALANCE_BOARD_H
#define BALANCE_BOARD_H
#include "Shared.h"
#include "WireProtocol.h"

class BalanceBoard
{
  public:
    BalanceBoard();
    //LED wrappers
    void LEDContinous(RGB_t color);
    void LEDBlink(RGB_t colorA, RGB_t colorB, unsigned int period);
    void LEDBlink(RGB_t colorA, unsigned int period);
    void LEDFade(RGB_t colorA, RGB_t colorB, unsigned int period);
    void LEDFade(RGB_t colorA, unsigned int period);
    void LEDOff();
    //balance data wrappers
    void setCalibration(float calibration);
    void setOffset(float offset);
    bool readData();
    float getWeight();    
  private:
    bool hasNewData();
    void LEDSetType(byte type);
    void LEDSetColorA(RGB_t color);
    void LEDSetColorB(RGB_t color);
    void LEDSetPeriod(unsigned int time);
    float raw_data;
    float calibration;
    float offset;
};
#endif