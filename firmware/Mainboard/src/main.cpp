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
	//start serial communication for debugging
	Serial.begin(115200);
	LEDContr.begin();
	//Bluetooth device name
	SerialBT.begin("Bar Bot 4");
	Serial.println("Bluetooth started");

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
	protocol.addCommand(
		"Delay",
		[](int param_c, char** param_v){
			if(param_c == 1){
				long t = atoi(param_v[0]);
				if( t > 0 && t < 5000){
					state_m.start_delay(t);
					return true;
				}
			}
			return false;
		},
		[](){
			return state_m.status == BAR_BOT_IDLE;
		}
	);
		protocol.addCommand(
		"Pump",
		[](int param_c, char** param_v){
			if(param_c == 1){
				long t = atoi(param_v[0]);
				if( t > 0 && t < 5000){
					state_m.start_clean(0, t);
					return true;
				}
			}
			return false;
		},
		[](){
			return state_m.status == BAR_BOT_IDLE;
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
