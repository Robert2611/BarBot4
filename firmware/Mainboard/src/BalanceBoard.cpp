#include "BalanceBoard.h"

BalanceBoard::BalanceBoard()
{
	raw_data = 0;
	calibration = 1;
	offset = 0;
}

void BalanceBoard::LEDSetType(byte type)
{
	WireProtocol::sendCommand(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_TYPE, &type, 1);
}
void BalanceBoard::LEDSetColorA(RGB_t color)
{
	WireProtocol::sendCommand(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_COLOR_A, (byte *)&color, 3);
}
void BalanceBoard::LEDSetColorB(RGB_t color)
{
	WireProtocol::sendCommand(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_COLOR_B, (byte *)&color, 3);
}
void BalanceBoard::LEDSetPeriod(unsigned int time)
{
	WireProtocol::sendCommand(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_TIME, (byte *)&time, sizeof(time));
}

void BalanceBoard::LEDContinous(RGB_t color)
{
	LEDSetColorA(color);
	LEDSetType(BALANCE_LED_TYPE_CONTINOUS);
}

void BalanceBoard::LEDOff()
{
	LEDSetType(BALANCE_LED_TYPE_OFF);
}

void BalanceBoard::LEDBlink(RGB_t colorA, RGB_t colorB, unsigned int period)
{
	LEDSetColorA(colorA);
	LEDSetColorA(colorB);
	LEDSetPeriod(period);
	LEDSetType(BALANCE_LED_TYPE_BLINK);
}
void BalanceBoard::LEDBlink(RGB_t colorA, unsigned int period)
{
	//second color is black
	LEDBlink(colorA, {0, 0, 0}, period);
}
void BalanceBoard::LEDFade(RGB_t colorA, RGB_t colorB, unsigned int period)
{
	LEDSetColorA(colorA);
	LEDSetColorA(colorB);
	LEDSetPeriod(period);
	LEDSetType(BALANCE_LED_TYPE_FADE);
}
void BalanceBoard::LEDFade(RGB_t colorA, unsigned int period)
{
	//second color is black
	LEDFade(colorA, {0, 0, 0}, period);
}

bool BalanceBoard::hasNewData()
{
	bool has_data;
	bool success = WireProtocol::getBool(BALANCE_BOARD_ADDRESS, BALANCE_CMDBALANCE_HAS_NEW_DATA, &has_data);
	return success && has_data;
}

void BalanceBoard::setCalibration(float _calibration)
{
	this->calibration = _calibration;
}

void BalanceBoard::setOffset(float _offset)
{
	this->offset = _offset;
}

bool BalanceBoard::readData()
{
	if (!hasNewData())
		return false;
	float data;
	bool success = WireProtocol::getFloat(BALANCE_BOARD_ADDRESS, BALANCE_CMDBALANCE_GET_DATA, &data);
	//only safe the data if it is valid and not higher than it can possibly be (24 bit of the HX711)
	if (success && !isnan(data) && data < (2<<24) ){
		raw_data = data;
		return true;
	}
	return false;
}

float BalanceBoard::getWeight()
{
	return (raw_data - offset) * calibration;
}