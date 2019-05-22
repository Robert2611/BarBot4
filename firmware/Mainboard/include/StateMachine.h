#ifndef BAR_BOT_H
#define BAR_BOT_H

#include "AccelStepper.h"
#include "LEDController.h"
#include "Configuration.h"
#include "BalanceBoard.h"

enum BarBotStatus_t
{
	Idle,
	HomingRough,
	HomingFine,
	MoveToDraft,
	Drafting,
	Stirring,
	Cleaning,
	MoveToStir,
	MoveToPos,
	Delay,
	Error,
	ErrorIngredientEmpty,
	ErrorCommunicationToBalance
};

extern "C"
{
	typedef void (*BarBotStatusChangedHandler)(BarBotStatus_t);
};

class StateMachine
{
public:
	StateMachine(BalanceBoard *_balance);
	void begin();

	BarBotStatus_t status;
	byte pump_index;

	BarBotStatusChangedHandler onStatusChanged;
	AccelStepper *stepper;
	LEDAnimator *leds;

	float position_in_mm();
	void update();

	void start_homing();
	void start_clean(int _pump_index, unsigned long _draft_time_millis);
	void start_draft(int _pump_index, float _draft_weight);
	void start_stir(long duration);
	void start_moveto(long position_in_mm);
	void start_delay(long duration);

	void set_max_speed(float speed);
	void set_max_accel(float accel);

	void reset_error();

	float get_last_draft_remaining_weight();

private:
	bool update_balance();
	bool is_homed();
	void start_pump(int pump_index, uint32_t power_pwm);
	void stop_pumps();
	void set_status(BarBotStatus_t new_status);
	float get_current_ingredient_position_in_mm();
	void set_target_position(long pos_in_mm);
	long mm_to_steps(float mm);
	int current_microstep;
	bool startup;
	BalanceBoard *balance;

	unsigned long balance_last_check_millis;
	unsigned long balance_last_data_millis;
	unsigned long current_action_start_millis;
	unsigned long current_action_duration;

	long stirring_time;
	long delay_time;
	float weight_glas;
	float weight_before_draft;
	float target_draft_weight;
	unsigned long draft_timeout_last_check_millis;
	float draft_timeout_last_weight;

};
#endif // ifndef BAR_BOT_H
