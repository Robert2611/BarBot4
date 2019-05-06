#ifndef BAR_BOT_H
#define BAR_BOT_H

#include "AccelStepper.h"
#include "LEDController.h"
#include "Configuration.h"
#include "BalanceBoard.h"

enum BarBotStatus_t{
	Idle,
	HomingRough,
	HomingRetract,
	HomingFine,
	MoveToDraft,
	Drafting,
	Stirring,
	Cleaning,
	MoveToStir,
	MoveToPos,
	Delay,
	Error,
	ErrorIngredientEmpty
};


extern "C" {
typedef void (*BarBotStatusChangedHandler) (BarBotStatus_t);
};

class StateMachine {
public:
	StateMachine(BalanceBoard* _balance);
	void begin();

	BarBotStatus_t status;
	long current_action_start_millis;
	long current_action_duration;
	byte current_action_index;

	BarBotStatusChangedHandler onStatusChanged;
	AccelStepper *stepper;
	LEDAnimator *leds;

	float position_in_mm();
	void update();

	void start_homing();
	void start_clean(int pump_index, float target_weight);
	void start_draft(int pump_index, long duration);
	void start_stir(long duration);
	void start_moveto(long position_in_mm);
	void start_delay(long duration);

	void set_max_speed(long speed);
	void set_max_accel(long accel);

	void reset_error();

private:
	void update_balance();
	bool is_homed();
	void start_pump(int pump_index, uint32_t power_pwm);
	void stop_pumps();
	void set_status(BarBotStatus_t new_status);
	float get_current_ingredient_position_in_mm();
	void set_target_position(long pos_in_mm);
	long mm_to_steps(float mm);
	int current_microstep;
	bool startup;
	BalanceBoard* balance;
	float weight_before_draft;
	float target_draft_weight;
	unsigned long balance_last_check_millis;
	unsigned long balance_last_data_millis;
};
#endif // ifndef BAR_BOT_H
