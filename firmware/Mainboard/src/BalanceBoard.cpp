#include "BalanceBoard.h"

BalanceBoard::BalanceBoard()
{
	raw_data = 0;
	calibration = 1;
	offset = 0;
}

bool BalanceBoard::setLEDType(byte type)
{
	return WireProtocol::sendCommand(BALANCE_BOARD_ADDRESS, BALANCE_CMD_SET_LED_TYPE, &type, 1) == 0;
}

void BalanceBoard::LEDOff()
{
	setLEDType(BALANCE_LED_TYPE_OFF);
}

bool BalanceBoard::hasNewData()
{
	bool has_data;
	bool success = WireProtocol::getBool(BALANCE_BOARD_ADDRESS, BALANCE_CMD_HAS_NEW_DATA, &has_data);
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
	bool success = WireProtocol::getFloat(BALANCE_BOARD_ADDRESS, BALANCE_CMD_GET_DATA, &data);
	//only safe the data if it is valid and not higher than it can possibly be (24 bit of the HX711)
	if (success && !isnan(data) && data < (2 << 24))
	{
		raw_data = data;
		return true;
	}
	return false;
}

float BalanceBoard::getWeight()
{
	return ((float)(raw_data - offset)) / calibration;
}