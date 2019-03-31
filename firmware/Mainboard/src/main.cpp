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

bool balance_has_data()
{
	Wire.beginTransmission(BALANCE_BOARD_ADDRESS);
	Wire.write(0x00);
	Wire.endTransmission();
	byte returned = Wire.requestFrom(BALANCE_BOARD_ADDRESS, 1);
	return returned == 1 && Wire.read();
}

float balance_get_raw_data()
{
	float result = 0;
	Wire.beginTransmission(BALANCE_BOARD_ADDRESS);
	Wire.write(0x01);
	Wire.endTransmission();
	byte returned = Wire.requestFrom(BALANCE_BOARD_ADDRESS, sizeof(float));
	if (returned == sizeof(float))
	{
		Wire.readBytes((byte *)&result, sizeof(float));
	}
	return result;
}
float balance_get_data()
{
	float result = 0;
	Wire.beginTransmission(BALANCE_BOARD_ADDRESS);
	Wire.write(0x02);
	Wire.endTransmission();
	byte returned = Wire.requestFrom(BALANCE_BOARD_ADDRESS, sizeof(float));
	if (returned == sizeof(float))
	{
		Wire.readBytes((byte *)&result, sizeof(float));
	}
	return result;
}
long last_millis = 0;
void loop()
{
	if (millis() > last_millis + 3)
	{
		last_millis = millis();
		if (balance_has_data())
		{
			Serial.println(balance_get_data());
		}		
	}
}
