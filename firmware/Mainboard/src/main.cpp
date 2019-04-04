#include "Arduino.h"
#include "BluetoothSerial.h"
#include "Protocol.h"
#include "LEDController.h"
#include "Wire.h"
#include "Shared.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

TaskHandle_t BluetoothTask;
TaskHandle_t LEDTask;

BluetoothSerial SerialBT;
Protocol protocol(&SerialBT);
LEDController LEDC;

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
void balanceLEDSetType(byte type)
{
	I2C_SEND_COMMAND(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_TYPE, &type, 1);
}
void balanceLEDSetColorA(RGB color)
{
	I2C_SEND_COMMAND(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_COLOR_A, (byte *)&color, 3);
}
void balanceLEDSetColorB(RGB color)
{
	I2C_SEND_COMMAND(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_COLOR_B, (byte *)&color, 3);
}
void balanceLEDSetPeriod(unsigned int time)
{
	I2C_SEND_COMMAND(BALANCE_BOARD_ADDRESS, BALANCE_CMDLED_SET_TIME, (byte *)&time, sizeof(time));
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
							10000,	 //stack depth
							NULL,	  //parameters
							0,		   //priority
							&LEDTask,  //out: task handle
							0);		   //core

	Wire.begin();
}

long last_millis = 0;
void loop()
{
	if (millis() > last_millis + 3)
	{
		last_millis = millis();
		//check if balance has new data
		bool has_data = false;
		if (I2C_GET_BOOL(BALANCE_BOARD_ADDRESS, BALANCE_CMDBALANCE_HAS_NEW_DATA, &has_data) && has_data)
		{
			//if new data is there get it
			float data;
			if (I2C_GET_FLOAT(BALANCE_BOARD_ADDRESS, BALANCE_CMDBALANCE_GET_DATA, &data))
			{
				RGB test = {0, (byte)(-data / 20000), 0};
				balanceLEDSetColorA(test);
				balanceLEDSetType(BALANCE_LED_TYPE_CONTINOUS);
			}
		}
	}
	yield();
}
