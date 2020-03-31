#ifndef LEDCONTROLLER_H
#define LEDCONTROLLER_H

#include "Shared.h"
#include "Arduino.h"
#include "NeoPixelBus.h"

#define BALANCE_LED_PIXEL_COUNT 24

class LEDController
{
public:
	LEDController(int data_pin);
	void begin();
	void update(bool force = false);
	void setType(byte type);

private:
	int data_pin;
	int type;
	unsigned long last_change;
	int frame;
	unsigned long frame_start_millis;
	NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod> *stripe;
};

#endif
