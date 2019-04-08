#ifndef BAR_BOT_H
#define BAR_BOT_H

#include "AccelStepper.h"
#include "LEDController.h"
#include "Configuration.h"





//STATUS
#define BAR_BOT_IDLE              0
#define BAR_BOT_HOMING_ROUGH      1
#define BAR_BOT_HOMING_RETRACT    2
#define BAR_BOT_HOMING_FINE       3
#define BAR_BOT_MOVETO_DRAFT      4
#define BAR_BOT_DRAFTING          5
#define BAR_BOT_STIRING           8
#define BAR_BOT_CLEANING          10
#define BAR_BOT_MOVETO_STIR_X     11
#define BAR_BOT_MOVETO_POS        12
#define BAR_BOT_DELAY             13
#define BAR_BOT_ERROR             255



extern "C" {
typedef void (*BarBotStatusChangedHandler) (int);
};

enum Z_Direction_t{
	UP,
	DOWN
};

class StateMachine {
public:
	StateMachine();
	void begin();

	int status;
	long current_action_start_millis;
	long current_action_duration;
	byte current_action_index;

	BarBotStatusChangedHandler onStatusChanged;
	AccelStepper *stepper;
	LEDController *leds;

	float position_in_mm();
	void update();

	void start_homing();
	void start_clean(int pump_index, long duration);
	void start_draft(int pump_index, long duration);
	void start_stir(long duration);
	void start_moveto(long position_in_mm);
	void start_delay(long duration);

	void set_max_speed(long speed);
	void set_max_accel(long accel);

private:
	bool is_homed();
	void start_pump(int pump_index, byte power_pwm);
	void stop_pumps();
	void set_status(int new_status);
	float get_current_ingredient_position_in_mm();
	bool stir_pos_reached(Z_Direction_t up_down);
	void set_target_position(long pos_in_mm);
	long mm_to_steps(float mm);
	int current_microstep;
	bool startup;
};
#endif // ifndef BAR_BOT_H
