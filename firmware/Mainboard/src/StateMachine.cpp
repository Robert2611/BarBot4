#include "StateMachine.h"

StateMachine::StateMachine(BalanceBoard *_balance)
{
	this->balance = _balance;
	startup = true;
	status = BarBotStatus_t::Idle;
	current_action_start_millis = 0;
	current_action_duration = 0;
	current_action_index = 0;

	stepper = new AccelStepper(AccelStepper::DRIVER, PIN_PLATFORM_MOTOR_STEP, PIN_PLATFORM_MOTOR_DIR);
	//leds = new LEDController(LED_R, LED_G, LED_B);
	set_max_speed(mm_to_steps(100));
	set_max_accel(mm_to_steps(20));
}

void StateMachine::begin()
{
	pinMode(PIN_PLATFORM_MOTOR_HOME, INPUT_PULLUP);

	pinMode(PIN_PUMP_SERIAL_DATA, OUTPUT);
	pinMode(PIN_PUMP_NOT_ENABLED, OUTPUT);
	pinMode(PIN_PUMP_SERIAL_RCLK, OUTPUT);
	pinMode(PIN_PUMP_SERIAL_SCLK, OUTPUT);

	//initialize PWM chanel for the pump
	ledcSetup(LEDC_CHANNEL_PUMP, 5000, 10);
	ledcAttachPin(PIN_PUMP_NOT_ENABLED, LEDC_CHANNEL_PUMP);

	stop_pumps();

	//stepper->setPinsInverted(true, true); //invert (dir?,step?,enable?)
	//stepper->setMaxSpeed(options->max_speed * PLATFORM_MOTOR_MICROSTEPS);
	//stepper->setAcceleration(options->max_accel * PLATFORM_MOTOR_MICROSTEPS);

	//leds->begin();
	//TODO: Make sure stirring device is out of the way
	if (false)
		start_homing();
}

void StateMachine::update()
{
	update_balance();
	switch (status)
	{
	case BarBotStatus_t::Idle:
	case BarBotStatus_t::Error:
	case BarBotStatus_t::ErrorIngredientEmpty:
		//nothing to do here
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
			set_status(BarBotStatus_t::HomingFine);
			stepper->setCurrentPosition(0);
			stepper->setSpeed(PLATFORM_MOTOR_HOMING_SPEED * PLATFORM_MOTOR_MICROSTEPS);
			set_target_position(100);
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
		if (millis() > (unsigned long)(current_action_start_millis + current_action_duration))
			set_status(BarBotStatus_t::Idle);
		break;

	case BarBotStatus_t::MoveToDraft:
		if (stepper->currentPosition() == stepper->targetPosition())
		{
			//x-position is reached
			set_status(BarBotStatus_t::Drafting);
			current_action_start_millis = millis();
			start_pump(current_action_index, PUMP_POWER_PWM);
		}
		else
		{
			stepper->run();
		}
		break;

	case BarBotStatus_t::Drafting:
		if (millis() > (unsigned long)(current_action_start_millis + current_action_duration))
		{
			stop_pumps();
			set_status(BarBotStatus_t::Idle);
		}
		break;

	case BarBotStatus_t::Cleaning:
		if (balance->getWeight() >= weight_before_draft + target_draft_weight)
		{
			stop_pumps();
			set_status(BarBotStatus_t::Idle);
		}
		break;

	case BarBotStatus_t::MoveToStir:
		if (stepper->currentPosition() == stepper->targetPosition())
			//x-position is reached
			yield();
		else
			stepper->run();
		break;

	case BarBotStatus_t::Stirring:
		//draft-duration is interpreted as stirring duration
		if (millis() > (unsigned long)(current_action_start_millis + current_action_duration))
		{
			//stop stirring
		}
		break;
	}
	//leds->update();
}

void StateMachine::update_balance()
{
	//ask for new data every 3 ms to avoid blocking the bus
	if (millis() > balance_last_check_millis + 3)
	{
		balance_last_check_millis = millis();
		//check if balance has new data
		if (balance->readData())
		{			
			balance_last_data_millis = millis();
			//balance class saves the data so no need to copy it here

			//print the recieved weight on serial if debug was defined
			Serial.println(balance->getWeight());			
		}
	}
}

///region: getters ///
bool StateMachine::is_homed()
{
	//read two times to be sure...
	return digitalRead(PIN_PLATFORM_MOTOR_HOME) && digitalRead(PIN_PLATFORM_MOTOR_HOME);
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
///endregion: getters ///

///region: actions ///
void StateMachine::start_clean(int pump_index, float target_weight)
{
	current_action_start_millis = millis();
	float weight = balance->getWeight();
	if (weight > TOTAL_WEIGHT_MAX)
		return;
	weight_before_draft = weight;
	target_draft_weight = target_weight;
	start_pump(pump_index, PUMP_POWER_PWM);
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

void StateMachine::start_draft(int pump_index, long duration)
{
	current_action_index = pump_index;
	current_action_duration = duration;
	set_target_position(FIRST_PUMP_POSITION + PUMP_DISTANCE * pump_index);
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::Drafting);
}

void StateMachine::start_stir(long duration)
{
	//move to stirring position
	current_action_duration = duration;	
	set_target_position(STIRRING_POSITION);
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::MoveToStir);
}

void StateMachine::start_delay(long duration)
{
	current_action_start_millis = millis();
	current_action_duration = duration;
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::Delay);
}

void StateMachine::start_moveto(long position_in_mm)
{
	set_target_position(position_in_mm);
	//status has to be set last to avoid multi core problems
	set_status(BarBotStatus_t::MoveToPos);
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

void StateMachine::reset_error(){
	if(status > BarBotStatus_t::Error){
		set_status(BarBotStatus_t::Idle);
	}
}

void StateMachine::set_target_position(long position_in_mm)
{
	if (position_in_mm > PLATFORM_MOTOR_MAXPOS_MM)
		position_in_mm = PLATFORM_MOTOR_MAXPOS_MM;
	long steps = mm_to_steps(position_in_mm);
	Serial.println(steps);
	stepper->moveTo(steps);
}

void StateMachine::set_max_speed(long speed)
{
	stepper->setMaxSpeed(speed * PLATFORM_MOTOR_MICROSTEPS);
}

void StateMachine::set_max_accel(long accel)
{
	stepper->setAcceleration(accel * PLATFORM_MOTOR_MICROSTEPS);
}
///endregion: setters ///

///region: pump ///
void StateMachine::start_pump(int pump_index, uint32_t power_pwm)
{
	//no output while writing
	ledcWrite(LEDC_CHANNEL_PUMP, 0);

	//write serial data to pump board
	digitalWrite(PIN_PUMP_SERIAL_RCLK, LOW);
	int inverted_index = 11 - pump_index;
	for (int byte_index = 1; byte_index >= 0; byte_index--)
	{
		for (int i = 0; i < 8; i++)
		{
			byte bit_index = byte_index * 8 + i;
			digitalWrite(PIN_PUMP_SERIAL_SCLK, LOW);
			digitalWrite(PIN_PUMP_SERIAL_DATA, bit_index == inverted_index);
			digitalWrite(PIN_PUMP_SERIAL_SCLK, HIGH);
			digitalWrite(PIN_PUMP_SERIAL_SCLK, LOW);
		}
	}
	digitalWrite(PIN_PUMP_SERIAL_RCLK, HIGH);
	digitalWrite(PIN_PUMP_SERIAL_DATA, LOW);
	delay(50);
	//inverted output, because the enabled pin low active
	if (pump_index >= 0 && pump_index < DRAFT_PORTS_COUNT && power_pwm > 0)
		ledcWrite(LEDC_CHANNEL_PUMP, power_pwm);
}

void StateMachine::stop_pumps()
{
	start_pump(-1, 0);
}
///endregion: pump ///