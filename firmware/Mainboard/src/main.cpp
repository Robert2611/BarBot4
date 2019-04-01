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

void setup()
{
	//start serial communication for debugging
	Serial.begin(115200);
	LEDC.begin();
	//Bluetooth device name
	SerialBT.begin("Bar Bot 4");
	Serial.println("Bluetooth started");

	//start bluetooth task on core 0, loop runs on core 1
	xTaskCreatePinnedToCore(DoBluetoothTask, "BluetoothTask", 10000, NULL, 1, &BluetoothTask, 0);

	//start LED task with high priority on core 0
	xTaskCreatePinnedToCore(DoLEDTask, "LEDTask", 10000, NULL, 0, &LEDTask, 0);

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
				Serial.println(data);
			}
		}
	}
}
