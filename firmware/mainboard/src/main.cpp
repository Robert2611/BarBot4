#include "Arduino.h"
#include "BluetoothSerial.h"
#include "Protocol.h"
#include "Shared.h"
#include "LEDController.h"
#include "Wire.h"
#include "MCP23X17.h"

#include "Configuration.h"
#include "BalanceBoard.h"
#include "StrawBoard.h"
#include "StateMachine.h"
#include "CrusherBoard.h"

#define SERIAL_DEBUG

TaskHandle_t BluetoothTask;
TaskHandle_t LEDTask;

BluetoothSerial SerialBT;
BalanceBoard balance;
MixerBoard mixer;
StrawBoard straw_board;
CrusherBoard crusher_board;

SPIClass hspi(HSPI);
MCP23X17 mcp(PIN_IO_CS, &hspi);

StateMachine state_m(&balance, &mixer, &straw_board, &crusher_board, &mcp, &SerialBT);

Protocol protocol(&SerialBT);
LEDController LEDContr;

void DoLEDandBluetoothTask(void *parameters)
{
	for (;;)
	{
		if (state_m.is_started())
		{
			//only listen to commands when startup is done
			if (!protocol.acceptsCommands())
				protocol.setAcceptsCommand(true);
		}
		else
		{
			Serial.print("Starting (");
			Serial.print(state_m.status);
			Serial.println(")");
		}
		//always update
		protocol.update();

		//update LED controller
		LEDContr.setPlatformPosition(state_m.position_in_mm() + HOME_DISTANCE);
		LEDContr.setDraftPosition(HOME_DISTANCE + FIRST_PUMP_POSITION + PUMP_DISTANCE * state_m.get_drafting_pump_index());
		LEDContr.update();

		//make sure system tasks have time too
		delay(1);
	}
}

void addCommands()
{
	//test command that returns done after a defined time
	protocol.addDoCommand(
		"Delay",
		[](int param_c, char **param_v, long *result)
		{
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
		[](int *error_code, long *parameter)
		{
			if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else
				return CommandStatus_t::Running;
		});
	protocol.addDoCommand(
		"Draft",
		[](int param_c, char **param_v, long *result)
		{
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
		[](int *error_code, long *parameter)
		{
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
		"Crush",
		[](int param_c, char **param_v, long *result)
		{
			if (param_c == 1)
			{
				long w = atoi(param_v[0]);
				if (w > 0 && w < 400)
				{
					state_m.start_crushing(w);
					return true;
				}
			}
			return false;
		},
		[](int *error_code, long *parameter)
		{
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
		"Mix",
		[](int param_c, char **param_v, long *result)
		{
			if (param_c == 1)
			{
				long d = atol(param_v[0]);
				if (d > 0)
				{
					state_m.start_mixing(min(d, 255l));
					return true;
				}
			}
			return false;
		},
		[](int *error_code, long *parameter)
		{
			if (state_m.status > BarBotStatus_t::Error)
			{
				(*error_code) = state_m.status;
				(*parameter) = 0; //error code sensefull??
				state_m.reset_error();
				return CommandStatus_t::Error;
			}
			else if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else
				return CommandStatus_t::Running;
		});
	protocol.addDoCommand(
		"Clean",
		[](int param_c, char **param_v, long *result)
		{
			if (param_c == 2)
			{
				long index = atoi(param_v[0]);
				long time = atoi(param_v[1]);
				if (index >= 0 && index < DRAFT_PORTS_COUNT && time > 100 && time <= 10000)
				{
					state_m.start_clean(index, time);
					return true;
				}
			}
			return false;
		},
		[](int *error_code, long *parameter)
		{
			if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else
				return CommandStatus_t::Running;
		});
	protocol.addDoCommand(
		"Straw",
		[](int param_c, char **param_v, long *result)
		{
			if (param_c == 0)
			{
				state_m.start_dispense_straw();
				return true;
			}
			return false;
		},
		[](int *error_code, long *parameter)
		{
			if (state_m.status > BarBotStatus_t::Error)
			{
				(*error_code) = state_m.status;
				(*parameter) = 0; //error code sensefull??
				state_m.reset_error();
				return CommandStatus_t::Error;
			}
			else if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else
				return CommandStatus_t::Running;
		});
	protocol.addDoCommand(
		"Home",
		[](int param_c, char **param_v, long *result)
		{
			if (state_m.status == Idle)
			{
				state_m.start_homing();
				return true;
			}
			return false;
		},
		[](int *error_code, long *parameter)
		{
			if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else
				return CommandStatus_t::Running;
		});
	protocol.addDoCommand(
		"Move",
		[](int param_c, char **param_v, long *result)
		{
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
		[](int *error_code, long *parameter)
		{
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
	//PlatformLED needs to be sent via I2C in the main loop, so it must be a "Do" command
	protocol.addDoCommand(
		"PlatformLED",
		[](int param_c, char **param_v, long *result)
		{
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
		[](int *error_code, long *parameter)
		{
			if (state_m.status == BarBotStatus_t::Idle)
				return CommandStatus_t::Done;
			else if (state_m.status == BarBotStatus_t::SetBalanceLED)
				return CommandStatus_t::Running;
			else
			{
				(*error_code) = state_m.status;
				state_m.reset_error();
				return CommandStatus_t::Error;
			}
		});
	protocol.addSetCommand("SetSpeed",
						   [](int param_c, char **param_v, long *result)
						   {
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
	protocol.addSetCommand("SetAccel",
						   [](int param_c, char **param_v, long *result)
						   {
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
	protocol.addSetCommand("SetBalanceCalibration",
						   [](int param_c, char **param_v, long *result)
						   {
							   if (param_c == 1)
							   {
								   long cal = atol(param_v[0]);
								   if (cal != 0)
								   {
									   balance.setCalibration(cal);
									   return true;
								   }
							   }
							   return false;
						   });
	protocol.addSetCommand("SetBalanceOffset",
						   [](int param_c, char **param_v, long *result)
						   {
							   if (param_c == 1)
							   {
								   long offset = atol(param_v[0]);
								   balance.setOffset(offset);
								   return true;
							   }
							   return false;
						   });
	protocol.addSetCommand("SetPumpPower",
						   [](int param_c, char **param_v, long *result)
						   {
							   if (param_c == 1)
							   {
								   long a = atoi(param_v[0]);
								   if (a > 0 && a <= 100)
								   {
									   state_m.set_pump_power(a);
									   return true;
								   }
							   }
							   return false;
						   });
	protocol.addSetCommand("SetLED",
						   [](int param_c, char **param_v, long *result)
						   {
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
						   [](int param_c, char **param_v, long *result)
						   {
							   (*result) = (long)balance.getWeight();
							   return true;
						   });
	protocol.addGetCommand("HasGlas",
						   [](int param_c, char **param_v, long *result)
						   {
							   (*result) = balance.getWeight() > GLASS_WEIGHT_MIN;
							   return true;
						   });
	protocol.addGetCommand("GetConnectedBoards",
						   [](int param_c, char **param_v, long *result)
						   {
							   //TODO: Find a way to make synchronous I2C communication possible as this has to be called twice to work
							   state_m.start_pingAll();
							   (*result) = state_m.get_ping_result();
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
	xTaskCreatePinnedToCore(DoLEDandBluetoothTask, //Task function
							"LEDandBluetoothTask", //Task name
							10000,				   //stack depth
							NULL,				   //parameters
							1,					   //priority
							&BluetoothTask,		   //out: task handle
							0);					   //core

	addCommands();

	Wire.begin();
	//Wire.setClock(50000)
	//disable pullups for i2c
	digitalWrite(SCL, LOW);
	digitalWrite(SDA, LOW);
	hspi.begin();
	state_m.begin();
}

void loop()
{
	state_m.update();
	yield();
}
