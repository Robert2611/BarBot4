#include "Arduino.h"
#include "BluetoothSerial.h"
#include "Protocol.h"
#include "LEDController.h"
#include "Wire.h"
#include "Shared.h"
#include "Configuration.h"
#include "BalanceBoard.h"
#include "StateMachine.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

TaskHandle_t BluetoothTask;
TaskHandle_t LEDTask;

BluetoothSerial SerialBT;
Protocol protocol(&SerialBT);
LEDController LEDC(PIXEL_COUNT, PIN_NEOPIXEL);
BalanceBoard balance;
StateMachine state_m;

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
		LEDC.update();
		delay(100);
	}
}

void setup()
{
	//start serial communication for debugging
	Serial.begin(115200);
	LEDC.begin();
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
	Wire.begin();
	state_m.begin();
}

long last_millis = 0;
void loop()
{
	state_m.update();
	if (millis() > last_millis + 3)
	{
		last_millis = millis();
		//check if balance has new data
		if(balance.readData()){
			float data = balance.getWeight();
			//RGB test = {0, (byte)(-data / 20000), 0};
		}
	}
	yield();
}
