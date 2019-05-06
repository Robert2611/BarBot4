#include "Arduino.h"
#include "BluetoothSerial.h"
#include "Protocol.h"
#include "Shared.h"
#include "LEDController.h"
#include "Wire.h"

#include "Configuration.h"
#include "BalanceBoard.h"
#include "StateMachine.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

#define SERIAL_DEBUG

TaskHandle_t BluetoothTask;
TaskHandle_t LEDTask;

BluetoothSerial SerialBT;
BalanceBoard balance;
StateMachine state_m(&balance);

Protocol protocol(&SerialBT);
LEDAnimator LEDContr;


void DoBluetoothTask(void *parameters)
{
	for (;;)
	{
		protocol.update();
		delay(10);
	}
}

void DoLEDTask(void *parameters)
{
	for (;;)
	{
		LEDContr.update();
		delay(100);
	}
}

void setup()
{
#ifdef SERIAL_DEBUG
	//start serial communication for debugging
	Serial.begin(115200);
#endif
	LEDContr.begin();
	//Bluetooth device name
	SerialBT.begin("Bar Bot 4");
#ifdef SERIAL_DEBUG
	Serial.println("Bluetooth started");
#endif

	//start bluetooth task on core 0, loop runs on core 1
	xTaskCreatePinnedToCore(DoBluetoothTask, //Task function
							"BluetoothTask", //Task name
							10000,			 //stack depth
							NULL,			 //parameters
							1,				 //priority
							&BluetoothTask,  //out: task handle
							0);				 //core

	//start LED task with high priority 1 on core 0
	xTaskCreatePinnedToCore(DoLEDTask, //Task function
							"LEDTask", //Task name
							10000,	   //stack depth
							NULL,	   //parameters
							0,		   //priority
							&LEDTask,  //out: task handle
							0);		   //core
	balance.setCalibration(PUMP_CALIBRATION);
	balance.setOffset(PUMP_OFFSET);

	//test command that just returns done after a defined time
	protocol.addDoCommand(
		"Delay",
		[](int param_c, char** param_v, long *result){
			if(param_c == 1){
				long t = atoi(param_v[0]);
				if( t > 0 && t < 5000){
					state_m.start_delay(t);
					return true;
				}
			}
			return false;
		},
		[](int *error_code, long *parameter){
			if(state_m.status > BarBotStatus_t::Error){
				(*error_code) = state_m.status;
				state_m.reset_error();
				return CommandStatus_t::Error;
			}
		}
	);
	protocol.addDoCommand(
		"Pump",
		[](int param_c, char** param_v, long *result){
			if(param_c == 1){
				long t = atoi(param_v[0]);
				if( t > 0 && t < 5000){
					state_m.start_clean(0, t);
					return true;
				}
			}
			return false;
		},
		[](int *error_code, long *parameter){
			if(state_m.status > BarBotStatus_t::Error){
				(*error_code)= state_m.status;
				state_m.reset_error();
				return CommandStatus_t::Error;
			}
		}
	);
	protocol.addDoCommand(
		"Move",
		[](int param_c, char** param_v, long *result){
			if(param_c == 1){
				long t = atoi(param_v[0]);
				if( t > 0 && t < 5000){
					state_m.start_moveto(t);
					return true;
				}
			}
			return false;
		},
		[](int *error_code, long *parameter){
			if(state_m.status > BarBotStatus_t::Error){
				(*error_code) = state_m.status;
				state_m.reset_error();
				return CommandStatus_t::Error;
			}
		}
	);
	protocol.addSetCommand(
		"SetSomething",
		[](int param_c, char** param_v, long *result){
			if(param_c == 1){
				long t = atoi(param_v[0]);
				if( t > 0 && t < 5000){
					//Set some values here!
					return true;
				}
			}
			return false;
		}
	);
	protocol.addGetCommand(
		"GetSomething",
		[](int param_c, char** param_v, long *result){
			if(param_c == 1){
				long t = atoi(param_v[0]);
				if( t > 0 && t < 5000){
					//Set return values here!
					(*result) = 100;
					return true;
				}
			}
			return false;
		}
	);
	Wire.begin();
	state_m.begin();
}

long last_millis = 0;
void loop()
{
	state_m.update();
	yield();
}
