#include "StrawBoard.h"

StrawBoard:: StrawBoard(){
}

bool StrawBoard:: StartDispense(){
    for (int i = 0; i < STRAW_SEND_RETRIES; i++)
    {
        //was it transmitted successfully?
        if (WireProtocol::sendCommand(STRAW_BOARD_ADRESSS, STRAW_CMD_DISPENSE))
            return true;
    }
    return false;
}

bool StrawBoard:: IsDispensing(){
	bool is_dispensing;
	bool success = WireProtocol::getBool(STRAW_BOARD_ADRESSS, STRAW_CMD_GET_IS_DISPENSING, &is_dispensing);
	return success && is_dispensing;
}

bool StrawBoard:: IsError(){
    bool dispense_successfull;
	bool success = WireProtocol::getBool(STRAW_BOARD_ADRESSS, STRAW_CMD_GET_SUCCESSFUL, &dispense_successfull);
	return success ? !dispense_successfull : true;
}
