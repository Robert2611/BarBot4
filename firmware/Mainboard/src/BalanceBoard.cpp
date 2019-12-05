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

bool BalanceBoard::LEDOff()
{
	return setLEDType(BALANCE_LED_TYPE_OFF);
}

bool BalanceBoard::hasNewData(bool *has_data)
{
	return WireProtocol::getBool(BALANCE_BOARD_ADDRESS, BALANCE_CMD_HAS_NEW_DATA, has_data);
}

void BalanceBoard::setCalibration(float _calibration)
{
	this->calibration = _calibration;
}

void BalanceBoard::setOffset(float _offset)
{
	this->offset = _offset;
}

float BalanceBoard::getWeight()
{
	return ((float)(raw_data - offset)) / calibration;
}

BalanceUpdateResult_t BalanceBoard::update()
{
	//ask for new data every 3 ms to avoid blocking the bus
	if (millis() < last_check_millis + 3)
		return Balance_NoData;

	bool has_data = false;
	if (!hasNewData(&has_data))
		return Balance_CommunicationError;
	last_check_millis = millis();
	if (!has_data)
	{
		if (millis() > last_data_millis + BALANCE_DATA_TIMEOUT)
			return Balance_Timeout;
		else
			return Balance_NoData;
	}
	float data;
	bool success = WireProtocol::getFloat(BALANCE_BOARD_ADDRESS, BALANCE_CMD_GET_DATA, &data);
	//only safe the data if it is valid and not higher than it can possibly be (24 bit of the HX711)
	if (success && !isnan(data) && data < (2 << 24))
	{
		raw_data = data;
		last_data_millis = millis();
		return Balance_DataRead;
	}
	return Balance_CommunicationError;
}