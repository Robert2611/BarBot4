#include "StateMachine.h"

StateMachine::StateMachine(BalanceBoard *_balance, MixerBoard *_mixer, MCP23X17 *_mcp, Adafruit_SSD1306 *_display)
{
	this->balance = _balance;
	this->mixer = _mixer;
	this->mcp = _mcp;
	this->display = _display;
	startup = true;
	status = BarBotStatus_t::Idle;
	current_action_start_millis = 0;

	stepper = new AccelStepper(AccelStepper::DRIVER, PIN_PLATFORM_MOTOR_STEP, PIN_PLATFORM_MOTOR_DIR);
	//invert dir pin
	stepper->setPinsInverted(true);
	set_max_speed(100);
	set_max_accel(20);
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

	pinMode(PIN_IO_RESET, OUTPUT);
	pinMode(PIN_IO_CS, OUTPUT);

	init_mcp();

	mixer->StartMoveTop();
	set_status(BarBotStatus_t::MoveMixerUp);
}

void StateMachine::update()
{
	switch (status)
	{
	case BarBotStatus_t::Idle:
		update_balance();
		break;

	case BarBotStatus_t::Error:
	case BarBotStatus_t::ErrorIngredientEmpty:
	case BarBotStatus_t::ErrorCommunicationToBalance:
	case BarBotStatus_t::ErrorI2C:
		//nothing to do here
		break;

	case BarBotStatus_t::MoveMixerUp:
		if (mixer->IsAtTop())
		{
			if (startup)
				start_homing();
			else
				set_status(BarBotStatus_t::Idle);
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
		if (is_homed() || (current_microstep % PLATFORM_MOTOR_MICROSTEPS != 0))
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
			draft_timeout_last_check_millis = millis();
			//this is an old value!
			draft_timeout_last_weight = balance->getWeight();
			start_pump(pump_index, PUMP_POWER_PWM);
			set_status(BarBotStatus_t::Drafting);
		}
		else
		{
			stepper->run();
		}
		break;

	case BarBotStatus_t::Drafting:
		if (update_balance())
		{
			//Serial.println(get_last_draft_remaining_weight());
			if (balance->getWeight() > target_draft_weight)
			{
				//success
				stop_pumps();
				set_status(BarBotStatus_t::Idle);
			}
		}
		else if (millis() > balance_last_check_millis + DRAFT_TIMOUT_MILLIS)
		{
			//error
			stop_pumps();
			set_status(BarBotStatus_t::ErrorCommunicationToBalance);
		}
		//check for timeout
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
		//else just wait
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
				Serial.println("Move to Bottom");
			}
			else if (mixer->IsAtBottom())
			{
				Serial.println("At Bottom");
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
				Serial.println("At Bottom");
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
	}
}

bool StateMachine::update_balance()
{
	//ask for new data every 3 ms to avoid blocking the bus
	if (millis() > balance_last_check_millis + 3)
	{
		balance_last_check_millis = millis();
		//check if balance has new data
		if (balance->readData())
		{
			//balance class saves the data so no need to copy it here
			balance_last_data_millis = millis();
			//Serial.println(balance->getWeight());
			return true;
		}
	}
	return false;
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
	start_pump(_pump_index, PUMP_POWER_PWM);
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

///endregion: actions ///

///region: setters ///
void StateMachine::set_status(BarBotStatus_t new_status)
{
	if (new_status != status)
	{
		status = new_status;
		update_display();
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
///endregion: setters ///

///region: pump ///

void StateMachine::init_mcp()
{
	//initialize the mcp
	mcp->beginSPI(PIN_IO_CS);
	for (int i = 0; i < DRAFT_PORTS_COUNT; i++)
		mcp->pinMode(i, OUTPUT);
	mcp->writeGPIOBA(0);
	//reset off
	digitalWrite(PIN_IO_RESET, HIGH);
}

void StateMachine::start_pump(int _pump_index, uint32_t power_pwm)
{
	if (_pump_index < 0)
		mcp->writeGPIOBA(0);
	else
		mcp->writeGPIOBA(1 << _pump_index);
}

void StateMachine::stop_pumps()
{
	start_pump(-1, 0);
}
///endregion: pump ///

void StateMachine::update_display()
{
	display->clearDisplay();
	display->setTextSize(1);			  // Normal 1:1 pixel scale
	display->setTextColor(SSD1306_WHITE); // Draw white text
	display->setCursor(0, 0);			  // Start at top-left corner
	display->print("Status: ");
	display->print(StatusNames[status]);
	display->display();
}