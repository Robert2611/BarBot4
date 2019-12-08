#include "StateMachine.h"

StateMachine::StateMachine(BalanceBoard *_balance, MixerBoard *_mixer, StrawBoard *_straw_board, MCP23X17 *_mcp, BluetoothSerial *_bt)
{
	this->balance = _balance;
	this->mixer = _mixer;
	this->straw_board = _straw_board;
	this->mcp = _mcp;
	this->bt = _bt;
	startup = true;
	status = BarBotStatus_t::Idle;
	current_action_start_millis = 0;

	stepper = new AccelStepper(AccelStepper::DRIVER, PIN_PLATFORM_MOTOR_STEP, PIN_PLATFORM_MOTOR_DIR);
	//invert dir pin
	stepper->setPinsInverted(true);
	set_max_speed(100);
	set_max_accel(20);
	set_pump_power(80);
	balance->setCalibration(-1040);
	balance->setOffset(-123865);
}

void StateMachine::begin()
{
	pinMode(PIN_PLATFORM_MOTOR_HOME, INPUT);
	pinMode(PIN_PLATFORM_MOTOR_EN, OUTPUT);
	//enable motor
	digitalWrite(PIN_PLATFORM_MOTOR_EN, LOW);

	pinMode(PIN_BUTTON, INPUT);
	pinMode(PIN_CRUSHER_SENSE, INPUT);
	pinMode(PIN_SERVO, OUTPUT);
	pinMode(PIN_LED, OUTPUT);

	//initialize PWM for the pump on channel 0 with 10 bit resolution and 5kHz
	ledcSetup(LEDC_CHANNEL_PUMP, PUMP_POWER_FREQUENCY, 10);
	ledcAttachPin(PIN_PUMP_ENABLED, LEDC_CHANNEL_PUMP);
	ledcWrite(LEDC_CHANNEL_PUMP, 0);

	init_mcp();

	move_mixer_up_sent = false;
	set_status(BarBotStatus_t::MoveMixerUp);
	while (!mixer->StartMoveTop())
	{
		delay(100);
	}
	move_mixer_up_sent = true;
}

void StateMachine::update()
{
	switch (status)
	{
	case BarBotStatus_t::Idle:
		// we do not check for any errors here!
		balance->update();
		break;

	case BarBotStatus_t::Error:
	case BarBotStatus_t::ErrorIngredientEmpty:
	case BarBotStatus_t::ErrorI2C:
	case BarBotStatus_t::ErrorStrawsEmpty:
	case BarBotStatus_t::ErrorGlasRemoved:
	case BarBotStatus_t::ErrorCommunicationToBalance:
		//nothing to do here
		break;

	case BarBotStatus_t::MoveMixerUp:
		if (!move_mixer_up_sent)
		{
			//only set the flag if the sending actually worke
			if (mixer->StartMoveTop())
			{
				move_mixer_up_sent = true;
			}
		}
		else
		{
			if (mixer->IsAtTop())
			{
				if (startup)
					start_homing();
				else
					set_status(BarBotStatus_t::Idle);
			}
		}
		break;
	/** HOMING START **/
	case BarBotStatus_t::HomingRough:
		if (!is_homed())
		{
			stepper->run();
			current_microstep--;
		}
		else
		{
			stepper->setCurrentPosition(0);
			stepper->setSpeed(PLATFORM_MOTOR_HOMING_SPEED * PLATFORM_MOTOR_MICROSTEPS);
			set_target_position(100);
			set_status(BarBotStatus_t::HomingFine);
		}
		break;

	case BarBotStatus_t::HomingFine:
		//move to fulls step position, so pos = 0 is full step!
		if ((current_microstep % PLATFORM_MOTOR_MICROSTEPS != 0) || is_homed())
		{
			stepper->runSpeed();
			current_microstep++;
		}
		else
		{
			stepper->setCurrentPosition(0);
			stepper->setSpeed(0);
			set_target_position(0);
			set_status(BarBotStatus_t::Idle);
			if (startup)
				startup = false;
		}
		break;

		/** HOMING END **/

	case BarBotStatus_t::MoveToPos:
		if (stepper->currentPosition() == stepper->targetPosition())
		{
			//x-position is reached
			set_status(BarBotStatus_t::Idle);
		}
		else
			stepper->run();
		break;

	case BarBotStatus_t::Delay:
		if (millis() > (unsigned long)(current_action_start_millis + delay_time))
			set_status(BarBotStatus_t::Idle);
		break;

	case BarBotStatus_t::MoveToDraft:
		if (stepper->currentPosition() == stepper->targetPosition())
		{
			//draft position is reached
			//get new weight from the balance or throw error
			BalanceUpdateResult_t res = balance->update();
			//TODO: read until weight is stable
			if (res == Balance_DataRead)
			{
				if (balance->getWeight() > GLASS_WEIGHT_MIN)
				{
					draft_timeout_last_check_millis = millis();
					draft_timeout_last_weight = balance->getWeight();
					start_pump(pump_index, (pump_power_percent * 1024) / 100);
					set_status(BarBotStatus_t::Drafting);
				}
				else
				{
					set_status(BarBotStatus_t::ErrorGlasRemoved);
				}
			}
			else if (res == Balance_CommunicationError)
				set_status(BarBotStatus_t::ErrorI2C);
			else if (res == Balance_Timeout)
				set_status(BarBotStatus_t::ErrorCommunicationToBalance);
		}
		else
		{
			stepper->run();
		}
		break;

	case BarBotStatus_t::Drafting:
	{
		//new data avaiable?
		BalanceUpdateResult_t res = balance->update();
		if (res == Balance_DataRead)
		{
			//Serial.println(get_last_draft_remaining_weight());
			if (balance->getWeight() > target_draft_weight)
			{
				//success
				stop_pumps();
				set_status(BarBotStatus_t::Idle);
			}
			else if (millis() > draft_timeout_last_check_millis + DRAFT_TIMOUT_MILLIS)
			{
				if (balance->getWeight() < draft_timeout_last_weight + DRAFT_TIMOUT_WEIGHT)
				{
					//error
					stop_pumps();
					set_status(BarBotStatus_t::ErrorIngredientEmpty);
				}
				else
				{
					//reset the timeout
					draft_timeout_last_check_millis = millis();
					draft_timeout_last_weight = balance->getWeight();
				}
			}
		}
		//forward i2c error
		else if (res == Balance_CommunicationError)
		{
			stop_pumps();
			set_status(BarBotStatus_t::ErrorI2C);
		}
		//forward timeout
		else if (res == Balance_Timeout)
		{
			stop_pumps();
			set_status(BarBotStatus_t::ErrorCommunicationToBalance);
		}
		//else just wait
	}
	break;

	case BarBotStatus_t::Cleaning:
		if (millis() > current_action_start_millis + current_action_duration)
		{
			stop_pumps();
			set_status(BarBotStatus_t::Idle);
		}
		break;

	case BarBotStatus_t::MoveToStir:
		if (stepper->currentPosition() == stepper->targetPosition())
		{
			//x-position is reached
			if (mixer->GetTargetPosition() != MIXER_POSITION_BOTTOM)
			{
				mixer->StartMoveBottom();
			}
			else if (mixer->IsAtBottom())
			{
				current_action_start_millis = millis();
				mixer->StartMixing();
				set_status(BarBotStatus_t::Stirring);
			}
		}
		else
		{
			stepper->run();
		}
		break;

	case BarBotStatus_t::Stirring:
		if (millis() > (unsigned long)(current_action_start_millis + stirring_time))
		{
			if (mixer->IsMixing())
			{
				mixer->StopMixing();
			}
			else if (mixer->GetTargetPosition() != MIXER_POSITION_TOP)
			{ //stopped but movement not yet triggered
				if (!mixer->StartMoveTop())
				{
					set_status(BarBotStatus_t::ErrorI2C);
				}
			}
			else if (mixer->IsAtTop()) //stopped, movement triggered, top position reached
				set_status(BarBotStatus_t::Idle);
			//else: top position not reached yet -> do nothing
		}
		break;

	case BarBotStatus_t::SetBalanceLED:
		if (balance->setLEDType(balance_LED_type))
			set_status(BarBotStatus_t::Idle);
		else
			set_status(BarBotStatus_t::ErrorI2C);
		break;

	case BarBotStatus_t::DispenseStraw:
		if (!dispense_straw_sent)
		{
			//tell the board to start the dispensing
			if (straw_board->StartDispense())
			{
				current_action_start_millis = millis();
				child_last_check_millis = millis();
				dispense_straw_sent = true;
			}
			else
			{
				set_status(BarBotStatus_t::ErrorI2C);
			}
		}
		else if (millis() > child_last_check_millis + CHILD_UPDATE_PERIOD)
		{
			//check if dispensing is done yet
			if (!straw_board->IsDispensing())
			{
				if (straw_board->IsError())
				{
					set_status(BarBotStatus_t::ErrorStrawsEmpty);
				}
				else
				{
					set_status(BarBotStatus_t::Idle);
				}
			}
			else
			{
				child_last_check_millis = millis();
			}
			//TODO: implement timeout
		}
		break;
	}
}

///region: getters ///
bool StateMachine::is_homed()
{
	//read two times to be sure...
	return digitalRead(PIN_PLATFORM_MOTOR_HOME) && digitalRead(PIN_PLATFORM_MOTOR_HOME);
}

bool StateMachine::is_started()
{
	return !startup;
}

long StateMachine::mm_to_steps(float mm)
{
	//round to full steps to avoid stop in PLATFORM_MOTOR_MICROSTEPS
	return (long)(PLATFORM_MOTOR_MICROSTEPS * round(PLATFORM_MOTOR_FULLSTEPS_PER_MM * mm));
}

float StateMachine::position_in_mm()
{
	return (float)stepper->currentPosition() / (PLATFORM_MOTOR_MICROSTEPS * PLATFORM_MOTOR_FULLSTEPS_PER_MM);
}

float StateMachine::get_last_draft_remaining_weight()
{
	return target_draft_weight - balance->getWeight();
}
///endregion: getters ///

///region: actions ///
void StateMachine::start_clean(int _pump_index, unsigned long _draft_time_millis)
{
	current_action_start_millis = millis();
	current_action_duration = _draft_time_millis;
	start_pump(pump_index, (pump_power_percent * 1024) / 100);
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::Cleaning);
}

void StateMachine::start_homing()
{
	current_microstep %= PLATFORM_MOTOR_MICROSTEPS;
	set_target_position(-2000);
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::HomingRough);
}

void StateMachine::start_draft(int _pump_index, float target_weight)
{
	pump_index = _pump_index;
	weight_before_draft = balance->getWeight();
	target_draft_weight = weight_before_draft + target_weight;
	Serial.print("target_draft_weight = ");
	Serial.println(target_draft_weight);
	set_target_position(FIRST_PUMP_POSITION + PUMP_DISTANCE * _pump_index);

	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::MoveToDraft);
}

void StateMachine::start_stir(long duration)
{
	//move to stirring position
	stirring_time = duration;
	set_target_position(STIRRING_POSITION);
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::MoveToStir);
}

void StateMachine::start_delay(long duration)
{
	current_action_start_millis = millis();
	delay_time = duration;
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::Delay);
}

void StateMachine::start_moveto(long position_in_mm)
{
	set_target_position(position_in_mm);
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::MoveToPos);
}

void StateMachine::start_setBalanceLED(byte type)
{
	balance_LED_type = type;
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::SetBalanceLED);
}

void StateMachine::start_dispense_straw()
{
	dispense_straw_sent = false;
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::DispenseStraw);
}

///endregion: actions ///

///region: setters ///
void StateMachine::set_status(BarBotStatus_t new_status)
{
	if (new_status != status)
	{
		status = new_status;
		if (onStatusChanged != NULL)
			onStatusChanged(status);
	}
}

void StateMachine::reset_error()
{
	if (status > BarBotStatus_t::Error)
	{
		set_status(BarBotStatus_t::Idle);
	}
}

void StateMachine::set_target_position(long position_in_mm)
{
	if (position_in_mm > PLATFORM_MOTOR_MAXPOS_MM)
		position_in_mm = PLATFORM_MOTOR_MAXPOS_MM;
	long steps = mm_to_steps(position_in_mm);
	stepper->moveTo(steps);
}

void StateMachine::set_max_speed(float speed)
{
	stepper->setMaxSpeed(mm_to_steps(speed));
}

void StateMachine::set_max_accel(float accel)
{
	stepper->setAcceleration(mm_to_steps(accel));
}

void StateMachine::set_pump_power(byte percent)
{
	pump_power_percent = percent;
}
///endregion: setters ///

///region: pump ///

void StateMachine::init_mcp()
{
	pinMode(PIN_IO_RESET, OUTPUT);
	//reset off
	digitalWrite(PIN_IO_RESET, HIGH);
	//initialize the mcp
	mcp->begin();
	if (mcp->readRegister(MCP23X17_IODIRA) != 0xFF)
		Serial.println("Initializing MCP failed");

	//A0 to A7 are used by pumps, so make them all outputs
	mcp->writeRegister(MCP23X17_IODIRA, 0b00000000);
	//B0 to B3 are pumps, the rest is unused, so leave it as input
	mcp->writeRegister(MCP23X17_IODIRB, 0b11110000);
	stop_pumps();
}

void StateMachine::start_pump(int _pump_index, uint32_t power_pwm)
{
	if (_pump_index < 0 || _pump_index >= DRAFT_PORTS_COUNT)
	{
		stop_pumps();
		return;
	}
	uint16_t pos = 0;
	bitWrite(pos, _pump_index % 8, 1);
	ledcWrite(LEDC_CHANNEL_PUMP, power_pwm);
	//set only the bit associated with
	mcp->writeRegister(MCP23X17_GPIOA, _pump_index < 8 ? pos : 0);
	mcp->writeRegister(MCP23X17_GPIOB, _pump_index < 8 ? 0 : pos);
}

void StateMachine::stop_pumps()
{
	ledcWrite(LEDC_CHANNEL_PUMP, 0);
	//all outputs off
	mcp->writeRegister(MCP23X17_GPIOA, 0);
	mcp->writeRegister(MCP23X17_GPIOB, 0);
}
///endregion: pump ///

int StateMachine::getDraftingPumpIndex()
{
	if (status == MoveToDraft || status == Drafting)
		return pump_index;
	else
		return -1;
}