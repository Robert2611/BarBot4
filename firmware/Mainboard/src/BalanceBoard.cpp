#include "BalanceBoard.h"

BalanceBoard::BalanceBoard()
{
	raw_data = 0;
	calibration = 1;
}

void BalanceBoard::LEDSetType(byte type)
{
	I2C_SEND_COMMAND(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_TYPE, &type, 1);
}
void BalanceBoard::LEDSetColorA(RGB color)
{
	I2C_SEND_COMMAND(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_COLOR_A, (byte *)&color, 3);
}
void BalanceBoard::LEDSetColorB(RGB color)
{
	I2C_SEND_COMMAND(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_COLOR_B, (byte *)&color, 3);
}
void BalanceBoard::LEDSetPeriod(unsigned int time)
{
	I2C_SEND_COMMAND(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_TIME, (byte *)&time, sizeof(time));
}

void BalanceBoard::LEDContinous(RGB color)
{
	LEDSetColorA(color);
	LEDSetType(BALANCE_LED_TYPE_CONTINOUS);
}

void BalanceBoard::LEDOff()
{
	LEDSetType(BALANCE_LED_TYPE_OFF);
}

void BalanceBoard::LEDBlink(RGB colorA, RGB colorB, unsigned int period)
{
	LEDSetColorA(colorA);
	LEDSetColorA(colorB);
	LEDSetPeriod(period);
	LEDSetType(BALANCE_LED_TYPE_BLINK);
}
void BalanceBoard::LEDBlink(RGB colorA, unsigned int period)
{
	//second color is black
	LEDBlink(colorA, {0, 0, 0}, period);
}
void BalanceBoard::LEDFade(RGB colorA, RGB colorB, unsigned int period)
{
	LEDSetColorA(colorA);
	LEDSetColorA(colorB);
	LEDSetPeriod(period);
	LEDSetType(BALANCE_LED_TYPE_FADE);
}
void BalanceBoard::LEDFade(RGB colorA, unsigned int period)
{
	//second color is black
	LEDFade(colorA, {0, 0, 0}, period);
}

bool BalanceBoard::hasNewData()
{
	bool has_data;
	bool success = I2C_GET_BOOL(BALANCE_BOARD_ADDRESS, BALANCE_CMDBALANCE_HAS_NEW_DATA, &has_data);
	return success && has_data;
}

void BalanceBoard::setCalibration(float _calibration)
{
	this->calibration = _calibration;
}

bool BalanceBoard::readData()
{
	if (!hasNewData())
		return false;
	float data;
	bool success = I2C_GET_FLOAT(BALANCE_BOARD_ADDRESS, BALANCE_CMDBALANCE_GET_DATA, &data);
	if (success)
		raw_data = data;
	return success;
}

float BalanceBoard::getWeight()
{
	return raw_data * calibration;
}