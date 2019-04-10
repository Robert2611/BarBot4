#include "StateMachine.h"

StateMachine::StateMachine()
{
	return;
	startup = true;
	status = BAR_BOT_IDLE;
	current_action_start_millis = 0;
	current_action_duration = 0;
	current_action_index = 0;

	stepper = new AccelStepper(AccelStepper::DRIVER, X_MOTOR_STEP, X_MOTOR_DIR);
	//leds = new LEDController(LED_R, LED_G, LED_B);
	set_max_speed(1800);
	set_max_accel(800);
}

void StateMachine::start_clean(int pump_index, long duration)
{
	current_action_start_millis = millis();
	start_pump(pump_index, PUMP_POWER_PWM);
	current_action_duration = duration;
	set_status(BAR_BOT_CLEANING);
}


void StateMachine::start_draft(int pump_index, long duration)
{
	current_action_index = pump_index;
	current_action_duration = duration;
	set_status(BAR_BOT_MOVETO_DRAFT);
	set_target_position(FIRST_PUMP_POSITION + PUMP_DISTANCE * pump_index);
}

void StateMachine::begin()
{
	return;
	pinMode(X_MOTOR_HOME, INPUT_PULLUP);

	pinMode(PUMP_SERIAL_DATA, OUTPUT);
	pinMode(PUMP_NOT_ENABLED, OUTPUT);
	pinMode(PUMP_SERIAL_RCLK, OUTPUT);
	pinMode(PUMP_SERIAL_SCLK, OUTPUT);

	//stop_pumps();

	//stepper->setPinsInverted(true, true); //invert (dir?,step?,enable?)
	//stepper->setMaxSpeed(options->max_speed * MICROSTEPS);
	//stepper->setAcceleration(options->max_accel * MICROSTEPS);

	//leds->begin();
    //TODO: Make sure stirring device is out of the way
	if (false)
		start_homing();
}

bool StateMachine::is_homed()
{
	//read two times to be sure...
	return digitalRead(X_MOTOR_HOME) && digitalRead(X_MOTOR_HOME);
}

long StateMachine::mm_to_steps(float mm)
{
	//round to full steps to avoid stop in microsteps
	return (long)(MICROSTEPS * round(FULLSTEPS_PER_MM * mm));
}

float StateMachine::position_in_mm()
{
	return (float)stepper->currentPosition() / (MICROSTEPS * FULLSTEPS_PER_MM);
}

void StateMachine::start_homing()
{
	current_microstep %= MICROSTEPS;
	set_target_position(-2000);
	set_status(BAR_BOT_HOMING_ROUGH);
}

void StateMachine::set_status(int new_status)
{
	if (new_status != status) {
		status = new_status;
		if (onStatusChanged != NULL)
			onStatusChanged(status);
	}
}

void StateMachine::start_stir(long duration)
{
	//move to stirring position
	current_action_duration = duration;
	set_status(BAR_BOT_MOVETO_STIR_X);
	set_target_position(STIRRING_POSITION);
}

void StateMachine::set_target_position(long position_in_mm)
{
	if (position_in_mm > MAX_X_POS_MM)
		position_in_mm = MAX_X_POS_MM;
	stepper->moveTo(mm_to_steps(position_in_mm));
}

void StateMachine::start_moveto(long position_in_mm)
{
	set_status(BAR_BOT_MOVETO_POS);
	set_target_position(position_in_mm);
}

void StateMachine::start_delay(long duration)
{
	current_action_start_millis = millis();
	current_action_duration = duration;
	set_status(BAR_BOT_DELAY);
}

void StateMachine::update()
{
	switch (status) {
	/** HOMING START **/
	case BAR_BOT_HOMING_ROUGH:
		if (!is_homed()) {
			stepper->run();
			current_microstep--;
		} else {
			set_status(BAR_BOT_HOMING_FINE);
			stepper->setCurrentPosition(0);
			stepper->setSpeed(HOME_SPEED * MICROSTEPS);
			set_target_position(100);
		}
		break;

	case BAR_BOT_HOMING_FINE:
		//move to fulls step position, so pos = 0 is full step!
		if (is_homed() || (current_microstep % MICROSTEPS != 0)) {
			stepper->runSpeed();
			current_microstep++;
		} else {
			stepper->setCurrentPosition(0);
			stepper->setSpeed(0);
			set_target_position(0);
			set_status(BAR_BOT_IDLE);
			if (startup)
				startup = false;
		}
		break;

	/** HOMING END **/

	case BAR_BOT_MOVETO_POS:
		if (stepper->currentPosition() == stepper->targetPosition())
			//x-position is reached
			set_status(BAR_BOT_IDLE);
		else
			stepper->run();
		break;

	case BAR_BOT_DELAY:
		if (millis() > (unsigned long)(current_action_start_millis + current_action_duration))
			set_status(BAR_BOT_IDLE);
		break;

	case BAR_BOT_MOVETO_DRAFT:
		if (stepper->currentPosition() == stepper->targetPosition()) {
			//x-position is reached
			set_status(BAR_BOT_DRAFTING);
			current_action_start_millis = millis();
			start_pump(current_action_index, PUMP_POWER_PWM);
		} else {
			stepper->run();
		}
		break;

	case BAR_BOT_DRAFTING:
		if (millis() > (unsigned long)(current_action_start_millis + current_action_duration)) {
			stop_pumps();
			set_status(BAR_BOT_IDLE);
		}
		break;

	case BAR_BOT_CLEANING:
		if (millis() > (unsigned long)(current_action_start_millis + current_action_duration)) {
			stop_pumps();
			set_status(BAR_BOT_IDLE);
		}
		break;

	case BAR_BOT_MOVETO_STIR_X:
		if (stepper->currentPosition() == stepper->targetPosition())
			//x-position is reached
            yield();
		else
			stepper->run();
		break;

	case BAR_BOT_STIRING:
		//draft-duration is interpreted as stirring duration
		if (millis() > (unsigned long)(current_action_start_millis + current_action_duration)) {
			//stop stirring
		}
		break;
	}
	//leds->update();
}

void StateMachine::set_max_speed(long speed)
{
	stepper->setMaxSpeed(speed * MICROSTEPS);
}

void StateMachine::set_max_accel(long accel)
{
	stepper->setAcceleration(accel * MICROSTEPS);
}

void StateMachine::start_pump(int pump_index, byte power_pwm)
{
	//no output while writing
	digitalWrite(PUMP_NOT_ENABLED, HIGH);

	//write serial data to pump board
	digitalWrite(PUMP_SERIAL_RCLK, LOW);
	int inverted_index = 11 - pump_index;
	for (int byte_index = 1; byte_index >= 0; byte_index--) {
		for (int i = 0; i < 8; i++) {
			byte bit_index = byte_index * 8 + i;
			digitalWrite(PUMP_SERIAL_SCLK, LOW);
			digitalWrite(PUMP_SERIAL_DATA, bit_index == inverted_index);
			digitalWrite(PUMP_SERIAL_SCLK, HIGH);
			digitalWrite(PUMP_SERIAL_SCLK, LOW);
		}
	}
	digitalWrite(PUMP_SERIAL_RCLK, HIGH);
	digitalWrite(PUMP_SERIAL_DATA, LOW);
	delay(50);
	//inverted output, because the enabled pin low active
	if (pump_index >= 0 && pump_index < 12 && power_pwm > 0)
		digitalWrite(PUMP_NOT_ENABLED, LOW);
	//analogWrite(PUMP_NOT_ENABLED, 255 - power_pwm);
}

void StateMachine::stop_pumps()
{
	start_pump(-1, 0);
}
