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
	SerialBT.begin("Bar Bot 4.0");
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
							10000,	 //stack depth
							NULL,	  //parameters
							0,		   //priority
							&LEDTask,  //out: task handle
							0);		   //core
	balance.setCalibration(BALANCE_CALIBRATION);
	balance.setOffset(BALANCE_OFFSET);

	//test command that just returns done after a defined time
	protocol.addDoCommand(
		"Delay",
		[](int param_c, char **param_v, long *result) {
			if (param_c == 1)
			{
				long t = atoi(param_v[0]);
				if (t > 0 && t < 5000)
				{
					state_m.start_delay(t);
					return true;
				}
			}
			return false;
		},
		[](int *error_code, long *parameter) {
			if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else
				return CommandStatus_t::Running;
		});
	protocol.addDoCommand(
		"Draft",
		[](int param_c, char **param_v, long *result) {
			if (param_c == 2)
			{
				long i = atoi(param_v[0]);
				long w = atoi(param_v[1]);
				if (i >= 0 && i < DRAFT_PORTS_COUNT && w > 0 && w < 400)
				{
					state_m.start_draft(i, w);
					return true;
				}
			}
			return false;
		},
		[](int *error_code, long *parameter) {
			if (state_m.status > BarBotStatus_t::Error)
			{
				(*error_code) = state_m.status;
				(*parameter) = state_m.get_last_draft_remaining_weight();
				state_m.reset_error();
				return CommandStatus_t::Error;
			}
			else if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else
				return CommandStatus_t::Running;
		});
	protocol.addDoCommand(
		"Pump",
		[](int param_c, char **param_v, long *result) {
			if (param_c == 2)
			{
				long index = atoi(param_v[0]);
				long time = atoi(param_v[1]);
				if (index >= 0 && index < DRAFT_PORTS_COUNT && time > 100 && time < 4000)
				{
					state_m.start_clean(index, time);
					return true;
				}
			}
			return false;
		},
		[](int *error_code, long *parameter) {
			if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else
				return CommandStatus_t::Running;
		});
	protocol.addDoCommand(
		"Home",
		[](int param_c, char **param_v, long *result) {
			if (state_m.status == Idle)
			{
				state_m.start_homing();
				return true;
			}
			return false;
		},
		[](int *error_code, long *parameter) {
			if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else
				return CommandStatus_t::Running;
		});
	protocol.addDoCommand(
		"Move",
		[](int param_c, char **param_v, long *result) {
			if (param_c == 1)
			{
				long t = atoi(param_v[0]);
				if (t >= 0 && t < 5000)
				{
					state_m.start_moveto(t);
					return true;
				}
			}
			return false;
		},
		[](int *error_code, long *parameter) {
			if (state_m.status > BarBotStatus_t::Error)
			{
				(*error_code) = state_m.status;
				state_m.reset_error();
				return CommandStatus_t::Error;
			}
			else if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else
				return CommandStatus_t::Running;
		});
	protocol.addSetCommand(
		"SetSomething",
		[](int param_c, char **param_v, long *result) {
			if (param_c == 1)
			{
				long t = atoi(param_v[0]);
				if (t > 0 && t < 5000)
				{
					//Set some values here!
					return true;
				}
			}
			return false;
		});
	protocol.addGetCommand(
		"GetWeight",
		[](int param_c, char **param_v, long *result) {
			(*result) = balance.getWeight();
			return true;
		});
	Wire.begin();
	//disable pullups for i2c
	digitalWrite(SCL, LOW);
	digitalWrite(SDA, LOW);
	state_m.begin();
}

long last_millis = 0;
void loop()
{
	state_m.update();
	yield();
}
