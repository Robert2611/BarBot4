#include "Shared.h"

class BalanceBoard
{
  public:
    BalanceBoard();
    //LED wrappers
    void LEDContinous(RGB color);
    void LEDBlink(RGB colorA, RGB colorB, unsigned int period);
    void LEDBlink(RGB colorA, unsigned int period);
    void LEDFade(RGB colorA, RGB colorB, unsigned int period);
    void LEDFade(RGB colorA, unsigned int period);
    void LEDOff();
    //balance data wrappers
    void setCalibration(float calibration);
    bool readData();
    float getWeight();    
  private:
    bool hasNewData();
    void LEDSetType(byte type);
    void LEDSetColorA(RGB color);
    void LEDSetColorB(RGB color);
    void LEDSetPeriod(unsigned int time);
    float raw_data;
    float calibration;
};