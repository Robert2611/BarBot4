#include "Arduino.h"
#include "BluetoothSerial.h"
#include "Protocol.h"
#include "Shared.h"
#include "LEDController.h"
#include "Wire.h"
#include "MCP23X17.h"

#include "Configuration.h"
#include "BalanceBoard.h"
#include "StateMachine.h"

#include "Adafruit_GFX.h"
#include "Adafruit_SSD1306.h"

#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

#define SERIAL_DEBUG

TaskHandle_t BluetoothTask;
TaskHandle_t LEDTask;

BluetoothSerial SerialBT;
BalanceBoard balance;
MixerBoard mixer;
MCP23X17 mcp;
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire);

StateMachine state_m(&balance, &mixer, &mcp, &display);

Protocol protocol(&SerialBT);
LEDController LEDContr;

void DoBluetoothTask(void *parameters)
{
	for (;;)
	{
		//only listen to commands when startup is done
		if (state_m.is_started())
			protocol.update();
		else
			Serial.print("Starting (");
		Serial.print(state_m.status);
		Serial.println(")");
		delay(10);
	}
}

void DoLEDTask(void *parameters)
{
	for (;;)
	{
		LEDContr.setPosition((state_m.position_in_mm() + HOME_DISTANCE) / 1000 * PIXEL_COUNT);
		LEDContr.update();
		delay(10);
	}
}

void addCommands()
{
	//test command that returns done after a defined time
	protocol.addDoCommand("Delay",
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
	protocol.addDoCommand("Draft",
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
	protocol.addDoCommand("Stir",
						  [](int param_c, char **param_v, long *result) {
							  if (param_c == 1)
							  {
								  long d = atoi(param_v[0]);
								  if (d > 0)
								  {
									  state_m.start_stir(min(d, 10000l));
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
	protocol.addDoCommand("Pump",
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
	protocol.addDoCommand("Home",
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
	protocol.addDoCommand("Move",
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
	//PlatformLED needs to be sent via I2C, so it is done in the main loop so it must be a Do command
	protocol.addDoCommand("PlatformLED",
						  [](int param_c, char **param_v, long *result) {
							  if (param_c == 1)
							  {
								  long a = atoi(param_v[0]);
								  if (a >= 0 && a < 10)
								  {
									  state_m.start_setBalanceLED(a);
									  return true;
								  }
							  }
							  return false;
						  },
						  [](int *error_code, long *parameter) {
							  if (state_m.status == BarBotStatus_t::Idle)
								  return CommandStatus_t::Done;
							  else if (state_m.status == BarBotStatus_t::SetBalanceLED)
								  return CommandStatus_t::Running;
							  else
							  {
								  (*error_code) = state_m.status;
								  return CommandStatus_t::Error;
							  }
						  });
	protocol.addSetCommand("SetSpeed",
						   [](int param_c, char **param_v, long *result) {
							   if (param_c == 1)
							   {
								   long s = atoi(param_v[0]);
								   if (s > 0 && s < 5000)
								   {
									   state_m.set_max_speed(s);
									   return true;
								   }
							   }
							   return false;
						   });
	protocol.addSetCommand("SetBalanceCalibration",
						   [](int param_c, char **param_v, long *result) {
							   if (param_c == 1)
							   {
								   long cal = atoi(param_v[0]);
								   if (cal > 0 && cal < 10000)
								   {
									   balance.setCalibration(-cal);
									   return true;
								   }
							   }
							   return false;
						   });
	protocol.addSetCommand("SetBalanceOffset",
						   [](int param_c, char **param_v, long *result) {
							   if (param_c == 1)
							   {
								   long offset = atoi(param_v[0]);
								   if (offset > 0 && offset < 10000)
								   {
									   balance.setCalibration(-offset);
									   return true;
								   }
							   }
							   return false;
						   });
	protocol.addSetCommand("SetAccel",
						   [](int param_c, char **param_v, long *result) {
							   if (param_c == 1)
							   {
								   long a = atoi(param_v[0]);
								   if (a > 0 && a < 5000)
								   {
									   state_m.set_max_accel(a);
									   return true;
								   }
							   }
							   return false;
						   });
	protocol.addSetCommand("SetLED",
						   [](int param_c, char **param_v, long *result) {
							   if (param_c == 1)
							   {
								   long a = atoi(param_v[0]);
								   if (a >= 0 && a < 10)
								   {
									   LEDContr.setType(a);
									   return true;
								   }
							   }
							   return false;
						   });
	protocol.addGetCommand("GetWeight",
						   [](int param_c, char **param_v, long *result) {
							   (*result) = balance.getWeight();
							   return true;
						   });
	protocol.addGetCommand("HasGlas",
						   [](int param_c, char **param_v, long *result) {
							   (*result) = balance.getWeight() > GLASS_WEIGHT_MIN;
							   return true;
						   });
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

	addCommands();

	Wire.begin();
	//Wire.setClock(50000)
	//disable pullups for i2c
	digitalWrite(SCL, LOW);
	digitalWrite(SDA, LOW);

	if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C))
	{
		Serial.println("error");
		for (;;)
			yield();
	}
	state_m.begin();
}

void loop()
{
	state_m.update();
	yield();
}
