#ifndef BAR_BOT_H
#define BAR_BOT_H

#include "AccelStepper.h"
#include "LEDController.h"
#include "Configuration.h"
#include "BalanceBoard.h"
#include "MixerBoard.h"
#include "StrawBoard.h"
#include "CrusherBoard.h"
#include "MCP23X17.h"
#include "esp_bt_main.h"
#include "esp_bt_device.h"
#include "BluetoothSerial.h"

enum BarBotStatus_t
{
	Idle,
	HomingRough,
	HomingFine,
	MoveToDraft,
	Drafting,
	Mixing,
	MoveToClean,
	Cleaning,
	MoveToMixer,
	MoveToPos,
	Delay,
	SetBalanceLED,
	DispenseStraw,
	MoveToCrusher,
	CrushingIce,
	//errors
	Error = 32,
	ErrorIngredientEmpty,
	ErrorCommunicationToBalance,
	ErrorI2C,
	ErrorStrawsEmpty,
	ErrorGlasRemoved,
	ErrorMixingFailed,
};

extern "C"
{
	typedef void (*BarBotStatusChangedHandler)(BarBotStatus_t);
};

class StateMachine
{
public:
	StateMachine(BalanceBoard *, MixerBoard *, StrawBoard *, CrusherBoard *, MCP23X17 *, BluetoothSerial *);
	void begin();

	BarBotStatus_t status;
	byte pump_index;

	BarBotStatusChangedHandler onStatusChanged;
	AccelStepper *stepper;

	float position_in_mm();
	void update();
	void start_homing();
	void start_clean(int _pump_index, unsigned long _draft_time_millis);
	void start_draft(int _pump_index, float _draft_weight);
	void start_mixing(long duration);
	void start_moveto(long position_in_mm);
	void start_delay(long duration);
	void start_setBalanceLED(byte type);
	void start_dispense_straw();
	void start_crushing(float _ice_weight);
	void set_max_speed(float speed);
	void set_max_accel(float accel);
	void set_pump_power(byte percent);
	void reset_error();
	float get_last_draft_remaining_weight();
	bool is_started();
	int getDraftingPumpIndex();

private:
	bool is_homed();
	void start_pump(int pump_index, uint32_t power_pwm);
	void stop_pumps();
	void set_status(BarBotStatus_t new_status);
	float get_current_ingredient_position_in_mm();
	void set_target_position(long pos_in_mm);
	long mm_to_steps(float mm);
	void init_mcp();

	byte balance_LED_type;
	int current_microstep;
	bool startup;
	BalanceBoard *balance;
	MixerBoard *mixer;
	StrawBoard *straw_board;
	CrusherBoard *crusher;
	MCP23X17 *mcp;
	BluetoothSerial *bt;

	unsigned long child_last_check_millis;

	unsigned long current_action_start_millis;
	unsigned long current_action_duration;

	byte mixing_seconds;
	long delay_time;
	float weight_glas;
	float weight_before_draft;
	float target_draft_weight;
	unsigned long draft_timeout_last_check_millis;
	float draft_timeout_last_weight;
	bool dispense_straw_sent;
	bool mixer_start_sent;
	byte pump_power_percent;
};
#endif // ifndef BAR_BOT_H
